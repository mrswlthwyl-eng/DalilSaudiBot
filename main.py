from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


TOKEN = "8935363149:AAFacfjJb-vzgpb_dNg0sXnvmXmkhPxgxD8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في دليلي الجامعي.\n\n"
        "أنا مساعدك الذكي للإجابة على أسئلة الجامعات السعودية."
    )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("Bot is running...")

    app.run_polling()

if __name__ == "__main__":
    main()
