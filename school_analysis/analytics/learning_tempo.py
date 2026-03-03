import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

def show_learning_tempo(df: pd.DataFrame):
    """
    Анализ темпа обучения (скорость изменения процента по месяцам).
    Определяет ускоряющихся, стабильных и тормозящихся учеников.
    """
    st.markdown("## 🧭 Темповые кластеры (когнитивные ритмы)")
    st.caption("Изменение успеваемости по месяцам показывает, кто ускоряется, кто стабилен, а кто теряет темп.")

    required = {'student', 'month_id', 'task_percent'}
    if not required.issubset(df.columns):
        st.error(f"Не хватает колонок: {required - set(df.columns)}")
        return

    # усреднение по месяцам
    trend = (
        df.groupby(['student', 'month_id'], as_index=False)['task_percent']
          .mean().sort_values(['student', 'month_id'])
    )

    # разница между месяцами
    trend['delta'] = trend.groupby('student')['task_percent'].diff()

    # средний темп по каждому ученику
    speed = trend.groupby('student')['delta'].mean().reset_index()
    speed.rename(columns={'delta': 'learning_speed'}, inplace=True)

    # классификация
    median_speed = speed['learning_speed'].median()
    speed['category'] = np.select(
        [
            speed['learning_speed'] > median_speed + 2,
            speed['learning_speed'] < median_speed - 2,
        ],
        ['🟩 ускоряющийся', '🟥 тормозящийся'],
        default='🟨 стабильный'
    )

    # визуализация
    fig = px.bar(
        speed.sort_values('learning_speed', ascending=False),
        x='student', y='learning_speed', color='category',
        color_discrete_map={
            '🟩 ускоряющийся': '#81C784',
            '🟨 стабильный': '#FFF176',
            '🟥 тормозящийся': '#E57373',
        },
        title='Темп изменения успеваемости по ученикам'
    )
    fig.update_layout(
        xaxis_title=None, yaxis_title="Средняя скорость прироста (%)",
        showlegend=True, height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # табличка для уточнения
    st.dataframe(
        speed.sort_values('learning_speed', ascending=False).style.format({'learning_speed': '{:.1f}'}),
        use_container_width=True
    )

    st.info("🧩 Ускоряющиеся ученики требуют сложных задач; тормозящиеся — поддержки и снижения темпа.")


