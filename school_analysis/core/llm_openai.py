from __future__ import annotations

import os
from typing import Optional, Dict, Any
import pandas as pd
import streamlit as st

from openai import OpenAI
from school_analysis.core.metrics import build_teacher_evidence

# ============================================================
# 🔧 НАСТРОЙКИ ПО УМОЛЧАНИЮ
# ============================================================

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 700


# ============================================================
# 🔌 КЛИЕНТ OPENAI (один на всё приложение)
# ============================================================

@st.cache_resource
def get_client() -> OpenAI:
    """
    Создаём единый OpenAI-клиент.
    Ключ берём из Streamlit secrets или из переменных окружения.
    """
    api_key = None

    if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]

    api_key = api_key or os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "❌ OPENAI_API_KEY не найден. "
            "Добавь его в .streamlit/secrets.toml или в переменные окружения."
        )

    return OpenAI(api_key=api_key)


# ============================================================
# 🤖 УНИВЕРСАЛЬНЫЙ ВЫЗОВ МОДЕЛИ
# ============================================================

def ask_openai(
    *,
    input_text: str,
    system_text: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_output_tokens: int = DEFAULT_MAX_TOKENS,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Единая точка входа для всех панелей (teacher / admin / parent / student).
    """

    client = get_client()

    if system_text:
        composed_input = (
            f"SYSTEM:\n{system_text.strip()}\n\n"
            f"USER:\n{input_text.strip()}"
        )
    else:
        composed_input = input_text.strip()

    response = client.responses.create(
        model=model,
        input=composed_input,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        metadata=metadata or {},
    )

    return getattr(response, "output_text", "").strip()


# ============================================================
# 📊 КОНТЕКСТ ДЛЯ УЧИТЕЛЯ (СЖАТИЕ ДАННЫХ)
# ============================================================

def build_teacher_context(df_c: pd.DataFrame, *, top_n: int = 5) -> str:
    
    dff = df_c.copy()

    # Гарантируем month (если вдруг прилетел только month_id)
    if "month" not in dff.columns and "month_id" in dff.columns:
        dff["month"] = dff["month_id"].astype(str)

    # Определяем класс/предмет из данных
    selected_class = str(dff["class"].dropna().iloc[0]) if "class" in dff.columns and not dff["class"].dropna().empty else ""
    selected_subject = str(dff["subject"].dropna().iloc[0]) if "subject" in dff.columns and not dff["subject"].dropna().empty else "Все предметы"

    ev = build_teacher_evidence(
        dff,
        selected_class=selected_class,
        selected_subject=selected_subject,
        top_n=top_n,
        risk_threshold_pct=50.0,
    )

    weak_tasks = ev["tables"]["weak_tasks"]
    weak_students = ev["tables"]["weak_students"]
    strong_students = ev["tables"]["strong_students"]
    risk_share = ev["kpis"]["risk_share_students_pct"]
    overall = ev["kpis"]["overall_mean_pct"]

    def fmt_df(df: pd.DataFrame, cols: List[str], fmt_map: Optional[dict] = None) -> str:
        if df is None or df.empty:
            return "- нет данных"
        lines = []
        for _, r in df.iterrows():
            parts = []
            for c in cols:
                v = r[c]
                if fmt_map and c in fmt_map:
                    parts.append(fmt_map[c](v))
                else:
                    parts.append(str(v))
            lines.append("- " + " — ".join(parts))
        return "\n".join(lines)

    context = f"""
КОНТЕКСТ (единые метрики проекта)

Класс: {selected_class}
Предмет: {selected_subject}

Средний результат по выборке: {overall:.1f}%
Доля учеников в зоне риска (<50%): {risk_share:.1f}%

Топ проблемных заданий (средняя успешность по месяцам — как в тепловой карте):
{fmt_df(weak_tasks, ["task_name", "avg_monthly_success_pct"], fmt_map={"avg_monthly_success_pct": lambda x: f"{float(x):.1f}%"})}

Слабые ученики (по среднему результату):
{fmt_df(weak_students, ["student", "avg_success_pct"], fmt_map={"avg_success_pct": lambda x: f"{float(x):.1f}%"})}

Сильные ученики (по среднему результату):
{fmt_df(strong_students, ["student", "avg_success_pct"], fmt_map={"avg_success_pct": lambda x: f"{float(x):.1f}%"})}

Определения:
- {ev["definitions"]["task_metric"]}
- {ev["definitions"]["risk_metric"]}
""".strip()

    return context



# ============================================================
# 🎓 SYSTEM PROMPT ДЛЯ УЧИТЕЛЯ
# ============================================================

def teacher_system_prompt() -> str:
    return (
        "Ты аналитический AI-помощник учителя по пробным экзаменам. "
        "Твоя задача — интерпретировать предоставленный контекст и предложить действия. "

        "Правила: "
        "1) Опирайся ТОЛЬКО на данные из контекста, ничего не выдумывай. "
        "2) Не пересчитывай проценты и не выводи новые числа — используй только те значения, что уже есть в контексте. "
        "3) Все проценты в контексте — это средняя успешность по месяцам (та же метрика, что в тепловой карте). "
        "4) Если данных недостаточно, прямо напиши, каких данных не хватает и что нужно добавить. "

        "Формат ответа: "
        "— 3–6 коротких пунктов с конкретными шагами на 1–2 недели; "
        "— упомяни топ проблемных заданий и предложи, как их отработать; "
        "— если уместно, выдели группу риска и предложи 1–2 меры поддержки."
    )