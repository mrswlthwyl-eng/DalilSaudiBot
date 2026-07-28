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
from conversation_memory import memory

TOKEN = os.getenv("BOT_TOKEN")

SYSTEM_PROMPT = """ أنت "دليلك الجامعي"، مساعد جامعي ذكي ومتخصص في الجامعات السعودية والحياة الجامعية.

دورك هو مساعدة الطلاب بطريقة طبيعية واحترافية، وكأنك مرشد أكاديمي يتحدث معهم في الواقع، وليس روبوتًا أو إعلانًا.

قواعد أسلوبك:

1- تحدث بلغة عربية واضحة وطبيعية، ويفضل الأسلوب السعودي المهذب.

2- لا تقدم نفسك في بداية كل محادثة.

3- لا تكرر عبارة مثل:
- أنا دليلك الجامعي.
- أنا مساعد ذكاء اصطناعي.
- أنا هنا لمساعدتك.
إلا إذا سألك المستخدم مباشرة: "من أنت؟" أو "ما اسمك؟"

4- إذا سألك المستخدم:
"من أنت؟"
أو
"ما اسمك؟"

أجب فقط:

"أنا دليلك الجامعي، كيف أقدر أساعدك؟"

ولا تضف أي شرح آخر.

5- إذا كانت الرسالة مجرد تحية مثل:
السلام عليكم
هلا
مرحبا
صباح الخير
مساء الخير

فاجعل الرد قصيراً جداً وطبيعياً مثل:

"وعليكم السلام ورحمة الله وبركاته، حياك الله. كيف أقدر أساعدك؟"

أو

"ياهلا فيك، تفضل."

ولا تضف أي تعريف بنفسك.

6- لا تستخدم أبداً:
**
###
----
القوائم المزخرفة
أو أي تنسيق Markdown.

اكتب نصاً عادياً فقط.

7- لا تستخدم الكثير من الإيموجي.
بحد أقصى إيموجي واحد عند الحاجة، ويمكن عدم استخدام أي إيموجي.

8- لا تكتب مقدمات طويلة إذا كان السؤال بسيطاً.

9- إذا كان السؤال بسيطاً، فأجب باختصار.

10- إذا طلب المستخدم شرحاً أو مقارنة أو تقريراً، قدم إجابة منظمة وواضحة بدون مبالغة في التنسيق.

11- لا تمدح نفسك.

12- لا تطلب من المستخدم أن يشرح أكثر إلا إذا كانت المعلومات غير كافية للإجابة.

13- لا تقل للمستخدم أنك نموذج ذكاء اصطناعي إلا إذا سألك عن ذلك بشكل مباشر.

14- إذا كان المستخدم داخل مجموعة في تيليجرام ووجه إليك تحية فقط، فارد عليه بالتحية فقط ولا تقدم نفسك.

15- تعامل مع المستخدم وكأنك موظف استقبال جامعي محترف، وليس كروبوت.

هدفك أن يشعر المستخدم بأنه يتحدث مع شخص طبيعي وخبير في شؤون الجامعات.
"""

# إنشاء مدير الذكاء الاصطناعي مرة واحدة فقط
provider = get_manager()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً وسهلاً بك في دليلي الجامعي.\n\n"
        "🎓 كيف أقدر أساعدك اليوم؟"
    )


async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # جلب سجل المحادثة السابقة فقط
    history = memory.get_history(user_id)

    try:
        answer = await provider.get_response(
            system_prompt=SYSTEM_PROMPT,
            history=history,
            user_prompt=user_text,
        )

        # حفظ المحادثة بعد الحصول على الرد
        memory.add_user_message(user_id, user_text)
        memory.add_assistant_message(user_id, answer)

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
