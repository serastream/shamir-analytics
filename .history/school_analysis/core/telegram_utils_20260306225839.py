import asyncio
import io
from telegram import Bot
import streamlit as st

def _get_token():
    token = st.secrets.get("TELEGRAM_BOT_TOKEN")
    if not token:
        st.error("Критическая ошибка: TELEGRAM_BOT_TOKEN не найден в secrets!")
        return None
    return token.strip()

def send_message(chat_id: int, text: str):
    """Отправка обычного текстового сообщения"""
    token = _get_token()
    if not token: return False

    async def _send():
        bot = Bot(token=token)
        async with bot:
            await bot.send_message(chat_id=int(chat_id), text=text, parse_mode="HTML")
            
    try:
        asyncio.run(_send())
        return True
    except Exception as e:
        st.error(f"Ошибка Telegram (текст): {e}")
        return False

def send_report_with_chart(chat_id: int, text: str, fig=None):
    """Отправка сообщения с графиком Plotly"""
    token = _get_token()
    if not token: return False

    async def _send():
        bot = Bot(token=token)
        async with bot:
            if fig is not None:
                # Конвертация Plotly фигуры в байты изображения
                img_bytes = fig.to_image(format="png", engine="kaleido")
                await bot.send_photo(chat_id=int(chat_id), photo=img_bytes, caption=text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=int(chat_id), text=text, parse_mode="HTML")

    try:
        # Для работы внутри потоков Streamlit иногда лучше использовать такой запуск:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_send())
        return True
    except Exception as e:
        st.error(f"Ошибка Telegram (график): {e}")
        return False