from io import BytesIO
from typing import Optional, Union
import os

import streamlit as st
from telegram import Bot


# ============================================================
# 🔐 BOT
# ============================================================

def get_bot() -> Bot:
    token = None

    if hasattr(st, "secrets"):
        token = st.secrets.get("TELEGRAM_BOT_TOKEN")

    if not token:
        token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан")

    return Bot(token=token)


# ============================================================
# ✉️ TEXT
# ============================================================

def send_message(chat_id: int, text: str, parse_mode: str = "Markdown"):
    bot = get_bot()
    bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)


# ============================================================
# 🖼 IMAGE
# ============================================================

def send_image(
    chat_id: int,
    image: Union[str, BytesIO],
    caption: Optional[str] = None
):
    bot = get_bot()

    if isinstance(image, str):
        with open(image, "rb") as f:
            bot.send_photo(chat_id=chat_id, photo=f, caption=caption)
        return

    if isinstance(image, BytesIO):
        image.seek(0)
        bot.send_photo(chat_id=chat_id, photo=image, caption=caption)
        return

    raise ValueError("image должен быть path или BytesIO")


# ============================================================
# 📄 PDF / FILE
# ============================================================

def send_document(
    chat_id: int,
    data: Union[str, BytesIO],
    filename: str,
    caption: Optional[str] = None
):
    bot = get_bot()

    if isinstance(data, str):
        with open(data, "rb") as f:
            bot.send_document(chat_id=chat_id, document=f, filename=filename, caption=caption)
        return

    if isinstance(data, BytesIO):
        data.seek(0)
        bot.send_document(chat_id=chat_id, document=data, filename=filename, caption=caption)
        return