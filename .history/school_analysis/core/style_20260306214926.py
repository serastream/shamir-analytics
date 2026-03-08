import streamlit as st

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