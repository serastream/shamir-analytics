# school_analysis/core/metrics.py
# ============================================================
# METRICS (Single Source of Truth)
# - Только расчёты (pandas), НИКАКОГО streamlit/seaborn/matplotlib
# - Все проценты внутри считаем в шкале 0..1 (success_01)
# - Для UI/текста переводим в проценты *100
# ============================================================

from __future__ import annotations

import re
from typing import List, Tuple, Optional, Dict, Any
import pandas as pd
import numpy as np

# ============================================================
# 1) Константы месяцев
# ============================================================

MONTH_ALIAS_DEFAULT = {
    "1": "Август", "2": "Сентябрь", "3": "Октябрь", "4": "Ноябрь",
    "5": "Декабрь", "6": "Январь", "7": "Февраль", "8": "Март",
    "9": "Апрель", "10": "Май", "11": "Экзамен",
}
MONTH_ORDER_DEFAULT = list(MONTH_ALIAS_DEFAULT.values())


# ============================================================
# 2) Валидация и служебные хелперы (внутренние)
# ============================================================

def _require_cols(df: pd.DataFrame, cols: List[str], where: str = "") -> None:
    """Бросаем понятную ошибку, если не хватает колонок."""
    missing = [c for c in cols if c not in df.columns]
    if missing:
        msg = f"В df нет колонок {missing}"
        if where:
            msg += f" (нужно для {where})"
        raise KeyError(msg)


def _sort_tasks_human(index: pd.Index) -> List[str]:
    """Сортировка: 'Задание 1, Задание 2, ...'."""
    def sort_key(name: str):
        name = str(name).strip()
        match = re.search(r"\d+", name)
        number = int(match.group()) if match else float("inf")
        base_word = re.split(r"\s+", name)[0].capitalize()
        priority = 0 if base_word.lower().startswith("задание") else 1
        return (priority, base_word.lower(), number, name.lower())
    return sorted([str(x) for x in index], key=sort_key)


# ============================================================
# 3) Нормализация
# ============================================================

def normalize_task_percent_to_01(df: pd.DataFrame, col: str = "task_percent") -> pd.Series:
    """
    Приводит task_percent к шкале 0..1.
    Поддерживает входные шкалы:
      - 0..1
      - 0..100 (автоопределение по max>1.5)
    df не мутирует.
    """
    _require_cols(df, [col], where="normalize_task_percent_to_01")
    s = pd.to_numeric(df[col], errors="coerce")
    mx = s.dropna().max() if not s.dropna().empty else None
    if mx is not None and mx > 1.5:
        s = s / 100.0
    return s.clip(0, 1)


def normalize_month(
    df: pd.DataFrame,
    month_col: str = "month",
    month_alias: Optional[dict] = None,
    month_order: Optional[list] = None
) -> pd.Categorical:
    """
    Нормализует колонку месяца к категориальному виду с правильным порядком.
    month может быть '1', 1, 'Август', 'Сентябрь' и т.п.
    """
    _require_cols(df, [month_col], where="normalize_month")
    month_alias = month_alias or MONTH_ALIAS_DEFAULT
    month_order = month_order or MONTH_ORDER_DEFAULT

    s = df[month_col].astype(str).str.strip().replace(month_alias)
    return pd.Categorical(s, categories=month_order, ordered=True)


# ============================================================
# 4) Каноническая таблица для heatmap (и для LLM)
# ============================================================

def task_perf_table_for_heatmap(
    df: pd.DataFrame,
    *,
    mode: str,
    hide_empty_months: bool,
    selected_class: str,
    selected_subject: str = "Все предметы",
    selected_student: Optional[str] = None,
    month_col: str = "month",
    month_alias: Optional[dict] = None,
    month_order: Optional[list] = None,
) -> Tuple[pd.DataFrame, List[str], List[str], float]:
    """
    ЕДИНЫЙ ИСТОЧНИК ПРАВДЫ для тепловой карты.

    Возвращает:
      class_avg_01         — pivot-таблица в шкале 0..1 + колонка 'Среднее'
      months_to_show       — какие месяцы показываем
      months_without_data  — какие месяцы пустые
      overall_mean_01      — среднее по столбцу 'Среднее' (0..1)

    mode ∈ {"Заданиям", "Ученикам", "Задания конкретного ученика"}
    """

    required = ["class", "subject", "student", "task_name", "task_percent", month_col]
    _require_cols(df, required, where="task_perf_table_for_heatmap")

    dff = df.loc[df["class"] == selected_class].copy()
    if selected_subject != "Все предметы":
        dff = dff.loc[dff["subject"] == selected_subject]
    if mode == "Задания конкретного ученика" and selected_student:
        dff = dff.loc[dff["student"] == selected_student]

    if dff.empty:
        return pd.DataFrame(), [], [], float("nan")

    # 1) проценты -> 0..1
    dff["_tp"] = normalize_task_percent_to_01(dff, "task_percent")

    # 2) месяц -> категориальный
    month_alias = month_alias or MONTH_ALIAS_DEFAULT
    month_order = month_order or MONTH_ORDER_DEFAULT
    dff["_month"] = normalize_month(dff, month_col, month_alias, month_order)

    months_with_data = pd.Series(dff["_month"].dropna().unique()).tolist()
    months_without_data = [m for m in month_order if m not in months_with_data]
    months_to_show = [m for m in month_order if m in months_with_data] if hide_empty_months else month_order

    # 3) pivot по режиму
    if mode == "Ученикам":
        student_month = (
            dff.groupby(["student", "_month"], observed=True)["_tp"]
               .mean()
               .reset_index()
        )
        class_avg = (
            student_month.pivot(index="student", columns="_month", values="_tp")
                         .reindex(columns=months_to_show)
        )
        class_avg = class_avg.sort_index()
    else:
        class_avg = (
            dff.groupby(["task_name", "_month"], observed=True)["_tp"]
               .mean()
               .unstack("_month")
               .reindex(columns=months_to_show)
        )
        class_avg = class_avg.loc[_sort_tasks_human(class_avg.index)]

    # 4) 'Среднее' = среднее по месяцам (месяцы равновесны)
    class_avg["Среднее"] = class_avg.mean(axis=1, skipna=True)
    class_avg = class_avg.reindex(columns=months_to_show + ["Среднее"])

    overall_mean_01 = float(class_avg["Среднее"].mean(skipna=True))
    return class_avg, months_to_show, months_without_data, overall_mean_01


# ============================================================
# 5) KPI уровня класса/предмета
# ============================================================

def overall_mean_percent(df_f: pd.DataFrame, *, selected_class: str, selected_subject: str) -> float:
    """
    Средний результат по выборке (как в heatmap): mean по 'Среднее' * 100.
    """
    table, _, _, overall_01 = task_perf_table_for_heatmap(
        df_f,
        mode="Заданиям",
        hide_empty_months=False,
        selected_class=selected_class,
        selected_subject=selected_subject,
        selected_student=None,
        month_col="month",
    )
    if table.empty or pd.isna(overall_01):
        return float("nan")
    return overall_01 * 100


def top_weak_tasks(df_f: pd.DataFrame, *, selected_class: str, selected_subject: str, top_n: int = 5) -> pd.DataFrame:
    """
    Топ проблемных заданий по метрике heatmap ('Среднее' по месяцам).
    Возвращает: task_name | avg_monthly_success_pct
    """
    table, _, _, _ = task_perf_table_for_heatmap(
        df_f,
        mode="Заданиям",
        hide_empty_months=False,
        selected_class=selected_class,
        selected_subject=selected_subject,
        selected_student=None,
        month_col="month",
    )
    if table.empty or "Среднее" not in table.columns:
        return pd.DataFrame(columns=["task_name", "avg_monthly_success_pct"])

    worst = (
        table[["Среднее"]]
        .reset_index()
        .rename(columns={"Среднее": "avg_monthly_success_01"})
        .sort_values("avg_monthly_success_01", ascending=True)
        .head(top_n)
    )
    worst["avg_monthly_success_pct"] = worst["avg_monthly_success_01"] * 100
    return worst[["task_name", "avg_monthly_success_pct"]]


# ============================================================
# 6) KPI уровня учеников
# ============================================================

def students_avg_percent(df_f: pd.DataFrame) -> pd.DataFrame:
    """
    Средняя успешность ученика по ВСЕМ строкам (не по месяцам).
    Возвращает: student | avg_success_pct
    """
    _require_cols(df_f, ["student", "task_percent"], where="students_avg_percent")
    s01 = normalize_task_percent_to_01(df_f, "task_percent")
    tmp = df_f[["student"]].copy()
    tmp["_tp"] = s01
    out = (
        tmp.groupby("student", as_index=False)["_tp"]
           .mean()
           .rename(columns={"_tp": "avg_success_01"})
           .sort_values("avg_success_01", ascending=True)
    )
    out["avg_success_pct"] = out["avg_success_01"] * 100
    return out[["student", "avg_success_pct"]]


def risk_students_share(df_f: pd.DataFrame, *, threshold_pct: float = 50.0) -> float:
    """
    Доля учеников в риске (по ученикам, а не по строкам):
    - считаем avg по ученику
    - доля < threshold_pct
    """
    by_student = students_avg_percent(df_f)
    if by_student.empty:
        return float("nan")
    return float((by_student["avg_success_pct"] < threshold_pct).mean() * 100)


def risk_students_list(df_f: pd.DataFrame, *, threshold_pct: float = 50.0) -> pd.DataFrame:
    """
    Список учеников в риске: student | avg_success_pct
    """
    by_student = students_avg_percent(df_f)
    if by_student.empty:
        return pd.DataFrame(columns=["student", "avg_success_pct"])
    out = by_student.loc[by_student["avg_success_pct"] < threshold_pct].copy()
    return out.sort_values("avg_success_pct", ascending=True).reset_index(drop=True)


# ============================================================
# 7) Точечные метрики (для запросов “ученик × задание”)
# ============================================================

def student_task_monthly(
    df_f: pd.DataFrame,
    *,
    student: str,
    task_name: str,
    month_col: str = "month",
) -> pd.DataFrame:
    """
    Ученик × задание → успешность по месяцам.
    Возвращает: month | success_pct
    """
    _require_cols(df_f, ["student", "task_name", "task_percent", month_col], where="student_task_monthly")

    d = df_f.loc[(df_f["student"] == student) & (df_f["task_name"].astype(str) == str(task_name))].copy()
    if d.empty:
        return pd.DataFrame(columns=["month", "success_pct"])

    d["_tp"] = normalize_task_percent_to_01(d, "task_percent")
    d["_month"] = normalize_month(d, month_col)

    out = (
        d.groupby("_month", as_index=False)["_tp"]
         .mean()
         .rename(columns={"_month": "month", "_tp": "success_01"})
         .sort_values("month")
    )
    out["success_pct"] = out["success_01"] * 100
    return out[["month", "success_pct"]]


def student_tasks_avg_monthly(
    df_f: pd.DataFrame,
    *,
    student: str,
    month_col: str = "month",
) -> pd.DataFrame:
    """
    Для одного ученика: средняя успешность по заданиям, но ЧЕСТНО по месяцам:
    1) task × month mean
    2) потом mean по месяцам
    Возвращает: task_name | avg_monthly_success_pct
    """
    _require_cols(df_f, ["student", "task_name", "task_percent", month_col], where="student_tasks_avg_monthly")

    d = df_f.loc[df_f["student"] == student].copy()
    if d.empty:
        return pd.DataFrame(columns=["task_name", "avg_monthly_success_pct"])

    d["_tp"] = normalize_task_percent_to_01(d, "task_percent")
    d["_month"] = normalize_month(d, month_col)

    monthly = (
        d.groupby(["task_name", "_month"], observed=True)["_tp"]
         .mean()
         .reset_index()
    )
    avgm = (
        monthly.groupby("task_name", as_index=False)["_tp"]
               .mean()
               .rename(columns={"_tp": "avg_monthly_success_01"})
               .sort_values("avg_monthly_success_01", ascending=True)
    )
    avgm["avg_monthly_success_pct"] = avgm["avg_monthly_success_01"] * 100
    return avgm[["task_name", "avg_monthly_success_pct"]]


def class_monthly_mean(df_f: pd.DataFrame, *, month_col: str = "month") -> pd.DataFrame:
    """
    Динамика класса по месяцам: month | mean_success_pct
    (По текущему df_f: т.е. уже отфильтрован по классу/предмету.)
    """
    _require_cols(df_f, ["task_percent", month_col], where="class_monthly_mean")
    d = df_f.copy()
    d["_tp"] = normalize_task_percent_to_01(d, "task_percent")
    d["_month"] = normalize_month(d, month_col)

    out = (
        d.groupby("_month", as_index=False)["_tp"]
         .mean()
         .rename(columns={"_month": "month", "_tp": "mean_success_01"})
         .sort_values("month")
    )
    out["mean_success_pct"] = out["mean_success_01"] * 100
    return out[["month", "mean_success_pct"]]


# ============================================================
# 8) Evidence pack для LLM (учитель)
# ============================================================

def build_teacher_evidence(
    df_f: pd.DataFrame,
    *,
    selected_class: str,
    selected_subject: str,
    top_n: int = 5,
    risk_threshold_pct: float = 50.0,
) -> Dict[str, Any]:
    """
    Готовит "пакет доказательств" (evidence pack) для LLM.
    LLM НЕ должен пересчитывать — он должен интерпретировать это.

    Возвращает dict:
      - definitions: текстовые определения метрик
      - kpis: ключевые показатели
      - tables: небольшие таблицы (топы/списки)
    """
    # KPI
    overall = overall_mean_percent(df_f, selected_class=selected_class, selected_subject=selected_subject)
    risk_share = risk_students_share(df_f, threshold_pct=risk_threshold_pct)

    # Таблицы
    weak_tasks = top_weak_tasks(df_f, selected_class=selected_class, selected_subject=selected_subject, top_n=top_n)

    by_student = students_avg_percent(df_f)
    weak_students = by_student.head(top_n).copy()
    strong_students = by_student.tail(top_n).sort_values("avg_success_pct", ascending=False).copy()

    risk_list = risk_students_list(df_f, threshold_pct=risk_threshold_pct)

    return {
        "definitions": {
            "task_metric": "Проценты по заданиям = средняя успешность по месяцам (колонка 'Среднее' в тепловой карте).",
            "scale": "Внутри расчётов шкала 0..1, в выводе показано 0..100%.",
            "risk_metric": f"Риск = ученик со средним результатом ниже {risk_threshold_pct:.0f}%.",
        },
        "kpis": {
            "overall_mean_pct": overall,
            "risk_share_students_pct": risk_share,
            "selected_class": selected_class,
            "selected_subject": selected_subject,
        },
        "tables": {
            "weak_tasks": weak_tasks,                 # task_name + avg_monthly_success_pct
            "weak_students": weak_students,           # student + avg_success_pct
            "strong_students": strong_students,       # student + avg_success_pct
            "risk_students": risk_list,               # student + avg_success_pct
        }
    }


def prepare_task_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Диагностика учебных пробелов по заданиям.
    Ожидает колонки: subject, class, task_id, task_score, (task_percent или max_score).
    Возвращает avg_percent в шкале 0..100.
    """
    # Если проценты по заданию не готовы — досчитаем
    if "task_percent" not in df.columns and {"task_score", "max_score"}.issubset(df.columns):
        df = df.copy()
        df["task_percent"] = (df["task_score"] / df["max_score"] * 100).round(1)

    required = {"subject", "class", "task_id", "task_score", "task_percent"}
    missing = required - set(df.columns)
    if missing:
        return pd.DataFrame(columns=[
            "subject", "class", "task_id",
            "avg_score", "avg_percent",
            "zero_count", "total_students", "zero_share"
        ])

    diag = (
        df.groupby(["subject", "class", "task_id"])
          .agg(
              avg_score=("task_score", "mean"),
              avg_percent=("task_percent", "mean"),
              zero_count=("task_score", lambda x: (x.fillna(0) == 0).sum()),
              total_students=("task_score", "count")
          )
          .reset_index()
    )
    diag["zero_share"] = (diag["zero_count"] / diag["total_students"]).replace({0: np.nan}).fillna(0) * 100
    diag["avg_percent"] = diag["avg_percent"].round(1)
    diag["avg_score"] = diag["avg_score"].round(2)
    diag["zero_share"] = diag["zero_share"].round(1)
    return diag


def prepare_class_heatmap(df: pd.DataFrame) -> dict:
    """
    Pivot-таблицы для heatmap по каждому предмету (класс × задание).
    Возвращает проценты 0..100 (для удобства отображения).
    Ожидает: class, subject, task_id, task_percent
    """
    required = {"class", "subject", "task_id", "task_percent"}
    missing = required - set(df.columns)
    if missing:
        return {}

    dff = df.copy()
    dff["_tp"] = normalize_task_percent_to_01(dff, "task_percent") * 100

    class_task = (
        dff.groupby(["class", "subject", "task_id"], as_index=False)["_tp"]
           .mean()
           .rename(columns={"_tp": "task_percent"})
    )

    heatmaps = {
        subj: class_task[class_task["subject"] == subj]
              .pivot(index="class", columns="task_id", values="task_percent")
        for subj in sorted(dff["subject"].dropna().unique())
    }
    return heatmaps
