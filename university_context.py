Enter"""
University Context Manager for Telegram Bot
Manages university-specific context for group chats and routes questions appropriately.
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class University:
    """Represents a Saudi university with all its identifiers."""
    name_ar: str
    name_en: str
    abbreviations: List[str]
    aliases: List[str]
    
    def matches(self, text: str) -> bool:
        """Check if the given text matches this university."""
        text_lower = text.lower().strip()
        
        # Check all possible identifiers
        all_identifiers = [self.name_ar.lower(), self.name_en.lower()] + \
                         [abbr.lower() for abbr in self.abbreviations] + \
                         [alias.lower() for alias in self.aliases]
        
        return any(identifier in text_lower for identifier in all_identifiers)
    
    def get_primary_name(self) -> str:
        """Get the primary Arabic name of the university."""
        return self.name_ar


# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Manages SQLite database operations for university context."""
    
    def __init__(self, db_path: str = "university_context.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_universities (
                    chat_id INTEGER PRIMARY KEY,
                    group_name TEXT NOT NULL,
                    university_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def set_university(self, chat_id: int, group_name: str, university_name: str):
        """Save or update university for a group."""
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO group_universities (chat_id, group_name, university_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    group_name = excluded.group_name,
                    university_name = excluded.university_name,
                    updated_at = excluded.updated_at
            """, (chat_id, group_name, university_name, now, now))
            conn.commit()
    
    def get_university(self, chat_id: int) -> Optional[Dict]:
        """Get university info for a group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT chat_id, group_name, university_name, created_at, updated_at FROM group_universities WHERE chat_id = ?",
                (chat_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    "chat_id": row[0],
                    "group_name": row[1],
                    "university_name": row[2],
                    "created_at": row[3],
                    "updated_at": row[4]
                }
            return None
    
    def remove_university(self, chat_id: int):
        """Remove university association for a group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM group_universities WHERE chat_id = ?", (chat_id,))
            conn.commit()


# ============================================================================
# SAUDI UNIVERSITIES DATABASE
# ============================================================================

class SaudiUniversities:
    """Complete list of all Saudi universities with their identifiers."""
    
    UNIVERSITIES = [
        University(
            name_ar="جامعة أم القرى",
            name_en="Umm Al-Qura University",
            abbreviations=["UQU", "Umm Al-Qura"],
            aliases=["أم القرى", "ام القرى"]
        ),
        University(
            name_ar="الجامعة الإسلامية",
            name_en="Islamic University of Madinah",
            abbreviations=["IU"],
            aliases=["الجامعة الاسلامية", "جامعة المدينة", "المدينة"]
        ),
        University(
            name_ar="جامعة الإمام محمد بن سعود الإسلامية",
            name_en="Imam Muhammad ibn Saud Islamic University",
            abbreviations=["IMSIU"],
            aliases=["الإمام", "امام", "جامعة الإمام"]
        ),
        University(
            name_ar="جامعة الملك سعود",
            name_en="King Saud University",
            abbreviations=["KSU"],
            aliases=["الملك سعود", "جامعة الرياض"]
        ),
        University(
            name_ar="جامعة الملك عبدالعزيز",
            name_en="King Abdulaziz University",
            abbreviations=["KAU"],
            aliases=["الملك عبدالعزيز", "عبدالعزيز", "جامعة جدة"]
        ),
        University(
            name_ar="جامعة الملك فهد للبترول والمعادن",
            name_en="King Fahd University of Petroleum and Minerals",
            abbreviations=["KFUPM"],
            aliases=["البترول", "المعادن", "جامعة الظهران"]
        ),
        University(
            name_ar="جامعة الملك فيصل",
            name_en="King Faisal University",
            abbreviations=["KFU"],
            aliases=["الملك فيصل", "جامعة الأحساء", "الاحساء"]
        ),
        University(
            name_ar="جامعة الملك خالد",
            name_en="King Khalid University",
            abbreviations=["KKU"],
            aliases=["الملك خالد", "جامعة أبها", "ابها"]
        ),
        University(
            name_ar="جامعة القصيم",
            name_en="Qassim University",
            abbreviations=["QU"],
            aliases=["القصيم"]
        ),
        University(
            name_ar="جامعة طيبة",
            name_en="Taibah University",
            abbreviations=["TU"],
            aliases=["طيبة", "جامعة المدينة المنورة"]
        ),
        University(
            name_ar="جامعة الطائف",
            name_en="Taif University",
            abbreviations=["TU"],
            aliases=["الطائف"]
        ),
        University(
            name_ar="جامعة حائل",
            name_en="University of Hail",
            abbreviations=["UOH"],
            aliases=["حائل"]
        ),
        University(
            name_ar="جامعة جازان",
            name_en="Jazan University",
            abbreviations=["JAZANU"],
            aliases=["جازان"]
        ),
        University(
            name_ar="جامعة الجوف",
            name_en="Jouf University",
            abbreviations=["JU"],
            aliases=["الجوف"]
        ),
        University(
            name_ar="جامعة الباحة",
            name_en="Al Baha University",
            abbreviations=["BU"],
            aliases=["الباحة"]
        ),
        University(
            name_ar="جامعة تبوك",
            name_en="University of Tabuk",
            abbreviations=["UT"],
            aliases=["تبوك"]
        ),
        University(
            name_ar="جامعة نجران",
            name_en="Najran University",
            abbreviations=["NU"],
            aliases=["نجران"]
        ),
        University(
            name_ar="جامعة الحدود الشمالية",
            name_en="Northern Border University",
            abbreviations=["NBU"],
            aliases=["الحدود الشمالية", "عرعر"]
        ),
        University(
            name_ar="جامعة الأميرة نورة بنت عبدالرحمن",
            name_en="Princess Nourah Bint Abdulrahman University",
            abbreviations=["PNU"],
            aliases=["الأميرة نورة", "الاميرة نورة", "جامعة البنات"]
        ),
        University(
            name_ar="جامعة الملك سعود بن عبدالعزيز للعلوم الصحية",
            name_en="King Saud bin Abdulaziz University for Health Sciences",
            abbreviations=["KSAU-HS"],
            aliases=["العلوم الصحية", "الحرس الوطني"]
        ),
        University(
            name_ar="جامعة الإمام عبدالرحمن بن فيصل",
            name_en="Imam Abdulrahman Bin Faisal University",
            abbreviations=["IAU"],
            aliases=["الإمام عبدالرحمن", "امام عبدالرحمن", "جامعة الدمام"]
        ),
        University(
            name_ar="جامعة الملك عبدالله للعلوم والتقنية",
            name_en="King Abdullah University of Science and Technology",
            abbreviations=["KAUST"],
            aliases=["الملك عبدالله", "ثول"]
        ),
        University(
            name_ar="جامعة الأمير سطام بن عبدالعزيز",
            name_en="Prince Sattam Bin Abdulaziz University",
            abbreviations=["PSAU"],
            aliases=["الأمير سطام", "الامير سطام", "جامعة الخرج"]
        ),
        University(
            name_ar="جامعة شقراء",
            name_en="Shaqra University",
            abbreviations=["SU"],
            aliases=["شقراء"]
        ),
        University(
            name_ar="جامعة المجمعة",
            name_en="Majmaah University",
            abbreviations=["MU"],
            aliases=["المجمعة"]
        ),
        University(
            name_ar="الجامعة السعودية الإلكترونية",
            name_en="Saudi Electronic University",
            abbreviations=["SEU"],
            aliases=["السعودية الإلكترونية", "الالكترونية", "التعليم الإلكتروني"]
        ),
        University(
            name_ar="جامعة جدة",
            name_en="University of Jeddah",
            abbreviations=["UJ"],
            aliases=["جدة"]
        ),
        University(
            name_ar="جامعة بيشة",
            name_en="University of Bisha",
            abbreviations=["UB"],
            aliases=["بيشة"]
        ),
        University(
            name_ar="جامعة حفر الباطن",
            name_en="University of Hafr Al Batin",
            abbreviations=["UHB"],
            aliases=["حفر الباطن"]
        ),
        University(
            name_ar="جامعة الأمير محمد بن فهد",
            name_en="Prince Mohammad Bin Fahd University",
            abbreviations=["PMU"],
            aliases=["الأمير محمد بن فهد", "الامير محمد بن فهد"]
        ),
        University(
            name_ar="جامعة اليمامة",
            name_en="Al Yamamah University",
            abbreviations=["YU"],
            aliases=["اليمامة"]
        ),
        University(
            name_ar="جامعة الفيصل",
            name_en="Alfaisal University",
            abbreviations=["AU"],
            aliases=["الفيصل"]
        ),
        University(
            name_ar="جامعة دار العلوم",
            name_en="Dar Al Uloom University",
            abbreviations=["DAU"],
            aliases=["دار العلوم"]
        ),
        University(
            name_ar="جامعة عفت",
            name_en="Effat University",
            abbreviations=["EU"],
            aliases=["عفت"]
        ),
        University(
            name_ar="جامعة الأمير مقرن بن عبدالعزيز",
            name_en="Prince Muqrin Bin Abdulaziz University",
            abbreviations=["PMU"],
            aliases=["الأمير مقرن", "الامير مقرن"]
        ),
        University(
            name_ar="جامعة رياض العلم",
            name_en="Riyadh Elm University",
            abbreviations=["REU"],
            aliases=["رياض العلم"]
        ),
        University(
            name_ar="جامعة المستقبل",
            name_en="Al Mustaqbal University",
            abbreviations=["AMU"],
            aliases=["المستقبل"]
        ),
        University(
            name_ar="جامعة الأعمال والتكنولوجيا",
            name_en="University of Business and Technology",
            abbreviations=["UBT"],
            aliases=["الأعمال والتكنولوجيا", "الاعمال والتكنولوجيا"]
        ),
        University(
            name_ar="كلية الأمير سلطان للسياحة والإدارة",
            name_en="Prince Sultan College for Tourism and Management",
            abbreviations=["PSC"],
            aliases=["الأمير سلطان", "الامير سلطان", "كلية السياحة"]
        ),
    ]
    
    @classmethod
    def detect_university(cls, text: str) -> Optional[University]:
        """Try to detect a university from the given text."""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Try exact matches first, then partial
        for university in cls.UNIVERSITIES:
            if university.matches(text):
                return university
        
        return None
    
    @classmethod
    def extract_mentioned_university(cls, text: str) -> Optional[University]:
        """Extract university mentioned in a message (if any)."""
        if not text:
            return None
        
        return cls.detect_university(text)
    
    @classmethod
    def get_all_universities(cls) -> List[University]:
        """Get the list of all universities."""
        return cls.UNIVERSITIES


# ============================================================================
# UNIVERSITY CONTEXT MANAGER
# ============================================================================

class UniversityContextManager:
    """
    Main class for managing university context in Telegram groups.
    Handles detection, storage, and message routing logic.
    """
    
    def __init__(self, db_path: str = "university_context.db"):
        self.db = DatabaseManager(db_path)
        self.universities_db = SaudiUniversities()
    
    def detect_university_from_group_name(self, group_name: str) -> Optional[University]:
        """
        Try to automatically detect university from group name.
        
        Args:
            group_name: The name of the Telegram group
            
        Returns:
            University object if detected, None otherwise
        """
        return self.universities_db.detect_university(group_name)
    
    def set_group_university(self, chat_id: int, group_name: str, university_name: str) -> bool:
        """
        Set the university for a group.
        
        Args:
            chat_id: Telegram chat ID
            group_name: Group name
            university_name: University name to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify the university exists
            detected = self.universities_db.detect_university(university_name)
            if not detected:
                return False
            
            self.db.set_university(chat_id, group_name, detected.get_primary_name())
            logger.info(f"Set university '{detected.get_primary_name()}' for chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting university: {e}")
            return False
    
    def get_group_university(self, chat_id: int) -> Optional[Dict]:
        """
        Get the university associated with a group.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            Dictionary with university info or None
        """
        return self.db.get_university(chat_id)
    
    def handle_new_group(self, chat_id: int, group_name: str) -> Optional[str]:
        """
        Handle when bot is added to a new group.
        Attempts to auto-detect university from group name.
        
        Args:
            chat_id: Telegram chat ID
            group_name: Group name
            
        Returns:
            University name if detected, None otherwise
        """
        university = self.detect_university_from_group_name(group_name)
        
        if university:
            self.db.set_university(chat_id, group_name, university.get_primary_name())
            logger.info(f"Auto-detected university '{university.get_primary_name()}' for group '{group_name}'")
            return university.get_primary_name()
        else:
            logger.info(f"Could not auto-detect university for group '{group_name}'")
            return None
    
    def should_process_message(self, chat_id: int, message_text: str, chat_type: str) -> Tuple[bool, str]:
        """
        Determine if a message should be processed by Gemini.
        
        Args:
            chat_id: Telegram chat ID
            message_text: The message text
            chat_type: 'group' or 'private'
            
        Returns:
            Tuple of (should_process, reason/message)
        """
        # Private chats: always process
        if chat_type == "private":
            return True, ""
        
        # Group chats: check university context
        group_university = self.get_group_university(chat_id)
        
        # No university set for this group
        if not group_university:
            return False, (
                "⚠️ لم يتم تحديد الجامعة لهذه المجموعة بعد.\n"
                "يمكن للمشرفين استخدام الأمر:\n"
                "/set_university اسم الجامعة\n\n"
                "مثال: /set_university جامعة الطائف"
            )
        
        current_uni_name = group_university["university_name"]
        
        # Check if message mentions another university
        mentioned_uni = self.universities_db.extract_mentioned_university(message_text)
        
        if mentioned_uni and mentioned_uni.get_primary_name() != current_uni_name:
            return False, (
                f"❌ هذه المجموعة مخصصة لـ **{current_uni_name}** فقط.\n\n"
                f"لا يمكنني الإجابة عن أسئلة تخص **{mentioned_uni.get_primary_name()}** داخل هذه المجموعة.\n\n"
                "📌 يرجى:\n"
                "• طرح سؤالك في مجموعة الجامعة المعنية\n"
                "• أو مراسلتي في المحادثة الخاصة للإجابة عن أي جامعة"
            )
        
        # Valid message for this group's university
        return True, current_uni_name
    
    def get_gemini_context(self, university_name: str) -> str:
        """
        Generate context string for Gemini API.
        
        Args:
            university_name: The university name
            
        Returns:
            Context string for Gemini
        """
        return f"""Current University:
{university_name}

Chat Type:
University Group

Answer ONLY according to this university.
Never answer according to another university.
If the user's message mentions another university, do not answer it."""
    
    def get_available_universities_list(self) -> str:
        """Get a formatted list of all available universities."""
        universities = self.universities_db.get_all_universities()
        uni_list = "\n".join([f"• {uni.get_primary_name()}" for uni in universities])
        return f"الجامعات المتاحة:\n\n{uni_list}"


# ============================================================================
# BOT INTEGRATION HELPERS
# ============================================================================

class BotIntegration:
    """
    Helper class for easy integration with the main Telegram bot.
    Provides ready-to-use functions for common bot operations.
    """
    
    def __init__(self, context_manager: UniversityContextManager):
        self.manager = context_manager
    
    async def handle_bot_added_to_group(self, chat_id: int, group_name: str):
        """Handle when bot is added to a group."""
        detected_uni = self.manager.handle_new_group(chat_id, group_name)
        
        if detected_uni:
            return (
                f"✅ تم اكتشاف الجامعة تلقائياً: **{detected_uni}**\n\n"
                "🔍 سأجيب الآن عن أسئلتكم المتعلقة بهذه الجامعة.\n"
                "📌 ملاحظة: لن أجيب عن أسئلة تخص جامعات أخرى داخل هذه المجموعة."
            )
        else:
            return (
                "👋 مرحباً! لم أتمكن من تحديد جامعتكم تلقائياً من اسم المجموعة.\n\n"
                "📌 يمكن للمشرفين استخدام الأمر:\n"
                "/set_university اسم الجامعة\n\n"
                "مثال: /set_university جامعة الطائف\n\n"
                "لعرض قائمة الجامعات المتاحة:\n"
                "/list_universities"
            )
    
    async def handle_set_university(self, chat_id: int, group_name: str, university_name: str, is_admin: bool):
        """Handle the /set_university command."""
        if not is_admin:
            return "❌ هذا الأمر متاح للمشرفين فقط."
        
        if not university_name:
            return (
                "❌ يرجى تحديد اسم الجامعة.\n\n"
                "طريقة الاستخدام:\n"
                "/set_university اسم الجامعة\n\n"
                "مثال: /set_university جامعة الطائف\n\n"
                "لعرض قائمة الجامعات المتاحة:\n"
                "/list_universities"
            )
        
        success = self.manager.set_group_university(chat_id, group_name, university_name)
        
        if success:
            return f"✅ تم تعيين الجامعة بنجاح: **{university_name}**"
        else:
            return (
                "❌ لم يتم التعرف على هذه الجامعة.\n"
                "تأكد من كتابة الاسم بشكل صحيح أو استخدم:\n"
                "/list_universities لعرض الجامعات المتاحة"
            )
    
    async def handle_message(self, chat_id: int, message_text: str, chat_type: str):
        """
        Handle incoming message and decide routing.
        
        Returns:
            Tuple of (should_send_to_gemini, context_or_message, is_error)
            - If should_send_to_gemini is True: context_or_message contains Gemini context
            - If should_send_to_gemini is False: context_or_message contains reply text
        """
        should_process, result = self.manager.should_process_message(chat_id, message_text, chat_type)
        
        if not should_process:
            return False, result, False
        
        if chat_type == "private":
            # For private chats, try to detect mentioned university for context
            mentioned = self.manager.universities_db.extract_mentioned_university(message_text)
            if mentioned:
                context = self.manager.get_gemini_context(mentioned.get_primary_name())
            else:
                context = "You are a helpful assistant for Saudi university students. Answer questions about any Saudi university."
            
            return True, context, False
        else:
            # Group chat with valid university context
            uni_name = result  # result is the university name
            context = self.manager.get_gemini_context(uni_name)
            return True, context, False
    
    def get_list_universities_response(self):
        """Get response for /list_universities command."""
        return self.manager.get_available_universities_list()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the context manager
    context_manager = UniversityContextManager()
    bot_integration = BotIntegration(context_manager)
    
    # Test auto-detection
    print("=== Auto Detection Test ===")
    test_names = [
        "طلاب جامعة الطائف",
        "جامعة جدة",
        "KSU Students",
        "UJ Community",
        "مجموعة غير معروفة"
    ]
    
    for name in test_names:
        result = context_manager.detect_university_from_group_name(name)
        print(f"Group: {name}")
        print(f"Detected: {result.get_primary_name() if result else 'None'}")
        print()
    
    # Test message routing
    print("=== Message Routing Test ===")
    test_cases = [
        {
            "chat_id": 12345,
            "group_name": "طلاب جامعة الطائف",
            "message": "متى يبدأ التسجيل؟",
            "chat_type": "group",
            "description": "Question about own university"
        },
        {
            "chat_id": 12345,
            "group_name": "طلاب جامعة الطائف",
            "message": "متى تنزل مكافأة جامعة جدة؟",
            "chat_type": "group",
            "description": "Question about another university"
        }
    ]
    
    # First set the university for the test group
    context_manager.handle_new_group(12345, "طلاب جامعة الطائف")
    
    for test in test_cases:
        print(f"Test: {test['description']}")
        print(f"Message: {test['message']}")
        
        should_process, result, is_error = bot_integration.handle_message(
            test['chat_id'],
            test['message'],
            test['chat_type']
        )
        
        print(f"Should send to Gemini: {should_process}")
        if should_process:
            print(f"Context: {result[:100]}...")
        else:
            print(f"Response: {result}")
        print()
