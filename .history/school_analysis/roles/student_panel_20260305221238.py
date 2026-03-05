import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random


def show(df: pd.DataFrame, student_id: int, student_name: str):
    st.header(f"🚀 Личный кабинет: {student_name}")

    # --- защита от отсутствующих колонок (чтобы не падало) ---
    required = {"student_id", "month_id", "task_percent", "task_name"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"В данных не хватает колонок: {missing}")
        return

    # --- фильтруем ученика ---
    df_student = df.query("student_id == @student_id").copy()
    if df_student.empty:
        st.info("Пока нет данных по этому ученику.")
        return

    # --- нормализуем и сортируем ---
    df_student["month_id"] = pd.to_numeric(df_student["month_id"], errors="coerce")
    df_student["task_percent"] = pd.to_numeric(df_student["task_percent"], errors="coerce")
    df_student = df_student.dropna(subset=["month_id"]).sort_values("month_id")

    # --- агрегат по месяцам: "XP" = средний % выполнения заданий за месяц ---
    monthly = (
        df_student.groupby("month_id", as_index=False)
        .agg(avg_score=("task_percent", "mean"))
        .sort_values("month_id")
    )
    monthly["avg_score"] = monthly["avg_score"].clip(0, 100)

    last_score = float(monthly["avg_score"].iloc[-1]) if not monthly.empty else 0.0

    # ============================================================
    # БЛОК 1: РАНГИ И XP
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

    col_rank1, col_rank2 = st.columns([1, 2])

    with col_rank1:
        st.markdown(
            f"<h2 style='text-align:center; color:{color};'>{icon}<br>{rank}</h2>",
            unsafe_allow_html=True
        )

    with col_rank2:
        st.write(f"**Твой текущий уровень:** {last_score:.1f} XP (средний % за последний месяц)")
        progress = min(1.0, max(0.0, last_score / 100.0))
        st.progress(progress)

        to_next = max(0.0, next_threshold - last_score)
        if next_threshold < 100:
            st.caption(f"До следующего ранга осталось **{to_next:.1f}** балла(ов).")
        else:
            st.caption("Ты на верхнем ранге. Дальше — только легенда 😄")

    st.markdown("---")

    # ============================================================
    # БЛОК 2: АЧИВКИ
    # ============================================================
    st.subheader("🏆 Твои достижения")
    achievements = st.columns(4)

    # Ачивка 1: рост к прошлому месяцу
    with achievements[0]:
        if len(monthly) >= 2 and (monthly["avg_score"].iloc[-1] > monthly["avg_score"].iloc[-2]):
            st.markdown("📈 **Набирающий высоту**\n\nРезультат вырос по сравнению с прошлым месяцем!")
        else:
            st.markdown("🔒 *Растишка*\n\n(Улучши результат в следующем месяце)")

    # Ачивка 2: есть 100% по любому заданию (хотя бы раз)
    with achievements[1]:
        if (df_student["task_percent"] >= 100).fillna(False).any():
            st.markdown("🎯 **Снайпер**\n\nЕсть хотя бы одно задание на 100%!")
        else:
            st.markdown("🔒 *Меткий глаз*\n\n(Реши хотя бы одну задачу без ошибок)")

    # Ачивка 3: стабильность (нет провалов ниже 40 в тех месяцах, где писал)
    with achievements[2]:
        if (monthly["avg_score"] > 40).all():
            st.markdown("🛡️ **Непробиваемый**\n\nНи одного провального месяца (ниже 40)!")
        else:
            st.markdown("🔒 *Щит*\n\n(Не допускай падения ниже 40)")

    # Ачивка 4: рекорд
    with achievements[3]:
        if len(monthly) > 1 and np.isclose(last_score, monthly["avg_score"].max(), atol=1e-6):
            st.balloons()
            st.markdown("👑 **На пике формы**\n\nЭто твой лучший результат за всё время!")
        else:
            st.markdown("🔒 *Рекордсмен*\n\n(Побей свой лучший результат)")

    st.markdown("---")

    # ============================================================
    # БЛОК 3: ГРАФИК ПРОГРЕССА
    # ============================================================
    st.subheader("📊 Твоя кривая силы")
    fig_progress = px.line(
        monthly,
        x="month_id",
        y="avg_score",
        markers=True,
        title="Динамика среднего результата по месяцам",
    )
    fig_progress.update_traces(line_color=color)
    fig_progress.update_layout(yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig_progress, use_container_width=True)

    st.markdown("---")

    # ============================================================
    # БЛОК 4: АНТИ-РЕЙТИНГ ЗАДАНИЙ (МИССИИ)
    # ============================================================
    col_task1, col_task2 = st.columns(2)

    # усредняем по заданиям (по всем предметам/месяцам ученика)
    task_avg = (
        df_student.groupby("task_name", as_index=False)["task_percent"]
        .mean()
        .sort_values("task_percent")
    )

    with col_task1:
        st.subheader("⚔️ Твои главные враги")
        weak_tasks = task_avg[task_avg["task_percent"] < 50].head(3)
        if not weak_tasks.empty:
            for _, row in weak_tasks.iterrows():
                st.warning(f"**{row['task_name']}** — {row['task_percent']:.1f}%")
            st.info("💡 Сфокусируйся на них — это самый быстрый способ поднять общий уровень.")
        else:
            st.success("Критических пробелов нет. Это реально сильная база 💪")

    with col_task2:
        st.subheader("🛡️ Твоя база (Опора)")
        strong_tasks = task_avg[task_avg["task_percent"] > 80].sort_values("task_percent", ascending=False).head(3)
        if not strong_tasks.empty:
            for _, row in strong_tasks.iterrows():
                st.success(f"**{row['task_name']}** — {row['task_percent']:.1f}%")
        else:
            st.write("Пока нет тем выше 80%. Значит, есть куда расти — и это хорошо.")

    st.markdown("---")

    # ============================================================
    # БЛОК 5: ПРОГНОЗ (линейный тренд по месячным средним)
    # ============================================================
    st.subheader("🔮 Прогноз результатов на экзамене")

    if len(monthly) >= 2:
        x = np.arange(len(monthly))
        y = monthly["avg_score"].values.astype(float)

        # тренд
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)

        # прогноз на 2 шага вперёд (условно "экзамен через 2 месяца")
        predicted_score = float(np.clip(p(len(monthly) + 1), 0, 100))
        current_trend = float(z[0])  # прирост в месяц

        col_pred1, col_pred2 = st.columns(2)

        with col_pred1:
            if current_trend > 0:
                st.metric("Ожидаемый балл", f"{predicted_score:.1f}", f"+{current_trend:.1f} в месяц")
                st.caption("🔥 Тренд растущий. Главное — не терять регулярность.")
            else:
                st.metric("Ожидаемый балл", f"{predicted_score:.1f}", f"{current_trend:.1f} в месяц")
                st.caption("⚠️ Тренд не растёт. Значит, пора менять стратегию подготовки.")

        with col_pred2:
            if predicted_score < 60:
                st.warning("**Статус:** Зона риска. Делай ставку на базовые задания и стабильность.")
            elif predicted_score < 85:
                st.info("**Статус:** Хороший потенциал. Сокращай «обидные ошибки» и добирай баллы.")
            else:
                st.success("**Статус:** Очень высокий уровень. Время шлифовать сложные задания!")
    else:
        st.info("🤖 Для прогноза нужно хотя бы 2 месяца статистики.")

    # ============================================================
    # БОНУС: МОТИВАЦИОННАЯ ФРАЗА
    # ============================================================
    st.markdown("---")
    quotes = [
        "Тяжело в учении — легко на экзамене!",
        "Твой единственный соперник — ты вчерашний.",
        "Маленькие шаги ведут к большим результатам.",
        "Даже самый высокий уровень начинается с первого XP."
    ]
    st.markdown(f"💬 *Совет дня: {random.choice(quotes)}*")