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

from telethon import TelegramClient
from telethon.sessions import StringSession

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
# إعدادات Telegram User API
# ============================================================

TELEGRAM_API_ID = os.getenv(
    "TELEGRAM_API_ID"
)

TELEGRAM_API_HASH = os.getenv(
    "TELEGRAM_API_HASH"
)

TELEGRAM_SESSION = os.getenv(
    "TELEGRAM_SESSION"
)


if not TELEGRAM_API_ID:
    raise RuntimeError(
        "TELEGRAM_API_ID غير موجود في Environment Variables"
    )


if not TELEGRAM_API_HASH:
    raise RuntimeError(
        "TELEGRAM_API_HASH غير موجود في Environment Variables"
    )


if not TELEGRAM_SESSION:
    raise RuntimeError(
        "TELEGRAM_SESSION غير موجود في Environment Variables"
    )


try:

    TELEGRAM_API_ID = int(
        TELEGRAM_API_ID
    )

except ValueError:

    raise RuntimeError(
        "TELEGRAM_API_ID يجب أن يكون رقمًا صحيحًا"
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

# مهم:
# هذا هو Channel ID الخاص بـ Telegram Bot API
BISHA_CHANNEL_ID = -1004493313338


BISHA_CHANNEL_USERNAME = (
    "Bishauniversity3"
)


BISHA_CHANNEL_URL = (
    "https://t.me/Bishauniversity3"
)


# ============================================================
# تحويل Channel ID من Bot API إلى Telethon
# ============================================================

def telegram_channel_id_to_telethon_id(
    channel_id
):
    """
    Telegram Bot API:
        -1004493313338

    Telethon:
        4493313338

    لذلك نحذف -100 من بداية الرقم.
    """

    try:

        channel_id = int(
            channel_id
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "Channel ID غير صالح"
        )


    absolute_id = abs(
        channel_id
    )


    absolute_string = str(
        absolute_id
    )


    if absolute_string.startswith(
        "100"
    ):

        return int(
            absolute_string[3:]
        )


    return absolute_id


# ============================================================
# الرقم الذي سيستخدمه Telethon
# ============================================================

BISHA_TELETHON_CHANNEL_ID = (
    telegram_channel_id_to_telethon_id(
        BISHA_CHANNEL_ID
    )
)


# ============================================================
# قاعدة معرفة منشورات القناة
# ============================================================

CHANNEL_DB_FILE = (
    "bisha_channel_knowledge.json"
)


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

    "وشلون",
    "شلون",
}


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """
أنت "دليلي جامعة بيشة".

أنت مساعد طلابي متخصص في جامعة بيشة فقط.

مصدر المعلومات الأساسي هو منشورات قناة دليلي جامعة بيشة.

لا تستخدم معلومات من جامعة أخرى.

لا تخترع أي معلومة.

لا تخترع أي موعد.

لا تخترع أي شرط.

لا تخترع أي رابط.

إذا كانت المعلومة غير موجودة بشكل مؤكد في منشورات القناة، قل:

ما لقيت المعلومة بشكل مؤكد في منشورات قناة دليلي جامعة بيشة حاليًا.

استخدم اللهجة السعودية البسيطة والواضحة عند الحاجة.

إذا كان السؤال بسيطًا أجب باختصار.

لا تقل للطالب إنك تبحث في قاعدة بيانات.

لا تقل إنك نموذج ذكاء اصطناعي إلا إذا سألك مباشرة.

لا تستخدم Markdown.

لا تكتب رابط منشور القناة بنفسك.

سيتم إضافة الرابط تلقائيًا.
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

            data = json.load(
                file
            )


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

def save_channel_database(
    data
):

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

    if not message_id:
        return ""

    return (
        f"{BISHA_CHANNEL_URL}/"
        f"{message_id}"
    )


# ============================================================
# تنظيف وتوحيد النص العربي
# ============================================================

def normalize_text(
    text
):

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
# استخراج نص رسالة Telegram
# ============================================================

def get_message_text(
    message
):

    if not message:

        return ""


    text = (

        getattr(
            message,
            "text",
            None
        )

        or getattr(
            message,
            "caption",
            None
        )

        or getattr(
            message,
            "message",
            None
        )

        or ""
    )


    return str(
        text
    ).strip()


# ============================================================
# إنشاء سجل المنشور
# ============================================================

def create_channel_record(
    message
):

    text = get_message_text(
        message
    )


    message_id = getattr(
        message,
        "id",
        None
    )


    message_date = getattr(
        message,
        "date",
        None
    )


    return {

        "message_id":
            message_id,

        "text":
            text,

        "normalized":
            normalize_text(
                text
            ),

        "date": (
            message_date.isoformat()
            if message_date
            else ""
        ),

        "link":
            make_channel_message_link(
                message_id
            ),

        "channel_id":
            BISHA_CHANNEL_ID,

        "channel_username":
            BISHA_CHANNEL_USERNAME,

        "media_type": (

            message.media.__class__.__name__

            if getattr(
                message,
                "media",
                None
            )

            else "text"
        ),

        "views":
            getattr(
                message,
                "views",
                None
            ),

        "forwards":
            getattr(
                message,
                "forwards",
                None
            ),

        "grouped_id":
            getattr(
                message,
                "grouped_id",
                None
            ),
    }


# ============================================================
# استيراد المنشورات القديمة تلقائيًا
# ============================================================

async def import_old_channel_posts():

    global channel_database


    print("")
    print("=" * 70)

    print(
        "بدء قراءة المنشورات السابقة من قناة جامعة بيشة..."
    )

    print("=" * 70)


    print(
        f"القناة: @{BISHA_CHANNEL_USERNAME}"
    )


    print(
        f"Channel ID Bot API: "
        f"{BISHA_CHANNEL_ID}"
    )


    print(
        f"Channel ID Telethon: "
        f"{BISHA_TELETHON_CHANNEL_ID}"
    )


    print(
        "جاري استخدام TELEGRAM_SESSION..."
    )


    client = None


    try:

        # ----------------------------------------------------
        # إنشاء عميل Telethon
        # ----------------------------------------------------

        client = TelegramClient(

            StringSession(
                TELEGRAM_SESSION
            ),

            TELEGRAM_API_ID,

            TELEGRAM_API_HASH
        )


        # ----------------------------------------------------
        # الاتصال
        # ----------------------------------------------------

        await client.connect()


        if not await client.is_user_authorized():

            print(
                "خطأ: TELEGRAM_SESSION غير مصرح به."
            )

            return


        print(
            "تم الاتصال بحساب Telegram بنجاح."
        )


        # ----------------------------------------------------
        # الوصول إلى القناة
        # ----------------------------------------------------

        print(
            f"جاري الوصول إلى القناة: "
            f"@{BISHA_CHANNEL_USERNAME}"
        )


        channel = await client.get_entity(
            BISHA_CHANNEL_USERNAME
        )


        # ----------------------------------------------------
        # استخراج ID الحقيقي من Telethon
        # ----------------------------------------------------

        real_channel_id = getattr(
            channel,
            "id",
            None
        )


        print(
            "=================================================="
        )


        print(
            f"Channel ID المطلوب Bot API:"
        )


        print(
            BISHA_CHANNEL_ID
        )


        print(
            f"Channel ID المطلوب لـ Telethon:"
        )


        print(
            BISHA_TELETHON_CHANNEL_ID
        )


        print(
            f"Channel ID الحقيقي من Telethon:"
        )


        print(
            real_channel_id
        )


        print(
            "=================================================="
        )


        # ----------------------------------------------------
        # التحقق الصحيح من القناة
        # ----------------------------------------------------

        if (
            real_channel_id
            != BISHA_TELETHON_CHANNEL_ID
        ):

            print(
                "❌ خطأ: القناة التي تم الوصول إليها "
                "ليست القناة المطلوبة."
            )


            print(
                f"المطلوب: "
                f"{BISHA_TELETHON_CHANNEL_ID}"
            )


            print(
                f"الموجود: "
                f"{real_channel_id}"
            )


            return


        print(
            "✅ تم التحقق من قناة جامعة بيشة بنجاح."
        )


        # ----------------------------------------------------
        # تحويل قاعدة المعرفة إلى Dictionary
        # ----------------------------------------------------

        posts = {

            item.get(
                "message_id"
            ):
                item

            for item in channel_database

            if item.get(
                "message_id"
            )
        }


        print(
            f"المنشورات الموجودة قبل الاستيراد: "
            f"{len(posts)}"
        )


        total = 0

        text_count = 0

        media_count = 0

        new_count = 0

        updated_count = 0


        # ----------------------------------------------------
        # قراءة كامل تاريخ القناة
        # ----------------------------------------------------

        async for message in client.iter_messages(

            channel,

            limit=None

        ):

            total += 1


            text = get_message_text(
                message
            )


            has_media = bool(
                getattr(
                    message,
                    "media",
                    None
                )
            )


            # ------------------------------------------------
            # منشور بدون نص
            # ------------------------------------------------

            if not text:

                if has_media:

                    media_count += 1

                continue


            text_count += 1


            # ------------------------------------------------
            # إنشاء سجل
            # ------------------------------------------------

            record = create_channel_record(
                message
            )


            message_id = record[
                "message_id"
            ]


            if message_id in posts:

                updated_count += 1

            else:

                new_count += 1


            posts[
                message_id
            ] = record


            # ------------------------------------------------
            # طباعة التقدم
            # ------------------------------------------------

            if total % 50 == 0:

                print(

                    f"تمت قراءة {total} "

                    f"| نصي: {text_count} "

                    f"| جديد: {new_count} "

                    f"| محدث: {updated_count}"

                )


        # ----------------------------------------------------
        # حفظ قاعدة المعرفة
        # ----------------------------------------------------

        channel_database = list(
            posts.values()
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


        print("")
        print("=" * 70)


        print(
            "✅ اكتمل استيراد المنشورات السابقة."
        )


        print(
            f"إجمالي الرسائل المقروءة: "
            f"{total}"
        )


        print(
            f"المنشورات النصية: "
            f"{text_count}"
        )


        print(
            f"المنشورات الجديدة: "
            f"{new_count}"
        )


        print(
            f"المنشورات المحدثة: "
            f"{updated_count}"
        )


        print(
            f"منشورات الوسائط بدون نص: "
            f"{media_count}"
        )


        print(
            f"إجمالي قاعدة المعرفة: "
            f"{len(channel_database)}"
        )


        print("=" * 70)


    except Exception as e:

        print("")
        print(
            "❌ حدث خطأ أثناء استيراد القناة:"
        )


        print(
            repr(e)
        )


        print(
            "سيستمر البوت باستخدام قاعدة المعرفة الموجودة."
        )


    finally:

        if client:

            try:

                await client.disconnect()

            except Exception:

                pass


        print(
            "تم إغلاق اتصال Telegram User API."
        )


# ============================================================
# استقبال منشورات القناة الجديدة
# ============================================================

async def handle_channel_post(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    global channel_database


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

        "message_id":
            message.message_id,

        "text":
            text,

        "normalized":
            normalize_text(
                text
            ),

        "date": (

            message.date.isoformat()

            if message.date

            else ""
        ),

        "link":
            make_channel_message_link(
                message.message_id
            ),

        "channel_id":
            BISHA_CHANNEL_ID,

        "channel_username":
            BISHA_CHANNEL_USERNAME,
    }


    # --------------------------------------------------------
    # حذف النسخة القديمة
    # --------------------------------------------------------

    channel_database = [

        item

        for item in channel_database

        if item.get(
            "message_id"
        )
        != message.message_id
    ]


    # --------------------------------------------------------
    # إضافة النسخة الجديدة
    # --------------------------------------------------------

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


    print("")
    print("=" * 60)


    print(
        "تم استقبال منشور جديد من قناة جامعة بيشة"
    )


    print(
        f"Message ID: "
        f"{message.message_id}"
    )


    print(
        f"Text: "
        f"{text[:200]}"
    )


    print(
        f"Link: "
        f"{record['link']}"
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
# كلمات يتم تجاهلها في البحث
# ============================================================

STOP_WORDS = {

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

    "طريقة",
    "طريقه",
}


# ============================================================
# العبارات القوية
# ============================================================

STRONG_PHRASES = [

    "البريد الجامعي",
    "الايميل الجامعي",
    "الاميل الجامعي",

    "تفعيل البريد",
    "تفعيل الايميل",

    "بلاك بورد",
    "البلاك بورد",

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

    "كلمة المرور",

    "كلمة السر",

    "الايبان",

    "المكافاة",

    "التسجيل الجامعي",

    "القبول الجامعي",
]


# ============================================================
# البحث عن أفضل منشور
# ============================================================

def find_best_channel_post(
    query
):

    if not channel_database:

        return None, 0


    query_normalized = normalize_text(
        query
    )


    query_words = extract_keywords(
        query
    )


    useful_words = (

        query_words

        - {
            normalize_text(word)

            for word in STOP_WORDS
        }
    )


    best_item = None

    best_score = 0


    for item in channel_database:

        content = item.get(
            "normalized",
            ""
        )


        original_text = item.get(
            "text",
            ""
        )


        if not content or not original_text:

            continue


        content_words = set(
            content.split()
        )


        score = 0


        # ----------------------------------------------------
        # تطابق الكلمات
        # ----------------------------------------------------

        common_words = (

            useful_words

            .intersection(
                content_words
            )
        )


        score += (
            len(common_words) * 8
        )


        # ----------------------------------------------------
        # العبارات القوية
        # ----------------------------------------------------

        for phrase in STRONG_PHRASES:

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

                    score += 35


        # ----------------------------------------------------
        # تطابق الموضوع
        # ----------------------------------------------------

        for topic in BISHA_TOPICS:

            normalized_topic = (
                normalize_text(
                    topic
                )
            )


            if not normalized_topic:

                continue


            if (
                normalized_topic
                in query_normalized
            ):

                if (
                    normalized_topic
                    in content
                ):

                    score += 15


        # ----------------------------------------------------
        # تطابق كامل
        # ----------------------------------------------------

        if (
            query_normalized

            and query_normalized
            in content
        ):

            score += 60


        # ----------------------------------------------------
        # نسبة الكلمات المتطابقة
        # ----------------------------------------------------

        if useful_words:

            matched_ratio = (

                len(common_words)

                /

                len(useful_words)
            )


            if matched_ratio >= 0.7:

                score += 20

            elif matched_ratio >= 0.5:

                score += 10


        # ----------------------------------------------------
        # أفضل نتيجة
        # ----------------------------------------------------

        if score > best_score:

            best_score = score

            best_item = item


        elif (
            score == best_score
            and best_item is not None
        ):

            current_id = item.get(
                "message_id",
                0
            )


            best_id = best_item.get(
                "message_id",
                0
            )


            if current_id > best_id:

                best_item = item


    return (
        best_item,
        best_score
    )


# ============================================================
# البحث عن عدة منشورات للذكاء الاصطناعي
# ============================================================

def search_channel(
    query,
    limit=8
):

    if not channel_database:

        return []


    query_normalized = normalize_text(
        query
    )


    query_words = extract_keywords(
        query
    )


    useful_words = (

        query_words

        - {
            normalize_text(word)

            for word in STOP_WORDS
        }
    )


    results = []


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

            useful_words

            .intersection(
                content_words
            )
        )


        score += (
            len(common_words) * 5
        )


        if (
            query_normalized

            and query_normalized
            in content
        ):

            score += 40


        for phrase in STRONG_PHRASES:

            normalized_phrase = (
                normalize_text(
                    phrase
                )
            )


            if (

                normalized_phrase
                in query_normalized

                and

                normalized_phrase
                in content

            ):

                score += 25


        if score > 0:

            results.append(
                (
                    score,
                    item
                )
            )


    results.sort(

        key=lambda x: (

            x[0],

            x[1].get(
                "message_id",
                0
            )
        ),

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


    for topic in BISHA_TOPICS:

        topic_normalized = (
            normalize_text(
                topic
            )
        )


        if (

            topic_normalized

            and

            topic_normalized
            in normalized

        ):

            return True


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

        "تخصصي",

        "تحويل تخصص",
    ]


    for phrase in request_phrases:

        if (

            normalize_text(
                phrase
            )

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

            "هذا الحساب غير مفعل، "
            "يرجى التواصل مع المطور لتفعيل حسابك."
        )

    else:

        await update.message.reply_text(

            "هذه المجموعة غير مفعلة، "
            "يرجى التواصل مع المطور لتفعيلها."
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


    for value in [

        "**",
        "__",
        "###",
        "##",
        "#",

    ]:

        answer = answer.replace(
            value,
            ""
        )


    return answer.strip()


# ============================================================
# إنشاء رابط "اضغط هنا"
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

        f'<a href="{safe_link}">'
        "اضغط هنا"
        "</a>"
    )


# ============================================================
# إرسال المنشور الأصلي
# ============================================================

async def send_original_post(
    update,
    item
):

    if not update.message:

        return False


    text = item.get(
        "text",
        ""
    ).strip()


    link = item.get(
        "link",
        ""
    )


    if not text:

        return False


    safe_text = html.escape(
        text,
        quote=False
    )


    safe_text += (
        create_source_link(
            link
        )
    )


    try:

        await update.message.reply_text(

            safe_text,

            parse_mode="HTML",

            disable_web_page_preview=True
        )


        return True


    except Exception as e:

        print(
            f"Send Original Post Error: {e}"
        )


        return False


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


    if update.message:

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

            "وعليكم السلام ورحمة الله وبركاته، "
            "حياك الله 🌷"
        )


        return


    # --------------------------------------------------------
    # تجاهل الرسائل العادية
    # --------------------------------------------------------

    if not is_bisha_question(
        user_text
    ):

        return


    print("")
    print("=" * 70)


    print(
        f"سؤال الطالب: {user_text}"
    )


    print(
        f"عدد المنشورات في القاعدة: "
        f"{len(channel_database)}"
    )


    # --------------------------------------------------------
    # البحث عن أفضل منشور
    # --------------------------------------------------------

    best_post, best_score = (
        find_best_channel_post(
            user_text
        )
    )


    print(
        f"أفضل نتيجة: {best_score}"
    )


    if best_post:

        print(
            f"أفضل منشور: "
            f"{best_post.get('message_id')}"
        )


        print(
            f"النص: "
            f"{best_post.get('text', '')[:200]}"
        )

    else:

        print(
            "لم يتم العثور على منشور مناسب."
        )


    print("=" * 70)


    # --------------------------------------------------------
    # إرسال المنشور الأصلي عند التطابق القوي
    # --------------------------------------------------------

    if (

        best_post

        and best_score >= 45

    ):

        print(
            "سيتم إرسال المنشور الأصلي مباشرة."
        )


        sent = await send_original_post(

            update,

            best_post
        )


        if sent:

            memory.add_user_message(

                user_id,

                user_text
            )


            memory.add_assistant_message(

                user_id,

                best_post.get(
                    "text",
                    ""
                )
            )


            return


    # --------------------------------------------------------
    # استخدام الذكاء الاصطناعي
    # --------------------------------------------------------

    print(
        "لا يوجد تطابق قوي، سيتم استخدام الذكاء الاصطناعي."
    )


    matches = search_channel(

        user_text,

        limit=8
    )


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

التاريخ الميلادي:
{now.strftime("%Y-%m-%d")}

اليوم:
{now.strftime("%A")}

الوقت:
{now.strftime("%H:%M:%S")}

المنطقة الزمنية:
Asia/Riyadh
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

منشور قناة دليلي جامعة بيشة رقم:
{index}

رقم المنشور:
{item.get("message_id")}

تاريخ المنشور:
{item.get("date", "")}

رابط المنشور:
{item.get("link", "")}

محتوى المنشور:
{item.get("text", "")}

"""


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

أجب عن سؤال الطالب اعتمادًا على منشورات قناة دليلي جامعة بيشة فقط.

إذا وجدت منشورًا مناسبًا، اعتمد عليه.

إذا وجدت أكثر من منشور مناسب، اجمع المعلومات المفيدة منها.

إذا كانت هناك معلومات أحدث وأقدم، استخدم الأحدث إذا كان هناك تعارض.

إذا كان السؤال عن طريقة، اشرح الخطوات الموجودة في المنشورات.

إذا كان السؤال عن رابط، استخدم الرابط الموجود في المنشور.

إذا كان السؤال عن موعد، استخدم الموعد الموجود في المنشور فقط.

لا تخترع معلومات.

لا تخترع روابط.

لا تخترع مواعيد.

لا تخترع شروطًا.

لا تستخدم معلومات من جامعة أخرى.

إذا لم تجد إجابة مؤكدة، قل:

ما لقيت المعلومة بشكل مؤكد في منشورات قناة دليلي جامعة بيشة حاليًا.

أجب بشكل واضح ومختصر.
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
        # إضافة أفضل المصادر
        # ----------------------------------------------------

        added_links = set()


        for item in matches[:3]:

            link = item.get(
                "link",
                ""
            )


            if (

                link

                and link not in added_links

            ):

                safe_answer += (
                    create_source_link(
                        link
                    )
                )


                added_links.add(
                    link
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
            f"AI Error: {repr(e)}"
        )


        await update.message.reply_text(

            "حدثت مشكلة مؤقتة في خدمة دليلي، "
            "حاول مرة أخرى."
        )


# ============================================================
# عند تشغيل البوت
# ============================================================

async def on_startup(
    app: Application
):

    global channel_database


    print("")
    print("=" * 70)


    print(
        "بدء تشغيل DaliliSaudiBot..."
    )


    print("=" * 70)


    print(
        f"Bisha Channel ID Bot API: "
        f"{BISHA_CHANNEL_ID}"
    )


    print(
        f"Bisha Channel ID Telethon: "
        f"{BISHA_TELETHON_CHANNEL_ID}"
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
        f"Saved Channel Posts قبل الاستيراد: "
        f"{len(channel_database)}"
    )


    # --------------------------------------------------------
    # استيراد المنشورات القديمة
    # --------------------------------------------------------

    await import_old_channel_posts()


    print("")


    print(
        f"Saved Channel Posts بعد الاستيراد: "
        f"{len(channel_database)}"
    )


    print("=" * 70)


    print(
        "تم تجهيز قاعدة منشورات قناة جامعة بيشة."
    )


    print("=" * 70)


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


    print(
        "تم إيقاف DaliliSaudiBot."
    )


# ============================================================
# تشغيل البوت
# ============================================================

def main():

    app = (

        Application.builder()

        .token(
            TOKEN
        )

        .post_init(
            on_startup
        )

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
    # استقبال منشورات القناة الجديدة
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

    print("")
    print("=" * 70)


    print(
        "DaliliSaudiBot is starting..."
    )


    print(
        f"Bisha Channel ID Bot API: "
        f"{BISHA_CHANNEL_ID}"
    )


    print(
        f"Bisha Channel ID Telethon: "
        f"{BISHA_TELETHON_CHANNEL_ID}"
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


    print("=" * 70)


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

    try:

        main()

    except KeyboardInterrupt:

        print(
            "تم إيقاف البوت يدويًا."
        )

    except Exception as e:

        print("=" * 70)

        print(
            "خطأ أثناء تشغيل البوت:"
        )

        print(
            repr(e)
        )

        print("=" * 70)
