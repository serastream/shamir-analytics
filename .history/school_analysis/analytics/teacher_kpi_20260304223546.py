import streamlit as st
import pandas as pd
import plotly.express as px

def show_teacher_kpi(df):
    st.markdown("## 🏆 Рейтинг эффективности учителей")
    
    if df.empty:
        st.warning("Нет данных для расчета KPI.")
        return

    # Проверяем наличие необходимых колонок из preprocess.py
    required_cols = ['teacher', 'task_percent', 'month_id']
    if not all(col in df.columns for col in required_cols):
        st.error(f"В данных отсутствуют необходимые колонки для KPI: {set(required_cols) - set(df.columns)}")
        return

    teachers = df['teacher'].unique()
    kpi_results = []

    for teacher in teachers:
        if pd.isna(teacher) or teacher == "Не указан":
            continue
            
        t_data = df[df['teacher'] == teacher]
        
        # 1. Средний процент выполнения заданий (Качество знаний)
        avg_score = t_data['task_percent'].mean()
        
        # 2. Динамика (сравнение текущего месяца с предыдущим)
        months = sorted(t_data['month_id'].unique())
        progress = 0
        if len(months) >= 2:
            last_month = t_data[t_data['month_id'] == months[-1]]['task_percent'].mean()
            prev_month = t_data[t_data['month_id'] == months[-2]]['task_percent'].mean()
            progress = last_month - prev_month

        # Итоговый KPI (пример формулы: 80% - средний балл, 20% - прогресс)
        final_kpi = (avg_score * 0.8) + (progress * 0.2)
        
        kpi_results.append({
            "Учитель": teacher,
            "Средний %": round(avg_score, 1),
            "Прогресс": round(progress, 1),
            "KPI Score": round(final_kpi, 2)
        })

    if not kpi_results:
        st.info("Недостаточно данных для формирования рейтинга.")
        return

    # Создаем таблицу и сортируем
    ranking_df = pd.DataFrame(kpi_results).sort_values(by="KPI Score", ascending=False)

    # Визуализация
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Лидеры месяца")
        for i, row in ranking_df.head(3).iterrows():
            st.metric(label=row["Учитель"], value=f"{row['KPI Score']} pts", delta=f"{row['Прогресс']}%")

    with col2:
        fig = px.bar(
            ranking_df, 
            x="KPI Score", 
            y="Учитель", 
            orientation='h',
            title="Общий рейтинг",
            color="KPI Score",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(ranking_df, use_container_width=True)