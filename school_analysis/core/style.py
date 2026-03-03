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
