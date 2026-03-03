# school_analysis/analytics/diagnostics.py
# ============================================================
# UI + Визуализация (Streamlit/Seaborn/Matplotlib)
# ВАЖНО: никаких расчётов метрик тут больше нет.
# Расчёты берём из school_analysis.core.metrics
# ============================================================

import pandas as pd
import numpy as np
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import re

from school_analysis.core.metrics import (
    task_perf_table_for_heatmap,
    MONTH_ORDER_DEFAULT,
    prepare_task_diagnostics,   # оставляем доступным, если где-то импортируется из diagnostics
    prepare_class_heatmap,      # оставляем доступным, если где-то импортируется из diagnostics
)


def plot_class_task_performance(df: pd.DataFrame):
    st.markdown("#### 🧠 Анализ по месяцам")

    required_cols = {"class", "month", "subject", "task_name", "task_percent", "student"}
    if not required_cols.issubset(df.columns):
        st.warning(f"В данных должны быть колонки: {', '.join(sorted(required_cols))}")
        return

    # --- UI-стили ---
    st.markdown(
        "<style>"
        "div[data-testid='stVerticalBlock'] > div:has(> div[data-testid='column']){margin-bottom:0rem!important;}"
        ".stRadio > label {margin-bottom:0.25rem!important;}"
        "</style>",
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns([1, 1.1, 1.4, 1.4])

    with col1:
        selected_class = st.selectbox(
            "Класс:",
            sorted(df["class"].dropna().unique()),
            key="class_selector_task_perf",
            label_visibility="visible",
        )

    with col2:
        subjects = ["Все предметы"] + sorted(df["subject"].dropna().unique())
        selected_subject = st.selectbox(
            "Предмет:",
            subjects,
            key="subject_selector_task_perf",
            label_visibility="visible",
        )

    with col3:
        mode = st.radio(
            "Смотреть по:",
            ["Заданиям", "Ученикам", "Задания конкретного ученика"],
            key="aggregation_mode_task_perf",
            horizontal=True,
        )

    with col4:
        if mode == "Задания конкретного ученика":
            students_all = df.loc[df["class"] == selected_class, "student"].dropna().unique()
            selected_student = st.selectbox(
                "Ученик:",
                sorted(students_all),
                key="student_selector_specific",
                label_visibility="visible",
            )
        else:
            selected_student = None

        hide_empty_months = st.checkbox(
            "Скрыть пустые месяцы",
            value=False,
            key="hide_empty_months_task_perf",
            help="Убирает из теплокарты месяцы, где нет данных (класс не писал пробник).",
        )

    # --- Получаем каноническую таблицу (вся математика в metrics.py) ---
    try:
        class_avg, months_to_show, months_without_data, overall_mean = task_perf_table_for_heatmap(
            df,
            mode=mode,
            hide_empty_months=hide_empty_months,
            selected_class=selected_class,
            selected_subject=selected_subject,
            selected_student=selected_student,
            month_col="month",
        )
    except Exception as e:
        st.error(f"Ошибка подготовки тепловой карты: {e}")
        return

    if class_avg.empty:
        st.info("Нет данных по выбранному фильтру.")
        return

    # --- Визуализация ---
    cmap = LinearSegmentedColormap.from_list("grad", ["#ff0000", "#ffff00", "#00ff00"], N=256)

    # строка средних по месяцу (без 'Среднее')
    month_means = class_avg.drop(columns=["Среднее"], errors="ignore").mean(axis=0, skipna=True)
    month_means.name = "Средний по месяцу"
    class_avg_with_mean = pd.concat([class_avg, month_means.to_frame().T])

    # размеры
    month_order_full = MONTH_ORDER_DEFAULT
    n_months = len(month_order_full)
    fig_width = n_months + 1.2
    fig_height = max(4, 0.4 * len(class_avg_with_mean))

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    sns.heatmap(
        class_avg_with_mean,
        annot=True,
        fmt=".2f",
        cmap=cmap,
        linewidths=0.5,
        vmin=0,
        vmax=1,
        cbar=False,
        mask=class_avg_with_mean.isna(),
        annot_kws={"color": "black"},
        ax=ax
    )

    # --- Месяцы сверху ---
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    plt.xticks(rotation=45, ha="left")
    plt.yticks(rotation=0)

    # --- Серые зоны "Не писали" ---
    if not hide_empty_months:
        # months_to_show в этом режиме = полный порядок, иначе = только с данными
        for idx, month in enumerate(months_to_show):
            if month in months_without_data:
                y_center = len(class_avg_with_mean) / 2
                ax.axvspan(idx, idx + 1, facecolor="lightgray", alpha=0.15, zorder=0)
                ax.text(
                    idx + 0.5, y_center, "Не писали",
                    rotation=90, ha="center", va="center",
                    color="gray", fontsize=11, alpha=0.8,
                    fontstyle="italic", zorder=3
                )

    # --- Заголовок ---
    title_obj = {
        "Заданиям": "Средние баллы по заданиям",
        "Ученикам": "Средние баллы по ученикам",
        "Задания конкретного ученика": f"Результаты по заданиям — {selected_student}"
    }[mode]

    ax.set_title(
        f"{title_obj} — {selected_class}"
        + (f" ({selected_subject})" if selected_subject != "Все предметы" else ""),
        fontsize=12,
        pad=50,
    )

    ax.set_xlabel("")
    ax.set_ylabel("Задание" if mode != "Ученикам" else "Ученик")

    plt.tight_layout()
    st.pyplot(fig)

    st.markdown(f"**Средний результат по выборке:** {(overall_mean * 100):.1f}%")
