import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go

def show_influence_network(df: pd.DataFrame, corr_threshold: float = 0.7):
    """
    Строит сеть влияния на основе корреляций между траекториями учеников.
    Вес рёбер — степень схожести изменений результатов.
    """
    st.markdown("## 🔍 Сеть учебного влияния")
    st.caption("Показывает, как результаты учеников влияют друг на друга. Вес связи — степень схожести динамики.")

    required = {'student', 'month_id', 'task_percent'}
    if not required.issubset(df.columns):
        st.error(f"Не хватает колонок: {required - set(df.columns)}")
        return

    # таблица: месяцы × ученики
    pivot = df.pivot_table(index='month_id', columns='student', values='task_percent')
    corr = pivot.corr()

    # создаём граф
    G = nx.Graph()
    for s in corr.columns:
        G.add_node(s, value=df.loc[df['student'] == s, 'task_percent'].mean())

    for i in corr.columns:
        for j in corr.columns:
            if i != j and corr.loc[i, j] > corr_threshold:
                G.add_edge(i, j, weight=corr.loc[i, j])

    if len(G.nodes) == 0:
        st.warning("Недостаточно связей для построения сети.")
        return

    # координаты узлов (центральная компоновка)
    pos = nx.spring_layout(G, seed=42, k=0.8)

    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, line=dict(width=0.6, color='#aaa'),
        hoverinfo='none', mode='lines'
    )

    node_x, node_y, node_size, node_color, node_text = [], [], [], [], []
    for node, data in G.nodes(data=True):
        x, y = pos[node]
        avg = data['value']
        node_x.append(x)
        node_y.append(y)
        node_size.append(10 + avg / 5)
        color = '#E57373' if avg < 40 else '#FFF176' if avg < 65 else '#81C784'
        node_color.append(color)
        node_text.append(f"{node}<br>{avg:.0f}%")

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers+text',
        text=[n.split()[0] for n in G.nodes()], textposition="top center",
        hovertext=node_text,
        marker=dict(size=node_size, color=node_color, line_width=1)
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False, height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='white', paper_bgcolor='white',
        title="🕸️ Социограмма влияния (корреляции > 0.7)"
    )
    st.plotly_chart(fig, use_container_width=True)

    # — вывод лидеров влияния
    influence = dict(G.degree(weight='weight'))
    top3 = sorted(influence.items(), key=lambda x: x[1], reverse=True)[:3]
    st.markdown("### 🌟 Лидеры влияния в классе")
    for name, score in top3:
        st.markdown(f"**{name}** — индекс резонанса: `{score:.2f}`")

    st.caption("Высокий индекс резонанса означает, что изменения успехов этого ученика чаще совпадают с изменениями других.")
