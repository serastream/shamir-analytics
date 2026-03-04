import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import textwrap
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from school_analysis.analytics import diagnostics, comparison
from school_analysis.core.utils import format_delta
from school_analysis.core.attendance import attendance_widget
from school_analysis.analytics.teacher_kpi import show_teacher_kpi
#from school_analysis.analytics.forecast_utils import add_forecast_line

# ============================================================ #
#     ПАНЕЛЬ АДМИНИСТРАЦИИ
# ============================================================ #


def show(df: pd.DataFrame, data: dict):

    # === Вкладки ===
    tab1, tab2, tab3 = st.tabs(["📊 Аналитика школы", "🚪 Посещаемость", "⚙️ Настройки"])

    # --- TAB1: Аналитика ---
    with tab1:
        show_analytics(df, data)

    # --- TAB2: Отмечалка ---
    with tab2:
        st.markdown("### 🚪 Учёт посещаемости")
        #attendance_widget(df)
        st.info("Учёт посещаемости в разработке")

    # --- TAB3: Настройки ---
    with tab3:
        st.info("Раздел в разработке")


# ============================================================ #
#     АНАЛИТИКА ШКОЛЫ (включая индивидуальный отчёт)
# ============================================================ #

def show_analytics(df: pd.DataFrame, data: dict):
    # === 1️⃣ Пульс школы (версия 2.0, исправленный HTML) ===
    from streamlit.components.v1 import html as st_html

    month_order = [
    'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Экзамен'
    ]
    
    avg_school = df['exam_percent'].mean()

    # --- Динамика: за месяц и за весь период ---
    delta_month = 0.0   # последний месяц vs предыдущий
    delta_total = 0.0   # последний месяц vs первый месяц

    if 'month_id' in df.columns:
        monthly = df.groupby('month_id')['exam_percent'].mean().sort_index()

        if len(monthly) >= 2:
            delta_month = round(monthly.iloc[-1] - monthly.iloc[-2], 1)
            delta_total = round(monthly.iloc[-1] - monthly.iloc[0], 1)

    if {'student_id', 'month'}.issubset(df.columns):
        total_months = df['month'].nunique()
        involvement = (df.groupby('student_id')['month'].nunique() / total_months >= 0.8).mean() * 100
    else:
        involvement = np.nan

    subject_std = df.groupby('subject')['exam_percent'].mean().std()
    stability_index = max(0, 100 - subject_std * 2.5)

    strong = (df['exam_percent'] >= 70).mean() * 100
    weak = (df['exam_percent'] < 40).mean() * 100
    neutral = max(0, 100 - strong - weak)
    temp = 100 - (weak - strong)

    if temp > 70:
        mood, color = "🟩 Комфортная", "#2ecc71"
    elif temp > 40:
        mood, color = "🟨 Напряжённая", "#f1c40f"
    else:
        mood, color = "🟥 Критическая", "#e74c3c"

    class_means = df.groupby('class')['exam_percent'].mean()
    class_gap = class_means.max() - class_means.min() if not class_means.empty else 0

    subj_stats = df.groupby('subject')['exam_percent'].mean().sort_values(ascending=False)
    best_subj = subj_stats.head(2).round(1).to_dict()
    worst_subj = subj_stats.tail(2).round(1).to_dict()

    # --- визуальная шкала ---
    bar_html = f"""
    <div style="display:flex;height:12px;border-radius:6px;overflow:hidden;margin:8px 0;">
    <div style="width:{weak}%;background:#ff6b6b;"></div>
    <div style="width:{neutral}%;background:#ffe066;"></div>
    <div style="width:{strong}%;background:#51cf66;"></div>
    </div>
    """

    # --- текст для динамики месяца без “рост на -1.8” ---
    if delta_month > 0:
        month_phrase = f"Рост на {delta_month:+.1f} п.п. за последний месяц."
    elif delta_month < 0:
        month_phrase = f"Снижение на {delta_month:+.1f} п.п. за последний месяц."
    else:
        month_phrase = "Без изменений за последний месяц."

    # --- основной блок ---
    html_code = f"""
    <div style='background:#ffffff;padding:20px 26px;border-radius:12px;margin-top:8px;
                box-shadow:0 2px 6px rgba(0,0,0,0.07);font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
                color:#2C3E50;line-height:1.65;letter-spacing:0.2px;'>

    <div style='font-size:1.15rem;font-weight:600;margin-bottom:8px;'>
        📈 <span style="font-size:1.2rem;">Динамика успеваемости школы (за весь период):</span>
        <span style='color:{'green' if delta_total>0 else ('red' if delta_total<0 else '#555')};
                    font-weight:700;'>{delta_total:+.1f} п.п.</span>
        <span style='color:#777;font-weight:500;'> · за последний месяц: </span>
        <span style='color:{'green' if delta_month>0 else ('red' if delta_month<0 else '#555')};
                    font-weight:700;'>{delta_month:+.1f} п.п.</span>
    </div>

    <div style='font-size:1.05rem;margin-bottom:6px;'>
        Средний уровень успеваемости — <b>{avg_school:.1f}%</b>. {month_phrase}
    </div>

    <div style='margin-bottom:4px;'>
        Картина по школе:
        <span style='font-weight:600;'>
        <span style='color:#e74c3c;'>{weak:.1f}% учащихся в зоне риска</span> · 
        <span style='color:#f1c40f;'>{neutral:.1f}% показывают средний уровень</span> · 
        <span style='color:#2ecc71;'>{strong:.1f}% стабильно высокие результаты</span>
        </span>
    </div>

    {bar_html}

    <div style='margin-top:10px;font-size:1.05rem;'>
        📘 <b>Сильные предметы:</b> {' | '.join([f'<b>{k}</b> {v}%' for k,v in best_subj.items()])}<br>
        ⚠️ <b>Требуют внимания:</b> {' | '.join([f'<b>{k}</b> {v}%' for k,v in worst_subj.items()])}
    </div>

    </div>
    """

    st_html(html_code, height=250)


    # ============================================================
    # 🩺 ДИАГНОСТИКА УСТОЙЧИВЫХ ПРОБЕЛОВ (ADMIN: УСИЛЕННАЯ КАРТОЧКА КЛАССА)
    # ============================================================
    st.subheader("🩺 Диагностика устойчивых пробелов по заданиям")

    # --- Фильтры: класс слева, предмет справа ---
    col1, col2 = st.columns(2)

    with col1:
        selected_class = st.selectbox(
            "Выберите класс:",
            ["Все классы"] + sorted(df['class'].dropna().unique()),
            key="diag_class_avg"
        )

    with col2:
        selected_subject = st.selectbox(
            "Выберите предмет:",
            ["Все предметы"] + sorted(df['subject'].dropna().unique()),
            key="diag_subj_avg"
        )

    # --- фильтрация данных под выбор ---
    filtered_df = df.copy()
    if selected_class != "Все классы":
        filtered_df = filtered_df[filtered_df['class'] == selected_class]
    if selected_subject != "Все предметы":
        filtered_df = filtered_df[filtered_df['subject'] == selected_subject]

    # --- проверки колонок ---
    required_cols = {'student', 'class', 'subject', 'task_name', 'task_percent'}
    missing = required_cols - set(filtered_df.columns)
    if missing:
        st.error(f"В данных отсутствуют необходимые колонки: {missing}")
        st.stop()

    # --- 1) Средний % по каждому ученику и заданию (устойчивость по ученику) ---
    avg_task_by_student = (
        filtered_df.groupby(['student', 'class', 'subject', 'task_name'])['task_percent']
        .mean()
        .reset_index()
    )

    # --- 2) Устойчивые нули ---
    ZERO_THR = 0.2
    problem_tasks = avg_task_by_student[avg_task_by_student['task_percent'] <= ZERO_THR].copy()

    if problem_tasks.empty:
        st.success("🎉 Отлично! Устойчивых нулевых результатов не найдено по выбранным фильтрам.")
    else:

        # --- 3) Размер класса (в текущей выборке) ---
        class_sizes = (
            filtered_df.groupby('class')['student'].nunique()
            .rename('total_students')
            .reset_index()
        )

        # --- 4) Агрегат по заданиям ---
        task_failure_stats = (
            problem_tasks.groupby(['class', 'subject', 'task_name'])
            .agg(count_students=('student', 'nunique'))
            .reset_index()
            .merge(class_sizes, on='class', how='left')
        )

        task_failure_stats['share'] = (
            (task_failure_stats['count_students'] / task_failure_stats['total_students']) * 100
        ).round(1)

        # ============================================================
        # ✅ 5) Таблица view_df для карточки (гарантированно создаём)
        # ============================================================
        if selected_class == "Все классы":
            view_df = (
                task_failure_stats.groupby(['subject', 'task_name'], as_index=False)
                .agg(count_students=('count_students', 'sum'),
                    total_students=('total_students', 'sum'))
            )
            view_df['share'] = (view_df['count_students'] / view_df['total_students'] * 100).round(1)
            title = "Школа (все классы)"
        else:
            view_df = task_failure_stats[task_failure_stats['class'] == selected_class].copy()
            title = selected_class

        # На всякий случай: если после фильтров пусто
        if view_df.empty:
            st.info("Нет данных для формирования карточки по выбранным фильтрам.")
            st.stop()

        # Сортировка: худшее сверху
        view_df = view_df.sort_values(['share', 'count_students'], ascending=False).reset_index(drop=True)

        # worst_* теперь точно существуют
        # --- view_df уже создан и отсортирован выше ---
        worst_task = str(view_df.loc[0, 'task_name'])
        worst_share = float(view_df.loc[0, 'share'])

        title = selected_class if selected_class != "Все классы" else "Школа (все классы)"
        subject_txt = selected_subject if selected_subject != "Все предметы" else "все предметы"

        top_tasks = view_df.head(8).copy()

        # топ-3 и остальные
        top3 = top_tasks.head(3)
        rest = top_tasks.iloc[3:]

        top3_text = ", ".join([f"{r['task_name']} ({r['share']:.1f}%)" for _, r in top3.iterrows()])
        rest_text = ", ".join([f"{r['task_name']} ({r['share']:.1f}%)" for _, r in rest.iterrows()])

        # цвет акцента — по факту провала, но без ярлыков
        if worst_share >= 60:
            border = "#E74C3C"
            bg = "linear-gradient(135deg,#fff5f5,#fff1f1)"
            accent = "#C0392B"
        elif worst_share >= 30:
            border = "#F39C12"
            bg = "linear-gradient(135deg,#fffaf2,#fff6e6)"
            accent = "#B9770E"
        else:
            border = "#F1C40F"
            bg = "linear-gradient(135deg,#fffef4,#fffbe6)"
            accent = "#B7950B"

        card_html = (
            f"<div style='background:{bg};border-left:12px solid {border};"
            f"padding:18px 22px;margin:12px 0 16px 0;border-radius:14px;"
            f"box-shadow:0 6px 14px rgba(0,0,0,0.08);'>"

            # заголовок
            f"<div style='font-size:1.35rem;font-weight:900;color:#1f2d3d;"
            f"letter-spacing:0.2px;margin-bottom:10px;'>"
            f"{title} — {subject_txt}</div>"

            # краткий контекст (не кричащий)
            f"<div style='font-size:0.95rem;color:#5f6b73;margin-bottom:12px;'>"
            f"Задание с максимальным числом устойчивых нулей: "
            f"<b>{worst_task}</b> "
            f"(<span style='color:{accent};font-weight:800;'>{worst_share:.1f}%</span> учащихся)"
            f"</div>"

            # ключевой блок — задания
            f"<div style='font-size:1.05rem;color:#2C3E50;margin-bottom:6px;'>"
            f"<b>Основные проблемные задания:</b>"
            f"</div>"

            f"<div style='font-size:1.02rem;color:{accent};font-weight:900;"
            f"line-height:1.6;margin-bottom:8px;'>"
            f"{top3_text}"
            f"</div>"

            f"<div style='font-size:0.95rem;color:#6c7a80;'>"
            f"Также требуют внимания: "
            f"<span style='color:{accent};font-weight:700;'>{rest_text}</span>"
            f"</div>"

            f"</div>"
        )

        st.markdown(card_html, unsafe_allow_html=True)

    # ============================================================
    # 📈 ИНДИВИДУАЛЬНАЯ ДИНАМИКА УСПЕВАЕМОСТИ
    # ============================================================
    #st.markdown("---")
    #st.subheader("📈 Индивидуальная динамика ученика")
    with st.expander("📈 Индивидуальная динамика ученика (сравнение с классом)", expanded=True):
        # --- Фильтры ---
        col1, col2 = st.columns(2)

        classes_list = sorted(df["class"].dropna().unique())

        with col1:
            selected_class = st.selectbox(
                "Класс:",
                classes_list,
                key="student_dyn_class"
            )

        # Если класс изменился — сбросим выбранного ученика
        prev_class = st.session_state.get("student_dyn_prev_class")
        if prev_class != selected_class:
            st.session_state["student_dyn_student"] = None
            st.session_state["student_dyn_prev_class"] = selected_class

        students_list = sorted(
            df.loc[df["class"] == selected_class, "student"].dropna().unique()
        )

        with col2:
            selected_student = st.selectbox(
                "Ученик:",
                students_list,
                key="student_dyn_student",
                index=0 if st.session_state.get("student_dyn_student") in (None, "") else None
            )

        filtered_dyn = df[
            (df['class'] == selected_class) &
            (df['student'] == selected_student)
        ]
        if filtered_dyn.empty:
            st.warning("Нет данных по выбранному ученику.")
        else:

            # --- Мультивыбор предметов ---
            subjects_available = sorted(filtered_dyn['subject'].dropna().unique())
            selected_subjects = st.multiselect(
                "Выберите предметы:",
                subjects_available,
                default=subjects_available[:1]
            )
            filtered_dyn = filtered_dyn[filtered_dyn['subject'].isin(selected_subjects)]

            
            all_months = pd.DataFrame({
                'month_id': range(1, len(month_order) + 1),
                'month': month_order
            })

            # --- Средние значения по ученику ---
            student_perf = (
                filtered_dyn.groupby(['subject', 'month'], as_index=False)
                .agg({'task_percent': 'mean'})
            )

            # --- Средние значения по классу ---
            class_perf = (
                df[(df['class'] == selected_class) & (df['subject'].isin(selected_subjects))]
                .groupby(['subject', 'month'], as_index=False)
                .agg({'task_percent': 'mean'})
            )

            # --- Восстанавливаем пропущенные месяцы ---
            student_perf = (
                all_months[['month_id', 'month']]
                .merge(student_perf, on='month', how='left')
                .sort_values('month_id')
            )
            class_perf = (
                all_months[['month_id', 'month']]
                .merge(class_perf, on='month', how='left')
                .sort_values('month_id')
            )

            # --- Построение графика ---
            import plotly.graph_objects as go

            fig = go.Figure()

            for subj in selected_subjects:
                # --- Данные по классу ---
                c_df = class_perf[class_perf['subject'] == subj][['month_id', 'month', 'task_percent']].dropna(subset=['task_percent'])
                c_df = c_df.sort_values('month_id')
                months = c_df['month'].tolist()
                c_y = c_df['task_percent'].values

                # --- Данные по ученику ---
                s_df = student_perf[student_perf['subject'] == subj][['month_id', 'month', 'task_percent']]
                s_df = s_df.sort_values('month_id')
                s_y = s_df.set_index('month')['task_percent'].reindex(months).values

                # --- Линия класса ---
                fig.add_trace(go.Scatter(
                    x=months,
                    y=c_y,
                    mode='lines',
                    name="Средний результат класса",
                    line=dict(color='#B0B0B0', width=3, dash='dot'),
                    hovertemplate='Средний по классу: %{y:.1f}%<extra></extra>'
                ))

                # --- Линия ученика ---
                fig.add_trace(go.Scatter(
                    x=months,
                    y=s_y,
                    mode='lines+markers',
                    name=subj,
                    line=dict(color='#007BFF', width=4),
                    marker=dict(size=10, color='#007BFF', line=dict(width=2, color='white')),
                    hovertemplate='%{x}: %{y:.1f}%<extra></extra>'
                ))

                # --- Красные пунктирные линии между пропусками ---
                valid_idx = np.where(~pd.isna(s_y))[0]
                for i in range(len(valid_idx) - 1):
                    left, right = valid_idx[i], valid_idx[i + 1]
                    if right - left > 1 and right < len(months):
                        fig.add_trace(go.Scatter(
                            x=[months[left], months[right]],
                            y=[s_y[left], s_y[right]],
                            mode='lines',
                            line=dict(color='#E74C3C', width=2, dash='dot'),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        for miss in months[left + 1:right]:
                            fig.add_vrect(
                                x0=miss, x1=miss,
                                fillcolor='rgba(220,220,220,0.3)',
                                layer='below', line_width=0
                            )
                            fig.add_annotation(
                                x=miss,
                                yref="paper", y=0.5,
                                text="не писал(-а)",
                                showarrow=False,
                                font=dict(size=11, color='gray', style='italic'),
                                align="center"
                            )

            # --- Настройки графика ---
            fig.update_layout(
                title=dict(
                    text=f"Индивидуальная динамика: <b>{selected_student}</b> ({selected_class})<br>"
                        f"<span style='font-size:0.9em;color:#555;'>На фоне среднего результата класса</span>",
                    x=0.5, xanchor='center'
                ),
                yaxis=dict(
                    title='% выполнения заданий',
                    range=[0, 100],
                    gridcolor='rgba(200,200,200,0.3)',
                    zeroline=False
                ),
                xaxis=dict(
                    title='Месяц',
                    tickmode='array',
                    tickvals=month_order,
                    ticktext=month_order,
                    categoryorder='array',
                    categoryarray=month_order
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=560,
                margin=dict(t=100, b=40, l=60, r=40),
                legend=dict(
                    orientation="h",
                    yanchor="bottom", y=-0.35,
                    xanchor="center", x=0.5,
                    font=dict(size=12),
                    title_text=""
                ),
                hoverlabel=dict(font_size=13, font_family="Arial"),
                annotations=[
                    dict(
                        text="Школа «Шамир»",
                        x=1, y=-0.15,
                        xref="paper", yref="paper",
                        showarrow=False,
                        font=dict(size=11, color="gray"),
                        xanchor="right"
                    )
                ]
            )

            # --- Раздел под графиком ---
            st.markdown("### 🧾 Индивидуальный отчёт ученика")

            col1, col2 = st.columns([2, 1])

            with col1:
                st.plotly_chart(fig, use_container_width=True, key="student_dynamic_chart")

            with col2:
                st.markdown(f"### 👤 {selected_student}")

                # --- Подготовка данных для правой колонки ---
                df_s = filtered_dyn.copy()
                # фиксируем порядок месяцев
                month_order = ['Август','Сентябрь','Октябрь','Ноябрь','Декабрь',
                            'Январь','Февраль','Март','Апрель','Май','Экзамен']
                df_s['month'] = pd.Categorical(df_s['month'], month_order, ordered=True)
                df_s = df_s.sort_values('month')

                # Месяцы, когда ученик писал; и когда писал кто-то из класса
                months_student = df_s['month'].dropna().astype(str).unique().tolist()
                months_class = (df.loc[df['class'] == selected_class, 'month']
                                .dropna().astype(str).unique().tolist())
                missed_months = [m for m in months_class if m not in months_student]

                # Сводим по МЕСЯЦАМ, чтобы не мешать предметы между собой:
                # если выбран 1 предмет — это его значения,
                # если несколько — это среднее по ним за месяц.
                s_by_month = (df_s.groupby('month', observed=True)['task_percent']
                                .mean()
                                .reindex(month_order))

                # Корректный старт/финиш: первая и последняя ненулевые точки
                s_nonan = s_by_month.dropna()
                if len(s_nonan) >= 2:
                    first_month = str(s_nonan.index[0])
                    last_month  = str(s_nonan.index[-1])
                    first_score = float(s_nonan.iloc[0])
                    last_score  = float(s_nonan.iloc[-1])
                    score_growth = round(last_score - first_score, 1)
                else:
                    first_month = last_month = None
                    first_score = last_score = score_growth = None

                # Средний уровень (по всем выбранным предметам и месяцам ученика)
                mean_score = round(df_s['task_percent'].mean(), 1)

                # --- Вывод карточки ---
                st.markdown(f"**📅 Участвовал в {len(months_student)} из {len(months_class)} пробников.**")
                if missed_months:
                    st.markdown(f"Пропущены месяцы: *{', '.join(missed_months)}*")

                if last_score is not None:
                    st.markdown(f"**📈 Последний результат ({last_month}):** {last_score:.1f}%")
                else:
                    st.markdown("**📈 Последний результат:** —")

                st.markdown(f"**📊 Средний уровень:** {mean_score:.1f}%")

                if score_growth is None:
                    st.info("Недостаточно данных для расчёта динамики.")
                elif score_growth > 2:
                    st.success(f"Прогресс по сравнению с началом года: **+{score_growth:.1f}%**")
                elif score_growth < -2:
                    st.error(f"Снижение по сравнению с началом года: **{score_growth:.1f}%**")
                else:
                    st.info("Уровень остаётся стабильным")


                # --- Анализ по заданиям ---
                task_means = (
                    df_s.groupby('task_name')['task_percent']
                    .mean()
                    .sort_values(ascending=False)
                )
                strong_tasks = task_means[task_means > 95].index.tolist()
                weak_tasks = task_means[task_means < 35].index.tolist()
                first_name = str(selected_student).split()[1]

                if strong_tasks or weak_tasks:
                    text_parts = []
                    if strong_tasks:
                        formatted_strong = [t.replace('test', '').replace('text', '').strip() for t in strong_tasks]
                        top_strong = ', '.join(formatted_strong[:4])
                        text_parts.append(f"💪 {first_name} уверенно выполняет **{top_strong}**")
                    if weak_tasks:
                        formatted_weak = [t.replace('test', '').replace('text', '').strip() for t in weak_tasks]
                        top_weak = ', '.join(formatted_weak[:4])
                        text_parts.append(f"⚠️ Следует обратить внимание на **{top_weak}**, где результаты остаются ниже среднего уровня.")
                    st.markdown("<br>".join(text_parts), unsafe_allow_html=True)
                else:
                    st.markdown("Пока недостаточно данных для анализа по заданиям.")


    # ============================================================
    # 📊 СРАВНЕНИЕ КЛАССОВ И ПРЕДМЕТОВ + ДИНАМИКА (ТОЛЬКО СРЕДНИЙ %)
    # ============================================================
    st.subheader("📊 Сравнение классов и предметов и динамика успеваемости")

    # --- Данные: средний % по классам и предметам ---
    comparison = (
        df.groupby(['class', 'subject'], as_index=False)['exam_percent']
        .mean()
        .rename(columns={'exam_percent': 'value'})
    )

    # --- Порядок классов: сортировка по худшим (меньше = хуже) ---
    class_rank = comparison.groupby('class', as_index=False)['value'].mean()
    class_order = class_rank.sort_values('value', ascending=True)['class'].tolist()

    # --- Данные для динамики по месяцам ---
    trend_df = (
        df.groupby(['class', 'month', 'month_id', 'subject'], as_index=False)['exam_percent']
        .mean()
        .rename(columns={'exam_percent': 'value'})
    )

    trend_df['month'] = pd.Categorical(trend_df['month'], categories=month_order, ordered=True)
    trend_df = trend_df.sort_values(['class', 'month_id'])

    # --- Две колонки: слева таблица, справа динамика ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📉 Проблемные зоны школы")

        # ============================================================
        # 1) БЕЗ фильтров: работаем по всей школе
        # ============================================================
        base = df.copy()

        if base.empty:
            st.info("Нет данных для построения таблицы.")
            st.stop()

        # ============================================================
        # 2) Свод: класс × предмет (средний % и доля риска)
        # ============================================================
        summary = (
            base
            .groupby(["class", "subject"], as_index=False)
            .agg(
                avg_percent=("exam_percent", "mean"),
                risk_share=("exam_percent", lambda x: (x < 50).mean() * 100)
            )
        )

        # ============================================================
        # 3) Дельта за последний месяц (по exam_percent)
        # ============================================================
        monthly = (
            base
            .groupby(["class", "subject", "month_id"], as_index=False)["exam_percent"]
            .mean()
            .sort_values("month_id")
        )

        deltas = (
            monthly
            .groupby(["class", "subject"])["exam_percent"]
            .apply(lambda x: float(x.iloc[-1] - x.iloc[-2]) if len(x) >= 2 else 0.0)
            .reset_index(name="delta_month")
        )

        summary = summary.merge(deltas, on=["class", "subject"], how="left")

        summary["avg_percent"] = summary["avg_percent"].round(1)
        summary["risk_share"] = summary["risk_share"].round(1)
        summary["delta_month"] = summary["delta_month"].round(1)

        # ============================================================
        # 4) Сортировка: хуже → выше
        # ============================================================
        summary = summary.sort_values(
            ["avg_percent", "risk_share"],
            ascending=[True, False]
        ).reset_index(drop=True)

        # ============================================================
        # 5) Таблица для AgGrid
        # ============================================================
        grid_df = summary.rename(columns={
            "class": "Класс",
            "subject": "Предмет",
            "avg_percent": "Ср. %",
            "delta_month": "Δ мес",
            "risk_share": "Риск %"
        }).copy()

        grid_df["Зона"] = np.where(grid_df["Ср. %"] < 50, "🟥",
                   np.where(grid_df["Ср. %"] < 65, "🟨", "🟩"))
        
        # Если ничего ещё не выбрано — по умолчанию выберем первую строку
        if "admin_chosen_class" not in st.session_state and not grid_df.empty:
            st.session_state["admin_chosen_class"] = grid_df.iloc[0]["Класс"]
            st.session_state["admin_chosen_subject"] = grid_df.iloc[0]["Предмет"]

        gb = GridOptionsBuilder.from_dataframe(grid_df)

        gb.configure_default_column(
            filter=True,
            sortable=True,
            resizable=True,
            floatingFilter=False
        )

        gb.configure_column(
            "Ср. %",
            type=["numericColumn"],
            valueFormatter="value.toFixed(1)",
            cellStyle={
                "styleConditions": [
                    {"condition": "value < 50", "style": {"backgroundColor": "#f8d7da"}},
                    {"condition": "value >= 50 && value < 65", "style": {"backgroundColor": "#fff3cd"}},
                    {"condition": "value >= 65", "style": {"backgroundColor": "#d4edda"}},
                ]
            }
        )

        gb.configure_column(
            "Δ мес",
            type=["numericColumn"],
            valueFormatter="value >= 0 ? '+' + value.toFixed(1) : value.toFixed(1)",
            cellStyle={
                "styleConditions": [
                    {"condition": "value > 1", "style": {"color": "#27ae60", "fontWeight": "700"}},
                    {"condition": "value < -1", "style": {"color": "#c0392b", "fontWeight": "700"}},
                ]
            }
        )

        gb.configure_column(
            "Риск %",
            type=["numericColumn"],
            valueFormatter="value.toFixed(1)",
            cellStyle={
                "styleConditions": [
                    {"condition": "value >= 35", "style": {"color": "#c0392b", "fontWeight": "800"}},
                    {"condition": "value >= 20 && value < 35", "style": {"color": "#b7950b", "fontWeight": "700"}},
                ]
            }
        )
        gb.configure_column("Класс", width=70, pinned="left")
        gb.configure_column("Предмет", width=110, pinned="left")

        gb.configure_selection(selection_mode="single", use_checkbox=False)

        gb.configure_grid_options(
            enableRangeSelection=True,
            enableCellTextSelection=True,
            domLayout="normal"
        )

        grid = AgGrid(
            grid_df,
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            theme="streamlit",
            height=420,
            fit_columns_on_grid_load=True,
            key="admin_problem_grid"
        )

        selected_rows = grid.get("selected_rows", [])
        if isinstance(selected_rows, pd.DataFrame):
            selected_rows = selected_rows.to_dict("records")
        if selected_rows is None:
            selected_rows = []

        # ============================================================
        # 6) Выбор строки -> session_state -> переменные для правого графика
        # ============================================================
        if len(selected_rows) > 0:
            sel = selected_rows[0]
            st.session_state["admin_chosen_class"] = sel["Класс"]
            st.session_state["admin_chosen_subject"] = sel["Предмет"]

        chosen_class = st.session_state.get("admin_chosen_class")
        chosen_subject = st.session_state.get("admin_chosen_subject")

        if chosen_class and chosen_subject:
            st.markdown(
                f"🔍 **Выбрано:** класс **{chosen_class}**, предмет **{chosen_subject}**"
            )



           
    with col2:
        st.markdown(
            f"#### 📈 Динамика — {chosen_class} · {chosen_subject}"
        )

        # chosen_class / chosen_subject должны быть определены в col1 (через session_state)
        if not chosen_class or not chosen_subject:
            st.info("Выберите строку в таблице слева, чтобы увидеть динамику.")
            st.stop()

        filtered_trend = trend_df[
            (trend_df["class"] == chosen_class) &
            (trend_df["subject"] == chosen_subject)
        ].copy()

        if filtered_trend.empty:
            st.info("Нет данных по выбранной паре класс–предмет для динамики.")
            st.stop()

        # На всякий случай: правильный порядок месяцев
        if "month_id" in filtered_trend.columns:
            filtered_trend = filtered_trend.sort_values("month_id")

        fig_trend = px.line(
            filtered_trend,
            x="month",
            y="value",
            markers=True,
            labels={"month": "Месяц", "value": "Средний %"}  
        )

        fig_trend.add_hline(y=50, line_dash="dash", line_color="rgba(255,0,0,0.35)")
        fig_trend.add_hline(y=60, line_dash="dash", line_color="rgba(255,165,0,0.35)")
        fig_trend.add_hline(y=70, line_dash="dash", line_color="rgba(0,128,0,0.30)")

        fig_trend.update_layout(
            height=520,
            yaxis=dict(range=[0, 100]),
            xaxis=dict(
                tickmode="array",
                tickvals=month_order,
                ticktext=month_order,
                categoryorder="array",
                categoryarray=month_order
            ),
            margin=dict(t=40, b=70, l=40, r=10),
            legend=dict(orientation="h")  # легенда не нужна, предмет один
        )

        st.plotly_chart(fig_trend, use_container_width=True)

    show_teacher_kpi(df)