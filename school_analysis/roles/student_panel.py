import streamlit as st
import plotly.express as px
import pandas as pd

from school_analysis.analytics import dynamics
from school_analysis.analytics import overview as ov


def show(df: pd.DataFrame, student_id: int, student_name: str):
    st.header("🎯 Твоя персональная аналитика")
    st.subheader(f"Ученик: {student_name}")

    tab1, tab2 = st.tabs(["Динамика", "Сильные и слабые стороны"])

    with tab1:
        progress = ov.student_progress(df, student_id)
        st.dataframe(progress, use_container_width=True)
        if not progress.empty:
            fig = px.line(progress, x='month_id', y='avg_percent', color='subject', markers=True)
            fig.update_layout(yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Пока нет данных по динамике.")

    with tab2:
        strengths = ov.student_strengths_weaknesses(df, student_id)
        st.dataframe(strengths, use_container_width=True)
        if not strengths.empty:
            fig = px.bar(strengths, x='task_name', y='avg_percent', color='level')
            fig.update_layout(yaxis=dict(range=[0, 100]), xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Пока нет данных для анализа по заданиям.")
