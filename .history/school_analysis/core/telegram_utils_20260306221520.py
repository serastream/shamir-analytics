import os
from io import BytesIO
from typing import Optional, Union

import streamlit as st
from telegram import Bot
from telegram.error import TelegramError

# ============================================================
# 🔐 ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================================

def get_bot() -> Optional[Bot]:
    """
    Безопасно инициализирует объект бота.
    Пытается взять токен из st.secrets или переменных окружения.
    """
    token = None

    if hasattr(st, "secrets"):
        token = st.secrets.get("TELEGRAM_BOT_TOKEN")

    if not token:
        token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        # Мы не кидаем RuntimeError здесь, чтобы не обрушить весь Streamlit,
        # если учитель просто хочет посмотреть графики без рассылки.
        return None

    return Bot(token=token)


# ============================================================
# ✉️ ОТПРАВКА ТЕКСТА
# ============================================================

def send_message(chat_id: Union[int, str], text: str, parse_mode: str = "Markdown") -> bool:
    """
    Отправляет текстовое сообщение. 
    Возвращает True в случае успеха, False при ошибке.
    """
    bot = get_bot()
    if not bot:
        st.error("Ошибка: TELEGRAM_BOT_TOKEN не настроен в secrets.")
        return False

    try:
        # Telegram API требует chat_id как число
        bot.send_message(chat_id=int(chat_id), text=text, parse_mode=parse_mode)
        return True
    except (TelegramError, ValueError, TypeError) as e:
        st.error(f"Не удалось отправить сообщение пользователю {chat_id}: {e}")
        return False


# ============================================================
# 🖼 ОТПРАВКА ИЗОБРАЖЕНИЙ (Графиков)
# ============================================================

def send_image(
    chat_id: Union[int, str],
    image: Union[str, BytesIO],
    caption: Optional[str] = None
) -> bool:
    """
    Отправляет фото (можно передать путь к файлу или объект BytesIO с графиком Plotly/Matplotlib).
    """
    bot = get_bot()
    if not bot: return False

    try:
        if isinstance(image, str):
            with open(image, "rb") as f:
                bot.send_photo(chat_id=int(chat_id), photo=f, caption=caption)
        elif isinstance(image, BytesIO):
            image.seek(0)
            bot.send_photo(chat_id=int(chat_id), photo=image, caption=caption)
        return True
    except TelegramError as e:
        st.error(f"Ошибка при отправке изображения: {e}")
        return False


# ============================================================
# 📄 ОТПРАВКА ДОКУМЕНТОВ (PDF отчеты)
# ============================================================

def send_document(
    chat_id: Union[int, str],
    data: Union[str, BytesIO],
    filename: str,
    caption: Optional[str] = None
) -> bool:
    """
    Отправляет файл (например, PDF отчет).
    """
    bot = get_bot()
    if not bot: return False

    try:
        if isinstance(data, str):
            with open(data, "rb") as f:
                bot.send_document(chat_id=int(chat_id), document=f, filename=filename, caption=caption)
        elif isinstance(data, BytesIO):
            data.seek(0)
            bot.send_document(chat_id=int(chat_id), document=data, filename=filename, caption=caption)
        return True
    except TelegramError as e:
        st.error(f"Ошибка при отправке документа: {e}")
        return False