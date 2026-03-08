import io
import asyncio
from telegram import Bot
import streamlit as st

def send_report_with_chart(chat_id, text, fig=None):
    token = st.secrets.get("TELEGRAM_BOT_TOKEN")
    if not token: return False

    async def _send():
        bot = Bot(token=token.strip())
        async with bot:
            # Если передана фигура Plotly, конвертируем в картинку
            if fig is not None:
                img_bytes = fig.to_image(format="png", engine="kaleido")
                await bot.send_photo(chat_id=int(chat_id), photo=img_bytes, caption=text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=int(chat_id), text=text, parse_mode="HTML")

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_send())
        return True
    except Exception as e:
        st.error(f"Ошибка отправки: {e}")
        return False