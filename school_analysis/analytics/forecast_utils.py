import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go

def _month_index(series: pd.Series, month_order=None):
    """Создаёт индекс месяцев в правильном порядке."""
    if month_order:
        return {m: i for i, m in enumerate(month_order)}
    seen = []
    for m in series:
        if m not in seen:
            seen.append(m)
    return {m: i for i, m in enumerate(seen)}

def add_forecast_line(
    fig,
    df: pd.DataFrame,
    col_x: str = "month",
    col_y: str = "exam_percent",
    months: int = 2,
    direction: str = "forward",  # "forward" | "backward"
    month_order=None,
    color_forward: str = "orange",
    color_backward: str = "gray",
    corridor: bool = True,
    show_badge: bool = True,
):
    """
    Добавляет линию прогноза (вперёд или назад) с опциональным коридором ±5%.
    """
    metrics = {}
    if len(df) < 3 or df[col_y].isna().all():
        return fig, metrics

    df = df.dropna(subset=[col_x, col_y]).copy()
    month_map = _month_index(df[col_x], month_order)
    df["month_num"] = df[col_x].map(month_map)
    X = df[["month_num"]]
    y = df[col_y].astype(float)

    model = LinearRegression().fit(X, y)

    if direction == "forward":
        last = df["month_num"].max()
        future = np.arange(last + 1, last + months + 1)
        preds = model.predict(future.reshape(-1, 1))
        future_labels = [f"Месяц +{i}" for i in range(1, months + 1)]
        color = color_forward
        name = f"Прогноз (+{months})"
    else:
        last = df["month_num"].max()
        cut = last - months
        train = df[df["month_num"] <= cut]
        test = df[df["month_num"] > cut]
        if len(train) < 2 or len(test) == 0:
            return fig, metrics
        model = LinearRegression().fit(train[["month_num"]], train[col_y])
        preds = model.predict(test[["month_num"]])
        future_labels = test[col_x].tolist()
        color = color_backward
        name = f"Ретро-прогноз ({months})"
        mae = float(np.mean(np.abs(test[col_y] - preds)))
        metrics["MAE"] = mae

    # Основная пунктирная линия
    fig.add_trace(
        go.Scatter(
            x=future_labels,
            y=preds,
            mode="lines+markers",
            name=name,
            line=dict(dash="dash", color=color),
            marker=dict(color=color),
        )
    )

    # Коридор неопределённости ±5 %
    if corridor:
        upper = preds + 5
        lower = preds - 5
        fig.add_trace(
            go.Scatter(
                x=list(future_labels) + list(future_labels[::-1]),
                y=list(upper) + list(lower[::-1]),
                fill="toself",
                fillcolor=f"rgba(255,165,0,0.12)" if direction == "forward" else "rgba(128,128,128,0.12)",
                line=dict(color="rgba(255,255,255,0)"),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Мини-бейдж точности
    if show_badge and "MAE" in metrics:
        fig.add_annotation(
            text=f"MAE {metrics['MAE']:.1f}%",
            xref="paper", yref="paper",
            x=0.99, y=0.99,
            showarrow=False,
            align="right",
            font=dict(size=12, color=color),
            bgcolor="rgba(255,255,255,0.6)"
        )

    return fig, metrics
