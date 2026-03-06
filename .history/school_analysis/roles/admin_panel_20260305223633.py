import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def show_analytics(df: pd.DataFrame, data: dict):
    # --- 1. СТИЛИЗАЦИЯ (CSS) ---
    st.markdown("""
        <style>
        .kpi-card {
            background: white; padding: 20px; border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center;
            border-bottom: 5px solid #eee;
        }
        .kpi-value { font-size: 2rem; font-weight: bold; margin: 5px 0; }
        .kpi-label { font-size: 0.85rem; color: #666; text-transform: uppercase; letter-spacing: 1px; }
        .status-pill {
            padding: 4px 12px; border-radius: 50px; font-size: 0.8rem; font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Подготовка данных для KPI ---
    avg_school = df['exam_percent'].mean()
    
    # Расчет динамики
    delta_month = 0.0
    if 'month_id' in df.columns:
        monthly = df.groupby('month_id')['exam_percent'].mean().sort_index()
        if len(monthly) >= 2:
            delta_month = monthly.iloc[-1] - monthly.iloc[-2]

    risk_group = (df['exam_percent'] < 40).mean() * 100
    top_performers = (df['exam_percent'] >= 75).mean() * 100

    # --- 2. KPI БАННЕР (4 КАРТОЧКИ) ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f'<div class="kpi-card" style="border-color: #4e73df;"><div class="kpi-label">Средний балл</div><div class="kpi-value">{avg_school:.1f}%</div><div style="color: {"green" if delta_month >=0 else "red"}">{"▲" if delta_month >=0 else "▼"} {abs(delta_month):.1f}%</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card" style="border-color: #e74a3b;"><div class="kpi-label">В зоне риска</div><div class="kpi-value">{risk_group:.1f}%</div><div style="font-size: 0.8rem; color:#888">Нуждаются в поддержке</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card" style="border-color: #1cc88a;"><div class="kpi-label">Отличники</div><div class="kpi-value">{top_performers:.1f}%</div><div style="font-size: 0.8rem; color:#888">Стабильно 75+ балов</div></div>', unsafe_allow_html=True)
    with c4:
        # Индекс вовлеченности (сколько учеников сдали последний пробник)
        latest_month = df['month_id'].max()
        active_pct = (df[df['month_id'] == latest_month]['student_id'].nunique() / df['student_id'].nunique()) * 100
        st.markdown(f'<div class="kpi-card" style="border-color: #f6c23e;"><div class="kpi-label">Явка на пробник</div><div class="kpi-value">{active_pct:.0f}%</div><div style="font-size: 0.8rem; color:#888">За последний месяц</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. ТЕПЛОВАЯ КАРТА ПРОБЛЕМНЫХ ЗОН ---
    st.subheader("🗺️ Карта успеваемости: Классы и Предметы")
    
    # Готовим матрицу для Heatmap
    heatmap_data = df.groupby(['class', 'subject'])['exam_percent'].mean().unstack().fillna(0)
    
    fig_heat = px.imshow(
        heatmap_data,
        labels=dict(x="Предмет", y="Класс", color="Средний %"),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale="RdYlGn", # От красного к зеленому
        aspect="auto",
        text_auto=".1f"
    )
    fig_heat.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_heat, use_container_width=True)

    # --- 4. ДИАГНОСТИКА ПРОБЕЛОВ (В НОВОМ СТИЛЕ) ---
    st.markdown("---")
    col_diag_1, col_diag_2 = st.columns([1, 1])

    with col_diag_1:
        st.markdown("### 🩺 Критические темы")
        # Берем задания, где средний балл по школе < 50%
        task_fail = df.groupby(['subject', 'task_name'])['task_percent'].mean().reset_index()
        task_fail = task_fail.sort_values('task_percent').head(5)
        
        for _, row in task_fail.iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['subject']}**: {row['task_name']}")
                st.progress(row['task_percent']/100)
                st.caption(f"Средний балл школы: {row['task_percent']:.1f}%")

    with col_diag_2:
        st.markdown("### 📈 Лидеры роста")
        # Находим классы с самой большой позитивной дельтой
        if 'month_id' in df.columns:
            class_trend = df.groupby(['class', 'month_id'])['exam_percent'].mean().reset_index()
            # Упрощенная логика: последний месяц минус первый
            class_growth = class_trend.groupby('class').apply(lambda x: x.iloc[-1]['exam_percent'] - x.iloc[0]['exam_percent'] if len(x)>1 else 0)
            class_growth = class_growth.sort_values(ascending=False).head(5)

            for cls, val in class_growth.items():
                st.success(f"**{cls}** — прогресс **+{val:.1f} п.п.** за период")
        else:
            st.info("Данные о росте будут доступны после 2-го месяца обучения")

    # --- 5. ТАБЛИЦА-ДЕТАЛИЗАЦИЯ (ОБЛЕГЧЕННАЯ) ---
    st.markdown("---")
    st.subheader("📋 Детальная статистика по группам")
    # Оставляем AgGrid, но делаем его компактнее или заменяем на st.dataframe с новым дизайном
    grid_data = df.groupby(['class', 'subject']).agg(
        avg_score=('exam_percent', 'mean'),
        students=('student_id', 'nunique')
    ).reset_index().sort_values('avg_score')
    
    st.dataframe(
        grid_data,
        column_config={
            "class": "Класс",
            "subject": "Предмет",
            "avg_score": st.column_config.ProgressColumn("Средний балл", format="%.1f%%", min_value=0, max_value=100),
            "students": "Учеников"
        },
        use_container_width=True,
        hide_index=True
    )