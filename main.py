import os
import re
import json
import html

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
# Channel ID الخاص بـ Telethon
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

    "موقع الكلية",
    "موقع الكليات",
    
    
}


# ============================================================
# كلمات السؤال التي يتم تجاهلها في المطابقة
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

    "ليش",
    "لماذا",

    "كم",

    "اعرف",
    "تقدر",
    "اقدر",

    "اريد",
    "أريد",
    "اعطني",
    "عطني",

    "طريقة",
    "طريقه",

    "كيفية",
    "كيفيه",

    "رابط",
    "موعد",
    "شرح",

    "استفسار",
    "استفسر",

    "وشلون",
    "شلون",
}


# ============================================================
# العبارات المهمة جدًا
# ============================================================

STRONG_PHRASES = [

    # البريد
    "البريد الجامعي",
    "الايميل الجامعي",
    "الإيميل الجامعي",
    "الاميل الجامعي",
    "تفعيل البريد",
    "تفعيل الايميل",
    "تفعيل الإيميل",
    "تفعيل البريد الجامعي",
    "تفعيل الايميل الجامعي",

    # بلاك بورد
    "بلاك بورد",
    "البلاك بورد",
    "blackboard",

    # الرقم الجامعي
    "الرقم الجامعي",
    "رقم جامعي",

    # التخصص
    "تغيير التخصص",
    "تغيير تخصص",

    # التحويل
    "التحويل الداخلي",
    "التحويل الخارجي",
    "تحويل تخصص",

    # الانسحاب
    "الانسحاب من الجامعة",
    "الانسحاب من القبول",

    # الاعتذار
    "الاعتذار عن الفصل",

    # التأجيل
    "تأجيل الفصل",

    # الجدول
    "الجدول الدراسي",

    # التدريب
    "التدريب التطبيقي",
    "التدريب الميداني",

    # التقويم
    "التقويم الاكاديمي",
    "التقويم الأكاديمي",

    # الخدمات
    "الخدمات الالكترونية",
    "الخدمات الإلكترونية",

    # كلمة المرور
    "كلمة المرور",
    "كلمة السر",
    "الباسورد",

    # الآيبان
    "الايبان",
    "الآيبان",
    "iban",

    # المكافأة
    "المكافاة",
    "المكافأة",
    "المكافآت",

    # التسجيل
    "التسجيل الجامعي",

    # القبول
    "القبول الجامعي",
]


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
            f"Channel DB Load Error: {repr(e)}"
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
            f"Channel DB Save Error: {repr(e)}"
        )


# ============================================================
# قاعدة المعرفة الحالية
# ============================================================

channel_database = (
    load_channel_database()
)


# ============================================================
# إنشاء رابط المنشور
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
# استخراج نص الرسالة
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
# إنشاء سجل منشور
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
# استيراد المنشورات القديمة من القناة
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
        # إنشاء Telethon Client
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
                "❌ TELEGRAM_SESSION غير مصرح به."
            )

            return


        print(
            "✅ تم الاتصال بحساب Telegram بنجاح."
        )


        # ----------------------------------------------------
        # الوصول للقناة
        # ----------------------------------------------------

        print(
            f"جاري الوصول إلى القناة: "
            f"@{BISHA_CHANNEL_USERNAME}"
        )


        channel = await client.get_entity(
            BISHA_CHANNEL_USERNAME
        )


        # ----------------------------------------------------
        # استخراج ID الحقيقي
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
            f"Channel ID Bot API:"
        )

        print(
            BISHA_CHANNEL_ID
        )


        print(
            f"Channel ID Telethon المطلوب:"
        )

        print(
            BISHA_TELETHON_CHANNEL_ID
        )


        print(
            f"Channel ID الحقيقي:"
        )

        print(
            real_channel_id
        )


        print(
            "=================================================="
        )


        # ----------------------------------------------------
        # التحقق من القناة
        # ----------------------------------------------------

        if (
            real_channel_id
            != BISHA_TELETHON_CHANNEL_ID
        ):

            print(
                "❌ القناة التي تم الوصول إليها "
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
        # تحويل القاعدة إلى Dictionary
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
            # تجاهل الوسائط التي لا تحتوي على نص
            # ------------------------------------------------

            if not text:

                if has_media:

                    media_count += 1

                continue


            text_count += 1


            # ------------------------------------------------
            # إنشاء السجل
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
            # إظهار التقدم
            # ------------------------------------------------

            if total % 50 == 0:

                print(

                    f"تمت قراءة {total} "

                    f"| نصي: {text_count} "

                    f"| جديد: {new_count} "

                    f"| محدث: {updated_count}"

                )


        # ----------------------------------------------------
        # تحديث قاعدة المعرفة
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


    record = create_channel_record(
        message
    )


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
    # إضافة المنشور الجديد
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
    print("=" * 70)


    print(
        "✅ تم استقبال منشور جديد من قناة جامعة بيشة"
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
        f"{record.get('link', '')}"
    )


    print(
        f"Total Posts: "
        f"{len(channel_database)}"
    )


    print("=" * 70)


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
# حساب تطابق سؤال الطالب مع المنشور
# ============================================================

def calculate_post_score(
    query,
    item
):

    query_normalized = normalize_text(
        query
    )


    content = item.get(
        "normalized",
        ""
    )


    if not query_normalized or not content:

        return 0


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


    content_words = set(
        content.split()
    )


    score = 0


    # ========================================================
    # تطابق العبارة كاملة
    # ========================================================

    if (
        len(query_normalized) >= 8

        and query_normalized
        in content
    ):

        score += 80


    # ========================================================
    # تطابق الكلمات
    # ========================================================

    common_words = (

        useful_words

        .intersection(
            content_words
        )
    )


    score += (
        len(common_words) * 8
    )


    # ========================================================
    # نسبة تطابق الكلمات
    # ========================================================

    if useful_words:

        matched_ratio = (

            len(common_words)

            /

            len(useful_words)
        )


        if matched_ratio >= 0.80:

            score += 30

        elif matched_ratio >= 0.60:

            score += 20

        elif matched_ratio >= 0.40:

            score += 10


    # ========================================================
    # العبارات القوية
    # ========================================================

    for phrase in STRONG_PHRASES:

        normalized_phrase = normalize_text(
            phrase
        )


        if (
            normalized_phrase
            in query_normalized
        ):

            if (
                normalized_phrase
                in content
            ):

                score += 45


    # ========================================================
    # المواضيع
    # ========================================================

    for topic in BISHA_TOPICS:

        normalized_topic = normalize_text(
            topic
        )


        # تجاهل المواضيع العامة جدًا
        if normalized_topic in {
            "بيشه",
            "بيشه",
            "جامعه بيشه",
            "جامعه بيشه",
        }:

            continue


        if len(
            normalized_topic
        ) < 4:

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


    # ========================================================
    # الكلمات المهمة المفردة
    # ========================================================

    important_words = {

        "ايميل",
        "الايميل",
        "بريد",

        "تفعيل",

        "بلاك",
        "بورد",

        "رقم",
        "جامعي",

        "تخصص",
        "تحويل",

        "انسحاب",
        "اعتذار",
        "تاجيل",

        "جدول",

        "تدريب",

        "اختبار",
        "اختبارات",

        "نتائج",
        "درجات",

        "ايبان",

        "مكافاه",

        "نفاذ",

        "كلمه",
        "مرور",

        "تسجيل",
        "قبول",
    }


    important_matches = (

        useful_words

        .intersection(
            important_words
        )

        .intersection(
            content_words
        )
    )


    score += (
        len(important_matches) * 10
    )


    return score


# ============================================================
# البحث عن أفضل منشور
# ============================================================

def find_best_channel_post(
    query
):

    if not channel_database:

        return None, 0


    best_item = None
    best_score = 0


    for item in channel_database:

        score = calculate_post_score(
            query,
            item
        )


        if score > best_score:

            best_score = score

            best_item = item


        elif (
            score == best_score
            and score > 0
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
# تحديد نوع الرد
# ============================================================

def get_response_intro(
    user_text
):

    normalized = normalize_text(
        user_text
    )


    # --------------------------------------------------------
    # البريد / الإيميل
    # --------------------------------------------------------

    if (
        "ايميل" in normalized
        or "الايميل" in normalized
        or "بريد" in normalized
        or "البريد" in normalized
    ):

        return (
            "لتفعيل البريد الجامعي "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # بلاك بورد
    # --------------------------------------------------------

    if (
        "بلاك بورد" in normalized
        or "البلاك بورد" in normalized
        or "blackboard" in normalized
    ):

        return (
            "للدخول إلى بلاك بورد "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # الرقم الجامعي
    # --------------------------------------------------------

    if (
        "رقم جامعي" in normalized
        or "الرقم الجامعي" in normalized
        or "رقمي الجامعي" in normalized
    ):

        return (
            "للحصول على الرقم الجامعي "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # التسجيل
    # --------------------------------------------------------

    if (
        "تسجيل" in normalized
        or "التسجيل" in normalized
    ):

        return (
            "لإتمام التسجيل "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # القبول
    # --------------------------------------------------------

    if (
        "قبول" in normalized
        or "القبول" in normalized
    ):

        return (
            "بخصوص القبول، "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # المكافأة
    # --------------------------------------------------------

    if (
        "مكافاه" in normalized
        or "مكافاة" in normalized
        or "مكافآت" in normalized
        or "مكافئات" in normalized
    ):

        return (
            "بخصوص المكافأة، "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # الآيبان
    # --------------------------------------------------------

    if (
        "ايبان" in normalized
        or "الايبان" in normalized
        or "iban" in normalized
    ):

        return (
            "لإضافة أو تحديث الآيبان "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # التخصص
    # --------------------------------------------------------

    if (
        "تخصص" in normalized
        or "التخصص" in normalized
    ):

        return (
            "بخصوص التخصص، "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # التحويل
    # --------------------------------------------------------

    if (
        "تحويل" in normalized
        or "التحويل" in normalized
    ):

        return (
            "بخصوص التحويل، "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # الاعتذار
    # --------------------------------------------------------

    if "اعتذار" in normalized:

        return (
            "بخصوص الاعتذار، "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # التأجيل
    # --------------------------------------------------------

    if (
        "تاجيل" in normalized
        or "تأجيل" in user_text
    ):

        return (
            "بخصوص التأجيل، "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # الانسحاب
    # --------------------------------------------------------

    if (
        "انسحاب" in normalized
        or "الانسحاب" in normalized
    ):

        return (
            "بخصوص الانسحاب، "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # الجدول
    # --------------------------------------------------------

    if (
        "جدول" in normalized
        or "الجداول" in normalized
    ):

        return (
            "بخصوص الجدول الدراسي، "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # التدريب
    # --------------------------------------------------------

    if "تدريب" in normalized:

        return (
            "بخصوص التدريب، "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # الاختبارات
    # --------------------------------------------------------

    if (
        "اختبار" in normalized
        or "اختبارات" in normalized
    ):

        return (
            "بخصوص الاختبارات، "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # النتائج والدرجات
    # --------------------------------------------------------

    if (
        "نتائج" in normalized
        or "نتيجة" in normalized
        or "درجات" in normalized
        or "درجة" in normalized
    ):

        return (
            "بخصوص النتائج والدرجات، "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # نفاذ
    # --------------------------------------------------------

    if "نفاذ" in normalized:

        return (
            "للدخول عن طريق نفاذ "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # كلمة المرور
    # --------------------------------------------------------

    if (
        "كلمه المرور" in normalized
        or "كلمه السر" in normalized
        or "باسورد" in normalized
        or "كلمه" in normalized
        and "مرور" in normalized
    ):

        return (
            "لاستعادة أو تغيير كلمة المرور "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # الخدمات الإلكترونية
    # --------------------------------------------------------

    if (
        "خدمات الكترونيه" in normalized
        or "الخدمات الالكترونيه" in normalized
    ):

        return (
            "للدخول إلى الخدمات الإلكترونية "
            "اتبع الخطوات التالية:"
        )


    # --------------------------------------------------------
    # افتراضي
    # --------------------------------------------------------

    return (
        "بخصوص استفسارك، "
        "اتبع الخطوات التالية:"
    )


# ============================================================
# إنشاء رسالة الرد
# ============================================================

def create_guide_response(
    user_text,
    link
):

    if not link:

        return ""


    intro = get_response_intro(
        user_text
    )


    safe_link = html.escape(
        link,
        quote=True
    )


    return (

        f"{intro}\n\n"

        "للدخول للخطوات والشرح\n"

        f'<a href="{safe_link}">'
        "📎 اضغط هنا 📎"
        "</a>"
    )


# ============================================================
# إرسال رد إرشادي + رابط المنشور
# ============================================================

async def send_guide_response(
    update,
    user_text,
    item
):

    if not update.message:

        return False


    link = item.get(
        "link",
        ""
    )


    if not link:

        print(
            "❌ المنشور لا يحتوي على رابط."
        )

        return False


    response = create_guide_response(
        user_text,
        link
    )


    if not response:

        return False


    try:

        await update.message.reply_text(

            response,

            parse_mode="HTML",

            disable_web_page_preview=True
        )


        return True


    except Exception as e:

        print(
            f"Send Guide Response Error: "
            f"{repr(e)}"
        )


        return False


# ============================================================
# /start
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # --------------------------------------------------------
    # لا يوجد رد على /start
    # لأن البوت لا يرد إلا على الاستفسارات
    # التي لها منشور مطابق.
    # --------------------------------------------------------

    if not is_authorized(
        update
    ):

        log_unauthorized(
            update
        )

        return


    print(
        f"/start من المستخدم: "
        f"{update.effective_user.id}"
        if update.effective_user
        else "/start"
    )


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


    print("")
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


    # --------------------------------------------------------
    # المجموعات المسموحة
    # --------------------------------------------------------

    if chat_type in (

        ChatType.GROUP,

        ChatType.SUPERGROUP,

    ):

        return (

            update.effective_chat.id

            in ALLOWED_GROUPS
        )


    # --------------------------------------------------------
    # الخاص للمستخدمين المسموحين
    # --------------------------------------------------------

    if chat_type == ChatType.PRIVATE:

        if not update.effective_user:

            return False


        return (

            update.effective_user.id

            in ALLOWED_USERS
        )


    return False


# ============================================================
# الرد على رسائل الطلاب
# ============================================================

async def reply_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:

        return


    # --------------------------------------------------------
    # التحقق من الصلاحية
    # --------------------------------------------------------

    if not is_authorized(
        update
    ):

        log_unauthorized(
            update
        )

        # لا نرسل أي رد
        return


    # --------------------------------------------------------
    # المستخدم
    # --------------------------------------------------------

    user = update.effective_user


    if not user:

        return


    user_id = user.id


    # --------------------------------------------------------
    # نص الرسالة
    # --------------------------------------------------------

    user_text = (

        update.message.text

        or ""

    ).strip()


    if not user_text:

        return


    # --------------------------------------------------------
    # طباعة السؤال
    # --------------------------------------------------------

    print("")
    print("=" * 70)


    print(
        f"سؤال الطالب: {user_text}"
    )


    print(
        f"User ID: {user_id}"
    )


    print(
        f"عدد منشورات القناة: "
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
            f"{best_post.get('text', '')[:250]}"
        )


    else:

        print(
            "لا يوجد منشور مطابق."
        )


    print("=" * 70)


    # ========================================================
    # إذا لا يوجد منشور مناسب
    # لا يرد البوت إطلاقًا
    # ========================================================

    if not best_post:

        print(
            "❌ لا يوجد منشور مناسب → لا يوجد رد."
        )

        return


    # ========================================================
    # الحد الأدنى للتطابق
    # ========================================================

    MIN_MATCH_SCORE = 45


    if best_score < MIN_MATCH_SCORE:

        print(
            f"❌ التطابق ضعيف "
            f"({best_score} < {MIN_MATCH_SCORE})"
        )


        print(
            "لن يتم إرسال أي رد."
        )


        return


    # ========================================================
    # يوجد منشور مناسب
    # إرسال الصيغة المطلوبة
    # ========================================================

    print(
        "✅ تم العثور على منشور مناسب."
    )


    print(
        "سيتم إرسال الرد الإرشادي فقط."
    )


    sent = await send_guide_response(

        update,

        user_text,

        best_post
    )


    if sent:

        print(
            "✅ تم إرسال الرد بنجاح."
        )

    else:

        print(
            "❌ فشل إرسال الرد."
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
        "✅ تم تجهيز قاعدة منشورات قناة جامعة بيشة."
    )


    print(
        "✅ البوت لن يجيب إلا عند وجود منشور مطابق."
    )


    print(
        "✅ الذكاء الاصطناعي غير مستخدم في الردود."
    )


    print("=" * 70)


# ============================================================
# إغلاق البوت
# ============================================================

async def on_shutdown(
    app: Application
):

    print("")
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

        print("")
        print("=" * 70)


        print(
            "❌ خطأ أثناء تشغيل البوت:"
        )


        print(
            repr(e)
        )


        print("=" * 70)
