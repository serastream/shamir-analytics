import streamlit as st
import pandas as pd
import plotly.express as px

def show_teacher_kpi(df: pd.DataFrame):
    """
    Отображает интерфейс рейтинга учителей на основе KPI.
    KPI = (Средний балл * 0.4) + (Прогресс за месяц * 3) + (% учеников вне риска * 0.3)
    """
    st.markdown("## 🏆 Рейтинг эффективности преподавателей")
    
    if df.empty:
        st.warning("Недостаточно данных для расчета KPI.")
        return

    # 1. Подготовка данных
    # Берем два последних месяца для расчета прогресса
    months = sorted(df['month_id'].unique())
    if len(months) < 1:
        st.error("В данных отсутствуют метки месяцев (month_id).")
        return

    last_m = months[-1]
    prev_m = months[-2] if len(months) > 1 else last_m

    teachers = df['teacher'].unique()
    kpi_results = []

    for teacher in teachers:
        t_df = df[df['teacher'] == teacher]
        
        # Данные за текущий и прошлый месяц
        curr_data = t_df[t_df['month_id'] == last_m]
        prev_data = t_df[t_df['month_id'] == prev_m]
        
        if curr_data.empty:
            continue

        # --- КРИТЕРИЙ 1: Средний результат (%) ---
        avg_score = curr_data['task_percent'].mean()
        
        # --- КРИТЕРИЙ 2: Дельта прогресса ---
        prev_avg = prev_data['task_percent'].mean() if not prev_data.empty else avg_score
        delta = avg_score - prev_avg
        
        # --- КРИТЕРИЙ 3: Работа с зоной риска (% учеников > 33 баллов) ---
        # Показывает, сколько учеников учитель "вытянул" из зоны двойки
        safe_zone_pct = (curr_data['task_percent'] > 33).mean() * 100
        
        # --- ИТОГОВЫЙ KPI ---
        # Мы даем большой вес Прогрессу (x3), чтобы поощрять рост, а не просто высокий старт
        kpi_score = (avg_score * 0.4) + (delta * 3) + (safe_zone_pct * 0.3)
        
        # Ограничиваем шкалой 0-100 для красоты
        kpi_score = max(0, min(100, kpi_score))

        kpi_results.append({
            "Преподаватель": teacher,
            "KPI": round(kpi_score, 1),
            "Ср. балл": round(avg_score, 1),
            "Прогресс": round(delta, 1),
            "Вне риска %": round(safe_zone_pct, 1),
            "Статус": "🔥 Рост" if delta > 2 else "↘️ Спад" if delta < -2 else "➡️ Стабильно"
        })

    # Создаем таблицу рейтинга
    ranking_df = pd.DataFrame(kpi_results).sort_values(by="KPI", ascending=False)

    # 2. Визуализация: ТОП-3 карточки
    st.markdown("### Лидеры месяца")
    top_cols = st.columns(min(len(ranking_df), 3))
    for i, (_, row) in enumerate(ranking_df.head(3).iterrows()):
        with top_cols[i]:
            st.metric(
                label=f"{i+1}. {row['Преподаватель']}",
                value=f"{row['KPI']} pts",
                delta=f"{row['Прогресс']}% за месяц"
            )

    st.write("---")

    # 3. Интерактивная таблица
    st.markdown("### Сводная таблица KPI")
    
    # Цветовая индикация статуса
    def color_status(val):
        color = 'green' if 'Рост' in val else 'red' if 'Спад' in val else 'gray'
        return f'color: {color}; font-weight: bold'

    st.dataframe(
        ranking_df.style.applymap(color_status, subset=['Статус']),
        use_container_width=True,
        hide_index=True
    )

    # 4. Аналитический график
    st.markdown("### Матрица эффективности")
    fig = px.scatter(
        ranking_df,
        x="Ср. балл",
        y="Прогресс",
        size="KPI",
        color="Статус",
        hover_name="Преподаватель",
        text="Преподаватель",
        title="Соотношение уровня знаний и темпа роста (размер пузырька = KPI)",
        color_discrete_map={"🔥 Рост": "#2ecc71", "➡️ Стабильно": "#3498db", "↘️ Спад": "#e74c3c"}
    )
    fig.update_traces(textposition='top center')
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("ℹ️ Как считается KPI?"):
        st.write("""
        Формула KPI учитывает три фактора:
        1. **Уровень знаний (40%)**: Текущий средний процент выполнения заданий.
        2. **Динамика (30%)**: Изменение среднего балла по сравнению с прошлым месяцем. Коэффициент x3 делает прогресс очень весомым.
        3. **Социальная ответственность (30%)**: Процент учеников, набравших более 33% (порог 'выживания'). 
        
        *Система поощряет учителей, которые не только держат высокую планку, но и постоянно улучшают результаты своих учеников.*
        """)