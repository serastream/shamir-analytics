import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go

from school_analysis.analytics import diagnostics

from school_analysis.core.summary import generate_class_summary
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
                <div style='background:{color};
                            padding:0.5rem 0.6rem;
                            border-radius:0.5rem;
                            margin-bottom:0.4rem;
                            text-align:center;
                            font-weight:600;
                            font-size:1rem;
                            border:1px solid #ddd;'>
                    {r['student']} — {r['task_percent']:.0f}%
                </div>
                """,
                unsafe_allow_html=True,
            )


# -----------------------------------------------------------
# Проблемные ученики месяца
# -----------------------------------------------------------
def _render_teacher_focus_left(
    df_f: pd.DataFrame,
    current_month: int,
    selected_month_id: int | None,
    months_df: pd.DataFrame
):
    """
    Левый блок:
    1) Сверху: 3 проблемных задания за всё время (минимальный avg%)
    2) Ниже: проблемные задания выбранного месяца (если выбран конкретный месяц)
    3) Ниже: 3 рисковых ученика за всё время + перечисление их проблемных заданий
    """

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
        shade = "#f8dada" if avg_percent < 33 else "#ffe9b5" if avg_percent < 50 else "#faf5cf"
        col.markdown(
            f"""
            <div style="background:{shade};
                        border:1px solid #e0e0e0;
                        border-radius:0.85rem;
                        padding:0.75rem 0.85rem;
                        text-align:center;">
                <div style="font-size:1.05rem;font-weight:900;color:#222;">
                    {task_name}
                </div>
                <div style="font-size:0.9rem;font-weight:400;color:#666;margin-top:0.15rem;">
                всего {avg_percent:.0f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # =========================
    # 1) ТОП-3 ПРОБЛЕМНЫХ ЗАДАНИЯ ЗА ВСЁ ВРЕМЯ
    # =========================
    st.markdown("### 🧩 Проблемные задания класса (за всё время)")

    top_all = _top_bad_tasks(df_f, n=3)
    if top_all.empty:
        st.info("Недостаточно данных по тестовой части (1–20), чтобы выделить проблемные задания.")
    else:
        c = st.columns(3)
        for i, r in enumerate(top_all.itertuples(index=False)):
            _card_task(c[i], r.task_name, float(r.avg_percent))

    st.markdown("<hr style='margin:0.9rem 0;'>", unsafe_allow_html=True)

    # =========================
    # 2) ПРОБЛЕМНЫЕ ЗАДАНИЯ ВЫБРАННОГО МЕСЯЦА
    # =========================
    if selected_month_id is not None:
        df_m = df_f[df_f["month_id"] == selected_month_id].copy()
        month_name = months_df.loc[months_df["month_id"] == selected_month_id, "month"].iloc[0]
        st.markdown(f"### 📅 Проблемные задания — {month_name}")
        top_month = _top_bad_tasks(df_m, n=3)

        if top_month.empty:
            st.info("Нет данных по тестовой части (1–20) за выбранный месяц.")
        else:
            c2 = st.columns(3)
            for i, r in enumerate(top_month.itertuples(index=False)):
                _card_task(c2[i], r.task_name, float(r.avg_percent))

        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    else:
        st.markdown("### 📅 Месяц: все данные")
        st.caption("Выбран режим “Все месяцы”. Для задач месяца выбери конкретный месяц в фильтре.")
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    # =========================
    # 3) ТОП-3 РИСКОВЫХ УЧЕНИКА ЗА ВСЁ ВРЕМЯ + их проблемные задания
    # =========================
    st.markdown("### 👥 Ученики в зоне риска (за всё время)")

    df_test_all = _only_test_part(df_f)
    if df_test_all.empty:
        st.info("Нет данных по тестовой части (1–20), чтобы посчитать рисковых учеников.")
        return

    student_avg = (
        df_test_all.groupby("student", as_index=False)["task_percent"]
        .mean()
        .rename(columns={"task_percent": "avg_percent"})
        .sort_values("avg_percent", ascending=True)
    )
    risky = student_avg.head(3).copy()

    per_student_task = (
        df_test_all.groupby(["student", "task_name"], as_index=False)["task_percent"]
        .mean()
        .rename(columns={"task_percent": "avg_percent"})
    )

    def _weak_tasks(student_name: str, thr: float = 33.0) -> list[str]:
        d = per_student_task[per_student_task["student"] == student_name]
        d = d[d["avg_percent"] < thr].sort_values("avg_percent", ascending=True)
        return d["task_name"].tolist()

    if risky.empty:
        st.success("Рисковых учеников не найдено (или недостаточно данных).")
    else:
        for r in risky.itertuples(index=False):
            weak_list = _weak_tasks(r.student)
            weak_txt = ", ".join(weak_list[:5]) if weak_list else "—"
            avgp = float(r.avg_percent)

            shade = "#FFEBEE" if avgp < 33 else "#FFF3E0" if avgp < 50 else "#E8F5E9"

            st.markdown(
                f"""
                <div style="background:{shade};
                            border:1px solid #e6e6e6;
                            border-radius:0.65rem;
                            padding:0.55rem 0.75rem;
                            margin-bottom:0.35rem;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="font-size:0.98rem;font-weight:700;color:#222;">{r.student}</div>
                        <div style="font-size:0.98rem;font-weight:700;color:#111;">{avgp:.0f}%</div>
                    </div>
                    <div style="font-size:0.88rem;color:#555;margin-top:0.15rem;">
                        Проблемные задания: {weak_txt}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# -----------------------------------------------------------
# Основная панель учителя
# -----------------------------------------------------------
def show(df: pd.DataFrame):

    # ✅ КРИТИЧНО: инициализация session_state внутри show()
    st.session_state.setdefault("teacher_ai_question", "")
    st.session_state.setdefault("teacher_ai_answer", "")

    # --- Проверка входных данных ---
    required = {"teacher", "class", "subject", "month_id", "task_percent", "task_name", "student"}
    if not required.issubset(df.columns):
        st.error(f"В данных не хватает колонок: {required - set(df.columns)}")
        return

    # --- Фильтры (каскад: Учитель -> Класс -> Предмет -> Месяц) ---
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        teacher = st.selectbox(
            "Учитель:",
            sorted(df["teacher"].dropna().unique()),
            index=None,
            placeholder="Выберите преподавателя...",
            key="flt_teacher"
        )
    if not teacher:
        st.stop()

    df_t = df.query("teacher == @teacher")

    with c2:
        selected_class = st.selectbox(
            "Класс:",
            sorted(df_t["class"].dropna().unique()),
            index=None,
            placeholder="Выберите класс...",
            key="flt_class"
        )
    if not selected_class:
        st.stop()

    df_c = df_t.query("`class` == @selected_class")
    if df_c.empty:
        st.warning("Нет данных по выбранным фильтрам.")
        st.stop()

    with c3:
        selected_subject = st.selectbox(
            "Предмет:",
            sorted(df_c["subject"].dropna().unique()),
            index=None,
            placeholder="Выберите предмет...",
            key="flt_subject"
        )
    if not selected_subject:
        st.stop()

    df_f = df_c.query("subject == @selected_subject").copy()
    if df_f.empty:
        st.warning("Нет данных по выбранному предмету в этом классе.")
        st.stop()

    if "month" not in df_f.columns and "month_id" in df_f.columns:
        df_f["month"] = df_f["month_id"].astype(str)

    months_df = (
        df_f.dropna(subset=["month_id", "month"])
        .drop_duplicates(subset=["month_id"])
        .sort_values("month_id")[["month_id", "month"]]
    )
    month_options = ["Все месяцы"] + months_df["month"].tolist()

    with c4:
        selected_month = st.selectbox(
            "Месяц:",
            month_options,
            index=len(month_options) - 1,
            key="flt_month"
        )

    current_month = int(df_f["month_id"].max())

    if selected_month == "Все месяцы":
        selected_month_id = None
    else:
        selected_month_id = int(months_df.loc[months_df["month"] == selected_month, "month_id"].iloc[0])

    st.session_state["class_selector_task_perf"] = selected_class
    st.session_state["subject_selector_task_perf"] = selected_subject

    # --- Основные вкладки ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Планы и диагностика",
        "🕸 Социометрия обучения",
        "🧭 Темп обучения",
        "🔍 Сеть влияния",
        "🤖 AI-помощник"
    ])

    # ===========================================================
    # ВКЛАДКА 1 — Планы и диагностика
    # ===========================================================
    with tab1:
        left, right = st.columns([1, 1])

        with left:
            _render_teacher_focus_left(
                df_f,
                current_month=current_month,
                selected_month_id=selected_month_id,
                months_df=months_df
            )

        with right:
            st.markdown("<h2>🔍 Диагностика по заданиям</h2>", unsafe_allow_html=True)
            st.markdown("<hr style='margin-top:0.4rem;margin-bottom:1rem;'>", unsafe_allow_html=True)

            df_diag = df_f if selected_month_id is None else df_f[df_f["month_id"] == selected_month_id].copy()

            df_diag["task_name"] = df_diag["task_name"].astype(str)
            tasks_available = df_diag["task_name"].dropna().unique().tolist()

            if len(tasks_available) == 0:
                st.warning("Нет данных по заданиям для выбранного периода.")
            else:
                def extract_num(name):
                    import re
                    m = re.search(r"(\d+)", str(name))
                    return int(m.group(1)) if m else float("inf")

                tasks_sorted = sorted(tasks_available, key=extract_num)
                tasks_options = ["Все задания"] + tasks_sorted

                selected_task = st.selectbox(
                    "Выберите задание:",
                    tasks_options,
                    index=0,
                    key="teacher_task_selector",
                    placeholder="Выберите задание для анализа..."
                )

                df_task = df_diag if selected_task == "Все задания" else df_diag.query("task_name == @selected_task")

                student_perf = (
                    df_task.groupby(["student"], as_index=False)["task_percent"]
                    .mean()
                    .assign(task_percent=lambda x: x["task_percent"].clip(upper=100))
                )

                weak = student_perf[student_perf["task_percent"] < 55]
                mid = student_perf[(student_perf["task_percent"] >= 55) & (student_perf["task_percent"] < 70)]
                strong = student_perf[student_perf["task_percent"] >= 70]

                st.markdown(
                    f"<div style='font-size:1.2rem;margin-top:0.6rem;margin-bottom:0.4rem;color:#333;'>"
                    f"📘 Средний результат: <b>{student_perf['task_percent'].mean():.1f}%</b>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                def _show_compact(col, title, df_group, color):
                    col.markdown(f"**{title} ({len(df_group)})**")
                    if df_group.empty:
                        col.caption("—")
                    else:
                        for _, r in df_group.iterrows():
                            col.markdown(
                                f"<div style='background:{color};padding:0.3rem 0.5rem;border-radius:0.4rem;"
                                f"margin-bottom:0.3rem;font-size:0.9rem;text-align:center;'>"
                                f"{r['student']} — <b>{r['task_percent']:.0f}%</b></div>",
                                unsafe_allow_html=True,
                            )

                c1g, c2g, c3g = st.columns(3)
                _show_compact(c1g, "🟥 Слабые", weak, "#FFEBEE")
                _show_compact(c2g, "🟧 Средние", mid, "#FFF3E0")
                _show_compact(c3g, "🟩 Сильные", strong, "#E8F5E9")

        diagnostics.plot_class_task_performance(df_f)

        # ===========================================================
        # 🧠 РЕКОМЕНДАЦИИ ПО ПОДГОТОВКЕ (темы + задания) — компактный UX
        # ===========================================================
        st.markdown("## 🧠 Рекомендации по подготовке")

        def _badge(text: str, color: str, emoji: str = "") -> str:
            return f"""
            <span style="
                display:inline-block;
                padding:2px 10px;
                border-radius:999px;
                background:{color};
                color:#111;
                font-weight:700;
                font-size:0.9rem;
                margin-right:8px;
                border:1px solid rgba(0,0,0,0.08);
                white-space:nowrap;
            ">{emoji} {text}</span>
            """.strip()

        def _section(title: str, body_html: str) -> str:
            return f"""
            <div style="margin: 0.5rem 0 0.9rem 0;">
                <div style="font-weight:800;font-size:1.05rem;margin-bottom:0.35rem;">{title}</div>
                <div style="line-height:1.55;font-size:1.0rem;color:#222;">{body_html}</div>
            </div>
            """.strip()

        def _topics_inline_html(topics, topic_to_tasks, color="#8a0f0f", emoji="🔴"):
            """
            Одна строка на тему:
            🔴 ТЕМА — Задание 23 (0%); Задание 21 (12%)
            """
            lines = []
            for t in topics:
                t = str(t)
                tasks_line = topic_to_tasks.get(t, "")
                # делаем строку компактной
                if tasks_line:
                    lines.append(
                        f"<div style='margin:0.12rem 0;'>"
                        f"<span style='color:{color};font-weight:800;'>{emoji} {t}</span>"
                        f"<span style='color:#555;'> — {tasks_line}</span>"
                        f"</div>"
                    )
                else:
                    lines.append(
                        f"<div style='margin:0.12rem 0;'>"
                        f"<span style='color:{color};font-weight:800;'>{emoji} {t}</span>"
                        f"</div>"
                    )
            return "".join(lines)

        if "category" not in df_c.columns:
            st.info("Колонка category не найдена. Проверь preprocess: category должен подтягиваться из листа tasks.")
        else:
            # 1. Формируем список: "Весь класс" + список учеников
            student_options = ["Весь класс"] + sorted(df_c["student"].dropna().unique().tolist())
            
            if len(student_options) == 1: # Значит, кроме "Весь класс" никого нет
                st.info("Нет данных об учениках в выбранной выборке.")
            else:
                selected_student = st.selectbox("Анализировать:", student_options, key="student_reco_compact")

                # 2. Фильтруем данные: либо по ученику, либо берем всё (весь класс)
                if selected_student == "Весь класс":
                    df_st = df_c.copy()
                    report_type_name = "по всему классу"
                else:
                    df_st = df_c[df_c["student"] == selected_student].copy()
                    report_type_name = f"для ученика {selected_student}"

                df_st["category"] = df_st["category"].fillna("— тема не указана —").astype(str)

                if df_st.empty:
                    st.info(f"Нет данных {report_type_name}.")
                else:
                    # --- агрегируем средний % по темам (теперь это либо среднее ученика, либо среднее класса) ---
                    topic_stats = (
                        df_st.groupby("category", as_index=False)
                        .agg(avg_percent=("task_percent", "mean"))
                        .sort_values("avg_percent")
                    )
                    topic_stats["avg_percent"] = topic_stats["avg_percent"].round(1)

                    # --- пороги ---
                    LOW_THR = 40
                    MID_THR = 65

                    low_topics = topic_stats[topic_stats["avg_percent"] < LOW_THR]["category"].tolist()
                    mid_topics = topic_stats[
                        (topic_stats["avg_percent"] >= LOW_THR) & (topic_stats["avg_percent"] < MID_THR)
                    ]["category"].tolist()

                    # --- собираем: тема -> 1–2 самых слабых задания (среднее по выборке) ---
                    topic_to_tasks = {}
                    if "task_name" in df_st.columns:
                        task_by_topic = (
                            df_st.groupby(["category", "task_name"], as_index=False)["task_percent"]
                            .mean()
                            .rename(columns={"category": "topic"})
                            .sort_values(["topic", "task_percent"], ascending=[True, True])
                        )

                        topics_focus = (low_topics + mid_topics)[:16]
                        for t in topics_focus:
                            w = task_by_topic[task_by_topic["topic"] == t].head(2)
                            if w.empty:
                                continue
                            topic_to_tasks[str(t)] = "; ".join(
                                [f"{row.task_name} ({row.task_percent:.0f}%)" for row in w.itertuples()]
                            )

                    sections = []

                    # --- если проблемных тем нет ---
                    if not low_topics and not mid_topics:
                        ok = _badge("Проблемных тем не выявлено", "#d9fdd3", "🟢")
                        sections.append(_section(
                            f"{ok} Результат",
                            f"Результаты {report_type_name} выглядят стабильными. Продолжайте в текущем режиме."
                        ))
                    else:
                        # 🔴 приоритет
                        if low_topics:
                            red = _badge("В приоритете", "#ffd6d6", "🔴")
                            body = _topics_inline_html(
                                low_topics,
                                topic_to_tasks,
                                color="#8a0f0f",
                                emoji="🔴"
                            )
                            sections.append(_section(f"{red} Темы с наименьшим процентом выполнения", body))

                        # 🟠 закрепление
                        if mid_topics:
                            amber = _badge("На закрепление", "#ffe9b5", "🟠")
                            body = _topics_inline_html(
                                mid_topics,
                                topic_to_tasks,
                                color="#7a4a00",
                                emoji="🟠"
                            )
                            sections.append(_section(f"{amber} Темы, требующие внимания", body))

                    st.markdown("<br>".join(sections), unsafe_allow_html=True)
                      

        # ===========================================================
        # ВКЛАДКА 2 — Социометрия обучения (ПОЛНЫЙ КОД)
        # ===========================================================
        with tab2:
            st.markdown("<h2>🕸 Группы синхронности и траекторий</h2>", unsafe_allow_html=True)
            
            col_t1, col_t2 = st.columns([1, 2])
            with col_t1:
                threshold = st.slider(
                    "Чувствительность поиска связей", 
                    min_value=0.5, max_value=0.95, value=0.75, step=0.05,
                    help="Чем выше значение, тем более идентичными должны быть оценки учеников для появления линии связи."
                )
            with col_t2:
                st.caption("Линии показывают, что ученики одинаково ошибаются или растут. Цвет узла — средний балл (Красный < 50% < Зеленый).")

            # Подготовка данных
            df_dyn = df_f.groupby(["student", "month_id"], as_index=False)["task_percent"].mean()
            pivot = df_dyn.pivot_table(index="student", columns="month_id", values="task_percent").fillna(0)

            if pivot.shape[1] < 2:
                st.info("Недостаточно данных по месяцам для анализа динамики.")
            else:
                # Расчет корреляции
                similarity = pivot.T.corr()
                student_mean = df_dyn.groupby("student")["task_percent"].mean().to_dict()

                G = nx.Graph()
                for student in pivot.index:
                    avg = float(student_mean.get(student, 0))
                    G.add_node(student, avg=avg)

                # 1. СОЗДАНИЕ СВЯЗЕЙ (РЕБЕР)
                for i in similarity.index:
                    for j in similarity.columns:
                        if i != j and similarity.loc[i, j] > threshold:
                            G.add_edge(i, j, weight=float(similarity.loc[i, j]))

                # 2. ПЛАНИРОВКА И КЛАСТЕРИЗАЦИЯ
                communities = list(nx.community.greedy_modularity_communities(G))
                community_map = {name: idx for idx, comm in enumerate(communities) for name in comm}
                pos = nx.spring_layout(G, k=1.8, iterations=100, seed=42)

                # 3. ПОДГОТОВКА КООРДИНАТ ДЛЯ ЛИНИЙ (ТЕ САМЫЕ edge_x и edge_y)
                edge_x = []
                edge_y = []
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])

                # 4. ПОДГОТОВКА КООРДИНАТ ДЛЯ УЗЛОВ
                node_x = []
                node_y = []
                node_color = []
                node_size = []
                node_text = []

                for node in G.nodes:
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    
                    avg_val = float(G.nodes[node]["avg"])
                    node_color.append(avg_val) # Числовое значение для шкалы
                    node_size.append(20 + (avg_val / 5))
                    
                    comm_id = community_map.get(node, 0)
                    node_text.append(f"<b>{node}</b><br>Средний балл: {avg_val:.1f}%<br>Группа: {comm_id}")

                # 5. СТРОИМ ГРАФИК
                fig = go.Figure()

                # Добавляем линии
                fig.add_trace(go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=1, color='#BDC3C7'),
                    hoverinfo='none',
                    mode='lines'
                ))

                # Добавляем точки (учеников)
                fig.add_trace(go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    text=[n.split(' ')[0] for n in G.nodes],
                    textposition="top center",
                    hovertext=node_text,
                    hoverinfo='text',
                    marker=dict(
                        showscale=True,
                        colorscale='RdYlGn', # Цвета: Красный-Желтый-Зеленый
                        cmin=0,              # Минимум шкалы
                        cmax=100,            # Максимум шкалы
                        color=node_color,    # Привязка цвета к среднему баллу
                        size=node_size,
                        colorbar=dict(title="Успеваемость %", thickness=15),
                        line=dict(color='white', width=2)
                    )
                ))

                fig.update_layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0, l=0, r=0, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=600
                )

                st.plotly_chart(fig, use_container_width=True)
                
                # Инсайт под графиком
                if communities:
                    st.info(f"💡 Алгоритм выделил {len(communities)} групп(ы) со схожим стилем обучения.")

    # ===========================================================
    # ВКЛАДКА 3 — Темп обучения
    # ===========================================================
    with tab3:
        show_learning_tempo(df_f)

    # ===========================================================
    # ВКЛАДКА 4 — Сеть влияния
    # ===========================================================
    with tab4:
        show_influence_network(df_f)

    # ===========================================================
    # ВКЛАДКА 5 — AI-помощник
    # ===========================================================
    with tab5:
        st.markdown("## 🤖 AI-помощник учителя")
        st.caption(
            "Пиши запросы в свободной форме: "
            "'составь план на 2 недели', "
            "'кого срочно подтянуть', "
            "'что делать с заданием 12' и т.д."
        )

        # ✅ самый надежный вариант: text_area сам пишет в session_state по key
        st.text_area(
            "Запрос:",
            key="teacher_ai_question",
            placeholder=(
                "Например: "
                "'Сделай план работы на неделю для слабых учеников, "
                "упор на топ-3 проблемных задания.'"
            ),
            height=120
        )

        if st.button("Спросить 🤖 AI", type="primary"):
            question = st.session_state.get("teacher_ai_question", "").strip()
            if question:
                ctx = get_teacher_context_cached(df_f, top_n=5)
                prompt = f"{ctx}\n\nВОПРОС УЧИТЕЛЯ:\n{question}"

                try:
                    with st.spinner("🤖 Анализирую данные класса..."):
                        answer = ask_openai(
                            input_text=prompt,
                            system_text=teacher_system_prompt(),
                            max_output_tokens=2000,
                            metadata={"panel": "teacher", "feature": "assistant"}
                        )

                    st.session_state["teacher_ai_answer"] = answer

                except Exception as e:
                    st.error(f"Не удалось обратиться к AI: {e}")
            else:
                st.warning("Напиши запрос — поле пустое.")

        if st.session_state.get("teacher_ai_answer", ""):
            st.markdown("### Ответ")
            st.write(st.session_state["teacher_ai_answer"])