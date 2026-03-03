import pandas as pd
import streamlit as st

def create_results_summary(data: dict) -> pd.DataFrame:
    """
    Преобразует широкие таблицы results_* в длинный формат:
    каждая строка = один ученик, одно задание, один предмет.
    Добавляет справочные поля и рассчитывает проценты:
        - task_percent = task_score / max_score * 100
        - exam_percent = result / max_result * 100
    """

    results_long = []

    # === 1️⃣ Преобразуем все листы results_* из wide → long ===
    for sheet_name, df in data.items():
        if not sheet_name.startswith("results_"):
            continue

        required_cols = {'student_id', 'student', 'month_id', 'subject_id', 'class_id', 'result', 'mark'}
        if not required_cols.issubset(df.columns):
            st.warning(f"⚠️ В листе {sheet_name} отсутствуют обязательные колонки, пропускаем.")
            continue

        # --- постоянные поля ---
        id_vars = ['student', 'student_id', 'month_id', 'subject_id', 'class_id', 'result', 'mark']

        # --- task_* колонки ---
        task_cols = [c for c in df.columns if c.startswith('task_')]
        if not task_cols:
            st.warning(f"⚠️ В листе {sheet_name} нет столбцов task_*. Пропускаем.")
            continue

        # --- превращаем в длинный формат ---
        melted = df.melt(
            id_vars=id_vars,
            value_vars=task_cols,
            var_name='task_id',
            value_name='task_score'
        )
        melted['source_sheet'] = sheet_name
        results_long.append(melted)

    # === 2️⃣ Объединяем все результаты ===
    if not results_long:
        st.error("❌ Не найдено листов с результатами (results_*)")
        return pd.DataFrame()

    results_summary = pd.concat(results_long, ignore_index=True)

    # === 3️⃣ Добавляем справочники ===
    if 'subjects' in data:
        subj = data['subjects'][['subject_id', 'subject', 'max_result', 'teacher_id']].drop_duplicates()
        results_summary = results_summary.merge(subj, on='subject_id', how='left')

    if 'teachers' in data:
        tch = data['teachers'][['teacher_id', 'teacher']].drop_duplicates()
        results_summary = results_summary.merge(tch, on='teacher_id', how='left')

    if 'classes' in data:
        cls = data['classes'][['class_id', 'class']].drop_duplicates()
        results_summary = results_summary.merge(cls, on='class_id', how='left')

    if 'months' in data:
        mon = data['months'][['month_id', 'month']].drop_duplicates()
        results_summary = results_summary.merge(mon, on='month_id', how='left')

    if 'tasks' in data:
        task_cols = ['task_id', 'subject_id', 'task_name', 'max_score']

        # category может отсутствовать в старых версиях
        if 'category' in data['tasks'].columns:
            task_cols.append('category')

        tsk = data['tasks'][task_cols].drop_duplicates()
        results_summary = results_summary.merge(tsk, on=['task_id', 'subject_id'], how='left')

    # === 4️⃣ Расчёт процентов ===
    if {'task_score', 'max_score'}.issubset(results_summary.columns):
        results_summary['task_percent'] = (
            results_summary['task_score'] / results_summary['max_score'] * 100
        ).round(1)

    if {'result', 'max_result'}.issubset(results_summary.columns):
        results_summary['exam_percent'] = (
            results_summary['result'] / results_summary['max_result'] * 100
        ).round(1)

    # === 5️⃣ Финальный порядок колонок ===
    final_cols = [
    'student', 'student_id', 'class_id', 'class',
    'subject_id', 'subject', 'teacher',
    'month_id', 'month',
    'task_id', 'task_name'
    ]

    if 'category' in results_summary.columns:
        final_cols.append('category')

    final_cols += [
        'task_score', 'max_score', 'task_percent',
        'result', 'max_result', 'exam_percent', 'mark'
    ]


    # если внезапно чего-то нет (кривой справочник) — не упадём
    final_cols = [c for c in final_cols if c in results_summary.columns]
    results_summary = results_summary[final_cols]

    return results_summary
