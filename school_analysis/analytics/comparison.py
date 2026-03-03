import pandas as pd
import numpy as np

def analyze_task_difficulty(df: pd.DataFrame) -> pd.DataFrame:
    """Сложность заданий: средний % выполнения по каждому заданию."""
    task_stats = (
        df.groupby(['subject', 'task_name'])[['task_percent']]
        .mean()
        .reset_index()
        .rename(columns={'task_percent': 'avg_task_percent'})
    )
    task_stats['avg_task_percent'] = (task_stats['avg_task_percent'] * 100).round(1)
    return task_stats


def analyze_class_variation(df: pd.DataFrame) -> pd.DataFrame:
    """Вариативность результатов внутри классов."""
    variation = (
        df.groupby(['class', 'subject'])['task_percent']
        .agg(['mean', 'std'])
        .reset_index()
        .rename(columns={'mean': 'avg_percent', 'std': 'std_dev'})
    )
    variation['avg_percent'] = (variation['avg_percent'] * 100).round(1)
    return variation
