def generate_class_summary(
    df,
    last_month_id,
    risk_threshold=40
):
    import numpy as np

    # --- 1. Средние показатели ---
    avg_all_time = df["task_percent"].mean()

    last_month_df = df[df["month_id"] == last_month_id]
    avg_last_month = last_month_df["task_percent"].mean()

    delta = avg_last_month - avg_all_time

    # --- 2. Зона риска ---
    student_avg = (
        df.groupby("student", as_index=False)["task_percent"]
        .mean()
    )

    risk_students = student_avg[student_avg["task_percent"] < risk_threshold]
    risk_count = len(risk_students)
    risk_share = risk_count / student_avg.shape[0] * 100

    # --- 3. Проблемная зона ---
    task_avg = (
        last_month_df
        .groupby("task_name", as_index=False)["task_percent"]
        .mean()
        .sort_values("task_percent")
    )

    problem_task = task_avg.iloc[0]["task_name"]

    # --- 4. Характер динамики ---
    last_month_student_avg = (
        last_month_df.groupby("student")["task_percent"].mean()
    )

    weak_students = student_avg[
        student_avg["task_percent"] < risk_threshold
    ]["student"]

    weak_last_month = last_month_student_avg.loc[
        last_month_student_avg.index.intersection(weak_students)
    ]

    dynamic_comment = (
        "снижение связано преимущественно с результатами группы риска"
        if weak_last_month.mean() < avg_last_month
        else "изменение показателя связано с колебаниями результатов сильных учеников"
    )

    # --- 5. Стабильность ---
    std = last_month_df["task_percent"].std()

    if std > 25:
        stability = "разброс результатов высокий"
    elif std > 15:
        stability = "разброс результатов умеренный"
    else:
        stability = "результаты класса достаточно равномерны"

    # --- 6. Текст саммари ---
    trend_word = "вырос" if delta > 0 else "снизился"
    trend_sign = "+" if delta > 0 else "–"

    summary = (
        f"Средний результат класса за всё время — {avg_all_time:.1f}%. "
        f"В последнем месяце показатель {trend_word} до {avg_last_month:.1f}% "
        f"({trend_sign}{abs(delta):.1f} п.п.).\n"
        f"В зоне риска — {risk_count} учеников ({risk_share:.0f}%). "
        f"Основная проблемная зона — {problem_task}.\n"
        f"{dynamic_comment.capitalize()}, {stability}."
    )

    return summary
