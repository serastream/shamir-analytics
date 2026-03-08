import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
from scipy.spatial.distance import pdist, squareform

from school_analysis.analytics import diagnostics
from school_analysis.core.summary import generate_class_summary
from school_analysis.core.style import apply_premium_styles  # Импортируем созданную функцию
from school_analysis.core.llm_openai import (
    ask_openai,
    build_teacher_context,
    teacher_system_prompt,
)

from school_analysis.analytics.action_plans import (
    show_action_plans_ui,
    StudentPlanConfig,
    TeacherGoalConfig
)

# Новые модули
from school_analysis.analytics.learning_tempo import show_learning_tempo
from school_analysis.analytics.influence_network import show_influence_network
from school_analysis.analytics.topic_recommendations import generate_category_recommendations


@st.cache_data(show_spinner=False)
def get_teacher_context_cached(df_c, top_n: int):
    return build_teacher_context(df_c, top_n=top_n)


# -----------------------------------------------------------
# Вспомогательная функция для карточек групп учеников
# -----------------------------------------------------------
def _show_group(col, title, df_group, color):
    col.markdown(f"### {title}")
    if df_group.empty:
        col.info("—")
    else:
        for _, r in df_group.iterrows():
            col.markdown(
                f"""
                <div class="premium-card" style="border-left: 5px solid {color}; padding: 10px 15px;">
                    <div style="font-weight:700; color:#1e293b;">{r['student']}</div>
                    <div style="color:{color}; font-weight:800;">{r['task_percent']:.0f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# -----------------------------------------------------------
# Проблемные ученики и задания (ОБНОВЛЕННЫЙ ДИЗАЙН)
# -----------------------------------------------------------
def _render_teacher_focus_left(
    df_f: pd.DataFrame,
    current_month: int,
    selected_month_id: int | None,
    months_df: pd.DataFrame
):
    def _only_test_part(d: pd.DataFrame) -> pd.DataFrame:
        d = d.copy()
        d["task_num"] = d["task_name"].astype(str).str.extract(r"(\d+)").astype(float)
        return d[d["task_num"].between(1, 20, inclusive="both")]

    def _top_bad_tasks(d: pd.DataFrame, n=3) -> pd.DataFrame:
        d = _only_test_part(d)
        if d.empty:
            return pd.DataFrame(columns=["task_name", "avg_percent"])
        out = (
            d.groupby("task_name", as_index=False)["task_percent"]
             .mean()
             .rename(columns={"task_percent": "avg_percent"})
             .sort_values("avg_percent", ascending=True)
             .head(n)
        )
        return out

    def _card_task(col, task_name: str, avg_percent: float):
        # Премиальный дизайн карточки задания
        if avg_percent < 40:
            color, bg = "#ef4444", "#fef2f2"
        elif avg_percent < 70:
            color, bg = "#f59e0b", "#fffbeb"
        else:
            color, bg = "#10b981", "#ecfdf5"

        col.markdown(f"""
            <div class="premium-card" style="border-top: 4px solid {color}; min-height: 120px; display: flex; flex-direction: column; justify-content: center;">
                <div style="color: {color}; font-weight: 700; font-size: 0.7rem; text-transform: uppercase; margin-bottom: 4px;">Задание</div>
                <div style="font-size: 1.1rem; font-weight: 800; color: #1e293b; line-height: 1.2;">{task_name}</div>
                <div style="margin-top: 10px; display: flex; align-items: center; gap: 6px;">
                    <div style="background: {bg}; color: {color}; padding: 2px 8px; border-radius: 6px; font-weight: 800; font-size: 0.9rem;">
                        {avg_percent:.0f}%
                    </div>
                    <span style="color: #64748b; font-size: 0.75rem;">средний балл</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 1) ТОП-3 ПРОБЛЕМНЫХ ЗАДАНИЯ ЗА ВСЁ ВРЕМЯ
    st.markdown("### 🧩 Проблемные задания (всегда)")
    top_all = _top_bad_tasks(df_f, n=3)
    if top_all.empty:
        st.info("Нет данных по тестовой части.")
    else:
        c = st.columns(3)
        for i, r in enumerate(top_all.itertuples(index=False)):
            _card_task(c[i], r.task_name, float(r.avg_percent))

    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

    # 2) ПРОБЛЕМНЫЕ ЗАДАНИЯ ВЫБРАННОГО МЕСЯЦА
    if selected_month_id is not None:
        df_m = df_f[df_f["month_id"] == selected_month_id].copy()
        month_name = months_df.loc[months_df["month_id"] == selected_month_id, "month"].iloc[0]
        st.markdown(f"### 📅 Проблемные в {month_name}")
        top_month = _top_bad_tasks(df_m, n=3)
        if not top_month.empty:
            c2 = st.columns(3)
            for i, r in enumerate(top_month.itertuples(index=False)):
                _card_task(c2[i], r.task_name, float(r.avg_percent))
    
    st.markdown("<hr style='opacity:0.2; margin: 20px 0;'>", unsafe_allow_html=True)

    # 3) ТОП-3 РИСКОВЫХ УЧЕНИКА
    st.markdown("### 👥 Ученики в зоне риска")
    df_test_all = _only_test_part(df_f)
    if not df_test_all.empty:
        student_avg = (
            df_test_all.groupby("student", as_index=False)["task_percent"]
            .mean()
            .rename(columns={"task_percent": "avg_percent"})
            .sort_values("avg_percent", ascending=True)
        )
        risky = student_avg.head(3).copy()
        per_student_task = df_test_all.groupby(["student", "task_name"], as_index=False)["task_percent"].mean()

        for r in risky.itertuples(index=False):
            weak_list = per_student_task[(per_student_task["student"] == r.student) & (per_student_task["task_percent"] < 40)]["task_name"].tolist()
            weak_txt = ", ".join(weak_list[:4]) if weak_list else "—"
            avgp = float(r.avg_percent)
            
            # Цвет в зависимости от критичности
            shade_color = "#ef4444" if avgp < 35 else "#f59e0b"

            st.markdown(f"""
                <div class="premium-card" style="display: flex; justify-content: space-between; align-items: center; padding: 15px 20px;">
                    <div>
                        <div style="font-weight: 700; color: #1e293b; font-size: 1rem;">{r.student}</div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top:2px;">Слабые зоны: <span style="color:#475569; font-weight:600;">{weak_txt}</span></div>
                    </div>
                    <div style="font-size: 1.2rem; font-weight: 800; color: {shade_color}; background: {shade_color}15; padding: 5px 12px; border-radius: 8px;">
                        {avgp:.0f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)


# -----------------------------------------------------------
# Основная панель учителя
# -----------------------------------------------------------
def show(df: pd.DataFrame):
    # ПРИМЕНЯЕМ ПРЕМИУМ СТИЛИ
    apply_premium_styles()

    # Инициализация session_state
    st.session_state.setdefault("teacher_ai_question", "")
    st.session_state.setdefault("teacher_ai_answer", "")

    # Проверка входных данных
    required = {"teacher", "class", "subject", "month_id", "task_percent", "task_name", "student"}
    if not required.issubset(df.columns):
        st.error(f"В данных не хватает колонок: {required - set(df.columns)}")
        return

    # --- Фильтры ---
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        teacher = st.selectbox("Учитель:", sorted(df["teacher"].dropna().unique()), index=None, placeholder="Выбор...", key="flt_teacher")
    if not teacher: 
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    df_t = df.query("teacher == @teacher")

    with c2:
        selected_class = st.selectbox("Класс:", sorted(df_t["class"].dropna().unique()), index=None, placeholder="Выбор...", key="flt_class")
    if not selected_class: 
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    df_c = df_t.query("`class` == @selected_class")

    with c3:
        selected_subject = st.selectbox("Предмет:", sorted(df_c["subject"].dropna().unique()), index=None, placeholder="Выбор...", key="flt_subject")
    if not selected_subject: 
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    df_f = df_c.query("subject == @selected_subject").copy()

    months_df = df_f.dropna(subset=["month_id", "month"]).drop_duplicates(subset=["month_id"]).sort_values("month_id")[["month_id", "month"]]
    month_options = ["Все месяцы"] + months_df["month"].tolist()

    with c4:
        selected_month = st.selectbox("Месяц:", month_options, index=len(month_options) - 1, key="flt_month")

    st.markdown('</div>', unsafe_allow_html=True)

    current_month = int(df_f["month_id"].max())
    selected_month_id = None if selected_month == "Все месяцы" else int(months_df.loc[months_df["month"] == selected_month, "month_id"].iloc[0])

    # --- Вкладки ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Диагностика", "🕸 Социометрия", "🧭 Темп", "🔍 Влияние", "🤖 AI Ассистент"
    ])

    # ВКЛАДКА 1 — Планы и диагностика
    with tab1:
        left, right = st.columns([1, 1.2])

        with left:
            _render_teacher_focus_left(df_f, current_month, selected_month_id, months_df)

        with right:
            st.markdown("<h3>🔍 Анализ по заданиям</h3>", unsafe_allow_html=True)
            df_diag = df_f if selected_month_id is None else df_f[df_f["month_id"] == selected_month_id].copy()
            tasks_available = sorted(df_diag["task_name"].dropna().unique().tolist())

            selected_task = st.selectbox("Выберите задание:", ["Все задания"] + tasks_available, key="t_task_sel")
            df_task = df_diag if selected_task == "Все задания" else df_diag.query("task_name == @selected_task")

            student_perf = df_task.groupby(["student"], as_index=False)["task_percent"].mean()
            
            st.markdown(f"""
                <div style="background:#f8fafc; padding:15px; border-radius:12px; border:1px solid #e2e8f0; margin-bottom:20px;">
                    <span style="color:#64748b;">Средний результат:</span> 
                    <span style="font-size:1.5rem; font-weight:800; color:#4f46e5; margin-left:10px;">{student_perf['task_percent'].mean():.1f}%</span>
                </div>
            """, unsafe_allow_html=True)

            c1g, c2g, c3g = st.columns(3)
            _show_group(c1g, "🟥 Слабые", student_perf[student_perf["task_percent"] < 50], "#ef4444")
            _show_group(c2g, "🟧 Средние", student_perf[(student_perf["task_percent"] >= 50) & (student_perf["task_percent"] < 75)], "#f59e0b")
            _show_group(c3g, "🟩 Сильные", student_perf[student_perf["task_percent"] >= 75], "#10b981")

        st.markdown("---")
        diagnostics.plot_class_task_performance(df_f)

    # ВКЛАДКА 2 — Социометрия
    with tab2:
        st.markdown("<h2>🕸 Группы синхронности</h2>", unsafe_allow_html=True)
        threshold = st.slider("Чувствительность связей", 0.5, 0.95, 0.75)
        
        df_dyn = df_f.groupby(["student", "month_id"], as_index=False)["task_percent"].mean()
        pivot = df_dyn.pivot_table(index="student", columns="month_id", values="task_percent").fillna(0)

        if pivot.shape[1] < 2:
            st.info("Нужно больше данных за разные месяцы.")
        else:
            corr_matrix = pivot.T.corr().fillna(0)
            avg_scores = pivot.mean(axis=1).values.reshape(-1, 1)
            dist_matrix = squareform(pdist(avg_scores))
            score_sim = 1 - (dist_matrix / 100) 

            G = nx.Graph()
            for student in pivot.index:
                G.add_node(student, avg=float(pivot.loc[student].mean()))

            for i_idx, s_i in enumerate(pivot.index):
                for j_idx, s_j in enumerate(pivot.index):
                    if i_idx >= j_idx: continue
                    weight = (corr_matrix.iloc[i_idx, j_idx] * 0.6) + (score_sim[i_idx, j_idx] * 0.4)
                    if weight > threshold:
                        G.add_edge(s_i, s_j, weight=weight)

            pos = nx.spring_layout(G, k=1.5, seed=42)
            edge_x, edge_y = [], []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]; x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None]); edge_y.extend([y0, y1, None])

            node_x, node_y, node_color, node_size = [], [], [], []
            for node in G.nodes:
                x, y = pos[node]
                node_x.append(x); node_y.append(y)
                avg = float(G.nodes[node]["avg"])
                node_color.append(avg); node_size.append(25 + (avg/4))

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color='#e2e8f0'), hoverinfo='none', mode='lines'))
            fig.add_trace(go.Scatter(
                x=node_x, y=node_y, mode='markers+text', text=[n.split(' ')[0] for n in G.nodes],
                textposition="top center", marker=dict(showscale=True, colorscale='RdYlGn', color=node_color, size=node_size, line=dict(color='white', width=2))
            ))
            fig.update_layout(showlegend=False, margin=dict(b=0, l=0, r=0, t=0), xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=False, showticklabels=False), height=500, plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)

    # ВКЛАДКА 3 — Темп
    with tab3:
        show_learning_tempo(df_f)

    # ВКЛАДКА 4 — Сеть влияния
    with tab4:
        show_influence_network(df_f)

    # ВКЛАДКА 5 — AI-помощник
    with tab5:
        st.markdown("<h3>🤖 AI-помощник учителя</h3>", unsafe_allow_html=True)
        
        q_container = st.container()
        with q_container:
            st.text_area(
                "Запрос к системе:",
                key="teacher_ai_question",
                placeholder="Напр: Составь план работы на неделю для группы 'Слабые'...",
                height=120
            )

            if st.button("Сгенерировать ответ ✨", type="primary"):
                question = st.session_state.get("teacher_ai_question", "").strip()
                if question:
                    ctx = get_teacher_context_cached(df_f, top_n=5)
                    prompt = f"{ctx}\n\nВОПРОС УЧИТЕЛЯ:\n{question}"
                    try:
                        with st.spinner("🤖 Нейросеть анализирует успеваемость..."):
                            answer = ask_openai(
                                input_text=prompt,
                                system_text=teacher_system_prompt(),
                                max_output_tokens=2000
                            )
                        st.session_state["teacher_ai_answer"] = answer
                    except Exception as e:
                        st.error(f"Ошибка AI: {e}")

        if st.session_state.get("teacher_ai_answer", ""):
            st.markdown("#### Ответ ассистента:")
            st.markdown(f"""
                <div style="background: #ffffff; padding: 25px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); color: #1e293b; line-height: 1.6;">
                    {st.session_state["teacher_ai_answer"]}
                </div>
            """, unsafe_allow_html=True)