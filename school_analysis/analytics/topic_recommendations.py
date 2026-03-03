import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return np.nan


def build_category_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Агрегация: ученик × предмет × категория.
    Ожидает колонки: student, subject, category, task_percent (+ желательно task_name).
    """
    required = {"student", "subject", "category", "task_percent"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Не хватает колонок: {missing}")

    dff = df.copy()
    dff["task_percent"] = dff["task_percent"].map(_safe_float)

    # если category пустая — лучше явно пометить
    dff["category"] = dff["category"].fillna("— категория не указана —").astype(str)

    stats = (
        dff.groupby(["student", "subject", "category"], as_index=False)
        .agg(
            avg_percent=("task_percent", "mean"),
            attempts=("task_percent", "count"),
            std_percent=("task_percent", "std"),
        )
    )
    stats["avg_percent"] = stats["avg_percent"].round(1)
    stats["std_percent"] = stats["std_percent"].fillna(0).round(1)
    return stats


def estimate_uplift_effect(
    df: pd.DataFrame,
    category_stats: pd.DataFrame,
    target_gain_pp: float = 15.0,
) -> pd.DataFrame:
    """
    (5) Прогноз эффекта: грубая оценка, насколько рост категории связан с итогом (exam_percent).
    Если exam_percent нет — вернёт NaN.

    Идея: по ученикам смотрим связь category_avg ↔ exam_percent внутри предмета.
    Это не каузальность, но помогает приоритизировать категории.
    """
    if "exam_percent" not in df.columns:
        out = category_stats.copy()
        out["expected_exam_uplift_pp"] = np.nan
        out["uplift_model_note"] = "exam_percent отсутствует"
        return out

    dff = df.copy()
    dff["task_percent"] = dff["task_percent"].map(_safe_float)
    dff["exam_percent"] = dff["exam_percent"].map(_safe_float)
    dff["category"] = dff["category"].fillna("— категория не указана —").astype(str)

    # на уровне ученик×предмет×категория: avg_category
    category_avg = (
        dff.groupby(["student", "subject", "category"], as_index=False)
        .agg(avg_category=("task_percent", "mean"))
    )

    # на уровне ученик×предмет: итог
    exam_by_student = (
        dff.groupby(["student", "subject"], as_index=False)
        .agg(exam=("exam_percent", "mean"))
    )

    m = category_avg.merge(exam_by_student, on=["student", "subject"], how="left")

    # оценка коэффициента на уровне subject: slope ~ cov(category, exam) / var(category)
    res = []
    for subj, g in m.groupby(["subject"]):
        g = g.dropna(subset=["avg_category", "exam"])
        if len(g) < 8 or g["avg_category"].std() == 0:
            slope = np.nan
        else:
            slope = np.cov(g["avg_category"], g["exam"], ddof=0)[0, 1] / np.var(g["avg_category"])
        res.append({"subject": subj, "slope_exam_per_category": slope})

    slopes = pd.DataFrame(res)
    out = category_stats.merge(slopes, on="subject", how="left")

    # ожидаемый рост итога при +target_gain_pp по категории (ограничим здравым смыслом)
    out["expected_exam_uplift_pp"] = (out["slope_exam_per_category"] * target_gain_pp).clip(-15, 25).round(1)
    out["uplift_model_note"] = np.where(
        out["slope_exam_per_category"].isna(),
        "мало данных для оценки связи",
        f"оценка при +{target_gain_pp:.0f} п.п. по категории"
    )
    return out


def generate_category_recommendations(
    df: pd.DataFrame,
    low_thr: int = 40,
    mid_thr: int = 65,
    unstable_std_thr: int = 20,
    class_risk_share_thr: float = 0.35,  # (2) если >=35% класса в риске по категории → групповая рекомендация
    prereq_graph: Optional[Dict[str, List[str]]] = None,  # (1) связи категорий: category -> prerequisites
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Возвращает:
    1) per_student_category: рекомендации ученик×категория (формат работы + связные категории + прогноз эффекта)
    2) class_category_actions: рекомендации на класс (групповые категории)

    prereq_graph:
      {"Функции": ["Координатная плоскость", "Линейные уравнения"], ...}
    """
    required = {"student", "subject", "category", "task_percent"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Не хватает колонок: {missing}")

    category_stats = build_category_stats(df)

    # (5) прогноз эффекта
    category_stats = estimate_uplift_effect(df, category_stats, target_gain_pp=15.0)

    # (2) групповые категории: доля учеников в риске по категории
    risk_flag = category_stats.assign(in_risk=lambda x: x["avg_percent"] < low_thr)
    class_category = (
        risk_flag.groupby(["subject", "category"], as_index=False)
        .agg(
            students=("student", "nunique"),
            risk_students=("in_risk", "sum"),
            risk_share=("in_risk", "mean"),
            class_avg=("avg_percent", "mean"),
        )
    )
    class_category["risk_share"] = class_category["risk_share"].round(3)
    class_category["class_avg"] = class_category["class_avg"].round(1)

    class_category_actions = class_category[class_category["risk_share"] >= class_risk_share_thr].copy()
    class_category_actions["class_action"] = np.where(
        class_category_actions["risk_share"] >= 0.5,
        "фронтальный разбор с нуля + мини-контроль",
        "фронтальный разбор + дифференцированное закрепление"
    )
    class_category_actions["class_text"] = class_category_actions.apply(
        lambda r: (
            f"Категория «{r['category']}» — зона риска: "
            f"{int(r['risk_students'])} из {int(r['students'])} учеников ({r['risk_share']*100:.0f}%) "
            f"ниже {low_thr}%. Рекомендуется: {r['class_action']}."
        ),
        axis=1
    )

    # (1)(3)(4) индивидуальные рекомендации
    rows = []
    for _, r in category_stats.iterrows():
        student = r["student"]
        subject = r["subject"]
        category = r["category"]
        avg_p = float(r["avg_percent"])
        std_p = float(r["std_percent"])
        uplift = r.get("expected_exam_uplift_pp", np.nan)

        # базовые действия (индив / ДЗ / стабилизация)
        if avg_p < low_thr:
            action = "индивидуальное занятие"
            why = f"устойчиво низкий результат по категории ({avg_p:.0f}%)"
        elif avg_p < mid_thr:
            action = "домашнее задание по категории"
            why = f"категория усвоена частично ({avg_p:.0f}%)"
        elif std_p >= unstable_std_thr:
            action = "стабилизация"
            why = f"нестабильность результатов (σ≈{std_p:.0f} п.п.)"
        else:
            continue

        # (4) формат работы
        if action == "индивидуальное занятие":
            format_hint = "Формат: 15–25 минут, разбор ошибок + 5–7 типовых шагов + мини-проверка в конце."
        elif action == "домашнее задание по категории":
            format_hint = "Формат: 6–10 задач по категории (от простого к типовым), проверка по критериям/шагам."
        else:
            format_hint = "Формат: короткие повторы (5–7 минут) + 2 контрольных мини-задачи на уроке."

        # (1) связанные категории
        prereqs = []
        if prereq_graph and isinstance(prereq_graph, dict):
            prereqs = prereq_graph.get(str(category), []) or []
        prereq_text = ""
        if prereqs:
            prereq_text = "Возможная причина: пробел в категории(ях) " + ", ".join([f"«{t}»" for t in prereqs]) + "."

        # (5) эффект
        effect_text = ""
        if pd.notna(uplift):
            effect_text = (
                f"Оценка эффекта: при усилении категории на ~15 п.п. "
                f"возможен сдвиг итога примерно на {uplift:+.1f} п.п. (ориентир)."
            )

        text = (
            f"**{student} — категория «{category}»**: {why}. "
            f"Рекомендуется: **{action}**. {format_hint} "
            f"{prereq_text} {effect_text}"
        ).strip()

        rows.append({
            "student": student,
            "subject": subject,
            "category": category,
            "avg_percent": round(avg_p, 1),
            "std_percent": round(std_p, 1),
            "action": action,
            "format_hint": format_hint,
            "linked_categories": ", ".join(prereqs) if prereqs else "",
            "expected_exam_uplift_pp": uplift,
            "recommendation_text": text,
        })

    per_student_category = pd.DataFrame(rows)
    return per_student_category, class_category_actions[
        ["subject", "category", "class_avg", "risk_share", "class_action", "class_text"]
    ].sort_values(["subject", "risk_share"], ascending=[True, False])
