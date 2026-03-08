import asyncio
import io
from telegram import Bot
import streamlit as st
import openai

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


def generate_ai_report(student_name, mean_score, growth, strong_tasks, weak_tasks, subject):
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    # Промпт для создания эмпатичного отчета
    prompt = f"""
    Ты — профессиональный куратор школы «Шамир». Напиши краткое сообщение родителю ученика по имени {student_name}.
    
    Статистика по предмету {subject}:
    - Средний результат: {mean_score}%
    - Динамика: {growth}% (если >0 - прогресс, если <0 - спад)
    - Сильные стороны: {strong_tasks}
    - Нужно подтянуть: {weak_tasks}
    
    Напиши текст в стиле заботливого наставника. 
    Используй <b></b> для жирного шрифта (HTML). 
    В конце добавь пожелание успехов. 
    Текст должен быть коротким (до 4-5 предложений), чтобы он хорошо смотрелся в Telegram под графиком.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content