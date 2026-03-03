import pandas as pd
import streamlit as st

def analyze_subject_dynamics(df: pd.DataFrame) -> pd.DataFrame:
    """Динамика результатов по месяцам и предметам."""
    dynamics = (
        df.groupby(['month_id', 'month', 'subject', 'class'])['task_percent']
        .mean()
        .reset_index()
        .sort_values(['subject', 'class', 'month_id'])
    )
    dynamics['avg_percent'] = (dynamics['task_percent'] * 100).round(1)
    return dynamics


@st.cache_data
def prepare_student_dynamics(df: pd.DataFrame) -> pd.DataFrame:
    """Агрегирует данные для индивидуальной динамики ученика."""
    student = (
        df.groupby(['student', 'class', 'subject', 'month_id', 'month'])
        .agg({'task_percent': 'mean'})
        .reset_index()
    )
    student['task_percent'] *= 100
    return student.sort_values('month_id')
