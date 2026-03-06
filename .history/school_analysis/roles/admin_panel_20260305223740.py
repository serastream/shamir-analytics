import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def show(df: pd.DataFrame, data: dict):
    # --- 1. СТИЛИЗАЦИЯ (CSS) ---
    st.markdown("""
        <style>
        .admin-kpi-card {
            background: white; padding: 20px; border-radius: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.03); text-align: center;
            border-bottom: 4px solid #eee; height: 100%;
        }
        .kpi-val { font-size: 1.8rem; font-weight: 800; color: #1f2d3d; margin: 5px 0; }
        .kpi-title { font-size: 0.8rem; color: #7f8c8d; text-transform: uppercase; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)

    # Вкладки
    tab1, tab2, tab3 = st.tabs(["📊 Аналитика", "🚪 Посещаемость", "⚙️ Настройки"])

    with tab1:
        render_analytics(df)

    with tab2:
        st.info("Раздел посещаемости в разработке")
        
    with tab3:
        st.info("Настройки системы")

def render_analytics(df: pd.DataFrame):
    st.title("🏛️ Центр управления школой")

    # --- Подготовка метрик ---
    avg_score = df['exam_percent'].mean()
    risk_pct = (df['exam_percent'] < 45).mean() * 100
    top_pct = (df['exam_percent'] > 75).mean() * 100
    
    # Расчет динамики (текущий месяц vs предыдущий)
    delta = 0
    if 'month_id' in df.columns:
        m_stats = df.groupby('month_id')['exam_percent'].mean().sort_index()
        if len(m_stats) >= 2:
            delta = m_stats.iloc[-1] - m_stats.iloc[-2]

    # --- 2. KPI БАННЕР ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="admin-kpi-card" style="border-color: #4e73df;"><div class="kpi-title">Средний балл</div><div class="kpi-val">{avg_score:.1f}%</div><div style="color:{"green" if delta>=0 else "red"}; font-size:0.9rem">{"▲" if delta>=0 else "▼"} {abs(delta):.1f}%</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="admin-kpi-card" style="border-color: #e74a3b;"><div class="kpi-title">Зона риска</div><div class="kpi-val">{risk_pct:.1f}%</div><div style="color:#888; font-size:0.8rem">нужна поддержка</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="admin-kpi-card" style="border-color: #1cc88a;"><div class="kpi-title">Отличники</div><div class="kpi-val">{top_pct:.1f}%</div><div style="color:#888; font-size:0.8rem">выше 75 баллов</div></div>', unsafe_allow_html=True)
    with c4:
        total_stud = df['student_id'].nunique()
        st.markdown(f'<div class="admin-kpi-card" style="border-color: #f6c23e;"><div class="kpi-title">Всего учеников</div><div class="kpi-val">{total_stud}</div><div style="color:#888; font-size:0.8rem">в активных группах</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. ТЕПЛОВАЯ КАРТА (ВМЕСТО ТАБЛИЦЫ) ---
    st.subheader("🗺️ Тепловая карта успеваемости (Класс / Предмет)")
    
    pivot_df = df.groupby(['class', 'subject'])['exam_percent'].mean().unstack().fillna(0)
    
    fig_heat = px.imshow(
        pivot_df,
        text_auto=".0f",
        aspect="auto",
        color_continuous_scale="RdYlGn",
        labels=dict(x="Предмет", y="Класс", color="Балл %")
    )
    fig_heat.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350)
    st.plotly_chart(fig_heat, use_container_width=True)

    # --- 4. ДИАГНОСТИКА И ДЕТАЛИ ---
    col_l, col_r = st.columns([1, 1])
    
    with col_l:
        st.subheader("🩺 Системные пробелы")
        # Ищем задачи, которые провалены у большинства
        bad_tasks = df.groupby(['subject', 'task_name'])['task_percent'].mean().reset_index()
        bad_tasks = bad_tasks.sort_values('task_percent').head(4)
        
        for _, r in bad_tasks.iterrows():
            with st.container(border=True):
                st.write(f"**{r['subject']}**: {r['task_name']}")
                st.progress(r['task_percent']/100)
                st.caption(f"Средний балл по школе: {r['task_percent']:.1f}%")

    with col_r:
        st.subheader("📊 Детальный обзор")
        st.dataframe(
            df.groupby(['class', 'subject'])['exam_percent'].mean().reset_index(),
            column_config={
                "class": "Класс",
                "subject": "Предмет",
                "exam_percent": st.column_config.ProgressColumn("Успеваемость", format="%.0f%%", min_value=0, max_value=100)
            },
            hide_index=True,
            use_container_width=True
        )