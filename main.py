import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from provider_manager import get_manager

TOKEN = os.getenv("BOT_TOKEN")

SYSTEM_PROMPT = """
ضع هنا البرومبت الكامل لدليلي الجامعي.
"""

# إنشاء مدير الذكاء الاصطناعي مرة واحدة فقط
provider = get_manager()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً وسهلاً بك في دليلي الجامعي.\n\n"
        "🎓 أنا مساعدك الذكي للإجابة على جميع أسئلتك المتعلقة بالجامعات السعودية."
    )


async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        answer = await provider.get_response(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_text,
        )

        await update.message.reply_text(answer)

    except Exception:
        await update.message.reply_text(
            "حدثت مشكلة مؤقتة في خدمة الذكاء الاصطناعي، يرجى المحاولة مرة أخرى."
        )


async def on_shutdown(app: Application):
    await provider.shutdown()


def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .post_shutdown(on_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            reply_message,
        )
    )

    print("🤖 DaliliSaudiBot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
