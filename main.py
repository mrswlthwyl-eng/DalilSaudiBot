import os
import requests

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

SYSTEM_PROMPT = """
ضع هنا البرومبت الكامل لدليلي الجامعي.
"""

MODEL = "mistral-small-latest"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً وسهلاً بك في دليلي الجامعي.\n\n"
        "🎓 أنا مساعدك الذكي للإجابة على جميع أسئلتك المتعلقة بالجامعات السعودية."
    )


async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_text,
                    },
                ],
            },
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        answer = data["choices"][0]["message"]["content"]

        await update.message.reply_text(answer)

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

    print("🤖 DalilSaudiBot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
