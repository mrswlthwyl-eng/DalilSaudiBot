import os
import re
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from hijridate import Hijri

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    TypeHandler,
    filters,
)

from provider_manager import get_manager
from conversation_memory import memory


# ============================================================
# إعدادات البوت
# ============================================================

TOKEN = os.getenv("BOT_TOKEN")

# ============================================================
# المجموعة المسموح للبوت بالرد فيها
# ============================================================

ALLOWED_GROUPS = {
    -1004452669915,
}

# ============================================================
# المستخدمون المسموح لهم باستخدام البوت في الخاص
# ============================================================

ALLOWED_USERS = {
    2076364383,
}

# ============================================================
# قناة جامعة بيشة
# ============================================================

BISHA_CHANNEL_ID = -1004493313338

# ============================================================
# اسم قاعدة البيانات
# ============================================================

DATABASE_FILE = "bisha_channel.db"

# ============================================================
# عدد النتائج المستخدمة في البحث
# ============================================================

MAX_SEARCH_RESULTS = 8


# ============================================================
# الذكاء الاصطناعي
# ============================================================

provider = get_manager()


# ============================================================
# قاعدة البيانات
# ============================================================

def get_db():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS channel_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            message_date TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(channel_id, message_id)
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_channel_posts_channel
        ON channel_posts(channel_id)
    """)

    conn.commit()
    conn.close()

    print("✅ قاعدة بيانات قناة جامعة بيشة جاهزة")


# ============================================================
# تنظيف النص
# ============================================================

def clean_text(text: str) -> str:

    if not text:
        return ""

    text = text.replace("\x00", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# إنشاء رابط منشور القناة
# ============================================================

def build_channel_message_url(message_id: int) -> str:

    internal_id = abs(BISHA_CHANNEL_ID) - 1000000000000

    return (
        f"https://t.me/c/"
        f"{internal_id}/"
        f"{message_id}"
    )


# ============================================================
# حفظ منشور القناة
# ============================================================

def save_channel_post(message):

    if not message:
        return

    text = (
        message.text
        or message.caption
        or ""
    )

    text = clean_text(text)

    if not text:
        return

    now = datetime.now(
        ZoneInfo("Asia/Riyadh")
    ).isoformat()

    message_date = ""

    if message.date:
        message_date = message.date.isoformat()

    conn = get_db()

    conn.execute("""
        INSERT INTO channel_posts (
            channel_id,
            message_id,
            text,
            message_date,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(channel_id, message_id)
        DO UPDATE SET
            text = excluded.text,
            message_date = excluded.message_date
    """, (
        BISHA_CHANNEL_ID,
        message.id,
        text,
        message_date,
        now,
    ))

    conn.commit()
    conn.close()

    print("=" * 60)
    print("📥 منشور جديد من قناة جامعة بيشة")
    print(f"Message ID: {message.id}")
    print(f"Text: {text[:200]}")
    print("=" * 60)


# ============================================================
# جلب منشورات القناة
# ============================================================

def get_recent_posts(limit=100):

    conn = get_db()

    rows = conn.execute("""
        SELECT
            message_id,
            text,
            message_date
        FROM channel_posts
        WHERE channel_id = ?
        ORDER BY message_id DESC
        LIMIT ?
    """, (
        BISHA_CHANNEL_ID,
        limit,
    )).fetchall()

    conn.close()

    return rows


# ============================================================
# الكلمات المتعلقة بجامعة بيشة
# ============================================================

BISHA_KEYWORDS = {

    # الجامعة
    "بيشة",
    "جامعة بيشة",
    "جامعه بيشه",
    "طلاب بيشة",
    "طلاب جامعه بيشه",

    # القبول
    "قبول",
    "القبول",
    "قبولي",
    "قبول جامعي",
    "منصة قبول",
    "قبول بيشة",

    # التسجيل
    "تسجيل",
    "التسجيل",
    "التسجيل الجامعي",
    "تسجيل المقررات",
    "تسجيل المواد",

    # Blackboard
    "blackboard",
    "black board",
    "بلاك بورد",
    "البلاك بورد",
    "البلاكبورد",

    # البريد
    "البريد الجامعي",
    "الايميل الجامعي",
    "الإيميل الجامعي",
    "ايميل الجامعة",
    "إيميل الجامعة",
    "البريد",

    # أكاديميت
    "اكاديميت",
    "أكاديميت",
    "اكاديميت جامعة بيشة",
    "أكاديميت جامعة بيشة",

    # الرقم الجامعي
    "الرقم الجامعي",
    "رقمي الجامعي",
    "رقم جامعي",
    "الرقم الجامعي",

    # المكافآت
    "المكافأة",
    "المكافآت",
    "مكافأة",
    "مكافآت",
    "المكافاه",
    "المكافأت",
    "متى تنزل المكافأة",
    "نزول المكافأة",

    # الآيبان
    "الايبان",
    "الإيبان",
    "الآيبان",
    "ايبان",
    "iban",

    # التخصص
    "تغيير التخصص",
    "تغيير تخصص",
    "التخصص",
    "التخصصات",

    # التحويل
    "تحويل",
    "التحويل",
    "التحويل الداخلي",
    "التحويل الخارجي",

    # الاعتذار
    "اعتذار",
    "الاعتذار",
    "اعتذار عن الفصل",
    "اعتذار عن مقرر",

    # التأجيل
    "تأجيل",
    "التأجيل",
    "تأجيل الفصل",

    # الانسحاب
    "انسحاب",
    "الانسحاب",
    "الانسحاب من الجامعة",
    "الانسحاب من القبول",

    # الجداول
    "الجدول",
    "الجداول",
    "الجدول الدراسي",
    "جدولي",

    # المقررات
    "المقرر",
    "المقررات",
    "المادة",
    "المواد",
    "الشعبة",
    "الشعب",

    # التدريب
    "التدريب",
    "التدريب الميداني",
    "التدريب التطبيقي",
    "التدريب التعاوني",

    # الدبلومات
    "الدبلوم",
    "الدبلومات",
    "دبلوم جامعة بيشة",
    "الدبلومات المدفوعة",

    # التقويم
    "التقويم الأكاديمي",
    "التقويم",
    "التقويم الجامعي",

    # الاختبارات
    "اختبار",
    "الاختبارات",
    "الاختبار",
    "اختبارات",
    "الاختبار النهائي",
    "الاختبارات النهائية",

    # النتائج
    "النتيجة",
    "النتائج",
    "نتائج الاختبارات",

    # الخدمات
    "الخدمات الإلكترونية",
    "الخدمات الاكاديمية",
    "الخدمات الأكاديمية",

    # البطاقة
    "البطاقة الجامعية",
    "البطاقة",

    # المواعيد
    "موعد التسجيل",
    "موعد القبول",
    "موعد الاختبار",
    "موعد المكافأة",

    # المنظومة
    "المنظومة الجامعية",
    "النظام الأكاديمي",
    "النظام الجامعي",
}


# ============================================================
# هل السؤال متعلق بجامعة بيشة؟
# ============================================================

def contains_bisha_topic(text: str) -> bool:

    text_lower = text.lower()

    for keyword in BISHA_KEYWORDS:

        if keyword.lower() in text_lower:
            return True

    return False


# ============================================================
# البحث في منشورات القناة
# ============================================================

def search_channel_posts(
    query: str,
    limit=MAX_SEARCH_RESULTS
):

    query = clean_text(query).lower()

    if not query:
        return []

    rows = get_recent_posts(500)

    query_words = set(
        word
        for word in re.findall(
            r"[\w\u0600-\u06FF]+",
            query
        )
        if len(word) >= 2
    )

    scored = []

    for row in rows:

        text = row["text"].lower()

        score = 0

        # تطابق العبارة كاملة
        if query in text:
            score += 30

        # تطابق الكلمات
        for word in query_words:

            if word in text:
                score += 3

        if score > 0:

            scored.append(
                (
                    score,
                    row
                )
            )

    scored.sort(
        key=lambda item: (
            item[0],
            item[1]["message_id"]
        ),
        reverse=True
    )

    return [
        row
        for score, row
        in scored[:limit]
    ]


# ============================================================
# البحث الذكي باستخدام AI
# ============================================================

async def find_best_channel_post(
    user_question: str
):

    # --------------------------------------------------------
    # البحث المباشر أولًا
    # --------------------------------------------------------

    direct_results = search_channel_posts(
        user_question
    )

    if direct_results:

        # إذا وجد تطابق مباشر قوي
        if len(direct_results) > 0:

            return direct_results[0]

    # --------------------------------------------------------
    # إذا لم نجد تطابقًا مباشرًا
    # نرسل أحدث المنشورات للذكاء الاصطناعي
    # --------------------------------------------------------

    recent_posts = get_recent_posts(100)

    if not recent_posts:

        return None

    posts_text = []

    for post in recent_posts:

        posts_text.append(
            f"""
MESSAGE_ID: {post['message_id']}

CONTENT:
{post['text']}
"""
        )

    source_text = "\n".join(
        posts_text
    )

    prompt = f"""
أنت محرك بحث داخلي لقناة جامعة بيشة.

سؤال الطالب:

{user_question}

هذه منشورات قناة جامعة بيشة:

{source_text}

مهمتك:

ابحث عن المنشور الأكثر ارتباطًا بسؤال الطالب.

إذا وجدت منشورًا مناسبًا:
أرسل رقم MESSAGE_ID فقط.

إذا لم تجد أي منشور مناسب:
أرسل فقط:
NONE

لا تكتب أي شيء آخر.
"""

    try:

        result = await provider.get_response(

            system_prompt="""
أنت محرك بحث داخلي لقناة جامعة بيشة.

مهمتك اختيار منشور موجود فعلًا في البيانات التي يتم إرسالها لك.

ممنوع اختراع رقم منشور.

ممنوع كتابة إجابة للطالب.

أرسل فقط MESSAGE_ID أو NONE.
""",

            history=[],

            user_prompt=prompt,
        )

        result = result.strip()

        if result.upper() == "NONE":

            return None

        match = re.search(
            r"\b(\d+)\b",
            result
        )

        if not match:

            return None

        message_id = int(
            match.group(1)
        )

        for post in recent_posts:

            if post["message_id"] == message_id:

                return post

    except Exception as e:

        print(
            f"❌ AI Search Error: {e}"
        )

    return None


# ============================================================
# إرسال نتيجة القناة
# ============================================================

async def send_channel_result(
    update: Update,
    post,
    intro="📚 لقيت لك الدليل المناسب:"
):

    if not post:

        return False

    message_url = build_channel_message_url(
        post["message_id"]
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔵 اضغط هنا",
                    url=message_url
                )
            ]
        ]
    )

    preview = post["text"]

    if len(preview) > 700:

        preview = (
            preview[:700]
            + "..."
        )

    await update.message.reply_text(

        f"{intro}\n\n"
        f"{preview}\n\n"
        f"للتفاصيل الكاملة اضغط على الزر بالأسفل.",

        reply_markup=keyboard
    )

    return True


# ============================================================
# الصلاحيات
# ============================================================

def is_authorized(
    update: Update
) -> bool:

    chat = update.effective_chat

    user = update.effective_user

    if not chat or not user:

        return False

    if chat.type in (
        "group",
        "supergroup"
    ):

        return (
            chat.id
            in ALLOWED_GROUPS
        )

    if chat.type == "private":

        return (
            user.id
            in ALLOWED_USERS
        )

    return False


# ============================================================
# تسجيل المحاولات غير المصرح بها
# ============================================================

def log_unauthorized(
    update: Update
):

    user = update.effective_user

    chat = update.effective_chat

    print("=" * 60)

    print(
        "🚫 محاولة استخدام غير مصرح بها"
    )

    print(
        f"Chat ID   : {chat.id}"
    )

    print(
        f"Chat Type : {chat.type}"
    )

    print(
        f"User ID   : {user.id}"
    )

    username = (
        f"@{user.username}"
        if user.username
        else "لا يوجد"
    )

    print(
        f"Username  : {username}"
    )

    print(
        f"Name      : {user.full_name}"
    )

    print("=" * 60)


# ============================================================
# رد عدم السماح
# ============================================================

async def handle_unauthorized(
    update: Update
):

    if not update.message:

        return

    if (
        update.effective_chat.type
        == "private"
    ):

        await update.message.reply_text(
            "هذا الحساب غير مفعل."
        )

    else:

        await update.message.reply_text(
            "هذه المجموعة غير مفعلة."
        )


# ============================================================
# التحيات
# ============================================================

GREETINGS = {

    "السلام عليكم",

    "السلام عليكم ورحمة الله",

    "السلام عليكم ورحمة الله وبركاته",

    "هلا",

    "هلا والله",

    "مرحبا",

    "مرحباً",

    "مرحبا",

    "اهلا",

    "أهلا",

    "أهلين",

    "ياهلا",

    "يا هلا",

    "صباح الخير",

    "مساء الخير",
}


def is_greeting(
    text: str
) -> bool:

    normalized = clean_text(
        text
    )

    return normalized in GREETINGS


async def handle_greeting(
    update: Update
):

    text = clean_text(
        update.message.text
    )

    if "السلام عليكم" in text:

        answer = (
            "وعليكم السلام ورحمة الله وبركاته، "
            "حياك الله 🌷"
        )

    elif "مساء الخير" in text:

        answer = (
            "مساء النور، حياك الله."
        )

    elif "صباح الخير" in text:

        answer = (
            "صباح النور، حياك الله."
        )

    else:

        answer = (
            "ياهلا وسهلا، حياك الله."
        )

    await update.message.reply_text(
        answer
    )


# ============================================================
# الوقت الحالي
# ============================================================

def get_time_context():

    now = datetime.now(
        ZoneInfo("Asia/Riyadh")
    )

    try:

        hijri = Hijri.today()

        hijri_date = (
            f"{hijri.day} "
            f"{hijri.month} "
            f"{hijri.year} هـ"
        )

    except Exception:

        hijri_date = "غير متوفر"

    days = {

        "Monday": "الاثنين",

        "Tuesday": "الثلاثاء",

        "Wednesday": "الأربعاء",

        "Thursday": "الخميس",

        "Friday": "الجمعة",

        "Saturday": "السبت",

        "Sunday": "الأحد",
    }

    current_day = days.get(
        now.strftime("%A"),
        now.strftime("%A")
    )

    return f"""
التاريخ الميلادي:
{now.strftime("%Y-%m-%d")}

التاريخ الهجري:
{hijri_date}

اليوم:
{current_day}

الوقت:
{now.strftime("%H:%M:%S")}

المنطقة الزمنية:
Asia/Riyadh
"""


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """

أنت "دليلك الجامعي"، مساعد طلابي متخصص في جامعة بيشة.

أنت تعمل داخل مجموعات طلاب جامعة بيشة.

مهمتك مساعدة الطلاب في الاستفسارات المتعلقة بجامعة بيشة.

المواضيع الأساسية التي تتعامل معها:

القبول
التسجيل
منصة قبول
Blackboard
البلاك بورد
البريد الجامعي
الإيميل الجامعي
أكاديميت
الرقم الجامعي
المكافآت
الآيبان
تغيير التخصص
التحويل
التحويل الداخلي
التحويل الخارجي
الاعتذار
التأجيل
الانسحاب
الجداول
المقررات
المواد
الشعب
التدريب
التدريب الميداني
الدبلومات
التقويم الأكاديمي
الاختبارات
النتائج
الخدمات الإلكترونية
البطاقة الجامعية
الأنظمة الأكاديمية

مصدر المعلومات الأساسي هو منشورات قناة جامعة بيشة.

لا تخترع أي معلومة.

لا تخمن المواعيد.

لا تخمن الرسوم.

لا تخمن الشروط.

لا تخمن الروابط.

إذا كانت المعلومة غير موجودة أو غير مؤكدة قل ذلك بوضوح.

إذا كان السؤال عن جامعة أخرى، فلا تجيب باعتبار المعلومات تخص جامعة بيشة.

استخدم اللغة العربية السعودية البسيطة.

كن مختصرًا عندما يكون السؤال بسيطًا.

إذا طلب الطالب شرحًا، اشرح له بشكل واضح ومنظم.

لا تستخدم Markdown.

لا تستخدم:

**
__
###
لا تمدح نفسك.
لا تقل إنك ذكاء اصطناعي إلا إذا سألك الطالب مباشرة.
تعامل مع الطالب كموظف استقبال جامعي محترف. """
============================================================
معالجة رسائل الطلاب
============================================================
async def reply_message( update: Update, context: ContextTypes.DEFAULT_TYPE ):
if not update.message:

    return

# --------------------------------------------------------
# الصلاحيات
# --------------------------------------------------------

if not is_authorized(update):

    log_unauthorized(
        update
    )

    await handle_unauthorized(
        update
    )

    return

# --------------------------------------------------------
# بيانات المستخدم
# --------------------------------------------------------

user_id = (
    update.effective_user.id
)

user_text = clean_text(
    update.message.text
)

if not user_text:

    return

print("=" * 60)

print(
    f"📝 سؤال الطالب: {user_text}"
)

print("=" * 60)

# --------------------------------------------------------
# التحيات
# --------------------------------------------------------

if is_greeting(
    user_text
):

    await handle_greeting(
        update
    )

    return

# --------------------------------------------------------
# الرسائل غير المتعلقة بجامعة بيشة
# --------------------------------------------------------

if not contains_bisha_topic(
    user_text
):

    print(
        "⏭️ تجاهل الرسالة: "
        "ليست مرتبطة بجامعة بيشة"
    )

    return

# --------------------------------------------------------
# البحث في قناة جامعة بيشة
# --------------------------------------------------------

post = await find_best_channel_post(
    user_text
)

# --------------------------------------------------------
# وجدنا منشورًا مناسبًا
# --------------------------------------------------------

if post:

    answer = (
        "📚 لقيت لك الدليل المناسب "
        "في قناة جامعة بيشة:"
    )

    await send_channel_result(
        update,
        post,
        answer
    )

    memory.add_user_message(
        user_id,
        user_text
    )

    memory.add_assistant_message(
        user_id,
        answer
    )

    return

# --------------------------------------------------------
# لا يوجد منشور مناسب
# الذكاء الاصطناعي يجيب
# --------------------------------------------------------

print(
    "⚠️ لم يتم العثور على منشور مباشر."
)

print(
    "🤖 سيتم استخدام الذكاء الاصطناعي."
)

history = memory.get_history(
    user_id
)

time_context = (
    get_time_context()
)

system_prompt = (
    SYSTEM_PROMPT
    + "\n\n"
    + time_context
)

try:

    answer = await provider.get_response(

        system_prompt=system_prompt,

        history=history,

        user_prompt=user_text,
    )

    # إزالة تنسيقات Markdown
    answer = re.sub(
        r"[*_`#]+",
        "",
        answer
    ).strip()

    memory.add_user_message(
        user_id,
        user_text
    )

    memory.add_assistant_message(
        user_id,
        answer
    )

    await update.message.reply_text(
        answer
    )

except Exception as e:

    print(
        f"❌ AI Error: {e}"
    )

    await update.message.reply_text(
        "حدثت مشكلة مؤقتة، "
        "حاول مرة أخرى."
    )
============================================================
استقبال منشورات قناة جامعة بيشة
============================================================
async def channel_post_handler( update: Update, context: ContextTypes.DEFAULT_TYPE ):
message = update.channel_post

if not message:

    return

# --------------------------------------------------------
# نتأكد أن المنشور من قناة جامعة بيشة
# --------------------------------------------------------

if message.chat.id != BISHA_CHANNEL_ID:

    return

print(
    "📢 منشور جديد من قناة جامعة بيشة"
)

save_channel_post(
    message
)
============================================================
/start
============================================================
async def start( update: Update, context: ContextTypes.DEFAULT_TYPE ):
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

    "👋 أهلاً وسهلاً بك في دليلك الجامعي.\n\n"
    "🎓 كيف أقدر أساعدك؟"
)
============================================================
إيقاف البوت
============================================================
async def on_shutdown( app: Application ):
try:

    await provider.shutdown()

except Exception as e:

    print(
        f"⚠️ Shutdown Error: {e}"
    )

print(
    "🛑 تم إيقاف البوت."
)
============================================================
تشغيل البوت
============================================================
def main():
# --------------------------------------------------------
# التأكد من وجود Token
# --------------------------------------------------------

if not TOKEN:

    raise RuntimeError(
        "❌ BOT_TOKEN غير موجود."
    )

# --------------------------------------------------------
# إنشاء قاعدة البيانات
# --------------------------------------------------------

init_database()

# --------------------------------------------------------
# إنشاء التطبيق
# --------------------------------------------------------

app = (
    Application.builder()
    .token(TOKEN)
    .post_shutdown(on_shutdown)
    .build()
)

# --------------------------------------------------------
# أمر /start
# --------------------------------------------------------

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

# --------------------------------------------------------
# استقبال منشورات القناة
# --------------------------------------------------------

app.add_handler(
    TypeHandler(
        Update,
        channel_post_handler
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
# تشغيل
# --------------------------------------------------------

print("=" * 60)
print("🤖 Bisha University Dalili Bot")
print("🎓 جامعة بيشة")
print(
    f"📢 Channel ID: {BISHA_CHANNEL_ID}"
)
print(
    f"👥 Groups: {ALLOWED_GROUPS}"
)
print("🟢 Bot is running...")
print("=" * 60)

app.run_polling(
    allowed_updates=Update.ALL_TYPES
)
