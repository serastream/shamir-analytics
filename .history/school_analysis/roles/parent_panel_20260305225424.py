import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show(df: pd.DataFrame, student_id: str, student_name: str):
    # --- 1. ПРЕМИАЛЬНЫЙ ДИЗАЙН (CSS) ---
    st.markdown("""
        <style>
        .main { background-color: #f8f9fc; }
        
        /* Шапка */
        .parent-header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 30px; border-radius: 20px; color: white;
            margin-bottom: 25px; box-shadow: 0 10px 20px rgba(30, 60, 114, 0.15);
        }
        
        /* Карточки похвалы и внимания */
        .praise-card {
            background: #f0fff4; padding: 20px; border-radius: 18px;
            border-left: 6px solid #38a169; box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            height: 100%;
        }
        .warning-card {
            background: #fffaf0; padding: 20px; border-radius: 18px;
            border-left: 6px solid #dd6b20; box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            height: 100%;
        }
        
        /* Стилизация предметов */
        .subject-box {
            background: white; padding: 15px; border-radius: 12px;
            margin-bottom: 10px; border: 1px solid #edf2f7;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- 2. ШАПКА ПАНЕЛИ ---
    st.markdown(f"""
        <div class="parent-header">
            <div style="font-size: 0.9rem; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px;">Личный кабинет родителя</div>
            <div style="font-size: 2.5rem; font-weight: 800; margin: 5px 0;">{student_name}</div>
            <div style="font-size: 1.1rem; opacity: 0.9;">Ваш ребенок показывает уверенные результаты в обучении</div>
        </div>
    """, unsafe_allow_html=True)

    # --- 3. ОСНОВНЫЕ МЕТРИКИ ---
    avg_score = df['exam_percent'].mean()
    subj_avg = df.groupby('subject')['exam_percent'].mean()
    best_subject = subj_avg.idxmax()
    worst_subject = subj_avg.idxmin()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Средний балл", f"{avg_score:.1f}%")
    with c2:
        st.metric("Лучший предмет", best_subject)
    with c3:
        st.metric("Требует внимания", worst_subject)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 4. НОВЫЕ РУБРИКИ: ПОХВАЛА И ВНИМАНИЕ ---
    st.subheader("💡 Аналитика родителя")
    col_praise, col_warning = st.columns(2)

    # Логика похвалы
    with col_praise:
        st.markdown(f"""
            <div class="praise-card">
                <div style="font-size: 1.2rem; font-weight: 800; color: #2f855a; margin-bottom: 10px;">🌟 За что похвалить?</div>
                <p style="font-size: 0.95rem; color: #2d3748; line-height: 1.6;">
                    <b>Блестящие результаты в {best_subject}:</b> Ваш ребенок набрал {subj_avg.max():.1f}%! 
                    Это результат выше среднего. Обязательно отметьте его старания — позитивное подкрепление 
                    поможет сохранить интерес к учебе.
                </p>
                <div style="font-size: 0.85rem; color: #48bb78; font-weight: 600;">✨ Совет: Спросите ребенка, что ему больше всего нравится в этом предмете.</div>
            </div>
        """, unsafe_allow_html=True)

    # Логика внимания
    with col_warning:
        st.markdown(f"""
            <div class="warning-card">
                <div style="font-size: 1.2rem; font-weight: 800; color: #c05621; margin-bottom: 10px;">🔍 На что обратить внимание?</div>
                <p style="font-size: 0.95rem; color: #2d3748; line-height: 1.6;">
                    <b>Сложности с {worst_subject}:</b> Здесь текущий балл составляет {subj_avg.min():.1f}%. 
                    Скорее всего, последние темы были сложными. Попробуйте мягко уточнить, 
                    нужна ли дополнительная консультация или помощь с домашним заданием.
                </p>
                <div style="font-size: 0.85rem; color: #ed8936; font-weight: 600;">🎯 Цель: Подтянуть {worst_subject} на 5-10% до конца месяца.</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 5. ГРАФИК ДИНАМИКИ ---
    st.subheader("📈 Динамика успеваемости")
    if 'month' in df.columns:
        trend = df.groupby('month', sort=False)['exam_percent'].mean().reset_index()
        fig = px.area(trend, x='month', y='exam_percent', line_shape='spline')
        fig.update_traces(line_color='#2a5298', fillcolor='rgba(42, 82, 152, 0.1)')
        fig.update_layout(
            height=350, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(range=[0, 105], title="Балл в %"), xaxis=dict(title="")
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- 6. ДЕТАЛИЗАЦИЯ ПО ПРЕДМЕТАМ ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📚 Состояние по всем предметам")

    for subject, score in subj_avg.items():
        # Динамический цвет
        color = "#38a169" if score > 70 else "#d69e2e" if score > 50 else "#e53e3e"
        
        st.markdown(f"""
            <div class="subject-box">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: 700; color: #2d3748; font-size: 1.1rem;">{subject}</span>
                    <span style="font-weight: 800; color: {color};">{score:.1f}%</span>
                </div>
                <div style="background: #edf2f7; height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: {color}; width: {score}%; height: 100%; border-radius: 6px;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- 7. КНОПКА СВЯЗИ ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.button(f"✉️ Отправить сообщение куратору {student_name}", use_container_width=True)