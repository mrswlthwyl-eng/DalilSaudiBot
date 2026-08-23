import os
import re
import json
import html
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from provider_manager import get_manager
from conversation_memory import memory


# ============================================================
# إعدادات البوت
# ============================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN غير موجود في Environment Variables")


# ============================================================
# الصلاحيات
# ============================================================

ALLOWED_GROUPS = {
    -1004452669915,
}

ALLOWED_USERS = {
    2076364383,
}


# ============================================================
# قناة دليلي جامعة بيشة
# ============================================================

BISHA_CHANNEL_ID = -1004493313338

CHANNEL_DB_FILE = "bisha_channel_knowledge.json"

MAX_CHANNEL_POSTS = 2000


# ============================================================
# مواضيع جامعة بيشة
# ============================================================

BISHA_TOPICS = {
    "التسجيل",
    "تسجيل",
    "التسجيل الجامعي",
    "القبول",
    "قبول",
    "بلاك بورد",
    "blackboard",
    "البلاك بورد",
    "البريد الجامعي",
    "الايميل الجامعي",
    "الإيميل الجامعي",
    "البريد",
    "الايميل",
    "الإيميل",
    "ايميل",
    "أكاديميت",
    "اكاديميت",
    "اكادميت",
    "الخدمات الأكاديمية",
    "الخدمات الاكاديمية",
    "الرقم الجامعي",
    "المكافأة",
    "المكافآت",
    "المكافاه",
    "المكافئات",
    "الآيبان",
    "ايبان",
    "iban",
    "تغيير التخصص",
    "التخصص",
    "التخصصات",
    "التحويل",
    "تحويل",
    "التحويل الداخلي",
    "التحويل الخارجي",
    "الاعتذار",
    "اعتذار",
    "الاعتذار عن الفصل",
    "تأجيل",
    "تاجيل",
    "تأجيل الفصل",
    "الانسحاب",
    "انسحاب",
    "الانسحاب من الجامعة",
    "الانسحاب من القبول",
    "الجداول",
    "الجدول",
    "الجدول الدراسي",
    "المقررات",
    "مقررات",
    "المقرر",
    "المادة",
    "التدريب",
    "التدريب الميداني",
    "التدريب التطبيقي",
    "الدبلومات",
    "الدبلوم",
    "الدبلومات المدفوعة",
    "التقويم الأكاديمي",
    "التقويم الاكاديمي",
    "التقويم",
    "المحاضرات",
    "المحاضرة",
    "الاختبارات",
    "الاختبار",
    "النتائج",
    "الدرجات",
    "الخدمات الإلكترونية",
    "الخدمات الالكترونية",
    "نفاذ",
    "النفاذ",
    "كلمة المرور",
    "الباسورد",
    "كلمة السر",
    "البوابة",
    "البوابة الإلكترونية",
    "المنظومة الجامعية",
    "جامعة بيشة",
    "جامعه بيشه",
    "بيشة",
    "بيشه",
}


# ============================================================
# كلمات السؤال
# ============================================================

QUESTION_WORDS = {
    "متى",
    "كيف",
    "وين",
    "اين",
    "فين",
    "كم",
    "هل",
    "وش",
    "ايش",
    "ماهو",
    "ماهي",
    "وشو",
    "ليش",
    "لماذا",
    "ابي",
    "ابغى",
    "احتاج",
    "ممكن",
    "طريقة",
    "طريقه",
    "رابط",
    "موعد",
    "شرح",
    "استفسار",
    "استفسر",
    "اعرف",
    "اقدر",
    "تقدر",
    "عندي",
    "عندكم",
    "اريد",
    "أريد",
    "اعطني",
    "عطني",
    "كيفية",
    "كيفيه",
}


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """
أنت دليلي جامعة بيشة.

أنت مساعد طلابي متخصص في جامعة بيشة فقط.

مهمتك مساعدة طلاب وطالبات جامعة بيشة في الاستفسارات المتعلقة بالجامعة.

المواضيع تشمل:

التسجيل
القبول
Blackboard
البريد الجامعي
أكاديميت
الرقم الجامعي
المكافآت
الآيبان
تغيير التخصص
التحويل
الاعتذار
التأجيل
الانسحاب
الجداول
المقررات
التدريب
الدبلومات
التقويم الأكاديمي
الخدمات الإلكترونية
المحاضرات
الاختبارات
النتائج
الدرجات
الحركات الأكاديمية
النفاذ
كلمة المرور
الأنظمة والخدمات الجامعية

مصدر المعلومات الأساسي هو منشورات قناة دليلي جامعة بيشة التي يتم تزويدك بها في السؤال.

لا تستخدم معلومات من جامعة أخرى.

لا تخلط جامعة بيشة مع أي جامعة أخرى.

إذا كانت المعلومة موجودة في منشورات القناة، اعتمد عليها.

إذا كانت هناك عدة منشورات مفيدة، اجمع المعلومات المناسبة منها.

لا تخترع أي رابط أو موعد أو رقم أو شرط.

إذا لم تجد المعلومة بشكل مؤكد في منشورات القناة، قل:

ما لقيت المعلومة بشكل مؤكد في منشورات قناة دليلي جامعة بيشة حاليًا.

إذا كان السؤال عن طريقة، اشرح الخطوات الموجودة في منشور القناة.

إذا كان السؤال عن رابط خدمة أو نظام، استخدم المعلومات الموجودة في منشور القناة.

لا تكتب روابط منشورات القناة بنفسك.

سيتم إضافة رابط المنشور المناسب تلقائيًا أسفل الإجابة.

لا تذكر للطالب أنك تبحث في قاعدة بيانات.

لا تقل إنك نموذج ذكاء اصطناعي إلا إذا سألك مباشرة.

استخدم اللهجة السعودية البسيطة والواضحة عند الحاجة.

إذا كان السؤال بسيطًا، أجب باختصار.

إذا طلب الطالب شرحًا، أعطه خطوات واضحة ومرتبة.

لا تستخدم Markdown.

لا تستخدم:
**
__
###
يمكن استخدام القوائم العادية والأرقام.
استخدم الإيموجي باعتدال.
إذا كانت الرسالة تحية فقط، فرد بتحية قصيرة وطبيعية.
جامعة بيشة هي الجامعة الأساسية التي تتحدث عنها.
إذا ذكر الطالب جامعة أخرى بشكل واضح، لا تستخدم معلومات جامعة بيشة للإجابة عنها.
"""


# ============================================================
# مدير الذكاء الاصطناعي
# ============================================================

provider = get_manager()


# ============================================================
# قاعدة بيانات منشورات القناة
# ============================================================

def load_channel_database():
    if not os.path.exists(CHANNEL_DB_FILE):
        return []

    try:
        with open(
            CHANNEL_DB_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except Exception as e:
        print(f"Channel DB Load Error: {e}")

    return []


def save_channel_database(data):
    try:
        if len(data) > MAX_CHANNEL_POSTS:
            data = data[-MAX_CHANNEL_POSTS:]

        with open(
            CHANNEL_DB_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:
        print(f"Channel DB Save Error: {e}")


channel_database = load_channel_database()


# ============================================================
# إنشاء رابط منشور القناة
# ============================================================

def make_channel_message_link(message_id):
    channel_number = str(abs(BISHA_CHANNEL_ID))

    if channel_number.startswith("100"):
        channel_number = channel_number[3:]

    return f"https://t.me/c/{channel_number}/{message_id}"


# ============================================================
# تنظيف النص
# ============================================================

def normalize_text(text):
    if not text:
        return ""

    text = text.lower()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
        "ـ": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(
        r"[^\w\s\u0600-\u06FF]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# استخراج نص الرسالة
# ============================================================

def get_message_text(message):
    if not message:
        return ""

    text = message.text or message.caption or ""

    return text.strip()


# ============================================================
# استقبال منشورات قناة جامعة بيشة
# ============================================================

async def handle_channel_post(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.channel_post

    if not message:
        return

    if message.chat.id != BISHA_CHANNEL_ID:
        return

    text = get_message_text(message)

    if not text:
        return

    record = {
        "message_id": message.message_id,
        "text": text,
        "normalized": normalize_text(text),
        "date": (
            message.date.isoformat()
            if message.date
            else ""
        ),
        "link": make_channel_message_link(
            message.message_id
        ),
    }

    global channel_database

    channel_database = [
        item
        for item in channel_database
        if item.get("message_id") != message.message_id
    ]

    channel_database.append(record)

    save_channel_database(channel_database)

    print("=" * 60)
    print("تم استقبال منشور جديد من قناة جامعة بيشة")
    print(f"Message ID: {message.message_id}")
    print(f"Text: {text[:200]}")
    print(f"Link: {record['link']}")
    print(f"Total Posts: {len(channel_database)}")
    print("=" * 60)


# ============================================================
# استخراج الكلمات
# ============================================================

def extract_keywords(text):
    normalized = normalize_text(text)

    return {
        word
        for word in normalized.split()
        if len(word) >= 2
    }


# ============================================================
# البحث في منشورات القناة
# ============================================================

def search_channel(query, limit=8):
    if not channel_database:
        return []

    query_normalized = normalize_text(query)
    query_words = extract_keywords(query)

    results = []

    normalized_topics = [
        normalize_text(topic)
        for topic in BISHA_TOPICS
    ]

    for item in channel_database:
        content = item.get(
            "normalized",
            ""
        )

        if not content:
            continue

        content_words = set(
            content.split()
        )

        score = 0

        common_words = (
            query_words.intersection(
                content_words
            )
        )

        score += len(common_words) * 4

        for topic in normalized_topics:
            if (
                topic
                and topic in query_normalized
                and topic in content
            ):
                score += 10

        if (
            query_normalized
            and query_normalized in content
        ):
            score += 30

        if score > 0:
            results.append(
                (
                    score,
                    item
                )
            )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        item
        for score, item in results[:limit]
    ]


# ============================================================
# معرفة هل السؤال متعلق بجامعة بيشة
# ============================================================

def is_bisha_question(text):
    normalized = normalize_text(text)

    for topic in BISHA_TOPICS:
        topic_normalized = normalize_text(topic)

        if (
            topic_normalized
            and topic_normalized in normalized
        ):
            return True

    words = set(
        normalized.split()
    )

    normalized_question_words = {
        normalize_text(word)
        for word in QUESTION_WORDS
    }

    return bool(
        words.intersection(
            normalized_question_words
        )
    )


# ============================================================
# التحيات
# ============================================================

def is_greeting(text):
    normalized = normalize_text(text)

    greetings = [
        "السلام عليكم",
        "السلام عليكم ورحمه الله",
        "السلام عليكم ورحمه الله وبركاته",
        "وعليكم السلام",
        "هلا",
        "مرحبا",
        "اهلا",
        "اهلين",
        "ياهلا",
        "صباح الخير",
        "مساء الخير",
        "مساء النور",
        "صباح النور",
    ]

    return any(
        normalized == normalize_text(greeting)
        for greeting in greetings
    )


# ============================================================
# التحقق من الصلاحية
# ============================================================

def is_authorized(update):
    if not update.effective_chat:
        return False

    chat_type = update.effective_chat.type

    if chat_type in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    ):
        return (
            update.effective_chat.id
            in ALLOWED_GROUPS
        )

    if chat_type == ChatType.PRIVATE:
        if not update.effective_user:
            return False

        return (
            update.effective_user.id
            in ALLOWED_USERS
        )

    return False


# ============================================================
# تسجيل الاستخدام غير المصرح
# ============================================================

def log_unauthorized(update):
    user = update.effective_user
    chat = update.effective_chat

    print("=" * 60)
    print("محاولة استخدام غير مصرح بها")

    if chat:
        print(f"Chat ID: {chat.id}")
        print(f"Chat Type: {chat.type}")

    if user:
        print(f"User ID: {user.id}")

        if user.username:
            print(f"Username: @{user.username}")
        else:
            print("Username: لا يوجد")

        print(f"Full Name: {user.full_name}")

    print("=" * 60)


# ============================================================
# التعامل مع غير المصرح لهم
# ============================================================

async def handle_unauthorized(update):
    if not update.message:
        return

    if (
        update.effective_chat.type
        == ChatType.PRIVATE
    ):
        await update.message.reply_text(
            "هذا الحساب غير مفعل، يرجى التواصل مع المطور لتفعيل حسابك."
        )
    else:
        await update.message.reply_text(
            "هذه المجموعة غير مفعلة، يرجى التواصل مع المطور لتفعيلها."
        )


# ============================================================
# تنظيف إجابة الذكاء الاصطناعي
# ============================================================

def clean_ai_answer(answer):
    if not answer:
        return ""

    answer = re.sub(
        r"```.*?```",
        "",
        answer,
        flags=re.DOTALL
    )

    answer = answer.replace("**", "")
    answer = answer.replace("__", "")
    answer = answer.replace("###", "")
    answer = answer.replace("##", "")
    answer = answer.replace("#", "")

    return answer.strip()


# ============================================================
# إنشاء رابط أزرق "اضغط هنا"
# ============================================================

def create_source_link(link):
    if not link:
        return ""

    safe_link = html.escape(
        link,
        quote=True
    )

    return (
        f'\n\n'
        f'<a href="{safe_link}">اضغط هنا</a>'
    )


# ============================================================
# /start
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not is_authorized(update):
        log_unauthorized(update)
        await handle_unauthorized(update)
        return

    await update.message.reply_text(
        "👋 أهلاً وسهلاً بك في دليلي جامعة بيشة.\n\n"
        "🎓 كيف أقدر أساعدك؟"
    )


# ============================================================
# الرد على أسئلة الطلاب
# ============================================================

async def reply_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    if not is_authorized(update):
        log_unauthorized(update)
        await handle_unauthorized(update)
        return

    user_id = update.effective_user.id

    user_text = (
        update.message.text or ""
    ).strip()

    if not user_text:
        return

    # --------------------------------------------------------
    # التحية
    # --------------------------------------------------------

    if is_greeting(user_text):
        await update.message.reply_text(
            "وعليكم السلام ورحمة الله وبركاته، حياك الله 🌷"
        )
        return

    # --------------------------------------------------------
    # تجاهل الرسائل العادية
    # --------------------------------------------------------

    if not is_bisha_question(user_text):
        return

    # --------------------------------------------------------
    # البحث في القناة
    # --------------------------------------------------------

    matches = search_channel(
        user_text,
        limit=8
    )

    print("=" * 60)
    print(f"سؤال الطالب: {user_text}")
    print(f"نتائج قناة بيشة: {len(matches)}")

    for item in matches:
        print(
            f"- {item.get('message_id')} "
            f"{item.get('text', '')[:120]}"
        )

    print("=" * 60)

    # --------------------------------------------------------
    # الوقت
    # --------------------------------------------------------

    now = datetime.now(
        ZoneInfo("Asia/Riyadh")
    )

    current_time_context = f"""
معلومات الوقت الحالية:
التاريخ الميلادي: {now.strftime("%Y-%m-%d")}
اليوم: {now.strftime("%A")}
الوقت: {now.strftime("%H:%M:%S")}
المنطقة الزمنية: Asia/Riyadh
"""

    # --------------------------------------------------------
    # تجهيز منشورات القناة للذكاء الاصطناعي
    # --------------------------------------------------------

    channel_context = ""

    for index, item in enumerate(
        matches,
        start=1
    ):
        channel_context += f"""
==================================================
منشور قناة دليلي جامعة بيشة رقم {index}
رقم المنشور: {item.get("message_id")}
رابط المنشور: {item.get("link")}
محتوى المنشور: {item.get("text")}
"""

    # --------------------------------------------------------
    # تعليمات السؤال
    # --------------------------------------------------------

    user_instruction = f"""
سؤال الطالب:
{user_text}

منشورات قناة دليلي جامعة بيشة المرتبطة بالسؤال:
{channel_context}

أجب عن سؤال الطالب اعتمادًا على المعلومات الموجودة في المنشورات أعلاه.

إذا وجدت منشورًا مناسبًا، استخدم معلوماته.
إذا وجدت أكثر من منشور مناسب، اجمع المعلومات المفيدة منها.
إذا كان السؤال عن طريقة، اشرح الخطوات الموجودة في المنشور.
إذا كان السؤال عن رابط خدمة أو نظام، اعتمد على الرابط الموجود في المنشور.

لا تخترع معلومات.
لا تخترع روابط.
لا تخترع مواعيد.
لا تخترع شروطًا.
لا تستخدم معلومات من جامعة أخرى.
لا تكتب رابط منشور القناة داخل الإجابة.
سيتم إضافة رابط المنشور المناسب تلقائيًا بعد الإجابة.

إذا لم تجد إجابة مؤكدة، قل:
ما لقيت المعلومة بشكل مؤكد في منشورات قناة دليلي جامعة بيشة حاليًا.
"""

    # --------------------------------------------------------
    # الذكاء الاصطناعي
    # --------------------------------------------------------

    try:
        history = memory.get_history(
            user_id
        )

        answer = await provider.get_response(
            system_prompt=(
                SYSTEM_PROMPT
                + "\n\n"
                + current_time_context
            ),
            history=history,
            user_prompt=user_instruction
        )

        answer = clean_ai_answer(
            answer
        )

        if not answer:
            answer = (
                "ما لقيت المعلومة بشكل مؤكد "
                "في منشورات قناة دليلي جامعة بيشة حاليًا."
            )

        # ----------------------------------------------------
        # اختيار أفضل منشور
        # ----------------------------------------------------

        source_link = ""

        if matches:
            source_link = matches[0].get(
                "link",
                ""
            )

        # ----------------------------------------------------
        # حفظ المحادثة
        # ----------------------------------------------------

        memory.add_user_message(
            user_id,
            user_text
        )

        memory.add_assistant_message(
            user_id,
            answer
        )

        # ----------------------------------------------------
        # حماية HTML
        # ----------------------------------------------------

        safe_answer = html.escape(
            answer,
            quote=False
        )

        # ----------------------------------------------------
        # إضافة زر اضغط هنا
        # ----------------------------------------------------

        if source_link:
            safe_answer += create_source_link(
                source_link
            )

        # ----------------------------------------------------
        # إرسال الرد
        # ----------------------------------------------------

        await update.message.reply_text(
            safe_answer,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as e:
        print(
            f"AI Error: {e}"
        )

        await update.message.reply_text(
            "حدثت مشكلة مؤقتة في خدمة دليلي، حاول مرة أخرى."
        )


# ============================================================
# إغلاق البوت
# ============================================================

async def on_shutdown(
    app: Application
):
    try:
        await provider.shutdown()
    except Exception as e:
        print(
            f"Shutdown Error: {e}"
        )


# ============================================================
# تشغيل البوت
# ============================================================

def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .post_shutdown(on_shutdown)
        .build()
    )

    # استقبال أمر /start
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # استقبال منشورات قناة بيشة
    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST,
            handle_channel_post
        )
    )

    # استقبال رسائل الطلاب
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            reply_message
        )
    )

    print(
        "DaliliSaudiBot is running..."
    )

    print(
        f"Bisha Channel ID: {BISHA_CHANNEL_ID}"
    )

    print(
        f"Allowed Groups: {ALLOWED_GROUPS}"
    )

    print(
        f"Saved Channel Posts: {len(channel_database)}"
    )

    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    main()
