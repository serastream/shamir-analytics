import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show(df: pd.DataFrame, student_id: str, student_name: str):
    # --- 1. ПРЕМИАЛЬНЫЙ CSS СТИЛЬ ---
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        
        /* Карточки KPI */
        .parent-kpi-card {
            background: white; padding: 25px; border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.02);
            border: 1px solid #f0f2f6; text-align: center;
        }
        .kpi-label { font-size: 0.8rem; color: #7f8c8d; text-transform: uppercase; font-weight: 600; margin-bottom: 10px; }
        .kpi-value { font-size: 2.2rem; font-weight: 800; color: #2c3e50; }
        
        /* Блок рекомендаций */
        .advisor-card {
            background: linear-gradient(135deg, #ffffff 0%, #f9f9ff 100%);
            padding: 25px; border-radius: 25px;
            border-left: 6px solid #4e73df;
            box-shadow: 0 10px 30px rgba(78, 115, 223, 0.05);
        }
        
        /* Прогресс-бары предметов */
        .subject-row {
            background: white; padding: 15px 20px; border-radius: 15px;
            margin-bottom: 10px; border: 1px solid #f0f2f6;
        }
        </style>
    """, unsafe_allow_html=True)

    # Заголовок
    st.markdown(f"### ✨ Личный кабинет родителя: {student_name}")
    st.markdown("---")

    # --- 2. ГЛАВНЫЕ ПОКАЗАТЕЛИ (KPI) ---
    # Расчеты (используем твои данные)
    avg_score = df['exam_percent'].mean()
    progress_delta = 5.4  # Имитация прогресса за месяц
    attendance = 98       # Имитация (можно подтянуть из данных)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="parent-kpi-card">
            <div class="kpi-label">Текущий балл</div>
            <div class="kpi-value">{avg_score:.1f}%</div>
            <div style="color: #27ae60; font-size: 0.9rem;">▲ {progress_delta}% за месяц</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="parent-kpi-card">
            <div class="kpi-label">Посещаемость</div>
            <div class="kpi-value">{attendance}%</div>
            <div style="color: #27ae60; font-size: 0.9rem;">Идеальный показатель</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        # Шкала "До цели" (например, цель 85%)
        target = 85
        st.markdown(f"""<div class="parent-kpi-card">
            <div class="kpi-label">До цели (85%)</div>
            <div class="kpi-value">{max(0, target - avg_score):.1f}%</div>
            <div style="color: #7f8c8d; font-size: 0.9rem;">осталось набрать</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. ДИНАМИКА И ПСИХОЛОГИЧЕСКАЯ ПОДДЕРЖКА ---
    col_chart, col_advisor = st.columns([1.5, 1])

    with col_chart:
        st.subheader("📈 Тренд развития")
        # Гладкий график прогресса
        if 'month' in df.columns:
            trend_df = df.groupby('month', sort=False)['exam_percent'].mean().reset_index()
            fig = px.area(trend_df, x='month', y='exam_percent', line_shape='spline')
            fig.update_traces(line_color='#4e73df', fillcolor='rgba(78, 115, 223, 0.1)')
            fig.update_layout(
                height=300, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(range=[0, 100], showgrid=True, gridcolor='#f0f0f0'),
                xaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_advisor:
        st.subheader("💡 Советы эксперта")
        st.markdown(f"""
            <div class="advisor-card">
                <div style="font-weight: 700; color: #2c3e50; margin-bottom: 10px;">Психологический комфорт</div>
                <p style="font-size: 0.9rem; color: #5a6c7d; line-height: 1.5;">
                    {student_name} показывает отличную динамику в точных науках. 
                    <b>Рекомендация:</b> Не нагружайте ребенка дополнительными занятиями в эти выходные, 
                    ему нужно восстановить ментальный ресурс перед пробником.
                </p>
                <div style="margin-top: 15px;">
                    <span class="status-badge" style="background: #e8f5e9; color: #2e7d32;">✅ Дисциплина в норме</span><br>
                    <span class="status-badge" style="background: #fff3e0; color: #ef6c00; margin-top: 5px; display: inline-block;">⚠️ Усталость: средняя</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- 4. СОСТОЯНИЕ ПО ПРЕДМЕТАМ ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📚 Детализация по предметам")

    subjects = df.groupby('subject')['exam_percent'].mean().reset_index()
    
    for _, row in subjects.iterrows():
        # Определяем статус
        score = row['exam_percent']
        status_text = "Лидер" if score > 75 else "Стабильно" if score > 50 else "Нужна помощь"
        status_color = "#27ae60" if score > 75 else "#f39c12" if score > 50 else "#e74c3c"

        st.markdown(f"""
            <div class="subject-row">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 700; color: #2c3e50; width: 120px;">{row['subject']}</div>
                    <div style="flex-grow: 1; margin: 0 20px;">
                        <div style="background: #eee; height: 8px; border-radius: 10px;">
                            <div style="background: {status_color}; width: {score}%; height: 8px; border-radius: 10px;"></div>
                        </div>
                    </div>
                    <div style="font-weight: 800; color: {status_color}; width: 50px; text-align: right;">{score:.0f}%</div>
                    <div style="margin-left: 20px; font-size: 0.8rem; background: #f8f9fa; padding: 3px 10px; border-radius: 5px; color: #7f8c8d; min-width: 100px; text-align: center;">
                        {status_text}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- 5. ФУТЕР ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.button(f"📞 Записаться на встречу с учителем {student_name}", use_container_width=True)