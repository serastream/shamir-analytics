import pandas as pd
import numpy as np

def analyze_school_overview(df: pd.DataFrame) -> pd.DataFrame:
    """Средние показатели по предметам, классам и учителям."""
    overview = (
        df.groupby(['subject', 'class', 'teacher'])['task_percent']
        .agg(['mean', 'std', 'count'])
        .reset_index()
        .rename(columns={'mean': 'avg_percent', 'std': 'variance', 'count': 'num_records'})
    )
    overview['avg_percent'] = (overview['avg_percent'] * 100).round(1)
    return overview


def analyze_teacher_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Оценка эффективности учителей."""
    teacher_stats = (
        df.groupby('teacher')['task_percent']
        .agg(['mean', 'std', 'count'])
        .reset_index()
        .rename(columns={'mean': 'avg_percent', 'std': 'variance'})
    )
    teacher_stats['avg_percent'] = (teacher_stats['avg_percent'] * 100).round(1)
    return teacher_stats

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

def student_progress(df: pd.DataFrame, student_id: int) -> pd.DataFrame:
    """Индивидуальная динамика ученика по предметам и месяцам."""
    personal = (
        df.query("student_id == @student_id")
        .groupby(['month_id', 'month', 'subject'])['task_percent']
        .mean()
        .reset_index()
        .sort_values(['subject', 'month_id'])
    )
    personal['avg_percent'] = (personal['task_percent'] * 100).round(1)
    return personal


def student_strengths_weaknesses(df: pd.DataFrame, student_id: int) -> pd.DataFrame:
    """Задания, в которых ученик успешен / испытывает трудности."""
    personal_tasks = (
        df.query("student_id == @student_id")
        .groupby(['subject', 'task_name'])['task_percent']
        .mean()
        .reset_index()
    )
    personal_tasks['avg_percent'] = (personal_tasks['task_percent'] * 100).round(1)
    personal_tasks['level'] = np.where(
        personal_tasks['avg_percent'] >= 70, 'сильная сторона',
        np.where(personal_tasks['avg_percent'] < 50, 'трудность', 'средний уровень')
    )
    return personal_tasks.sort_values('avg_percent', ascending=False)

def parent_monthly_summary(df: pd.DataFrame, student_id: int) -> pd.DataFrame:
    """Краткий отчёт для родителей: средний % по предметам за месяц."""
    summary = (
        df.query("student_id == @student_id")
        .groupby(['month_id', 'month', 'subject'])['task_percent']
        .mean()
        .reset_index()
    )
    summary['avg_percent'] = (summary['task_percent'] * 100).round(1)
    return summary


def parent_comparison_with_class(df: pd.DataFrame, student_id: int) -> pd.DataFrame:
    """Сравнение ученика с классом."""
    student_info = df.query("student_id == @student_id")[['student_id', 'class']].drop_duplicates()
    if student_info.empty:
        return pd.DataFrame(columns=['subject', 'student_avg', 'class_avg', 'difference'])

    class_name = student_info['class'].iloc[0]

    student_avg = (
        df.query("student_id == @student_id")
        .groupby('subject')['task_percent']
        .mean()
        .rename('student_avg')
    )

    class_avg = (
        df[df["class"] == class_name]
        .groupby('subject')['task_percent']
        .mean()
        .rename('class_avg')
    )

    comparison = pd.concat([student_avg, class_avg], axis=1).reset_index()
    comparison['difference'] = (comparison['student_avg'] - comparison['class_avg']) * 100
    comparison[['student_avg', 'class_avg']] = (comparison[['student_avg', 'class_avg']] * 100).round(1)
    comparison['difference'] = comparison['difference'].round(1)
    return comparison