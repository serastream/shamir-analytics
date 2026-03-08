import streamlit as st

def load_school_theme():
    st.markdown("""
    <style>
    /* === ОСНОВНОЙ ФОН И ШРИФТ === */
    .main {
        background-color: #0099cc; /* голубой фирменный цвет */
        font-family: 'Inter', 'Arial', sans-serif;
        color: white;
    }

    /* === САЙДБАР === */
    [data-testid="stSidebar"] {
        background-color: #0077aa;
        color: white;
    }
    [data-testid="stSidebar"] a {
        color: #ffffff !important;
        font-weight: 500;
        transition: 0.2s;
    }
    [data-testid="stSidebar"] a:hover {
        color: #ffe680 !important;
    }

    /* === КНОПКИ === */
    .stButton button {
        background-color: #00b5e2;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton button:hover {
        background-color: #00a0cb;
        transform: translateY(-1px);
    }

    /* === КАРТОЧКИ И МЕТРИКИ === */
    .metric-card {
        background-color: white;
        color: #0077aa;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .metric-card h3 {
        font-size: 16px;
        color: #0099cc;
        margin-bottom: 6px;
    }
    .metric-card p {
        font-size: 26px;
        font-weight: bold;
        margin: 0;
    }

    /* === ГРАФИКИ (фон и цвет линий) === */
    .plotly {
        background-color: white !important;
        border-radius: 12px;
        padding: 10px;
    }

    /* === ХЕДЕР === */
    h1, h2, h3, h4 {
        color: white !important;
        letter-spacing: 0.5px;
    }

    /* === ИНПУТЫ, ВЫБОРЫ === */
    .stSelectbox, .stMultiselect, .stTextInput, .stDateInput {
        background-color: white !important;
        color: #0077aa !important;
    }

    /* === ТАБЫ === */
    [data-baseweb="tab-list"] {
        background-color: #0077aa;
        border-radius: 10px;
        padding: 4px;
    }
    [data-baseweb="tab"] {
        color: white;
    }
    [data-baseweb="tab"]:hover {
        background-color: #00b5e2;
    }

    /* === УВЕДОМЛЕНИЯ === */
    .stAlert {
        background-color: #00b5e2;
        border-radius: 8px;
        color: white;
    }

    </style>
    """, unsafe_allow_html=True)

def apply_premium_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

        /* 1. Общий фон и шрифт */
        .stApp {
            background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
            font-family: 'Inter', sans-serif;
        }

        /* 2. Премиум-карточки (Glassmorphism) */
        .premium-card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #e2e8f0;
            margin-bottom: 16px;
            transition: all 0.3s ease;
        }
        .premium-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }

        /* 3. Стилизация вкладок (Tabs) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px 12px 0 0;
            padding: 10px 20px;
            font-weight: 600;
            color: #64748b;
        }
        .stTabs [aria-selected="true"] {
            background-color: #4f46e5 !important;
            color: white !important;
            border-color: #4f46e5 !important;
        }

        /* 4. Красивые заголовки */
        h1, h2, h3 {
            color: #0f172a !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
        }

        /* 5. Кастомные бейджи */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        </style>
    """, unsafe_allow_html=True)