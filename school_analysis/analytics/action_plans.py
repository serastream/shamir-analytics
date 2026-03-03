import streamlit as st
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict

# =====================================================================
# Конфигурации
# =====================================================================

@dataclass
class StudentPlanConfig:
    max_tasks_per_student: int = 3
    weak_threshold: int = 50
    min_gain_pp: int = 10


@dataclass
class TeacherGoalConfig:
    min_gain_pp: int = 7
    hard_target_cap: int = 85
    risk_share_reduction_pp: int = 10


# =====================================================================
# Вспомогательные функции
# =====================================================================

def _safe_percent(x):
    try:
        return float(x)
    except Exception:
        return np.nan


def _ensure_cols(df, cols):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Отсутствуют обязательные колонки: {missing}")


# =====================================================================
# Генерация задач
# =====================================================================

def generate_student_tasks(df: pd.DataFrame, month_id: int,
                           cfg: StudentPlanConfig = StudentPlanConfig(),
                           scope_filter: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    required = ['student', 'subject', 'task_name', 'task_percent']
    _ensure_cols(df, required)

    dff = df.copy()
    dff['task_percent'] = dff['task_percent'].map(_safe_percent)

    if scope_filter:
        for k, v in scope_filter.items():
            if k in dff.columns:
                dff = dff[dff[k] == v]

    avg_df = (
        dff.groupby(['student', 'subject', 'task_name'], as_index=False)['task_percent']
        .mean().rename(columns={'task_percent': 'avg_percent'})
    )

    weak = avg_df[avg_df['avg_percent'] < 33].copy()
    if weak.empty:
        return pd.DataFrame(columns=['student', 'class', 'subject', 'task_name', 'baseline', 'target', 'rationale'])

    weak['baseline'] = weak['avg_percent']
    weak['target'] = np.clip(weak['baseline'] + cfg.min_gain_pp, 0, 100)
    weak['rationale'] = "устойчиво низкий результат (<33%)"

    if 'class' in df.columns:
        weak = weak.merge(df[['student', 'class']].drop_duplicates(), on='student', how='left')

    return weak[['student', 'class', 'subject', 'task_name', 'baseline', 'target', 'rationale']]


def generate_teacher_goals(df: pd.DataFrame, month_id: int,
                           cfg: TeacherGoalConfig,
                           by='class',
                           prev_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    _ensure_cols(df, ['subject', 'task_percent'])
    df = df.copy()
    df['task_percent'] = df['task_percent'].map(_safe_percent)

    # --- Текущий месяц ---
    baseline = (
        df.groupby(['subject', by], as_index=False)['task_percent']
        .mean().rename(columns={'task_percent': 'baseline_avg'})
    )

    # --- Добавляем динамику, если есть данные за прошлый месяц ---
    if prev_df is not None and not prev_df.empty:
        prev_df = prev_df.copy()
        prev_df['task_percent'] = prev_df['task_percent'].map(_safe_percent)
        prev_avg = (
            prev_df.groupby(['subject', by], as_index=False)['task_percent']
            .mean().rename(columns={'task_percent': 'prev_avg'})
        )
        baseline = baseline.merge(prev_avg, on=['subject', by], how='left')
        baseline['delta'] = baseline['baseline_avg'] - baseline['prev_avg']
    else:
        baseline['prev_avg'] = np.nan
        baseline['delta'] = np.nan

    baseline['target_avg'] = np.clip(baseline['baseline_avg'] + cfg.min_gain_pp, 0, cfg.hard_target_cap)
    baseline['risk_share_baseline'] = (df['task_percent'] < 50).mean() * 100
    baseline['risk_share_target'] = np.clip(baseline['risk_share_baseline'] - cfg.risk_share_reduction_pp, 0, 100)
    baseline['goal_text'] = "Повысить средний результат и сократить долю слабых."
    baseline.rename(columns={by: 'owner'}, inplace=True)
    return baseline



# =====================================================================
# Streamlit UI
# =====================================================================

def show_action_plans_ui(df: pd.DataFrame, month_id: int,
                         cfg_student: StudentPlanConfig = StudentPlanConfig(),
                         cfg_teacher: TeacherGoalConfig = TeacherGoalConfig()):
    st.markdown("## 🗓️ Задания и цели месяца")

    # --- Отбираем текущий и предыдущий месяцы ---
    df_curr = df[df['month_id'] == month_id].copy()
    prev_df = df[df['month_id'] == (month_id - 1)].copy() if 'month_id' in df.columns else None

    if df_curr.empty:
        st.warning("Нет данных за выбранный месяц.")
        return

    # --- Задания месяца ---
    df_test = df_curr.copy()
    df_test["task_num"] = df_test["task_name"].astype(str).str.extract(r"(\d+)").astype(float)
    df_test = df_test[df_test["task_num"].between(1, 20, inclusive="both")]

    if not df_test.empty:
        task_summary = (
            df_test.groupby(["task_name"], as_index=False)["task_percent"]
            .mean().sort_values("task_percent", ascending=True)
        )
        top_weak = task_summary.head(3)
        cols = st.columns(3)

        for i, (_, row) in enumerate(top_weak.iterrows()):
            percent = row["task_percent"]
            shade = "#f8dada" if percent < 33 else "#ffe9b5" if percent < 50 else "#faf5cf"

            with cols[i]:
                st.markdown(
                    f"""
                    <div style="
                        background-color:{shade};
                        border-radius:0.8rem;
                        padding:0.9rem;
                        text-align:center;
                        border:1px solid #ddd;
                        line-height:1.4;">
                        <div style="font-size:1.5rem;font-weight:700;color:#222;margin-bottom:0.2rem;">
                            {row['task_name']}
                        </div>
                        <div style="font-size:1.1rem;font-weight:600;color:#555;">
                            {percent:.0f}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Нет данных по тестовой части (1–20).")

    # --- Расчёт планов и целей ---
    student_plans = generate_student_tasks(df_curr, month_id, cfg_student)
    teacher_goals = generate_teacher_goals(df_curr, month_id, cfg_teacher, prev_df=prev_df)

    st.markdown("<hr style='margin:1rem 0;'>", unsafe_allow_html=True)

    # --- Единая сводка ---
    avg = df["task_percent"].mean()
    weak_share = (df["task_percent"] < 50).mean() * 100

    # --- Цели по предмету и классу ---
    if not teacher_goals.empty:
        for _, row in teacher_goals.iterrows():
            # динамика среднего результата
            delta_str = ""
            if not np.isnan(row['delta']):
                arrow = "⬆️" if row['delta'] > 0 else "⬇️" if row['delta'] < 0 else "➡️"
                color = "#2e8b57" if row['delta'] > 0 else "#d9534f" if row['delta'] < 0 else "#777"
                delta_str = f"<span style='color:{color};font-weight:600;'>{arrow} {row['delta']:+.1f} п.п.</span>"

            # динамика доли слабых
            if 'risk_share_baseline' in row and 'risk_share_target' in row:
                risk_delta = row['risk_share_target'] - row['risk_share_baseline']
                arrow_risk = "⬇️" if risk_delta < 0 else "⬆️" if risk_delta > 0 else "➡️"
                color_risk = "#2e8b57" if risk_delta < 0 else "#d9534f" if risk_delta > 0 else "#777"
                risk_str = f"<span style='color:{color_risk};font-weight:600;'>{arrow_risk} {risk_delta:+.1f} п.п.</span>"
            else:
                risk_str = ""

            # темп изменения
            if not np.isnan(row.get('prev_avg', np.nan)) and row['prev_avg'] != 0:
                tempo = ((row['baseline_avg'] - row['prev_avg']) / row['prev_avg']) * 100
            else:
                tempo = np.nan
            tempo_str = f"{tempo:+.1f}%" if not np.isnan(tempo) else "—"

            # карточка
            st.markdown(
            f"""
            <div style="background:#f7f9fc;border-radius:0.6rem;padding:0.8rem 1rem;margin:0.5rem 0;
                        border:1px solid #e7e9ec;">
                <div style="font-size:1.05rem;font-weight:700;color:#222;">
                    🎯 {row['subject']} ({row['owner']}) — {row['baseline_avg']:.1f}% {delta_str} → <b>{row['target_avg']:.1f}%</b>
                </div>
                <div style="font-size:0.95rem;color:#333;margin-top:0.25rem;">
                    ⚠️ Доля слабых: {row['risk_share_baseline']:.1f}% {risk_str} → <b>{row['risk_share_target']:.1f}%</b>
                </div>
                <div style="font-size:0.9rem;color:#555;margin-top:0.25rem;">
                    Темп: <b>{tempo_str}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    