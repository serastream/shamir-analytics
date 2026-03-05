import streamlit as st
import pandas as pd
import plotly.express as px

def show(df_student, student_name):
    st.header(f"🚀 Личный кабинет: {student_name}")
    
    # Сортируем данные по месяцам для корректных графиков
    df_student = df_student.sort_values('month_id')
    
    # --- БЛОК 1: РАНГИ И XP (ГЕЙМИФИКАЦИЯ) ---
    last_score = df_student.iloc[-1]['avg_score'] if not df_student.empty else 0
    
    # Логика рангов
    if last_score < 40:
        rank, icon, color = "Искатель", "🥉", "#CD7F32"
    elif last_score < 65:
        rank, icon, color = "Ученик гильдии", "🥈", "#C0C0C0"
    elif last_score < 85:
        rank, icon, color = "Мастер", "🥇", "#FFD700"
    else:
        rank, icon, color = "Грандмастер", "💎", "#00FFFF"

    col_rank1, col_rank2 = st.columns([1, 2])
    with col_rank1:
        st.markdown(f"<h2 style='text-align: center; color: {color};'>{icon}<br>{rank}</h2>", unsafe_allow_html=True)
    
    with col_rank2:
        st.write(f"**Твой текущий уровень:** {last_score} XP (баллов)")
        # Прогресс до следующего уровня (ближайшая сотня или порог)
        next_level = 100
        progress = last_score / next_level
        st.progress(progress)
        st.caption(f"До уровня Грандмастер осталось {max(0, 85 - last_score)} баллов")

    st.markdown("---")

    # --- БЛОК 2: АЧИВКИ (СКРЫТЫЕ ДОСТИЖЕНИЯ) ---
    st.subheader("🏆 Твои достижения")
    
    achievements = st.columns(4)
    
    # Логика проверки ачивок
    with achievements[0]:
        # Ачивка 1: Рост 2 месяца подряд
        if len(df_student) >= 2 and df_student.iloc[-1]['avg_score'] > df_student.iloc[-2]['avg_score']:
            st.markdown("📈 **Набирающий высоту**\n\nБалл вырос по сравнению с прошлым месяцем!")
        else:
            st.markdown("🔒 *Растишка*\n\n(Улучши результат в след. месяце)")

    with achievements[1]:
        # Ачивка 2: Сверх-высокий балл за любое задание
        if (df_student['task_percent'] == 100).any():
            st.markdown("🎯 **Снайпер**\n\nЕсть хотя бы одно задание на 100%!")
        else:
            st.markdown("🔒 *Меткий глаз*\n\n(Реши хотя бы одну задачу без ошибок)")

    with achievements[2]:
        # Ачивка 3: Стабильность (нет двоек)
        if (df_student['avg_score'] > 40).all():
            st.markdown("🛡️ **Непробиваемый**\n\nНи одного проваленного месяца в году!")
        else:
            st.markdown("🔒 *Щит*\n\n(Не допускай падения ниже 40 баллов)")

    with achievements[3]:
        # Ачивка 4: Рекорд
        if last_score == df_student['avg_score'].max() and len(df_student) > 1:
            st.balloons() # Праздничный эффект!
            st.markdown("👑 **На пике формы**\n\nЭто твой лучший результат за все время!")
        else:
            st.markdown("🔒 *Рекордсмен*\n\n(Побей свой лучший результат)")

    st.markdown("---")

    # --- БЛОК 3: ГРАФИК ПРОГРЕССА ---
    st.subheader("📊 Твоя кривая силы")
    fig_progress = px.line(df_student, x='month_id', y='avg_score', 
                          markers=True, line_shape='spline',
                          title="Динамика среднего балла по месяцам")
    fig_progress.update_traces(line_color=color)
    st.plotly_chart(fig_progress, use_container_width=True)

    import numpy as np

    # --- БЛОК 4: АНТИ-РЕЙТИНГ ЗАДАНИЙ (МИССИИ) ---
    col_task1, col_task2 = st.columns(2)
    
    with col_task1:
        st.subheader("⚔️ Твои главные враги")
        # Берем задания с худшим процентом выполнения
        weak_tasks = df_student[df_student['task_percent'] < 50].sort_values('task_percent').head(3)
        if not weak_tasks.empty:
            for _, row in weak_tasks.iterrows():
                st.warning(f"**{row['task_name']}** — пройдено на {row['task_percent']}%")
            st.info("💡 Сосредоточься на этих темах, чтобы быстро поднять балл!")
        else:
            st.success("У тебя нет критических пробелов! Красавчик!")

    with col_task2:
        st.subheader("🛡️ Твоя база (Опора)")
        strong_tasks = df_student[df_student['task_percent'] > 80].sort_values('task_percent', ascending=False).head(3)
        if not strong_tasks.empty:
            for _, row in strong_tasks.iterrows():
                st.success(f"**{row['task_name']}** — стабильные {row['task_percent']}%")
        else:
            st.write("Пока нет тем, освоенных на 80%. Всё впереди!")

    # --- БОНУС: МОТИВАЦИОННАЯ ЦИТАТА ---
    st.markdown("---")
    quotes = [
        "Тяжело в учении — легко на экзамене!",
        "Твой единственный соперник — ты вчерашний.",
        "Маленькие шаги ведут к большим результатам.",
        "Даже самый высокий уровень начинается с первого XP."
    ]
    import random
    st.markdown(f"💬 *Совет дня: {random.choice(quotes)}*")

        # --- БЛОК 5: ПРОГНОЗ БАЛЛОВ (ПРЕДСКАЗАНИЕ) ---
    st.subheader("🔮 Прогноз результатов на экзамене")

    if len(df_student) >= 2:
        # Подготовка данных для простого линейного тренда
        x = np.arange(len(df_student)).reshape(-1, 1) # Порядковый номер месяца
        y = df_student['avg_score'].values
        
        # Считаем коэффициент наклона (упрощенная линейная регрессия)
        z = np.polyfit(x.flatten(), y, 1)
        p = np.poly1d(z)
        
        # Прогноз на "Экзаменационный месяц" (допустим, это через 2 месяца от текущего)
        predicted_score = min(100, round(p(len(df_student) + 1)))
        current_trend = z[0] # Скорость роста балла в месяц

        col_pred1, col_pred2 = st.columns(2)

        with col_pred1:
            if current_trend > 0:
                st.metric("Ожидаемый балл", f"{predicted_score}", f"+{round(current_trend, 1)} в месяц", delta_color="normal")
                st.caption("🔥 Ты идешь на подъем! Если сохранишь темп, это твой результат.")
            else:
                st.metric("Ожидаемый балл", f"{predicted_score}", f"{round(current_trend, 1)} в месяц", delta_color="inverse")
                st.caption("⚠️ Внимание: темп замедлился. Нужно поднажать, чтобы не потерять баллы.")

        with col_pred2:
            # Интерактивный совет на основе прогноза
            if predicted_score < 60:
                st.warning("**Статус:** Зона риска. Нужно сфокусироваться на 'базовых' заданиях (1-10).")
            elif predicted_score < 85:
                st.info("**Статус:** Хороший потенциал. Твоя задача — минимизировать 'обидные' ошибки.")
            else:
                st.success("**Статус:** Претендент на бюджет. Время браться за самые сложные задачи!")
    else:
        st.info("🤖 Для построения прогноза мне нужно хотя бы 2 месяца твоей статистики.")