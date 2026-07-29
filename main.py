import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from hijridate import Hijri

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
from knowledge_manager import get_knowledge_manager

TOKEN = os.getenv("BOT_TOKEN")

# ============================================================
# نظام الصلاحيات - المجموعات والحسابات المفعلة
# ============================================================
ALLOWED_GROUPS = {
    -1004452669915,
}

ALLOWED_USERS = {
    2076364383,
}

# ============================================================
# System Prompt
# ============================================================
SYSTEM_PROMPT = """  أنت "دليلك الجامعي"، مساعد جامعي ذكي ومتخصص في الجامعات السعودية والحياة الجامعية.

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

تعليمات تنسيق الرد:

- أرسل جميع الردود كنص عادي (Plain Text) فقط.
- لا تستخدم Markdown أو HTML أو أي تنسيق خاص.
- لا تستخدم ** أو __ أو # أو ## أو ### أو * أو ` أو ``` أو > أو أي رموز تنسيق أخرى.
- يسمح باستخدام القوائم العادية مثل:
  - ...
  • ...
  1.
  2.
  3.
- استخدم الفقرات والقوائم لتنظيم الرد عند الحاجة.
- يسمح باستخدام الإيموجي عندما يضيف معنى حقيقي للرد أو يسهّل فهم المعلومات.
- استخدم الإيموجي باعتدال، وبحد أقصى 3 إيموجي في الرد الواحد، إلا إذا كان الرد عبارة عن قائمة طويلة.
- اختر الإيموجي المناسب للسياق فقط، ولا تستخدمه للزينة أو المبالغة.
- يجب أن تكون جميع الردود جاهزة للعرض مباشرة داخل تيليجرام دون الحاجة إلى أي تعديل أو معالجة.

تعليمات تنسيق الرد:

- أرسل جميع الردود كنص عادي (Plain Text) فقط.
- يمنع استخدام Markdown أو HTML أو أي تنسيق خاص.
- لا تستخدم إطلاقًا: ** أو __ أو # أو ## أو ### أو * أو ` أو ``` أو > أو أي رموز تنسيق أخرى.
- يجب أن تكون جميع الرسائل جاهزة للعرض مباشرة داخل تيليجرام دون الحاجة إلى أي معالجة أو تعديل.
- يسمح باستخدام الإيموجي عندما يضيف معنى حقيقي للرد أو يساعد على توضيح المعلومات.
- استخدم الإيموجي باعتدال، وبحد أقصى 3 إيموجي في الرد الواحد، إلا إذا كان الرد عبارة عن قائمة طويلة تتطلب ذلك.
- اختر الإيموجي المناسب للسياق فقط، مثل:
  📍 للموقع.
  📞 للتواصل.
  🌐 للموقع الإلكتروني.
  📧 للبريد الإلكتروني.
  🕒 لأوقات الدوام.
  📅 للتواريخ.
  📚 للتخصصات.
  🎓 للجامعات.
  🏫 للكليات.
  📄 للمستندات.
  ✅ للمعلومات المؤكدة.
  ⚠️ للتنبيهات.
  ❌ عند عدم توفر معلومة أو خدمة.
  💡 للنصائح.
- لا تستخدم الإيموجي للزينة أو المبالغة، ولا تكرر نفس الإيموجي أكثر من مرة في الرد إلا عند الضرورة.
- اجعل الرد منظمًا وسهل القراءة باستخدام الفقرات أو القوائم البسيطة عند الحاجة، دون أي تنسيق خاص.

تعليمات دقة المعلومات:

- الدقة أهم من سرعة الإجابة.
- لا تخمن، ولا تفترض، ولا تخترع أي معلومة.
- لا تقدم أي تاريخ أو موعد أو رقم أو شرط أو لائحة إلا إذا كنت متأكدًا من صحتها.
- إذا لم تكن متأكدًا بنسبة عالية، فاذكر ذلك بوضوح ولا تؤلف إجابة.
- لا تستخدم معلومات قديمة أو منتهية الصلاحية على أنها معلومات حالية.
- عند السؤال عن مواعيد الدراسة أو التسجيل أو الاختبارات أو النتائج أو الإجازات، لا تذكر أي تاريخ إلا إذا كنت متأكدًا من صحته.
- إذا كان السؤال يعتمد على جامعة أو كلية أو دولة معينة ولم يذكرها المستخدم، فاطلب منه تحديدها أولًا قبل الإجابة.
- لا تقدم إجابة عامة لسؤال يحتاج معلومات خاصة بجامعة معينة.
- لا تذكر سنوات أو تواريخ أو أرقام عشوائية.
- إذا كانت المعلومة غير مؤكدة، فقل: "أحتاج معرفة اسم الجامعة أولاً حتى أقدم لك المعلومة الصحيحة."
- اعتبر أن أي معلومة تقدمها قد يعتمد عليها الطالب، لذلك يجب أن تكون دقيقة وموثوقة.
- لا تعطِ إجابة تبدو صحيحة إذا لم تكن متأكدًا منها.

تعليمات إضافية:

- ستصلك مع كل رسالة معلومات الوقت الحالية.
- اعتبرها المصدر الرسمي الوحيد للوقت والتاريخ.
- إذا سأل المستخدم عن الوقت أو التاريخ أو اليوم فأجب اعتمادًا على المعلومات المرسلة.
- لا تخمن الوقت أو التاريخ.
- لا تحسب التاريخ الهجري بنفسك.
- استخدم التاريخ الهجري المرسل لك فقط.
- لا تقل إنك لا تعرف الوقت أو التاريخ إذا كانت المعلومات موجودة.
- لا تستخدم Markdown.
- لا تستخدم ** أو __ أو # أو ``` أو *.
"""

# ============================================================
# Initialize AI & Knowledge
# ============================================================
provider = get_manager()
knowledge = get_knowledge_manager("knowledge")


# ============================================================
# نظام التحقق من الصلاحيات
# ============================================================
def is_authorized(update: Update) -> bool:
    chat_type = update.effective_chat.type

    if chat_type in ("group", "supergroup"):
        return update.effective_chat.id in ALLOWED_GROUPS
    elif chat_type == "private":
        return update.effective_user.id in ALLOWED_USERS

    return False


def log_unauthorized(update: Update):
    user = update.effective_user
    chat = update.effective_chat

    print("=" * 50)
    print("🚫 محاولة استخدام غير مصرح بها:")
    print(f"   Chat ID    : {chat.id}")
    print(f"   Chat Type  : {chat.type}")
    print(f"   User ID    : {user.id}")
    print(f"   Username   : @{user.username}" if user.username else "   Username   : لا يوجد")
    print(f"   Full Name  : {user.full_name}")
    print("=" * 50)


async def handle_unauthorized(update: Update):
    chat_type = update.effective_chat.type

    if chat_type == "private":
        await update.message.reply_text(
            "هذا الحساب غير مفعل، يرجى التواصل مع المطور لتفعيل حسابك."
        )
    else:
        await update.message.reply_text(
            "هذه المجموعة غير مفعلة، يرجى التواصل مع المطور لتفعيلها."
        )


# ============================================================
# أوامر البوت
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        log_unauthorized(update)
        await handle_unauthorized(update)
        return

    await update.message.reply_text(
        "👋 أهلاً وسهلاً بك في دليلي الجامعي.\n\n"
        "🎓 كيف أقدر أساعدك اليوم؟"
    )


async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        log_unauthorized(update)
        await handle_unauthorized(update)
        return

    user_id = update.effective_user.id
    user_text = update.message.text

    # ============================================================
    # Step 1: Try Knowledge Base first
    # ============================================================
    kb_result = knowledge.search(user_text)

    if kb_result.get("found"):
        print(f"✅ Knowledge Base Found: {kb_result}")

        # Build a clean answer from KB result
        lines = []
        if kb_result.get("title"):
            lines.append(f"📌 {kb_result['title']}")
        if kb_result.get("url"):
            lines.append(f"🔗 {kb_result['url']}")
        if kb_result.get("answer") and not kb_result.get("answer", "").startswith("http"):
            lines.append(kb_result["answer"])

        answer = "\n\n".join(lines)

        memory.add_user_message(user_id, user_text)
        memory.add_assistant_message(user_id, answer)

        await update.message.reply_text(answer)
        return  # Done, don't call Gemini

    # ============================================================
    # Step 2: Fallback to Gemini
    # ============================================================
    print("❌ Knowledge Base not found, calling Gemini...")

    history = memory.get_history(user_id)

    now = datetime.now(ZoneInfo("Asia/Riyadh"))

    try:
        hijri = Hijri.today()
        hijri_day = hijri.day
        hijri_month = hijri.month
        hijri_year = hijri.year
    except Exception:
        hijri_day = 1
        hijri_month = 1
        hijri_year = 1446

    HIJRI_MONTHS = {
        1: "محرم", 2: "صفر", 3: "ربيع الأول",
        4: "ربيع الآخر", 5: "جمادى الأولى", 6: "جمادى الآخرة",
        7: "رجب", 8: "شعبان", 9: "رمضان",
        10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة",
    }

    hijri_month_name = HIJRI_MONTHS.get(hijri_month, "محرم")
    hijri_date = f"{hijri_day} {hijri_month_name} {hijri_year} هـ"

    days = {
        "Monday": "الاثنين", "Tuesday": "الثلاثاء",
        "Wednesday": "الأربعاء", "Thursday": "الخميس",
        "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد",
    }

    current_day = days.get(now.strftime("%A"), now.strftime("%A"))

    current_time_context = f"""
==============================
معلومات الوقت الحالية

التاريخ الميلادي: {now.strftime("%Y-%m-%d")}
التاريخ الهجري: {hijri_date}
اليوم: {current_day}
الوقت: {now.strftime("%H:%M:%S")}
المنطقة الزمنية: Asia/Riyadh

هذه المعلومات صحيحة وحديثة.

إذا سألك المستخدم عن:
- الوقت
- التاريخ الميلادي
- التاريخ الهجري
- اليوم

فاستخدم هذه المعلومات فقط.

لا تخمن أي تاريخ أو وقت أو يوم مختلف.
==============================
"""

    system_prompt = SYSTEM_PROMPT + "\n\n" + current_time_context

    try:
        answer = await provider.get_response(
            system_prompt=system_prompt,
            history=history,
            user_prompt=user_text,
        )

        answer = re.sub(r"[*_`#]+", "", answer).strip()

        memory.add_user_message(user_id, user_text)
        memory.add_assistant_message(user_id, answer)

        await update.message.reply_text(answer)

    except Exception as e:
        print(f"AI Error: {e}")
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
        MessageHandler(filters.TEXT & ~filters.COMMAND, reply_message)
    )

    print("🤖 DaliliSaudiBot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
