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

# شخصية دليلي الجامعي
SYSTEM_PROMPT = """
ضع هنا البرومبت الكامل لدليلي الجامعي.
"""

# إنشاء النموذج مع الـ System Prompt
model = genai.GenerativeModel(
    model_name="gemini-3.6-flash",
    system_instruction=SYSTEM_PROMPT,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً وسهلاً بك في دليلي الجامعي.\n\n"
        "🎓 أنا مساعدك الذكي للإجابة على جميع أسئلتك المتعلقة بالجامعات السعودية."
    )


async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        response = model.generate_content(text)

        if response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text(
                "عذرًا، لم أتمكن من إنشاء رد."
            )

    except Exception as e:
        await update.message.reply_text(
            f"حدث خطأ:\n{str(e)}"
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
