import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show(df: pd.DataFrame, student_name: str):
    # --- ДИЗАЙНЕРСКИЙ CSS ---
    st.markdown("""
        <style>
        .parent-container { background-color: #fcfcfd; }
        .metric-card {
            background: white; padding: 25px; border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.03);
            border: 1px solid #f0f0f0; height: 100%;
        }
        .advisor-box {
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
            padding: 20px; border-radius: 15px; border-left: 5px solid #4a90e2;
        }
        .recommendation-item {
            padding: 10px 0; border-bottom: 1px solid #eee; font-size: 0.95rem;
        }
        .status-badge {
            padding: 5px 12px; border-radius: 50px; font-size: 0.8rem; font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # Заголовок приветствия
    st.markdown(f"### 👋 Добро пожаловать, родитель {student_name}")
    st.caption("Здесь вы можете отслеживать успехи вашего ребенка и получать рекомендации по обучению.")

    # --- БЛОК 1: ГЛАВНЫЕ ИНДИКАТОРЫ ---
    c1, c2, c3 = st.columns(3)
    
    # Расчет данных
    avg_score = df['exam_percent'].mean()
    attendance = 95 # Заглушка, если нет данных
    completion = (df['task_percent'] > 0).mean() * 100

    with c1:
        st.markdown(f"""
            <div class="metric-card">
                <div style="color: #666; font-size: 0.8rem; text-transform: uppercase;">Средний результат</div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #2c3e50;">{avg_score:.1f}%</div>
                <div style="color: #27ae60; font-size: 0.9rem;">● Стабильный уровень</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
            <div class="metric-card">
                <div style="color: #666; font-size: 0.8rem; text-transform: uppercase;">Посещаемость</div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #2c3e50;">{attendance}%</div>
                <div style="color: #27ae60; font-size: 0.9rem;">● Без пропусков</div>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
            <div class="metric-card">
                <div style="color: #666; font-size: 0.8rem; text-transform: uppercase;">Выполнение ДЗ</div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #2c3e50;">{completion:.0f}%</div>
                <div style="color: #f39c12; font-size: 0.9rem;">● Есть долги по темам</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- БЛОК 2: ДИНАМИКА И СОВЕТЫ ---
    col_chart, col_advice = st.columns([1.5, 1])

    with col_chart:
        st.subheader("📈 Тренд обучения")
        # График динамики баллов
        monthly_data = df.groupby('month', sort=False)['exam_percent'].mean().reset_index()
        fig = px.area(monthly_data, x='month', y='exam_percent', 
                      line_shape='spline', color_discrete_sequence=['#4a90e2'])
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=300, margin=dict(l=0, r=0, t=20, b=0),
            yaxis=dict(range=[0, 105], showgrid=True, gridcolor='#f0f0f0')
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_advice:
        st.subheader("💡 Советы эксперта")
        st.markdown(f"""
            <div class="advisor-box">
                <b>Ваш ребенок сейчас в 20% лучших по школе!</b><br>
                <p style="font-size: 0.9rem; color: #555; margin-top: 10px;">
                Мы заметили, что {student_name} отлично справляется с теорией, но теряет баллы на сложных задачах.
                </p>
                <div class="recommendation-item">🔍 Сфокусироваться на 2-й части математики</div>
                <div class="recommendation-item">🧪 Похвалить за прогресс в химии (+15%)</div>
                <div class="recommendation-item">📅 Запланировать отдых в это воскресенье</div>
            </div>
        """, unsafe_allow_html=True)

    # --- БЛОК 3: ПОДРОБНОСТИ ПО ПРЕДМЕТАМ ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📚 Состояние по предметам")
    
    # Группировка по предметам
    subj_df = df.groupby('subject').agg({
        'exam_percent': 'mean',
        'task_percent': 'min'
    }).reset_index()

    for _, row in subj_df.iterrows():
        with st.container(border=True):
            cols = st.columns([2, 3, 1])
            cols[0].markdown(f"**{row['subject']}**")
            
            # Визуальный индикатор прогресса
            status_color = "#27ae60" if row['exam_percent'] > 70 else "#f39c12" if row['exam_percent'] > 50 else "#e74c3c"
            cols[1].markdown(f"""
                <div style="background: #eee; height: 10px; border-radius: 5px; margin-top: 10px;">
                    <div style="background: {status_color}; width: {row['exam_percent']}%; height: 10px; border-radius: 5px;"></div>
                </div>
            """, unsafe_allow_html=True)
            
            cols[2].markdown(f"**{row['exam_percent']:.1f}%**")
            
            if row['exam_percent'] < 50:
                st.warning(f"Рекомендуем уделить внимание теме: 'Основы {row['subject']}'")

    # --- ФУТЕР (Кнопка связи) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("✉️ Связаться с куратором обучения", use_container_width=True)