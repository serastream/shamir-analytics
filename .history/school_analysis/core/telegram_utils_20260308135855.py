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
    Ты опытный куратор школы и педагог, который готовит краткий и понятный комментарий для родителя по графику успеваемости ученика.

    Данные ученика:
    - Имя: {student_name}
    - Предмет: {subject}
    - Средний результат: {mean_score}%
    - Динамика: {growth}%
    - Сильные задания: {strong_tasks}
    - Задания, требующие внимания: {weak_tasks}

    Напиши короткий текст для родителя в 4–6 предложениях.

    Требования к тексту:
    1. Начни с доброжелательного и профессионального вступления.
    2. Кратко интерпретируй общий результат ученика, чтобы родителю было понятно, что означает этот процент.
    3. Обязательно поясни динамику: если она положительная, подчеркни прогресс; если отрицательная — укажи, что есть над чем работать, без резкой критики.
    4. Укажи сильные стороны ученика через задания и сформулируй это как успех.
    5. Укажи одну или несколько зон роста, но мягко и конструктивно.
    6. Заверши текст выводом о дальнейшей работе или поддержкой ученика.
    7. Текст должен быть написан простым, понятным для родителя языком, без канцеляризмов и без сухого перечисления данных.
    8. Не используй шаблонные фразы вроде “желаем дальнейших успехов” и “свидетельствует о прогрессе”.
    9. Не пиши слишком восторженно и не пиши слишком формально.
    10. Используй HTML-теги <b></b> только для ключевых акцентов: результата, динамики, сильных сторон и зоны роста.
    11. Сделай это лаконично, чтобы родители сразу понимали о чем речь

    Сделай текст теплым, содержательным и конкретным. Это должен быть комментарий живого педагога, а не автоматическая сводка.
    """
        
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content