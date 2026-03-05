import streamlit as st
import pandas as pd
import plotly.express as px

def show_teacher_kpi(df):
    st.markdown("## 🏆 Рейтинг эффективности учителей")
    
    if df.empty:
        st.warning("Нет данных для расчета KPI.")
        return

    # --- БЛОК ФИЛЬТРОВ ---
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        # Получаем список месяцев из данных
        month_map = {row['month_id']: row['month'] for _, row in df[['month_id', 'month']].drop_duplicates().iterrows()}
        sorted_month_ids = sorted(month_map.keys())
        month_options = ["За всё время"] + [month_map[mid] for mid in sorted_month_ids]
        
        selected_month_name = st.selectbox("📅 Выберите период для анализа:", month_options)

    # --- ЛОГИКА ФИЛЬТРАЦИИ ---
    teachers = df['teacher'].unique()
    kpi_results = []

    for teacher in teachers:
        if pd.isna(teacher) or teacher == "Не указан": continue
        
        t_data_all = df[df['teacher'] == teacher]
        if t_data_all.empty: continue

        # Определяем, какие данные берем для расчета "Текущего" состояния
        if selected_month_name == "За всё время":
            current_avg = t_data_all['task_percent'].mean()
            # Сравниваем с самым первым месяцем (базой)
            first_month_id = sorted(t_data_all['month_id'].unique())[0]
            base_avg = t_data_all[t_data_all['month_id'] == first_month_id]['task_percent'].mean()
            progress = current_avg - base_avg
            period_label = "Весь период"
        else:
            # Ищем ID выбранного месяца
            curr_month_id = [mid for mid, name in month_map.items() if name == selected_month_name][0]
            t_data_month = t_data_all[t_data_all['month_id'] == curr_month_id]
            
            if t_data_month.empty: continue # Пропускаем, если у учителя нет данных за этот месяц
            
            current_avg = t_data_month['task_percent'].mean()
            
            # Ищем предыдущий месяц для этого учителя
            prev_months = [mid for mid in t_data_all['month_id'].unique() if mid < curr_month_id]
            if prev_months:
                prev_month_id = max(prev_months)
                prev_avg = t_data_all[t_data_all['month_id'] == prev_month_id]['task_percent'].mean()
                progress = current_avg - prev_avg
            else:
                progress = 0
            period_label = selected_month_name

        kpi_results.append({
            "Учитель": teacher,
            "Средний %": round(current_avg, 1),
            "Динамика": round(progress, 1),
            "KPI Score": round((current_avg * 0.7) + (progress * 0.3), 2),
            "Период": period_label
        })

    if not kpi_results:
        st.info("Нет данных для отображения за выбранный период.")
        return

    ranking_df = pd.DataFrame(kpi_results).sort_values(by="KPI Score", ascending=False)

    # --- ВИЗУАЛИЗАЦИЯ ---
    st.divider()
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Лидеры")
        for i, row in ranking_df.head(3).iterrows():
            st.metric(label=row["Учитель"], value=f"{row['KPI Score']}", delta=f"{row['Динамика']}%")

    with c2:
        fig = px.bar(
            ranking_df, x="KPI Score", y="Учитель", orientation='h',
            color="KPI Score", color_continuous_scale="RdYlGn",
            text="Средний %", title=f"Рейтинг: {selected_month_name}"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(ranking_df, use_container_width=True)