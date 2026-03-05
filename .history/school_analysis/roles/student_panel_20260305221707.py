import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random


def show(df: pd.DataFrame, student_id: int, student_name: str):
    st.header(f"🚀 Личный кабинет: {student_name}")

    # --- защита ---
    required = {"student_id", "month_id", "task_percent", "task_name", "subject"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"В данных не хватает колонок: {missing}")
        return

    # --- фильтр по ученику ---
    df_student_all = df.query("student_id == @student_id").copy()
    if df_student_all.empty:
        st.info("Пока нет данных по этому ученику.")
        return

    # --- нормализация ---
    df_student_all["month_id"] = pd.to_numeric(df_student_all["month_id"], errors="coerce")
    df_student_all["task_percent"] = pd.to_numeric(df_student_all["task_percent"], errors="coerce")
    if "exam_percent" in df_student_all.columns:
        df_student_all["exam_percent"] = pd.to_numeric(df_student_all["exam_percent"], errors="coerce")
    df_student_all = df_student_all.dropna(subset=["month_id"]).sort_values("month_id")

    # ============================================================
    # ФИЛЬТР: предмет
    # ============================================================
    st.markdown("### 🎛️ Фильтры")

    subjects = sorted([x for x in df_student_all["subject"].dropna().unique().tolist() if str(x).strip() != ""])
    subject_choice = st.selectbox(
        "📚 Предмет",
        options=["Все предметы"] + subjects,
        index=0
    )

    if subject_choice != "Все предметы":
        df_student = df_student_all[df_student_all["subject"] == subject_choice].copy()
    else:
        df_student = df_student_all.copy()

    if df_student.empty:
        st.info("По выбранному предмету данных пока нет.")
        return

    # ============================================================
    # Понимание процентов (объяснение)
    # ============================================================
    with st.expander("🧠 Что означают проценты?", expanded=True):
        st.markdown(
            """
- **% по заданиям** = `task_score / max_score * 100`  
  Показывает, насколько хорошо решены *конкретные задания* (1–…).
- **% по пробнику (экзамен)** = `result / max_result * 100`  
  Это общий результат *за весь пробник* (если он есть в данных).
            """
        )

    st.markdown("---")

    # ============================================================
    # РЕЖИМ: чем считать “XP” (по заданиям / по пробнику)
    # ============================================================
    mode = st.radio(
        "📌 На чём строить прогресс и ранги?",
        options=["По заданиям", "По пробнику (экзамен)"],
        horizontal=True
    )

    # --- monthly score ---
    if mode == "По пробнику (экзамен)" and "exam_percent" in df_student.columns and df_student["exam_percent"].notna().any():
        monthly = (
            df_student.groupby("month_id", as_index=False)
            .agg(avg_score=("exam_percent", "mean"))
            .sort_values("month_id")
        )
        score_label = "XP = средний % за пробник"
    else:
        monthly = (
            df_student.groupby("month_id", as_index=False)
            .agg(avg_score=("task_percent", "mean"))
            .sort_values("month_id")
        )
        score_label = "XP = средний % по заданиям"

    monthly["avg_score"] = monthly["avg_score"].clip(0, 100)
    last_score = float(monthly["avg_score"].iloc[-1]) if not monthly.empty else 0.0

    # ============================================================
    # БЛОК 1: РАНГИ И XP (красиво)
    # ============================================================
    if last_score < 40:
        rank, icon, color = "Искатель", "🥉", "#CD7F32"
        next_threshold = 40
    elif last_score < 65:
        rank, icon, color = "Ученик гильдии", "🥈", "#C0C0C0"
        next_threshold = 65
    elif last_score < 85:
        rank, icon, color = "Мастер", "🥇", "#FFD700"
        next_threshold = 85
    else:
        rank, icon, color = "Грандмастер", "💎", "#00FFFF"
        next_threshold = 100

    top = st.container(border=True)
    with top:
        c1, c2, c3 = st.columns([1.1, 1.2, 1.7])
        with c1:
            st.markdown(
                f"<h2 style='text-align:center; color:{color}; margin-bottom:0'>{icon}</h2>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<h3 style='text-align:center; color:{color}; margin-top:0'>{rank}</h3>",
                unsafe_allow_html=True
            )
        with c2:
            st.metric("Текущий XP", f"{last_score:.1f}")
            st.caption(score_label)
        with c3:
            st.caption("Прогресс к 100%")
            st.progress(min(1.0, max(0.0, last_score / 100.0)))
            if next_threshold < 100:
                st.caption(f"До следующего ранга: **{max(0.0, next_threshold - last_score):.1f}**")
            else:
                st.caption("Ты на верхнем ранге. Дальше — легенда 😄")

    st.markdown("---")

    # ============================================================
    # БЛОК 2: АЧИВКИ (аккуратно)
    # ============================================================
    st.subheader("🏆 Достижения")
    ach = st.columns(4)

    with ach[0]:
        if len(monthly) >= 2 and monthly["avg_score"].iloc[-1] > monthly["avg_score"].iloc[-2]:
            st.success("📈 Набирающий высоту\n\nРост к прошлому месяцу!")
        else:
            st.info("🔒 Растишка\n\nНужен рост в след. месяце")

    with ach[1]:
        if (df_student["task_percent"] >= 100).fillna(False).any():
            st.success("🎯 Снайпер\n\nЕсть 100% по заданию!")
        else:
            st.info("🔒 Меткий глаз\n\nСделай 100% по любой задаче")

    with ach[2]:
        if (monthly["avg_score"] > 40).all():
            st.success("🛡️ Непробиваемый\n\nНет провалов ниже 40!")
        else:
            st.info("🔒 Щит\n\nСтабильность важнее рывков")

    with ach[3]:
        if len(monthly) > 1 and np.isclose(last_score, monthly["avg_score"].max(), atol=1e-6):
            st.balloons()
            st.success("👑 На пике формы\n\nЭто твой рекорд!")
        else:
            st.info("🔒 Рекордсмен\n\nПобей лучший результат")

    st.markdown("---")

    # ============================================================
    # БЛОК 3: ГРАФИК ПРОГРЕССА
    # ============================================================
    st.subheader("📊 Прогресс по месяцам")
    fig = px.line(
        monthly, x="month_id", y="avg_score",
        markers=True,
        title=f"Динамика ({'пробник' if mode.startswith('По пробнику') else 'задания'})"
    )
    fig.update_traces(line_color=color)
    fig.update_layout(yaxis=dict(range=[0, 100]), xaxis_title="Месяц", yaxis_title="Процент / XP")
    st.plotly_chart(fig, use_container_width=True)

    # ============================================================
    # БЛОК 4: “за что проценты” — таблица (по выбранному месяцу)
    # ============================================================
    st.subheader("🧾 За что получились эти проценты")

    months_present = (
        df_student[["month_id", "month"]]
        .drop_duplicates()
        .sort_values("month_id")
    )
    month_labels = []
    for _, r in months_present.iterrows():
        label = f"{int(r['month_id'])}"
        if "month" in months_present.columns and pd.notna(r.get("month", None)):
            label = f"{int(r['month_id'])} — {r['month']}"
        month_labels.append(label)

    # по умолчанию — последний месяц
    month_idx = len(month_labels) - 1 if month_labels else 0
    chosen_label = st.selectbox("📅 Месяц", options=month_labels, index=month_idx)
    chosen_month_id = int(str(chosen_label).split("—")[0].strip())

    df_m = df_student[df_student["month_id"] == chosen_month_id].copy()

    # 4.1 Таблица по заданиям
    tasks_table = df_m[["task_name", "task_score", "max_score", "task_percent"]].copy()
    tasks_table = tasks_table.sort_values("task_percent", ascending=True)

    c_left, c_right = st.columns([1.25, 1])

    with c_left:
        st.markdown("**📌 Задания (баллы → %)**")
        st.dataframe(
            tasks_table,
            use_container_width=True,
            hide_index=True
        )
        st.caption("Здесь видно, за какие конкретно задания набраны проценты.")

    with c_right:
        st.markdown("**🎯 Итог пробника (если есть)**")
        if {"result", "max_result", "exam_percent"}.issubset(df_m.columns) and df_m["exam_percent"].notna().any():
            # берём одну строку (в данных повторяется на каждое задание)
            row = df_m.dropna(subset=["exam_percent"]).iloc[0]
            st.metric("Результат", f"{row['result']} / {row['max_result']}")
            st.metric("Процент", f"{row['exam_percent']:.1f}%")
        else:
            st.info("Нет данных по общему результату пробника в этом месяце.")

    st.markdown("---")

    # ============================================================
    # БЛОК 5: “враги/опора” (по предмету уже отфильтровано)
    # ============================================================
    st.subheader("⚔️ Сильные и слабые темы")

    task_avg = (
        df_student.groupby("task_name", as_index=False)["task_percent"]
        .mean()
        .sort_values("task_percent")
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Твои главные враги**")
        weak = task_avg[task_avg["task_percent"] < 50].head(5)
        if weak.empty:
            st.success("Критических пробелов нет 💪")
        else:
            for _, r in weak.iterrows():
                st.warning(f"**{r['task_name']}** — {r['task_percent']:.1f}%")

    with col2:
        st.markdown("**Твоя опора**")
        strong = task_avg[task_avg["task_percent"] > 80].sort_values("task_percent", ascending=False).head(5)
        if strong.empty:
            st.info("Пока нет тем >80%. Значит, есть где набрать лёгкие очки.")
        else:
            for _, r in strong.iterrows():
                st.success(f"**{r['task_name']}** — {r['task_percent']:.1f}%")

    st.markdown("---")

    # ============================================================
    # БЛОК 6: ПРОГНОЗ
    # ============================================================
    st.subheader("🔮 Прогноз")

    if len(monthly) >= 2:
        x = np.arange(len(monthly))
        y = monthly["avg_score"].values.astype(float)

        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)

        predicted = float(np.clip(p(len(monthly) + 1), 0, 100))
        trend = float(z[0])

        a, b = st.columns(2)
        with a:
            st.metric("Ожидаемый уровень", f"{predicted:.1f}", f"{trend:+.1f} / месяц")
            if trend > 0:
                st.caption("🔥 Тренд растущий. Важно закрепить регулярность.")
            else:
                st.caption("⚠️ Тренд слабый. Нужна смена стратегии (упор на слабые темы).")

        with b:
            if predicted < 60:
                st.warning("Статус: зона риска. Ставка на базу и стабильность.")
            elif predicted < 85:
                st.info("Статус: хороший потенциал. Убирай «обидные» ошибки.")
            else:
                st.success("Статус: очень высокий уровень. Шлифуй сложные задания!")
    else:
        st.info("Для прогноза нужно хотя бы 2 месяца статистики.")

    st.markdown("---")
    quotes = [
        "Тяжело в учении — легко на экзамене!",
        "Твой единственный соперник — ты вчерашний.",
        "Маленькие шаги ведут к большим результатам.",
        "Даже самый высокий уровень начинается с первого XP."
    ]
    st.markdown(f"💬 *Совет дня: {random.choice(quotes)}*")