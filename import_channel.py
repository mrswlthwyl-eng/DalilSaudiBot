import os
import json
import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession


# ============================================================
# إعدادات Telegram API
# ============================================================

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_SESSION = os.getenv("TELEGRAM_SESSION")

if not API_ID:
    raise RuntimeError(
        "TELEGRAM_API_ID غير موجود في Environment Variables"
    )

if not API_HASH:
    raise RuntimeError(
        "TELEGRAM_API_HASH غير موجود في Environment Variables"
    )

if not TELEGRAM_SESSION:
    raise RuntimeError(
        "TELEGRAM_SESSION غير موجود في Environment Variables"
    )

try:
    API_ID = int(API_ID)

except ValueError:
    raise RuntimeError(
        "TELEGRAM_API_ID يجب أن يكون رقمًا صحيحًا"
    )


# ============================================================
# معلومات قناة جامعة بيشة
# ============================================================

CHANNEL_USERNAME = "Bishauniversity3"

CHANNEL_URL = "https://t.me/Bishauniversity3"

CHANNEL_ID = -1004493313338


# ============================================================
# قاعدة المعرفة
# ============================================================

DATABASE_FILE = "bisha_channel_knowledge.json"


# ============================================================
# قراءة نص المنشور
# ============================================================

def get_message_text(message):

    if not message:
        return ""

    text = getattr(
        message,
        "message",
        None
    )

    if not text:
        return ""

    return str(text).strip()


# ============================================================
# تنظيف وتوحيد النص
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    text = str(text).lower()

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

    return " ".join(
        text.split()
    )


# ============================================================
# إنشاء رابط المنشور
# ============================================================

def make_message_link(message_id):

    return (
        f"{CHANNEL_URL}/{message_id}"
    )


# ============================================================
# تحميل قاعدة المعرفة
# ============================================================

def load_database():

    if not os.path.exists(
        DATABASE_FILE
    ):

        return []

    try:

        with open(
            DATABASE_FILE,
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
            f"خطأ في قراءة قاعدة المعرفة: {e}"
        )

    return []


# ============================================================
# حفظ قاعدة المعرفة
# ============================================================

def save_database(database):

    try:

        database.sort(
            key=lambda item:
            item.get(
                "message_id",
                0
            )
        )

        # حفظ مؤقت أولًا ثم استبدال الملف
        # لتقليل احتمال تلف JSON
        temp_file = (
            DATABASE_FILE + ".tmp"
        )

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                database,
                file,
                ensure_ascii=False,
                indent=2
            )

        os.replace(
            temp_file,
            DATABASE_FILE
        )

        print(
            f"تم حفظ {len(database)} منشور في قاعدة المعرفة."
        )

    except Exception as e:

        print(
            f"خطأ في حفظ قاعدة المعرفة: {e}"
        )


# ============================================================
# إنشاء سجل المنشور
# ============================================================

def create_record(message):

    text = get_message_text(
        message
    )

    media = getattr(
        message,
        "media",
        None
    )

    if media:

        media_type = (
            media.__class__.__name__
        )

    else:

        media_type = "text"

    return {
        "message_id": message.id,

        "text": text,

        "normalized": normalize_text(
            text
        ),

        "date": (
            message.date.isoformat()
            if message.date
            else ""
        ),

        "link": make_message_link(
            message.id
        ),

        "channel_id": CHANNEL_ID,

        "channel_username": CHANNEL_USERNAME,

        "channel_url": CHANNEL_URL,

        "media_type": media_type,

        "views": getattr(
            message,
            "views",
            None
        ),

        "forwards": getattr(
            message,
            "forwards",
            None
        ),

        "grouped_id": getattr(
            message,
            "grouped_id",
            None
        ),
    }


# ============================================================
# استيراد جميع منشورات القناة
# ============================================================

async def import_channel():

    print("")
    print("=" * 70)
    print("بدء استيراد قناة جامعة بيشة")
    print("=" * 70)

    print(
        f"القناة: @{CHANNEL_USERNAME}"
    )

    print(
        f"الرابط: {CHANNEL_URL}"
    )

    print(
        f"Channel ID: {CHANNEL_ID}"
    )

    print("=" * 70)


    # ========================================================
    # تحميل قاعدة المعرفة الموجودة
    # ========================================================

    old_database = load_database()

    posts = {
        item.get("message_id"): item
        for item in old_database
        if item.get("message_id")
    }

    print(
        f"المنشورات الموجودة مسبقًا: {len(posts)}"
    )


    # ========================================================
    # إنشاء Telegram Client باستخدام StringSession
    # ========================================================

    print("")
    print(
        "جاري تشغيل جلسة Telegram من TELEGRAM_SESSION..."
    )

    client = TelegramClient(
        StringSession(TELEGRAM_SESSION),
        API_ID,
        API_HASH
    )


    try:

        # ====================================================
        # الاتصال
        # ====================================================

        await client.connect()

        print(
            "تم الاتصال بـ Telegram."
        )


        # ====================================================
        # التحقق من تسجيل الدخول
        # ====================================================

        if not await client.is_user_authorized():

            print("")
            print(
                "خطأ: TELEGRAM_SESSION غير صالحة أو انتهت صلاحيتها."
            )

            return

        print(
            "تم التحقق من جلسة Telegram بنجاح."
        )


        # ====================================================
        # معلومات الحساب
        # ====================================================

        try:

            me = await client.get_me()

            print("")
            print(
                f"الحساب: {me.first_name or ''}"
            )

            if me.username:

                print(
                    f"Username: @{me.username}"
                )

            print(
                f"User ID: {me.id}"
            )

        except Exception as e:

            print(
                f"تعذر قراءة معلومات الحساب: {e}"
            )


        # ====================================================
        # الوصول إلى القناة
        # ====================================================

        print("")
        print(
            "جاري الوصول إلى قناة جامعة بيشة..."
        )

        try:

            channel = await client.get_entity(
                CHANNEL_USERNAME
            )

        except Exception as e:

            print("")
            print(
                "تعذر الوصول إلى القناة."
            )

            print(
                f"الخطأ: {e}"
            )

            return


        # ====================================================
        # معلومات القناة
        # ====================================================

        real_channel_id = getattr(
            channel,
            "id",
            None
        )

        channel_title = getattr(
            channel,
            "title",
            ""
        )

        print("")
        print(
            f"اسم القناة: {channel_title}"
        )

        print(
            f"Channel ID: {real_channel_id}"
        )


        # ====================================================
        # التحقق من القناة
        # ====================================================

        expected_channel_id = abs(
            CHANNEL_ID
        )

        if str(
            expected_channel_id
        ).startswith("100"):

            expected_channel_id = int(
                str(expected_channel_id)[3:]
            )

        if (
            real_channel_id
            != expected_channel_id
        ):

            print("")
            print(
                "خطأ: القناة التي تم الوصول إليها لا تطابق القناة المطلوبة."
            )

            print(
                f"ID الموجود: {real_channel_id}"
            )

            print(
                f"ID المطلوب: {expected_channel_id}"
            )

            return

        print("")
        print(
            "تم التحقق من قناة جامعة بيشة بنجاح."
        )


        # ====================================================
        # قراءة جميع المنشورات السابقة
        # ====================================================

        print("")
        print("=" * 70)
        print(
            "جاري قراءة جميع المنشورات السابقة..."
        )
        print(
            "سيتم قراءة كامل سجل القناة."
        )
        print(
            "قد تستغرق العملية وقتًا حسب عدد المنشورات."
        )
        print("=" * 70)


        total_messages = 0
        saved_messages = 0
        updated_messages = 0
        text_messages = 0
        media_messages = 0
        empty_messages = 0


        try:

            async for message in client.iter_messages(
                channel,
                limit=None
            ):

                total_messages += 1


                # --------------------------------------------
                # استخراج النص
                # --------------------------------------------

                text = get_message_text(
                    message
                )


                # --------------------------------------------
                # التحقق من الوسائط
                # --------------------------------------------

                has_media = bool(
                    getattr(
                        message,
                        "media",
                        None
                    )
                )


                # --------------------------------------------
                # منشور بدون نص
                # --------------------------------------------

                if not text:

                    if has_media:

                        media_messages += 1

                    else:

                        empty_messages += 1

                    continue


                text_messages += 1


                # --------------------------------------------
                # إنشاء سجل المنشور
                # --------------------------------------------

                record = create_record(
                    message
                )

                message_id = (
                    message.id
                )


                # --------------------------------------------
                # جديد أو موجود
                # --------------------------------------------

                if message_id in posts:

                    updated_messages += 1

                else:

                    saved_messages += 1


                posts[
                    message_id
                ] = record


                # --------------------------------------------
                # عرض التقدم
                # --------------------------------------------

                if (
                    total_messages % 50
                    == 0
                ):

                    print(
                        f"تمت قراءة: "
                        f"{total_messages} | "
                        f"نصي: "
                        f"{text_messages} | "
                        f"جديد: "
                        f"{saved_messages} | "
                        f"محدث: "
                        f"{updated_messages} | "
                        f"وسائط: "
                        f"{media_messages}"
                    )


                # --------------------------------------------
                # حفظ دوري كل 500 منشور
                # --------------------------------------------

                if (
                    total_messages % 500
                    == 0
                ):

                    print("")
                    print(
                        "حفظ نسخة احتياطية مؤقتة من البيانات..."
                    )

                    save_database(
                        list(posts.values())
                    )

        except Exception as e:

            print("")
            print(
                "حدث خطأ أثناء قراءة القناة:"
            )

            print(
                e
            )

            # حفظ ما تم جمعه حتى لحظة الخطأ
            database = list(
                posts.values()
            )

            save_database(
                database
            )

            raise


        # ====================================================
        # تحويل البيانات إلى قائمة
        # ====================================================

        database = list(
            posts.values()
        )


        # ====================================================
        # ترتيب المنشورات
        # ====================================================

        database.sort(
            key=lambda item:
            item.get(
                "message_id",
                0
            )
        )


        # ====================================================
        # الحفظ النهائي
        # ====================================================

        print("")
        print(
            "جاري حفظ قاعدة المعرفة النهائية..."
        )

        save_database(
            database
        )


        # ====================================================
        # عرض النتيجة
        # ====================================================

        print("")
        print("=" * 70)
        print(
            "اكتمل استيراد قناة جامعة بيشة"
        )
        print("=" * 70)

        print(
            f"إجمالي الرسائل المقروءة: "
            f"{total_messages}"
        )

        print(
            f"المنشورات النصية: "
            f"{text_messages}"
        )

        print(
            f"منشورات جديدة: "
            f"{saved_messages}"
        )

        print(
            f"منشورات محدثة: "
            f"{updated_messages}"
        )

        print(
            f"منشورات وسائط بدون نص: "
            f"{media_messages}"
        )

        print(
            f"رسائل فارغة: "
            f"{empty_messages}"
        )

        print(
            f"إجمالي قاعدة المعرفة: "
            f"{len(database)}"
        )

        print(
            f"ملف قاعدة المعرفة: "
            f"{DATABASE_FILE}"
        )

        print("=" * 70)


        # ====================================================
        # أول وآخر منشور
        # ====================================================

        if database:

            first_post = database[0]

            last_post = database[-1]

            print("")
            print(
                "أقدم منشور محفوظ:"
            )

            print(
                f"رقم المنشور: "
                f"{first_post.get('message_id')}"
            )

            print(
                f"الرابط: "
                f"{first_post.get('link')}"
            )

            print("")

            print(
                "أحدث منشور محفوظ:"
            )

            print(
                f"رقم المنشور: "
                f"{last_post.get('message_id')}"
            )

            print(
                f"الرابط: "
                f"{last_post.get('link')}"
            )


        print("")
        print(
            "تم حفظ المنشورات القديمة بنجاح."
        )

        print(
            "يمكن الآن استخدام قاعدة المعرفة مع main.py."
        )

        print("=" * 70)


    finally:

        await client.disconnect()

        print("")
        print(
            "تم إغلاق اتصال Telegram."
        )


# ============================================================
# التشغيل
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            import_channel()
        )

    except KeyboardInterrupt:

        print("")
        print(
            "تم إيقاف الاستيراد."
        )

    except Exception as e:

        print("")
        print("=" * 70)

        print(
            "حدث خطأ:"
        )

        print(
            e
        )

        print("=" * 70)
