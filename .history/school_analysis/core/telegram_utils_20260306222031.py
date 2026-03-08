import streamlit as st
from telegram import Bot

def send_simple_message(chat_id, text):
    """Просто отправляет текст, если есть токен и ID"""
    token = st.secrets.get("TELEGRAM_BOT_TOKEN")
    if not token or not chat_id:
        return False
    try:
        bot = Bot(token=token)
        # Сделаем задержку или асинхронность, но для простоты — прямой вызов
        import asyncio
        asyncio.run(bot.send_message(chat_id=int(chat_id), text=text, parse_mode='HTML'))
        return True
    except Exception as e:
        st.error(f"Ошибка: {e}")
        return False