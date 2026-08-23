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
    raise RuntimeError(
        "BOT_TOKEN غير موجود في Environment Variables"
    )


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

BISHA_CHANNEL_USERNAME = "Bishauniversity3"

BISHA_CHANNEL_URL = "https://t.me/Bishauniversity3"


# ============================================================
# قاعدة معرفة منشورات القناة
# ============================================================

CHANNEL_DB_FILE = "bisha_channel_knowledge.json"

MAX_CHANNEL_POSTS = 10000


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
    "الاختبارات النهائية",
    "النتائج",
    "الدرجات",
    "الدرجة",
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
# كلمات الاستفسار
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
    "وش",
    "وشلون",
    "شلون",
}


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """
أنت "دليلي جامعة بيشة".

أنت مساعد طلابي متخصص في جامعة بيشة فقط.

مهمتك مساعدة طلاب وطالبات جامعة بيشة في الاستفسارات المتعلقة بالجامعة.

تشمل المواضيع:

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
النفاذ
كلمة المرور
الأنظمة والخدمات الجامعية

مصدر المعلومات الأساسي:
منشورات قناة دليلي جامعة بيشة.

قواعد مهمة:

1. اعتمد على منشورات القناة عند توفرها.

2. لا تستخدم معلومات من جامعة أخرى.

3. لا تخلط جامعة بيشة مع جامعة أخرى.

4. لا تخترع أي معلومة.

5. لا تخترع أي موعد.

6. لا تخترع أي شرط.

7. لا تخترع أي رابط.

8. إذا كانت هناك عدة منشورات مرتبطة بالسؤال، اجمع المعلومات المفيدة منها.

9. إذا كان السؤال عن إجراء، اشرح الخطوات الموجودة في المنشورات.

10. إذا كان السؤال عن رابط خدمة أو نظام، استخدم الرابط الموجود في المنشور.

11. إذا لم تكن المعلومة موجودة بشكل مؤكد، قل:

ما لقيت المعلومة بشكل مؤكد في منشورات قناة دليلي جامعة بيشة حاليًا.

12. لا تقل للطالب إنك تبحث في قاعدة بيانات.

13. لا تقل إنك نموذج ذكاء اصطناعي إلا إذا سألك مباشرة.

14. استخدم اللهجة السعودية البسيطة والواضحة عند الحاجة.

15. إذا كان السؤال بسيطًا، أجب باختصار.

16. إذا طلب الطالب شرحًا، قدم خطوات واضحة ومرتبة.

17. لا تكتب رابط منشور القناة بنفسك.
سيتم إضافة رابط المنشور المناسب تلقائيًا.

18. لا تكتب عبارة "المصدر".

19. لا تستخدم Markdown.

20. لا تستخدم:
**
__
###
أو تنسيقات Markdown الأخرى.

21. يمكن استخدام القوائم العادية والأرقام.

22. استخدم الإيموجي باعتدال.

23. إذا كانت الرسالة مجرد تحية، فرد بتحية قصيرة وطبيعية.

24. أي سؤال جامعي بدون تحديد جامعة أخرى يعتبر متعلقًا بجامعة بيشة.

25. إذا ذكر الطالب جامعة أخرى بوضوح، لا تستخدم معلومات جامعة بيشة للإجابة عن تلك الجامعة.
"""


# ============================================================
# مدير الذكاء الاصطناعي
# ============================================================

provider = get_manager()


# ============================================================
# تحميل قاعدة المعرفة
# ============================================================

def load_channel_database():

    if not os.path.exists(
        CHANNEL_DB_FILE
    ):
        return []

    try:

        with open(
            CHANNEL_DB_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(
            data,
            list
        ):
            return data

    except Exception as e:

        print(
            f"Channel DB Load Error: {e}"
        )

    return []


# ============================================================
# حفظ قاعدة المعرفة
# ============================================================

def save_channel_database(data):

    try:

        if len(data) > MAX_CHANNEL_POSTS:

            data = data[
                -MAX_CHANNEL_POSTS:
            ]

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

        print(
            f"Channel DB Save Error: {e}"
        )


# ============================================================
# قاعدة المعرفة الحالية
# ============================================================

channel_database = (
    load_channel_database()
)


# ============================================================
# إنشاء رابط منشور القناة
# ============================================================

def make_channel_message_link(
    message_id
):

    return (
        f"{BISHA_CHANNEL_URL}/"
        f"{message_id}"
    )


# ============================================================
# تنظيف وتوحيد النص العربي
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    text = str(
        text
    ).lower()

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

        text = text.replace(
            old,
            new
        )

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

def get_message_text(
    message
):

    if not message:
        return ""

    text = (
        message.text
        or message.caption
        or ""
    )

    return text.strip()


# ============================================================
# استقبال منشورات القناة الجديدة
# ============================================================

async def handle_channel_post(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.channel_post

    if not message:
        return

    if (
        message.chat.id
        != BISHA_CHANNEL_ID
    ):
        return

    text = get_message_text(
        message
    )

    if not text:
        return

    record = {
        "message_id": message.message_id,

        "text": text,

        "normalized": normalize_text(
            text
        ),

        "date": (
            message.date.isoformat()
            if message.date
            else ""
        ),

        "link": make_channel_message_link(
            message.message_id
        ),

        "channel_id": BISHA_CHANNEL_ID,

        "channel_username":
            BISHA_CHANNEL_USERNAME,
    }

    global channel_database

    channel_database = [
        item
        for item in channel_database
        if item.get(
            "message_id"
        )
        != message.message_id
    ]

    channel_database.append(
        record
    )

    channel_database.sort(
        key=lambda item:
        item.get(
            "message_id",
            0
        )
    )

    save_channel_database(
        channel_database
    )

    print("=" * 60)
    print(
        "تم استقبال منشور جديد من قناة جامعة بيشة"
    )
    print(
        f"Message ID: {message.message_id}"
    )
    print(
        f"Text: {text[:200]}"
    )
    print(
        f"Link: {record['link']}"
    )
    print(
        f"Total Posts: "
        f"{len(channel_database)}"
    )
    print("=" * 60)


# ============================================================
# استخراج كلمات السؤال
# ============================================================

def extract_keywords(
    text
):

    normalized = normalize_text(
        text
    )

    return {
        word
        for word in normalized.split()
        if len(word) >= 2
    }


# ============================================================
# البحث الذكي في منشورات القناة
# ============================================================

def search_channel(
    query,
    limit=8
):

    if not channel_database:
        return []

    query_normalized = (
        normalize_text(query)
    )

    query_words = (
        extract_keywords(query)
    )

    results = []

    normalized_topics = [
        normalize_text(topic)
        for topic in BISHA_TOPICS
    ]

    # الكلمات التي لا تساعد كثيرًا في المطابقة
    stop_words = {
        "ابي",
        "ابغى",
        "احتاج",
        "ممكن",
        "عندي",
        "عندكم",
        "هل",
        "كيف",
        "متى",
        "وين",
        "اين",
        "فين",
        "وش",
        "ايش",
        "ماهو",
        "ماهي",
        "وشو",
        "كم",
        "اعرف",
        "تقدر",
        "اقدر",
        "اريد",
        "اعطني",
        "عطني",
    }

    useful_query_words = (
        query_words
        - {
            normalize_text(word)
            for word in stop_words
        }
    )

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

        # ----------------------------------------------------
        # تطابق الكلمات المهمة
        # ----------------------------------------------------

        common_words = (
            useful_query_words
            .intersection(
                content_words
            )
        )

        score += (
            len(common_words) * 5
        )

        # ----------------------------------------------------
        # تطابق المواضيع
        # ----------------------------------------------------

        for topic in normalized_topics:

            if not topic:
                continue

            if (
                topic in query_normalized
                and topic in content
            ):

                score += 12

        # ----------------------------------------------------
        # تطابق السؤال كاملًا
        # ----------------------------------------------------

        if (
            query_normalized
            and query_normalized in content
        ):

            score += 40

        # ----------------------------------------------------
        # تطابق العبارات
        # ----------------------------------------------------

        query_words_list = (
            list(useful_query_words)
        )

        for i in range(
            len(query_words_list)
        ):

            word = (
                query_words_list[i]
            )

            if len(word) >= 3:

                if word in content:

                    score += 2

        # ----------------------------------------------------
        # تطابق قوي لبعض المصطلحات
        # ----------------------------------------------------

        strong_phrases = [
            "بلاك بورد",
            "البريد الجامعي",
            "الرقم الجامعي",
            "تغيير التخصص",
            "التحويل الداخلي",
            "التحويل الخارجي",
            "الانسحاب من الجامعة",
            "الانسحاب من القبول",
            "الاعتذار عن الفصل",
            "تأجيل الفصل",
            "الجدول الدراسي",
            "التدريب التطبيقي",
            "التدريب الميداني",
            "التقويم الاكاديمي",
            "الخدمات الالكترونية",
            "كلمه المرور",
            "كلمه السر",
            "الايبان",
            "المكافاه",
        ]

        for phrase in strong_phrases:

            normalized_phrase = (
                normalize_text(
                    phrase
                )
            )

            if (
                normalized_phrase
                in query_normalized
            ):

                if (
                    normalized_phrase
                    in content
                ):

                    score += 20

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
        for score, item
        in results[:limit]
    ]


# ============================================================
# معرفة هل الرسالة سؤال جامعي
# ============================================================

def is_bisha_question(
    text
):

    normalized = normalize_text(
        text
    )

    # إذا ذكر موضوعًا جامعيًا
    for topic in BISHA_TOPICS:

        topic_normalized = (
            normalize_text(topic)
        )

        if (
            topic_normalized
            and topic_normalized
            in normalized
        ):

            return True

    # إذا كان سؤالًا واضحًا
    words = set(
        normalized.split()
    )

    normalized_question_words = {
        normalize_text(word)
        for word in QUESTION_WORDS
    }

    if words.intersection(
        normalized_question_words
    ):

        return True

    # إذا كانت الرسالة تحتوي على كلمات تدل على
    # طلب جامعي شائع حتى بدون كلمة سؤال
    request_phrases = [
        "ابي رابط",
        "ابغى رابط",
        "احتاج رابط",
        "عطني رابط",
        "وين الرابط",
        "متى التسجيل",
        "موعد التسجيل",
        "موعد القبول",
        "رقمي الجامعي",
        "رقم جامعي",
        "جدولي",
        "جدول دراسي",
        "مكافاتي",
        "مكافاتي",
        "تخصصي",
        "تحويل تخصص",
    ]

    for phrase in request_phrases:

        if (
            normalize_text(phrase)
            in normalized
        ):

            return True

    return False


# ============================================================
# التحيات
# ============================================================

def is_greeting(
    text
):

    normalized = normalize_text(
        text
    )

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
        normalized
        == normalize_text(
            greeting
        )
        for greeting in greetings
    )


# ============================================================
# التحقق من الصلاحية
# ============================================================

def is_authorized(
    update
):

    if not update.effective_chat:
        return False

    chat_type = (
        update.effective_chat.type
    )

    if chat_type in (
        ChatType.GROUP,
        ChatType.SUPERGROUP,
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

def log_unauthorized(
    update
):

    user = (
        update.effective_user
    )

    chat = (
        update.effective_chat
    )

    print("=" * 60)
    print(
        "محاولة استخدام غير مصرح بها"
    )

    if chat:

        print(
            f"Chat ID: {chat.id}"
        )

        print(
            f"Chat Type: {chat.type}"
        )

    if user:

        print(
            f"User ID: {user.id}"
        )

        if user.username:

            print(
                f"Username: @{user.username}"
            )

        else:

            print(
                "Username: لا يوجد"
            )

        print(
            f"Full Name: {user.full_name}"
        )

    print("=" * 60)


# ============================================================
# التعامل مع غير المصرح لهم
# ============================================================

async def handle_unauthorized(
    update
):

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

def clean_ai_answer(
    answer
):

    if not answer:
        return ""

    answer = re.sub(
        r"```.*?```",
        "",
        answer,
        flags=re.DOTALL
    )

    answer = answer.replace(
        "**",
        ""
    )

    answer = answer.replace(
        "__",
        ""
    )

    answer = answer.replace(
        "###",
        ""
    )

    answer = answer.replace(
        "##",
        ""
    )

    answer = answer.replace(
        "#",
        ""
    )

    return answer.strip()


# ============================================================
# إنشاء رابط أزرق "اضغط هنا"
# ============================================================

def create_source_link(
    link
):

    if not link:
        return ""

    safe_link = html.escape(
        link,
        quote=True
    )

    return (
        "\n\n"
        f'<a href="{safe_link}">اضغط هنا</a>'
    )


# ============================================================
# اختيار المصادر المناسبة
# ============================================================

def select_source_links(
    matches,
    max_sources=3
):

    links = []

    for item in matches:

        link = item.get(
            "link",
            ""
        )

        if (
            link
            and link not in links
        ):

            links.append(
                link
            )

        if len(links) >= max_sources:
            break

    return links


# ============================================================
# /start
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_authorized(
        update
    ):

        log_unauthorized(
            update
        )

        await handle_unauthorized(
            update
        )

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

    if not is_authorized(
        update
    ):

        log_unauthorized(
            update
        )

        await handle_unauthorized(
            update
        )

        return

    if not update.effective_user:
        return

    user_id = (
        update.effective_user.id
    )

    user_text = (
        update.message.text
        or ""
    ).strip()

    if not user_text:
        return

    # --------------------------------------------------------
    # التحية
    # --------------------------------------------------------

    if is_greeting(
        user_text
    ):

        await update.message.reply_text(
            "وعليكم السلام ورحمة الله وبركاته، حياك الله 🌷"
        )

        return

    # --------------------------------------------------------
    # تجاهل الرسائل العادية
    # --------------------------------------------------------

    if not is_bisha_question(
        user_text
    ):

        return

    # --------------------------------------------------------
    # البحث في منشورات القناة
    # --------------------------------------------------------

    matches = search_channel(
        user_text,
        limit=8
    )

    print("=" * 60)

    print(
        f"سؤال الطالب: {user_text}"
    )

    print(
        f"نتائج القناة: {len(matches)}"
    )

    for item in matches:

        print(
            f"- {item.get('message_id')} "
            f"{item.get('text', '')[:150]}"
        )

    print("=" * 60)

    # --------------------------------------------------------
    # الوقت الحالي
    # --------------------------------------------------------

    now = datetime.now(
        ZoneInfo(
            "Asia/Riyadh"
        )
    )

    current_time_context = f"""
معلومات الوقت الحالية:
التاريخ الميلادي: {now.strftime("%Y-%m-%d")}
اليوم: {now.strftime("%A")}
الوقت: {now.strftime("%H:%M:%S")}
المنطقة الزمنية: Asia/Riyadh
"""

    # --------------------------------------------------------
    # تجهيز سياق المنشورات
    # --------------------------------------------------------

    channel_context = ""

    for index, item in enumerate(
        matches,
        start=1
    ):

        channel_context += f"""
==================================================
منشور قناة دليلي جامعة بيشة رقم {index}

رقم المنشور:
{item.get("message_id")}

تاريخ المنشور:
{item.get("date", "")}

رابط المنشور:
{item.get("link", "")}

محتوى المنشور:
{item.get("text", "")}
"""

    # --------------------------------------------------------
    # إذا لا توجد نتائج
    # --------------------------------------------------------

    if not matches:

        channel_context = (
            "لم يتم العثور على منشور مطابق "
            "في قاعدة منشورات قناة جامعة بيشة."
        )

    # --------------------------------------------------------
    # تعليمات الذكاء الاصطناعي
    # --------------------------------------------------------

    user_instruction = f"""
سؤال الطالب:
{user_text}

المعلومات المتاحة من منشورات قناة دليلي جامعة بيشة:

{channel_context}

المطلوب:

أجب عن سؤال الطالب اعتمادًا على المعلومات الموجودة في منشورات القناة.

إذا وجدت منشورًا مناسبًا:
اعتمد عليه.

إذا وجدت أكثر من منشور مناسب:
اجمع المعلومات المفيدة منها.

إذا كانت هناك معلومات أحدث وأقدم:
انتبه إلى تاريخ المنشورات، ولا تستخدم معلومة قديمة إذا كان هناك منشور أحدث يناقضها.

إذا كان السؤال عن طريقة:
اشرح الخطوات الموجودة في المنشور.

إذا كان السؤال عن رابط:
اعتمد على الرابط الموجود في المنشور.

إذا كان السؤال عن موعد:
استخدم التاريخ أو الموعد الموجود في المنشور فقط.

لا تخترع معلومات.

لا تخترع روابط.

لا تخترع مواعيد.

لا تخترع شروطًا.

لا تستخدم معلومات من جامعة أخرى.

لا تكتب رابط منشور القناة داخل إجابتك.

سيتم إضافة رابط المنشور المناسب تلقائيًا.

إذا لم تجد إجابة مؤكدة في المنشورات المتاحة، قل:

ما لقيت المعلومة بشكل مؤكد في منشورات قناة دليلي جامعة بيشة حاليًا.

أجب بشكل واضح ومختصر، وباللهجة السعودية البسيطة عند الحاجة.
"""

    # --------------------------------------------------------
    # استدعاء الذكاء الاصطناعي
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
        # إضافة مصادر المنشورات
        # ----------------------------------------------------

        source_links = (
            select_source_links(
                matches,
                max_sources=3
            )
        )

        if source_links:

            for link in source_links:

                safe_answer += (
                    create_source_link(
                        link
                    )
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
        .post_shutdown(
            on_shutdown
        )
        .build()
    )

    # --------------------------------------------------------
    # /start
    # --------------------------------------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # --------------------------------------------------------
    # استقبال المنشورات الجديدة من القناة
    # --------------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST,
            handle_channel_post
        )
    )

    # --------------------------------------------------------
    # استقبال رسائل الطلاب
    # --------------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            reply_message
        )
    )

    # --------------------------------------------------------
    # معلومات التشغيل
    # --------------------------------------------------------

    print("=" * 60)

    print(
        "DaliliSaudiBot is running..."
    )

    print(
        f"Bisha Channel ID: "
        f"{BISHA_CHANNEL_ID}"
    )

    print(
        f"Bisha Channel: "
        f"@{BISHA_CHANNEL_USERNAME}"
    )

    print(
        f"Allowed Groups: "
        f"{ALLOWED_GROUPS}"
    )

    print(
        f"Allowed Users: "
        f"{ALLOWED_USERS}"
    )

    print(
        f"Saved Channel Posts: "
        f"{len(channel_database)}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # تشغيل البوت
    # --------------------------------------------------------

    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    main()
