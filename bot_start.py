import os
from datetime import datetime

import pandas as pd
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes


REGISTRY_PATH = os.getenv("TELEGRAM_REGISTRY_PATH", "telegram_registry.xlsx")
REGISTRY_SHEET = os.getenv("TELEGRAM_REGISTRY_SHEET", "telegram_users")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def load_registry() -> pd.DataFrame:
    df = pd.read_excel(REGISTRY_PATH, sheet_name=REGISTRY_SHEET)
    for c in ["role","person_id","name","class","code","telegram_username","chat_id","linked_at"]:
        if c not in df.columns:
            df[c] = None
    return df


def save_registry(df: pd.DataFrame) -> None:
    with pd.ExcelWriter(REGISTRY_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df.to_excel(w, sheet_name=REGISTRY_SHEET, index=False)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    tg_username = f"@{user.username}" if user and user.username else None
    code = context.args[0].strip() if context.args else None

    if not code:
        await update.message.reply_text(
            "Чтобы привязаться к школе, отправь:\n`/start ВАШ_КОД`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        df = load_registry()
    except Exception as e:
        await update.message.reply_text(f"Ошибка чтения реестра: {e}")
        return

    mask = df["code"].astype(str).str.strip().eq(str(code))
    if mask.sum() == 0:
        await update.message.reply_text("Код не найден. Проверь ввод.")
        return

    idx = df[mask].index[0]
    df.loc[idx, "chat_id"] = int(chat.id)
    df.loc[idx, "telegram_username"] = tg_username
    df.loc[idx, "linked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        save_registry(df)
    except Exception as e:
        await update.message.reply_text(f"Ошибка сохранения: {e}")
        return

    await update.message.reply_text(
        "✅ Привязка выполнена! Теперь отчёты будут приходить сюда.",
        parse_mode=ParseMode.MARKDOWN
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в окружении")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()


if __name__ == "__main__":
    main()
