import numpy as np

def format_delta(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "⚪ —"
    if x > 0:
        return f"🟢 +{x:.1f}"
    if x < 0:
        return f"🔴 {x:.1f}"
    return "⚪ 0.0"

MONTH_ORDER = [
    'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Экзамен'
]
