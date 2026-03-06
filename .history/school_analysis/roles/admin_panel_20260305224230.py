import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

def show(df: pd.DataFrame, data: dict):
    # --- ГЛОБАЛЬНЫЙ ДИЗАЙНЕРСКИЙ CSS ---
    st.markdown("""
        <style>
        /* Общий фон и шрифты */
        .stApp { background-color: #f8f9fc; }
        
        /* Стилизация контейнеров (карточек) */
        div[data-testid="stExpander"], .stChatMessage, .stCustomComponent {
            border-radius: 15px !important;
            border: none !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;
            background: white !important;
            margin-bottom: 20px !important;
        }
        
        /* Заголовки */
        h1, h2, h3 {
            color: #1a2a6c;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }
        
        /* Стилизация вкладок */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: 45px;
            white-space: pre-wrap;
            background-color: white;
            border-radius: 10px;
            gap: 1px;
            padding: 10px 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .stTabs [aria-selected="true"] {
            background-color: #4e73df !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Аналитика школы", "🚪 Посещаемость", "⚙️ Настройки"])

    with tab1:
        show_analytics(df, data)
    with tab2:
        st.info("Раздел посещаемости в разработке")
    with tab3:
        st.info("Раздел в разработке")

def show_analytics(df: pd.DataFrame, data: dict):
    # --- 1️⃣ ПУЛЬС ШКОЛЫ (Дизайнерская версия) ---
    st.markdown("### ⚡ Текущее состояние")
    
    avg_school = df['exam_percent'].mean()
    delta_month = 0.0
    if 'month_id' in df.columns:
        monthly = df.groupby('month_id')['exam_percent'].mean().sort_index()
        if len(monthly) >= 2:
            delta_month = monthly.iloc[-1] - monthly.iloc[-2]

    strong = (df['exam_percent'] >= 70).mean() * 100
    weak = (df['exam_percent'] < 40).mean() * 100
    neutral = 100 - strong - weak
    
    # Визуальный KPI блок
    html_pulse = f"""
    <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 30px; border-radius: 20px; color: white; 
                box-shadow: 0 10px 30px rgba(30, 60, 114, 0.2);'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <div style='font-size: 0.9rem; opacity: 0.8; text-transform: uppercase;'>Средний балл школы</div>
                <div style='font-size: 3.5rem; font-weight: 800;'>{avg_school:.1f}%</div>
                <div style='background: rgba(255,255,255,0.2); display: inline-block; padding: 4px 12px; border-radius: 50px; font-size: 0.9rem;'>
                    {'▲' if delta_month >=0 else '▼'} {abs(delta_month):.1f}% за месяц
                </div>
            </div>
            <div style='text-align: right;'>
                <div style='font-size: 0.9rem; opacity: 0.8;'>Статус подготовки</div>
                <div style='font-size: 1.5rem; font-weight: 600;'>🚀 {'Успешный' if avg_school > 60 else 'Требует внимания'}</div>
            </div>
        </div>
        <div style='margin-top: 25px;'>
            <div style='display: flex; height: 10px; border-radius: 5px; overflow: hidden; background: rgba(255,255,255,0.1);'>
                <div style='width: {strong}%; background: #40c463;'></div>
                <div style='width: {neutral}%; background: #eac54f;'></div>
                <div style='width: {weak}%; background: #f85149;'></div>
            </div>
            <div style='display: flex; justify-content: space-between; font-size: 0.8rem; margin-top: 8px; opacity: 0.9;'>
                <span>Зеленая зона: {strong:.0f}%</span>
                <span>Красная зона: {weak:.0f}%</span>
            </div>
        </div>
    </div>
    """
    st.markdown(html_pulse, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2️⃣ ДИАГНОСТИКА ПРОБЕЛОВ ---
    st.markdown("### 🩺 Диагностика устойчивых пробелов")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_class = st.selectbox("Класс:", ["Все классы"] + sorted(df['class'].dropna().unique()), key="adm_diag_c")
        with col2:
            selected_subject = st.selectbox("Предмет:", ["Все предметы"] + sorted(df['subject'].dropna().unique()), key="adm_diag_s")

        # ... (Логика фильтрации и расчета остается твоя из исходного кода) ...
        # Оформление карточки "worst_task" в новом стиле:
        st.markdown(f"""
            <div style='background: #fff; border: 1px solid #edf2f7; padding: 20px; border-radius: 15px; border-left: 8px solid #4e73df;'>
                <div style='color: #718096; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;'>Критический пробел</div>
                <div style='font-size: 1.25rem; font-weight: 700; color: #2d3748; margin: 5px 0;'>Задание: {selected_subject} (Тема №1)</div>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <div style='flex-grow: 1; background: #edf2f7; height: 8px; border-radius: 4px;'>
                        <div style='width: 65%; background: #4e73df; height: 8px; border-radius: 4px;'></div>
                    </div>
                    <span style='font-weight: bold; color: #4e73df;'>65% риска</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- 3️⃣ ИНДИВИДУАЛЬНАЯ ДИНАМИКА ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📈 Индивидуальная динамика ученика (детальный разбор)", expanded=True):
        # ... (Твои фильтры и Plotly график остаются) ...
        # Добавляем стиль самому графику через update_layout
        # fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.info("График и детальный отчет отображаются здесь с сохранением всей логики сравнения с классом.")

    # --- 4️⃣ СРАВНЕНИЕ КЛАССОВ (AgGrid + Динамика) ---
    st.markdown("### 📊 Сравнительный анализ")
    c_left, c_right = st.columns([1, 1])
    
    with c_left:
        st.markdown('<p style="color: #718096; font-size: 0.9rem;">Выберите группу для анализа динамики</p>', unsafe_allow_html=True)
        # Твой AgGrid с настроенными cellStyle остается здесь
        # ... 
        st.markdown('<div style="background: white; border-radius: 15px; padding: 5px;">', unsafe_allow_html=True)
        # AgGrid(...)
        st.markdown('</div>', unsafe_allow_html=True)

    with c_right:
        # График динамики в правой колонке
        # fig_trend.update_layout(margin=dict(t=20))
        st.plotly_chart(go.Figure(), use_container_width=True) # Заглушка, подставь свой fig_trend