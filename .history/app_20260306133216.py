import streamlit as st

# === Импорты из проекта ===
from school_analysis.core.loader import load_uploaded_excel
from school_analysis.core.preprocess import create_results_summary
from school_analysis.roles import admin_panel, teacher_panel, parent_panel, student_panel
from school_analysis.core.style import load_school_theme


# ------------------------------------------------
# ⚙️ Настройки приложения
# ------------------------------------------------
st.set_page_config(page_title="Школьная аналитика", layout="wide", page_icon="🎓")

# Если голубая тема не нравится — закомментируй следующую строку
#load_school_theme()

st.title('🎓 Аналитическая панель "Школа Шамир"')

# ------------------------------------------------
# 🔐 Секреты (из .streamlit/secrets.toml или Streamlit Cloud Secrets)
# ------------------------------------------------
def get_secret(key: str, default=None):
    """Безопасно достаём секрет: если нет — возвращаем default."""
    try:
        return st.secrets[key]
    except Exception:
        return default


ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "")
TEACHER_PASSWORD = get_secret("TEACHER_PASSWORD", "")


# ------------------------------------------------
# 📂 1. Загрузка Excel-файла
# ------------------------------------------------
st.sidebar.header("📂 Загрузка данных")
uploaded_file = st.sidebar.file_uploader("Выберите Excel-файл (.xlsx):", type=["xlsx"])

if not uploaded_file:
    st.info("⬆️ Загрузите Excel-файл для начала анализа.")
    st.stop()

data = load_uploaded_excel(uploaded_file)
df_results_summary = create_results_summary(data)

if df_results_summary.empty:
    st.error("❌ Не удалось сформировать агрегированные данные.")
    st.stop()
else:
    st.success("✅ Файл успешно загружен и данные подготовлены!")


# ------------------------------------------------
# 🔐 2. Авторизация пользователя
# ------------------------------------------------
st.sidebar.header("🔐 Авторизация")
ROLES = ["Администрация", "Учитель", "Ученик", "Родитель"]
role = st.sidebar.selectbox("Выберите роль:", ROLES)

student_id = None
student_name = None

# --- Администрация ---
if role == "Администрация":
    if not ADMIN_PASSWORD:
        st.error("❌ Не задан ADMIN_PASSWORD в secrets. Добавьте его в .streamlit/secrets.toml или Streamlit Cloud → Secrets.")
        st.stop()

    password = st.sidebar.text_input("Введите пароль администрации:", type="password")
    if password != ADMIN_PASSWORD:
        st.warning("Введите корректный пароль для доступа.")
        st.stop()
    st.sidebar.success("✅ Вход администратора выполнен.")

# --- Учитель ---
elif role == "Учитель":
    if not TEACHER_PASSWORD:
        st.error("❌ Не задан TEACHER_PASSWORD в secrets. Добавьте его в .streamlit/secrets.toml или Streamlit Cloud → Secrets.")
        st.stop()

    password = st.sidebar.text_input("Введите пароль учителя:", type="password")
    if password != TEACHER_PASSWORD:
        st.warning("Введите корректный пароль.")
        st.stop()
    st.sidebar.success("✅ Вход учителя выполнен.")

    # --- Родитель ---
    elif role == "Родитель":
        surname = st.sidebar.text_input("Введите фамилию ученика:").strip()
        if not surname:
            st.info("Введите фамилию ученика для продолжения.")
            st.stop()

        # Фильтруем данные по введенной фамилии
        matches = df_results_summary[df_results_summary["student"].astype(str).str.contains(surname, case=False, na=False)]
        
        if matches.empty:
            st.error("❌ Ученик с такой фамилией не найден.")
            st.stop()

        # Извлекаем список имен как чистый список Python (.tolist()), чтобы избежать проблем с индексами
        possible_students = sorted(matches["student"].unique().tolist())
        student_name = st.sidebar.selectbox("Выберите ученика:", possible_students)
        
        # Безопасно получаем student_id
        selected_row = matches[matches["student"] == student_name]
        if not selected_row.empty:
            student_id = selected_row["student_id"].iloc[0]
            st.sidebar.success(f"✅ Отчёт для родителя: {student_name}")
        else:
            st.error("Ошибка: данные ученика не найдены.")
            st.stop()

    # --- Ученик ---
    elif role == "Ученик":
        # Также используем .tolist() для чистого списка имен
        student_list = sorted(df_results_summary["student"].dropna().astype(str).unique().tolist())
        student_name = st.sidebar.selectbox("Выберите своё имя:", student_list)
        
        # Безопасный поиск ID
        selected_row = df_results_summary[df_results_summary["student"] == student_name]
        if not selected_row.empty:
            student_id = selected_row["student_id"].iloc[0]
            st.sidebar.success(f"✅ Привет, {student_name}!")
        else:
            st.error("Ошибка: ID ученика не найден.")
            st.stop()


# ------------------------------------------------
# 🧩 3. Интерфейс по ролям
# ------------------------------------------------
st.markdown("---")

if role == "Администрация":
    admin_panel.show(df_results_summary, data)

elif role == "Учитель":
    teacher_panel.show(df_results_summary)

elif role == "Родитель" and student_id is not None:
    parent_panel.show(df_results_summary, student_id, student_name)

elif role == "Ученик" and student_id is not None:
    student_panel.show(df_results_summary, student_id, student_name)

else:
    st.warning("Выберите роль для продолжения работы.")
