import os
import google.generativeai as genai

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# قراءة المتغيرات من Railway
TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ربط Gemini
genai.configure(api_key=GEMINI_API_KEY)

# اختيار نموذج Gemini
model = genai.GenerativeModel("gemini-2.5-flash")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في دليلي الجامعي.\n\n"
        "أنا مساعدك الذكي للإجابة على أسئلة الجامعات السعودية."
    )


async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        response = model.generate_content(text)

        await update.message.reply_text(response.text)

    except Exception as e:
        await update.message.reply_text(
            f"حدث خطأ:\n{e}"
        )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, reply_message)
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
