import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random

def show(df: pd.DataFrame, student_id: int, student_name: str):
    # --- СТИЛИЗАЦИЯ (CSS) ---
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .stMetric { background-color: #ffffff; border-radius: 15px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .achievement-card { 
            background: white; border-radius: 15px; padding: 20px; text-align: center; 
            border: 1px solid #eee; transition: 0.3s; height: 100%;
        }
        .achievement-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
        .rank-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border-radius: 20px; padding: 30px; margin-bottom: 25px;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Подготовка данных (твоя логика остается) ---
    df_student_all = df.query("student_id == @student_id").copy()
    if df_student_all.empty:
        st.info("👋 Привет! Твои результаты скоро появятся здесь.")
        return

    # Нормализация
    df_student_all["month_id"] = pd.to_numeric(df_student_all["month_id"], errors="coerce")
    df_student_all["task_percent"] = pd.to_numeric(df_student_all["task_percent"], errors="coerce")
    if "exam_percent" in df_student_all.columns:
        df_student_all["exam_percent"] = pd.to_numeric(df_student_all["exam_percent"], errors="coerce")
    df_student_all = df_student_all.dropna(subset=["month_id"]).sort_values("month_id")

    # --- ШАПКА ---
    st.title(f"🚀 Твой прогресс, {student_name}!")
    
    # --- ФИЛЬТРЫ ---
    subjects = sorted([x for x in df_student_all["subject"].dropna().unique().tolist() if str(x).strip() != ""])
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        subject_choice = st.pills("Выбери предмет для анализа:", options=["Все предметы"] + subjects, default="Все предметы")
    
    if subject_choice != "Все предметы":
        df_student = df_student_all[df_student_all["subject"] == subject_choice].copy()
    else:
        df_student = df_student_all.copy()

    # Считаем XP
    monthly = df_student.groupby("month_id", as_index=False).agg(avg_score=("task_percent", "mean")).sort_values("month_id")
    monthly["avg_score"] = monthly["avg_score"].clip(0, 100)
    last_score = float(monthly["avg_score"].iloc[-1]) if not monthly.empty else 0.0

    # --- БЛОК 1: РАНГ (HERO SECTION) ---
    if last_score < 40: rank, icon, color, grad = "Искатель", "🥉", "#CD7F32", "linear-gradient(135deg, #a8cABA 0%, #5D4157 100%)"
    elif last_score < 65: rank, icon, color, grad = "Ученик гильдии", "🥈", "#C0C0C0", "linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%)"
    elif last_score < 85: rank, icon, color, grad = "Мастер", "🥇", "#FFD700", "linear-gradient(135deg, #f6d365 0%, #fda085 100%)"
    else: rank, icon, color, grad = "Грандмастер", "💎", "#00FFFF", "linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)"

    st.markdown(f"""
        <div class="rank-card" style="background: {grad};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <p style="font-size: 1.2rem; margin-bottom: 0; opacity: 0.9;">Твой текущий статус:</p>
                    <h1 style="margin-top: 0; color: white;">{icon} {rank}</h1>
                </div>
                <div style="text-align: right;">
                    <p style="font-size: 2.5rem; font-weight: bold; margin-bottom: 0;">{last_score:.1f} XP</p>
                    <p style="opacity: 0.8;">из 100 возможных</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- БЛОК 2: АЧИВКИ (КАРТОЧКИ) ---
    st.subheader("🏆 Твои достижения")
    a1, a2, a3, a4 = st.columns(4)
    
    def achievement_card(col, title, desc, icon, active):
        opacity = "1" if active else "0.3"
        filter_gray = "" if active else "filter: grayscale(100%);"
        col.markdown(f"""
            <div class="achievement-card" style="opacity: {opacity}; {filter_gray}">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">{icon}</div>
                <div style="font-weight: bold; font-size: 1rem;">{title}</div>
                <div style="font-size: 0.8rem; color: #666;">{desc}</div>
            </div>
        """, unsafe_allow_html=True)

    with a1:
        is_growing = len(monthly) >= 2 and monthly["avg_score"].iloc[-1] > monthly["avg_score"].iloc[-2]
        achievement_card(a1, "Взлёт", "Растешь над собой", "🚀", is_growing)
    with a2:
        is_sniper = (df_student["task_percent"] >= 100).any()
        achievement_card(a2, "Снайпер", "Идеальное задание", "🎯", is_sniper)
    with a3:
        is_stable = (monthly["avg_score"] > 40).all()
        achievement_card(a3, "Щит", "Без провалов", "🛡️", is_stable)
    with a4:
        is_record = len(monthly) > 1 and last_score >= monthly["avg_score"].max()
        achievement_card(a4, "Король", "Твой рекорд", "👑", is_record)
        if is_record: st.balloons()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- БЛОК 3: ГРАФИКА И АНАЛИТИКА ---
    c_graph, c_prediction = st.columns([2, 1])
    
    with c_graph:
        st.markdown("### 📈 Динамика знаний")
        fig = px.area(monthly, x="month_id", y="avg_score", color_discrete_sequence=[color])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                          xaxis_title=None, yaxis_title=None, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with c_prediction:
        st.markdown("### 🔮 Будущее")
        if len(monthly) >= 2:
            z = np.polyfit(np.arange(len(monthly)), monthly["avg_score"].values, 1)
            predicted = float(np.clip(np.poly1d(z)(len(monthly) + 1), 0, 100))
            st.metric("Прогноз на экзамен", f"{predicted:.0f}%", f"{z[0]:+.1f} XP")
            st.markdown(f"<div style='background: white; padding: 10px; border-radius: 10px; border: 1px solid #eee; font-size: 0.9rem;'>{'🚀 Продолжай в том же духе!' if z[0] > 0 else '⚠️ Время поднажать на теорию!'}</div>", unsafe_allow_html=True)
        else:
            st.info("Нужно больше данных для предсказания")

    # --- БЛОК 4: ЗАДАНИЯ ---
    st.markdown("---")
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.markdown("### ⚔️ Твои «Боссы» (Слабые темы)")
        task_avg = df_student.groupby("task_name")["task_percent"].mean().sort_values()
        for task, val in task_avg.head(3).items():
            st.error(f"**{task}** — {val:.1f}%")
            st.progress(val/100)

    with col_r:
        st.markdown("### 🛡️ Твоя «База» (Сильные темы)")
        for task, val in task_avg.tail(3).sort_values(ascending=False).items():
            st.success(f"**{task}** — {val:.1f}%")
            st.progress(val/100)

    # --- ФУТЕР ---
    st.markdown("---")
    st.markdown(f"<p style='text-align: center; font-style: italic; color: #888;'>💬 {random.choice(['Твой единственный конкурент — ты вчерашний', 'Маленькие шаги ведут к большим целям', 'Просто начни, остальное приложится'])}</p>", unsafe_allow_html=True)