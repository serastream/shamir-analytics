import asyncio
from telegram import Bot
import streamlit as st

def send_message(chat_id: int, text: str):
    """Исправленная функция для синхронного вызова в Streamlit"""
    token = st.secrets.get("TELEGRAM_BOT_TOKEN")
    if not token:
        st.error("TELEGRAM_BOT_TOKEN не найден!")
        return False
        
    async def _send():
        bot = Bot(token=token)
        async with bot:
            await bot.send_message(chat_id=int(chat_id), text=text, parse_mode="HTML")
            
    try:
        # Запускаем асинхронную функцию внутри обычного кода
        asyncio.run(_send())
        return True
    except Exception as e:
        st.error(f"Ошибка Telegram: {e}")
        return False