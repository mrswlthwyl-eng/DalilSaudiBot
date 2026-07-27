from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8935363149:AAFacfjJb-vzgpb_dNg0sXnvmXmkhPxgxD8"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في دليلي الجامعي.\n\n"
        "أنا مساعدك الذكي للإجابة على أسئلة الجامعات السعودية."
    )


async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    await update.message.reply_text(
        f"📩 لقد أرسلت:\n\n{text}"
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
