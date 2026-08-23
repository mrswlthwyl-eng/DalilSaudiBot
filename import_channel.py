import os
import json
import asyncio

from telethon import TelegramClient


# ============================================================
# إعدادات Telegram API
# ============================================================

SESSION_NAME = "bisha_channel_import_session"

CHANNEL_USERNAME = "Bishauniversity3"

CHANNEL_URL = "https://t.me/Bishauniversity3"

CHANNEL_ID = -1004493313338

DATABASE_FILE = "bisha_channel_knowledge.json"


# ============================================================
# قراءة النص من المنشور
# ============================================================

def get_message_text(message):
    text = getattr(message, "message", None)

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
        text = text.replace(old, new)

    return " ".join(text.split())


# ============================================================
# رابط المنشور
# ============================================================

def make_message_link(message_id):
    return f"{CHANNEL_URL}/{message_id}"


# ============================================================
# تحميل قاعدة البيانات
# ============================================================

def load_database():
    if not os.path.exists(DATABASE_FILE):
        return []

    try:
        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except Exception as e:
        print(f"خطأ في قراءة قاعدة البيانات: {e}")

    return []


# ============================================================
# حفظ قاعدة البيانات
# ============================================================

def save_database(database):
    database.sort(
        key=lambda item: item.get(
            "message_id",
            0
        )
    )

    with open(
        DATABASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            database,
            file,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# إنشاء سجل المنشور
# ============================================================

def create_record(message):

    text = get_message_text(message)

    media = getattr(
        message,
        "media",
        None
    )

    if media:
        media_type = media.__class__.__name__
    else:
        media_type = "text"

    return {
        "message_id": message.id,

        "text": text,

        "normalized": normalize_text(text),

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
# استيراد جميع المنشورات
# ============================================================

async def import_channel():

    print("")
    print("=" * 70)
    print("بدء استيراد قناة جامعة بيشة")
    print("=" * 70)

    print(f"القناة: @{CHANNEL_USERNAME}")
    print(f"الرابط: {CHANNEL_URL}")
    print(f"Channel ID: {CHANNEL_ID}")

    print("=" * 70)

    # --------------------------------------------------------
    # تحميل البيانات القديمة إن وجدت
    # --------------------------------------------------------

    old_database = load_database()

    posts = {
        item.get("message_id"): item
        for item in old_database
        if item.get("message_id")
    }

    print(
        f"المنشورات الموجودة مسبقًا: {len(posts)}"
    )

    # --------------------------------------------------------
    # استخدام جلسة Telegram التي سجلت الدخول بها
    # --------------------------------------------------------

    if not os.path.exists(
        SESSION_NAME + ".session"
    ):
        print("")
        print("خطأ: ملف جلسة Telegram غير موجود.")
        print(
            f"المطلوب: {SESSION_NAME}.session"
        )
        return

    print("")
    print("جاري تشغيل جلسة Telegram...")

    client = TelegramClient(
        SESSION_NAME,
        None,
        None
    )

    try:

        await client.connect()

        # ----------------------------------------------------
        # التأكد من تسجيل الدخول
        # ----------------------------------------------------

        if not await client.is_user_authorized():

            print("")
            print("الجلسة غير مسجلة الدخول.")
            print(
                "شغّل login_telegram.py أولًا."
            )

            await client.disconnect()
            return

        print(
            "تم الاتصال بحساب Telegram بنجاح."
        )

        # ----------------------------------------------------
        # الوصول إلى القناة
        # ----------------------------------------------------

        print("")
        print("جاري الوصول إلى قناة جامعة بيشة...")

        channel = await client.get_entity(
            CHANNEL_USERNAME
        )

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

        # ----------------------------------------------------
        # التحقق من القناة
        # ----------------------------------------------------

        expected_id = abs(CHANNEL_ID)

        if str(expected_id).startswith("100"):
            expected_id = int(
                str(expected_id)[3:]
            )

        if real_channel_id != expected_id:

            print("")
            print(
                "خطأ: القناة التي تم الوصول إليها لا تطابق القناة المطلوبة."
            )

            print(
                f"ID الموجود: {real_channel_id}"
            )

            print(
                f"ID المطلوب: {expected_id}"
            )

            await client.disconnect()
            return

        print("")
        print(
            "تم التحقق من قناة جامعة بيشة بنجاح."
        )

        # ----------------------------------------------------
        # قراءة جميع المنشورات القديمة
        # ----------------------------------------------------

        print("")
        print("=" * 70)
        print("جاري قراءة جميع المنشورات السابقة...")
        print("سيتم قراءة كامل سجل القناة.")
        print("قد تستغرق العملية وقتًا حسب عدد المنشورات.")
        print("=" * 70)

        total_messages = 0
        saved_messages = 0
        updated_messages = 0
        text_messages = 0
        media_messages = 0
        empty_messages = 0

        async for message in client.iter_messages(
            channel,
            limit=None
        ):

            total_messages += 1

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
                    media_messages += 1
                else:
                    empty_messages += 1

                continue

            text_messages += 1

            # ------------------------------------------------
            # إنشاء سجل المنشور
            # ------------------------------------------------

            record = create_record(
                message
            )

            message_id = message.id

            if message_id in posts:
                updated_messages += 1
            else:
                saved_messages += 1

            posts[message_id] = record

            # ------------------------------------------------
            # عرض التقدم
            # ------------------------------------------------

            if total_messages % 50 == 0:

                print(
                    f"تمت قراءة: {total_messages} | "
                    f"نصي: {text_messages} | "
                    f"جديد: {saved_messages} | "
                    f"محدث: {updated_messages} | "
                    f"وسائط: {media_messages}"
                )

        # ----------------------------------------------------
        # تحويل إلى قائمة
        # ----------------------------------------------------

        database = list(
            posts.values()
        )

        database.sort(
            key=lambda item:
            item.get(
                "message_id",
                0
            )
        )

        # ----------------------------------------------------
        # حفظ قاعدة المعرفة
        # ----------------------------------------------------

        print("")
        print("جاري حفظ قاعدة المعرفة...")

        save_database(
            database
        )

        # ----------------------------------------------------
        # النتيجة
        # ----------------------------------------------------

        print("")
        print("=" * 70)
        print("اكتمل استيراد قناة جامعة بيشة")
        print("=" * 70)

        print(
            f"إجمالي الرسائل المقروءة: {total_messages}"
        )

        print(
            f"المنشورات النصية: {text_messages}"
        )

        print(
            f"منشورات جديدة: {saved_messages}"
        )

        print(
            f"منشورات محدثة: {updated_messages}"
        )

        print(
            f"منشورات وسائط بدون نص: {media_messages}"
        )

        print(
            f"رسائل فارغة: {empty_messages}"
        )

        print(
            f"إجمالي قاعدة المعرفة: {len(database)}"
        )

        print(
            f"ملف قاعدة المعرفة: {DATABASE_FILE}"
        )

        print("=" * 70)

        # ----------------------------------------------------
        # آخر منشور
        # ----------------------------------------------------

        if database:

            last_post = database[-1]

            print("")
            print("آخر منشور محفوظ:")

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
            "يمكن الآن تشغيل main.py."
        )

        print("=" * 70)

    except Exception as e:

        print("")
        print("=" * 70)
        print("حدث خطأ أثناء استيراد القناة")
        print("=" * 70)

        print(e)

        print("=" * 70)

    finally:

        await client.disconnect()

        print("")
        print(
            "تم إغلاق اتصال Telegram."
        )


# ============================================================
# تشغيل الملف
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
        print(
            f"خطأ: {e}"
        )
