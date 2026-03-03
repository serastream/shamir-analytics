from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from telegram import Bot
import streamlit as st

def generate_pdf_report(student_name, summary_df, comparison_df):
    """Генерация PDF-отчёта по ученику."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Отчёт по ученику: {student_name}", styles['Title']),
        Spacer(1, 12),
        Paragraph("Успеваемость по месяцам:", styles['Heading2']),
        Paragraph(summary_df.to_html(index=False), styles['Normal']),
        Spacer(1, 12),
        Paragraph("Сравнение с классом:", styles['Heading2']),
        Paragraph(comparison_df.to_html(index=False), styles['Normal'])
    ]
    doc.build(story)
    buffer.seek(0)
    return buffer


def send_pdf_to_telegram(file_path, chat_id, token):
    """Отправка PDF-файла пользователю в Telegram."""
    try:
        bot = Bot(token=token)
        with open(file_path, 'rb') as f:
            bot.send_document(chat_id=chat_id, document=f)
        st.success("📤 Отчёт успешно отправлен в Telegram!")
    except Exception as e:
        st.error(f"Ошибка при отправке: {e}")
