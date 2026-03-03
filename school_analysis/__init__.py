"""
Пакет school_analysis — аналитическая система для школьных данных.

Содержит:
- core: загрузка и подготовка данных
- analytics: аналитические расчёты и визуализация
- roles: интерфейсы для разных категорий пользователей
"""

# === Базовые компоненты ===
from .core.loader import load_uploaded_excel
from .core.preprocess import create_results_summary
from .core.utils import format_delta, MONTH_ORDER

# === Аналитика ===
from .analytics.overview import (
    analyze_school_overview,
    analyze_teacher_performance,
)
from .analytics.dynamics import (
    analyze_subject_dynamics,
    prepare_student_dynamics,
)
from .analytics.diagnostics import (
    prepare_task_diagnostics,
    prepare_class_heatmap,
    plot_class_task_performance,
)
from .analytics.comparison import (
    analyze_task_difficulty,
    analyze_class_variation,
)
from .analytics.reports import (
    generate_pdf_report,
    send_pdf_to_telegram,
)

# === Панели ролей ===
from .roles import admin_panel, teacher_panel, parent_panel, student_panel

__all__ = [
    # core
    "load_uploaded_excel",
    "create_results_summary",
    "format_delta",
    "MONTH_ORDER",

    # analytics
    "analyze_school_overview",
    "analyze_teacher_performance",
    "analyze_subject_dynamics",
    "prepare_student_dynamics",
    "prepare_task_diagnostics",
    "prepare_class_heatmap",
    "plot_class_task_performance",
    "analyze_task_difficulty",
    "analyze_class_variation",
    "generate_pdf_report",
    "send_pdf_to_telegram",

    # roles
    "admin_panel",
    "teacher_panel",
    "parent_panel",
    "student_panel",
]
