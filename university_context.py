"""
University Context Manager for Telegram Bot (Professional Edition)
Manages comprehensive university context including colleges, departments,
academic levels, and group types with advanced detection algorithms.
"""

import sqlite3
import logging
import re
import unicodedata
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class GroupType(Enum):
    """Types of university groups."""
    STUDENTS_MALE = "طلاب"
    STUDENTS_FEMALE = "طالبات"
    MIXED = "طلاب وطالبات"
    GRADUATES = "خريجين"
    FACULTY = "هيئة تدريس"
    STAFF = "موظفين"
    ANNOUNCEMENTS = "إعلانات"
    POSTGRADUATE = "دراسات عليا"
    COURSE_SPECIFIC = "مقرر دراسي"
    UNKNOWN = "غير محدد"


class AcademicLevel(Enum):
    """Academic levels."""
    LEVEL_1 = "المستوى الأول"
    LEVEL_2 = "المستوى الثاني"
    LEVEL_3 = "المستوى الثالث"
    LEVEL_4 = "المستوى الرابع"
    LEVEL_5 = "المستوى الخامس"
    LEVEL_6 = "المستوى السادس"
    LEVEL_7 = "المستوى السابع"
    LEVEL_8 = "المستوى الثامن"
    LEVEL_9 = "المستوى التاسع"
    LEVEL_10 = "المستوى العاشر"
    INTERNSHIP = "سنة الامتياز"
    PREPARATORY = "السنة التحضيرية"
    FRESHMAN = "دفعة جديدة"
    SENIOR = "سنة التخرج"
    ALUMNI = "خريج"
    UNKNOWN = "غير محدد"


# ============================================================================
# TEXT PROCESSING UTILITIES
# ============================================================================

class TextNormalizer:
    """Advanced text normalization for Arabic text."""
    
    # Arabic character normalization map
    ARABIC_NORMALIZATION = {
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا',
        'ة': 'ه', 'ى': 'ي', 'ئ': 'ي', 'ؤ': 'و',
        'ـ': '',  # Tatweel
    }
    
    # Emoji and symbol patterns
    EMOJI_PATTERN = re.compile(
        "[\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    
    SPECIAL_CHARS_PATTERN = re.compile(r'[_\-–—•··،,؛;:\'\"\(\)\[\]\{\}]')
    
    @classmethod
    def normalize_arabic(cls, text: str) -> str:
        """Normalize Arabic text by removing diacritics and standardizing characters."""
        if not text:
            return ""
        
        # Remove diacritics (tashkeel)
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        
        # Normalize Arabic characters
        for char, replacement in cls.ARABIC_NORMALIZATION.items():
            text = text.replace(char, replacement)
        
        return text
    
    @classmethod
    def clean_text(cls, text: str) -> str:
        """Clean text from emojis and special characters."""
        if not text:
            return ""
        
        # Remove emojis
        text = cls.EMOJI_PATTERN.sub(' ', text)
        
        # Replace special characters with spaces
        text = cls.SPECIAL_CHARS_PATTERN.sub(' ', text)
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @classmethod
    def normalize_for_matching(cls, text: str) -> str:
        """Full normalization pipeline for text matching."""
        text = cls.clean_text(text)
        text = cls.normalize_arabic(text)
        text = text.lower().strip()
        return text


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class College:
    """Represents a college within a university."""
    name: str
    keywords: List[str]
    
    def matches(self, text: str) -> bool:
        """Check if text matches this college."""
        text_normalized = TextNormalizer.normalize_for_matching(text)
        return any(
            TextNormalizer.normalize_for_matching(kw) in text_normalized
            for kw in self.keywords
        )


@dataclass
class Department:
    """Represents a department within a college."""
    name: str
    keywords: List[str]
    college_keywords: List[str] = field(default_factory=list)
    
    def matches(self, text: str) -> bool:
        """Check if text matches this department."""
        text_normalized = TextNormalizer.normalize_for_matching(text)
        return any(
            TextNormalizer.normalize_for_matching(kw) in text_normalized
            for kw in self.keywords
        )


@dataclass
class University:
    """Represents a Saudi university with comprehensive identifiers."""
    name_ar: str
    name_en: str
    abbreviations: List[str]
    aliases: List[str]
    unique_abbreviations: List[str] = field(default_factory=list)
    colleges: List[College] = field(default_factory=list)
    
    def __post_init__(self):
        """Filter out ambiguous abbreviations."""
        # Only keep abbreviations that are unique to this university
        self.unique_abbreviations = [
            abbr for abbr in self.abbreviations
            if self._is_unique_abbreviation(abbr)
        ]
    
    def _is_unique_abbreviation(self, abbr: str) -> bool:
        """Check if abbreviation is unique (not shared with other universities)."""
        # This will be set externally by SaudiUniversities class
        return getattr(self, '_abbr_unique_map', {}).get(abbr, True)
    
    def matches(self, text: str, use_ambiguous: bool = False) -> Tuple[bool, float]:
        """
        Check if the given text matches this university.
        
        Returns:
            Tuple of (matched, confidence_score)
        """
        text_normalized = TextNormalizer.normalize_for_matching(text)
        
        # Check primary names (high confidence)
        if TextNormalizer.normalize_for_matching(self.name_ar) in text_normalized:
            return True, 0.98
        
        if TextNormalizer.normalize_for_matching(self.name_en) in text_normalized:
            return True, 0.98
        
        # Check unique abbreviations (high confidence)
        for abbr in self.unique_abbreviations:
            abbr_normalized = TextNormalizer.normalize_for_matching(abbr)
            if re.search(rf'\b{re.escape(abbr_normalized)}\b', text_normalized):
                return True, 0.95
        
        # Check ambiguous abbreviations (lower confidence)
        if use_ambiguous:
            for abbr in self.abbreviations:
                if abbr not in self.unique_abbreviations:
                    abbr_normalized = TextNormalizer.normalize_for_matching(abbr)
                    if re.search(rf'\b{re.escape(abbr_normalized)}\b', text_normalized):
                        return True, 0.60  # Low confidence for ambiguous
        
        # Check aliases (medium-high confidence)
        for alias in self.aliases:
            alias_normalized = TextNormalizer.normalize_for_matching(alias)
            if alias_normalized in text_normalized:
                # Check if alias might be a city name conflict
                if self._is_city_conflict(alias):
                    return True, 0.75  # Lower confidence for city names
                return True, 0.90
        
        return False, 0.0
    
    def _is_city_conflict(self, alias: str) -> bool:
        """Check if alias could be confused with a city name."""
        city_names = ['جدة', 'الرياض', 'مكة', 'المدينة', 'الدمام', 'الطائف', 'تبوك', 'أبها']
        return TextNormalizer.normalize_for_matching(alias) in [
            TextNormalizer.normalize_for_matching(city) for city in city_names
        ]
    
    def get_primary_name(self) -> str:
        """Get the primary Arabic name."""
        return self.name_ar
    
    def extract_college(self, text: str) -> Optional[College]:
        """Extract college from text."""
        for college in self.colleges:
            if college.matches(text):
                return college
        return None
    
    def extract_department(self, text: str) -> Optional[Department]:
        """Extract department from text."""
        for college in self.colleges:
            for dept in college.departments if hasattr(college, 'departments') else []:
                if dept.matches(text):
                    return dept
        return None


# ============================================================================
# ENHANCED UNIVERSITY DATABASE
# ============================================================================

class AcademicStructures:
    """Common academic structures across Saudi universities."""
    
    # Common colleges
    COLLEGES = {
        "medicine": College(
            name="كلية الطب",
            keywords=["كلية الطب", "الطب", "طب", "medicine", "medical"]
        ),
        "engineering": College(
            name="كلية الهندسة",
            keywords=["كلية الهندسة", "الهندسة", "هندسة", "engineering"]
        ),
        "computer_science": College(
            name="كلية الحاسبات وتقنية المعلومات",
            keywords=[
                "كلية الحاسبات", "الحاسبات", "حاسبات", "تقنية المعلومات",
                "علوم الحاسب", "computer science", "علوم الحاسوب",
                "كلية الحاسب", "الحاسب الآلي", "الحاسب الالي"
            ]
        ),
        "business": College(
            name="كلية إدارة الأعمال",
            keywords=["كلية إدارة الأعمال", "إدارة الأعمال", "ادارة الاعمال",
                     "business", "الإدارة", "الادارة"]
        ),
        "pharmacy": College(
            name="كلية الصيدلة",
            keywords=["كلية الصيدلة", "الصيدلة", "صيدلة", "pharmacy"]
        ),
        "dentistry": College(
            name="كلية طب الأسنان",
            keywords=["كلية طب الأسنان", "طب الأسنان", "طب الاسنان", "dentistry"]
        ),
        "nursing": College(
            name="كلية التمريض",
            keywords=["كلية التمريض", "التمريض", "تمريض", "nursing"]
        ),
        "science": College(
            name="كلية العلوم",
            keywords=["كلية العلوم", "العلوم", "science"]
        ),
        "education": College(
            name="كلية التربية",
            keywords=["كلية التربية", "التربية", "تربية", "education"]
        ),
        "law": College(
            name="كلية الحقوق",
            keywords=["كلية الحقوق", "الحقوق", "حقوق", "law", "القانون"]
        ),
        "sharia": College(
            name="كلية الشريعة",
            keywords=["كلية الشريعة", "الشريعة", "شريعة", "الدراسات الإسلامية"]
        ),
        "arts": College(
            name="كلية الآداب",
            keywords=["كلية الآداب", "الآداب", "الاداب", "arts"]
        ),
        "applied_medical": College(
            name="كلية العلوم الطبية التطبيقية",
            keywords=["العلوم الطبية", "العلوم الطبية التطبيقية"]
        ),
        "architecture": College(
            name="كلية العمارة والتخطيط",
            keywords=["كلية العمارة", "العمارة", "عمارة", "التخطيط", "architecture"]
        ),
    }
    
    # Common departments
    DEPARTMENTS = {
        "software_engineering": Department(
            name="هندسة البرمجيات",
            keywords=["هندسة البرمجيات", "software engineering"],
            college_keywords=["الحاسبات", "الحاسب", "علوم الحاسب"]
        ),
        "computer_science_dept": Department(
            name="علوم الحاسب",
            keywords=["علوم الحاسب", "علوم الحاسوب", "computer science"],
            college_keywords=["الحاسبات", "الحاسب"]
        ),
        "information_systems": Department(
            name="نظم المعلومات",
            keywords=["نظم المعلومات", "information systems"],
            college_keywords=["الحاسبات", "الحاسب"]
        ),
        "artificial_intelligence": Department(
            name="الذكاء الاصطناعي",
            keywords=["الذكاء الاصطناعي", "ذكاء اصطناعي", "AI"],
            college_keywords=["الحاسبات", "الحاسب"]
        ),
        "civil_engineering": Department(
            name="الهندسة المدنية",
            keywords=["الهندسة المدنية", "مدني", "civil engineering"],
            college_keywords=["الهندسة"]
        ),
        "electrical_engineering": Department(
            name="الهندسة الكهربائية",
            keywords=["الهندسة الكهربائية", "كهرباء", "electrical"],
            college_keywords=["الهندسة"]
        ),
        "mechanical_engineering": Department(
            name="الهندسة الميكانيكية",
            keywords=["الهندسة الميكانيكية", "ميكانيكا", "mechanical"],
            college_keywords=["الهندسة"]
        ),
        "accounting": Department(
            name="المحاسبة",
            keywords=["المحاسبة", "محاسبة", "accounting"],
            college_keywords=["إدارة الأعمال", "الادارة"]
        ),
        "marketing": Department(
            name="التسويق",
            keywords=["التسويق", "تسويق", "marketing"],
            college_keywords=["إدارة الأعمال", "الادارة"]
        ),
        "islamic_studies": Department(
            name="الدراسات الإسلامية",
            keywords=["الدراسات الإسلامية", "الدراسات الاسلامية"],
            college_keywords=["الشريعة", "التربية"]
        ),
        "arabic": Department(
            name="اللغة العربية",
            keywords=["اللغة العربية", "عربي", "arabic"],
            college_keywords=["الآداب", "التربية"]
        ),
        "english": Department(
            name="اللغة الإنجليزية",
            keywords=["اللغة الإنجليزية", "اللغة الانجليزية", "انجليزي", "english"],
            college_keywords=["الآداب", "التربية"]
        ),
    }
    
    # Group type detection patterns
    GROUP_TYPE_PATTERNS = {
        GroupType.STUDENTS_MALE: ["طلاب", "طلبة", "students", "شباب"],
        GroupType.STUDENTS_FEMALE: ["طالبات", "بنات", "فتيات"],
        GroupType.MIXED: ["طلاب وطالبات", "طلبة وطالبات", "الجميع"],
        GroupType.GRADUATES: ["خريجين", "خريجون", "خريجات", "graduates", "alumni"],
        GroupType.FACULTY: ["هيئة تدريس", "أعضاء هيئة التدريس", "دكاترة", "faculty"],
        GroupType.STAFF: ["موظفين", "موظفات", "إداريين", "staff"],
        GroupType.ANNOUNCEMENTS: ["إعلانات", "اعلانات", "أخبار", "announcements"],
        GroupType.POSTGRADUATE: ["دراسات عليا", "ماجستير", "دكتوراه", "postgraduate"],
        GroupType.COURSE_SPECIFIC: ["مقرر", "كورس", "مادة", "course"],
    }
    
    # Academic level detection patterns
    ACADEMIC_LEVEL_PATTERNS = {
        AcademicLevel.PREPARATORY: ["تحضيري", "السنة التحضيرية", "تحضيرية"],
        AcademicLevel.LEVEL_1: ["المستوى الأول", "المستوى الاول", "مستوى أول", "مستوى 1"],
        AcademicLevel.LEVEL_2: ["المستوى الثاني", "مستوى ثاني", "مستوى 2"],
        AcademicLevel.LEVEL_3: ["المستوى الثالث", "مستوى ثالث", "مستوى 3"],
        AcademicLevel.LEVEL_4: ["المستوى الرابع", "مستوى رابع", "مستوى 4"],
        AcademicLevel.LEVEL_5: ["المستوى الخامس", "مستوى خامس", "مستوى 5"],
        AcademicLevel.LEVEL_6: ["المستوى السادس", "مستوى سادس", "مستوى 6"],
        AcademicLevel.LEVEL_7: ["المستوى السابع", "مستوى سابع", "مستوى 7"],
        AcademicLevel.LEVEL_8: ["المستوى الثامن", "مستوى ثامن", "مستوى 8"],
        AcademicLevel.SENIOR: ["سنة التخرج", "تخرج", "متوقع تخرج", "senior"],
        AcademicLevel.INTERNSHIP: ["امتياز", "سنة الامتياز", "internship"],
        AcademicLevel.ALUMNI: ["خريج", "متخرج", "alumni"],
        AcademicLevel.FRESHMAN: ["دفعة جديدة", "مستجد", "جديد", "freshman"],
    }


# ============================================================================
# COMPREHENSIVE SAUDI UNIVERSITIES DATABASE
# ============================================================================

class SaudiUniversities:
    """Complete database of all Saudi universities with corrected data."""
    
    @staticmethod
    def _create_university(name_ar, name_en, abbreviations, aliases, **kwargs):
        """Factory method to create University with proper initialization."""
        uni = University(
            name_ar=name_ar,
            name_en=name_en,
            abbreviations=abbreviations,
            aliases=aliases,
            **kwargs
        )
        # Add colleges
        uni.colleges = list(AcademicStructures.COLLEGES.values())
        return uni
    
    UNIVERSITIES = [
        _create_university(
            name_ar="جامعة أم القرى",
            name_en="Umm Al-Qura University",
            abbreviations=["UQU"],
            aliases=["أم القرى", "ام القرى"]
        ),
        _create_university(
            name_ar="الجامعة الإسلامية",
            name_en="Islamic University of Madinah",
            abbreviations=["IU"],
            aliases=["الجامعة الاسلامية", "المدينة المنورة"]
        ),
        _create_university(
            name_ar="جامعة الإمام محمد بن سعود الإسلامية",
            name_en="Imam Muhammad ibn Saud Islamic University",
            abbreviations=["IMSIU"],
            aliases=["الإمام", "امام"]
        ),
        _create_university(
            name_ar="جامعة الملك سعود",
            name_en="King Saud University",
            abbreviations=["KSU"],
            aliases=["الملك سعود"]
        ),
        _create_university(
            name_ar="جامعة الملك عبدالعزيز",
            name_en="King Abdulaziz University",
            abbreviations=["KAU"],
            aliases=["الملك عبدالعزيز", "عبدالعزيز"]  # Removed "جامعة جدة"
        ),
        _create_university(
            name_ar="جامعة الملك فهد للبترول والمعادن",
            name_en="King Fahd University of Petroleum and Minerals",
            abbreviations=["KFUPM"],
            aliases=["البترول", "المعادن"]
        ),
        _create_university(
            name_ar="جامعة الملك فيصل",
            name_en="King Faisal University",
            abbreviations=["KFU"],
            aliases=["الملك فيصل", "الأحساء", "الاحساء"]
        ),
        _create_university(
            name_ar="جامعة الملك خالد",
            name_en="King Khalid University",
            abbreviations=["KKU"],
            aliases=["الملك خالد", "أبها", "ابها"]
        ),
        _create_university(
            name_ar="جامعة القصيم",
            name_en="Qassim University",
            abbreviations=["QU"],
            aliases=["القصيم"]
        ),
        _create_university(
            name_ar="جامعة طيبة",
            name_en="Taibah University",
            abbreviations=["TU"],  # Will be flagged as ambiguous
            aliases=["طيبة", "المدينة المنورة"]
        ),
        _create_university(
            name_ar="جامعة الطائف",
            name_en="Taif University",
            abbreviations=["TU"],  # Will be flagged as ambiguous
            aliases=["الطائف"]
        ),
        _create_university(
            name_ar="جامعة حائل",
            name_en="University of Hail",
            abbreviations=["UOH"],
            aliases=["حائل"]
        ),
        _create_university(
            name_ar="جامعة جازان",
            name_en="Jazan University",
            abbreviations=["JAZANU"],
            aliases=["جازان"]
        ),
        _create_university(
            name_ar="جامعة الجوف",
            name_en="Jouf University",
            abbreviations=["JU"],
            aliases=["الجوف"]
        ),
        _create_university(
            name_ar="جامعة الباحة",
            name_en="Al Baha University",
            abbreviations=["BU"],
            aliases=["الباحة"]
        ),
        _create_university(
            name_ar="جامعة تبوك",
            name_en="University of Tabuk",
            abbreviations=["UT"],
            aliases=["تبوك"]
        ),
        _create_university(
            name_ar="جامعة نجران",
            name_en="Najran University",
            abbreviations=["NU"],
            aliases=["نجران"]
        ),
        _create_university(
            name_ar="جامعة الحدود الشمالية",
            name_en="Northern Border University",
            abbreviations=["NBU"],
            aliases=["الحدود الشمالية", "عرعر"]
        ),
        _create_university(
            name_ar="جامعة الأميرة نورة بنت عبدالرحمن",
            name_en="Princess Nourah Bint Abdulrahman University",
            abbreviations=["PNU"],
            aliases=["الأميرة نورة", "الاميرة نورة"]
        ),
        _create_university(
            name_ar="جامعة الإمام عبدالرحمن بن فيصل",
            name_en="Imam Abdulrahman Bin Faisal University",
            abbreviations=["IAU"],
            aliases=["الإمام عبدالرحمن", "امام عبدالرحمن", "الدمام"]
        ),
        _create_university(
            name_ar="جامعة الملك عبدالله للعلوم والتقنية",
            name_en="King Abdullah University of Science and Technology",
            abbreviations=["KAUST"],
            aliases=["الملك عبدالله", "ثول"]
        ),
        _create_university(
            name_ar="جامعة الأمير سطام بن عبدالعزيز",
            name_en="Prince Sattam Bin Abdulaziz University",
            abbreviations=["PSAU"],
            aliases=["الأمير سطام", "الامير سطام", "الخرج"]
        ),
        _create_university(
            name_ar="جامعة شقراء",
            name_en="Shaqra University",
            abbreviations=["SU"],
            aliases=["شقراء"]
        ),
        _create_university(
            name_ar="جامعة المجمعة",
            name_en="Majmaah University",
            abbreviations=["MU"],
            aliases=["المجمعة"]
        ),
        _create_university(
            name_ar="الجامعة السعودية الإلكترونية",
            name_en="Saudi Electronic University",
            abbreviations=["SEU"],
            aliases=["السعودية الإلكترونية", "الالكترونية"]
        ),
        _create_university(
            name_ar="جامعة جدة",
            name_en="University of Jeddah",
            abbreviations=["UJ"],
            aliases=["جدة"]  # This is correct - جامعة جدة exists independently
        ),
        _create_university(
            name_ar="جامعة بيشة",
            name_en="University of Bisha",
            abbreviations=["UB"],
            aliases=["بيشة"]
        ),
        _create_university(
            name_ar="جامعة حفر الباطن",
            name_en="University of Hafr Al Batin",
            abbreviations=["UHB"],
            aliases=["حفر الباطن"]
        ),
        _create_university(
            name_ar="جامعة الأمير محمد بن فهد",
            name_en="Prince Mohammad Bin Fahd University",
            abbreviations=["PMU"],
            aliases=["الأمير محمد بن فهد", "الامير محمد بن فهد"]
        ),
        _create_university(
            name_ar="جامعة اليمامة",
            name_en="Al Yamamah University",
            abbreviations=["YU"],
            aliases=["اليمامة"]
        ),
        _create_university(
            name_ar="جامعة الفيصل",
            name_en="Alfaisal University",
            abbreviations=["AU"],
            aliases=["الفيصل"]
        ),
        _create_university(
            name_ar="جامعة دار العلوم",
            name_en="Dar Al Uloom University",
            abbreviations=["DAU"],
            aliases=["دار العلوم"]
        ),
        _create_university(
            name_ar="جامعة عفت",
            name_en="Effat University",
            abbreviations=["EU"],
            aliases=["عفت"]
        ),
    ]
    
    # Track ambiguous abbreviations
    AMBIGUOUS_ABBREVIATIONS = {}
    
    @classmethod
    def _initialize_abbreviation_tracking(cls):
        """Identify and track ambiguous abbreviations."""
        abbr_count = {}
        
        for uni in cls.UNIVERSITIES:
            for abbr in uni.abbreviations:
                if abbr not in abbr_count:
                    abbr_count[abbr] = []
                abbr_count[abbr].append(uni.name_ar)
        
        # Find ambiguous ones
        cls.AMBIGUOUS_ABBREVIATIONS = {
            abbr: unis for abbr, unis in abbr_count.items()
            if len(unis) > 1
        }
        
        # Mark universities with ambiguous abbreviations
        for uni in cls.UNIVERSITIES:
            uni._abbr_unique_map = {}
            for abbr in uni.abbreviations:
                uni._abbr_unique_map[abbr] = abbr not in cls.AMBIGUOUS_ABBREVIATIONS
    
    @classmethod
    def detect_university(cls, text: str, confidence_threshold: float = 0.80) -> Tuple[Optional[University], float]:
        """
        Detect university with confidence scoring.
        
        Args:
            text: Text to analyze
            confidence_threshold: Minimum confidence to accept (0.0 to 1.0)
            
        Returns:
            Tuple of (detected_university_or_None, confidence_score)
        """
        if not text:
            return None, 0.0
        
        best_match = None
        best_confidence = 0.0
        
        for university in cls.UNIVERSITIES:
            matched, confidence = university.matches(text, use_ambiguous=False)
            
            if matched and confidence > best_confidence:
                best_match = university
                best_confidence = confidence
        
        # Only return if above threshold
        if best_confidence >= confidence_threshold:
            return best_match, best_confidence
        
        # If no match found with high confidence, try with ambiguous abbreviations
        if best_confidence < confidence_threshold:
            for university in cls.UNIVERSITIES:
                matched, confidence = university.matches(text, use_ambiguous=True)
                if matched and confidence > best_confidence:
                    best_match = university
                    best_confidence = confidence
        
        if best_confidence >= confidence_threshold:
            return best_match, best_confidence
        
        return None, best_confidence
    
    @classmethod
    def get_ambiguous_abbreviation_info(cls, abbr: str) -> Optional[List[str]]:
        """Get list of universities sharing an ambiguous abbreviation."""
        return cls.AMBIGUOUS_ABBREVIATIONS.get(abbr.upper())


# Initialize abbreviation tracking
SaudiUniversities._initialize_abbreviation_tracking()


# ============================================================================
# CONTEXT EXTRACTION
# ============================================================================

class ContextExtractor:
    """Extracts comprehensive context information from text."""
    
    @classmethod
    def extract_group_type(cls, text: str) -> GroupType:
        """Extract group type from text."""
        text_normalized = TextNormalizer.normalize_for_matching(text)
        
        for group_type, patterns in AcademicStructures.GROUP_TYPE_PATTERNS.items():
            if any(pattern in text_normalized for pattern in patterns):
                return group_type
        
        return GroupType.UNKNOWN
    
    @classmethod
    def extract_academic_level(cls, text: str) -> AcademicLevel:
        """Extract academic level from text."""
        text_normalized = TextNormalizer.normalize_for_matching(text)
        
        for level, patterns in AcademicStructures.ACADEMIC_LEVEL_PATTERNS.items():
            if any(pattern in text_normalized for pattern in patterns):
                return level
        
        return AcademicLevel.UNKNOWN
    
    @classmethod
    def extract_college(cls, text: str) -> Optional[College]:
        """Extract college from text."""
        text_normalized = TextNormalizer.normalize_for_matching(text)
        
        for college in AcademicStructures.COLLEGES.values():
            if college.matches(text_normalized):
                return college
        
        return None
    
    @classmethod
    def extract_department(cls, text: str) -> Optional[Department]:
        """Extract department from text."""
        text_normalized = TextNormalizer.normalize_for_matching(text)
        
        for dept in AcademicStructures.DEPARTMENTS.values():
            if dept.matches(text_normalized):
                return dept
        
        return None
    
    @classmethod
    def extract_full_context(cls, text: str) -> Dict:
        """Extract complete context information from text."""
        return {
            "group_type": cls.extract_group_type(text),
            "academic_level": cls.extract_academic_level(text),
            "college": cls.extract_college(text),
            "department": cls.extract_department(text),
        }


# ============================================================================
# DATABASE MANAGER (ENHANCED)
# ============================================================================

class DatabaseManager:
    """Enhanced database manager with support for all context information."""
    
    def __init__(self, db_path: str = "university_context.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create comprehensive database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main groups table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_universities (
                    chat_id INTEGER PRIMARY KEY,
                    group_name TEXT NOT NULL,
                    group_description TEXT,
                    university_name TEXT NOT NULL,
                    university_confidence REAL DEFAULT 1.0,
                    college_name TEXT,
                    department_name TEXT,
                    group_type TEXT,
                    academic_level TEXT,
                    auto_detected BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Group name change history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_name_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    old_name TEXT,
                    new_name TEXT,
                    changed_at TEXT NOT NULL,
                    FOREIGN KEY (chat_id) REFERENCES group_universities (chat_id)
                )
            """)
            
            conn.commit()
    
    def set_university(self, chat_id: int, group_name: str, university_name: str,
                      confidence: float = 1.0, college: str = None, department: str = None,
                      group_type: str = None, academic_level: str = None,
                      auto_detected: bool = True, description: str = None):
        """Save comprehensive university context."""
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO group_universities 
                (chat_id, group_name, group_description, university_name, university_confidence,
                 college_name, department_name, group_type, academic_level,
                 auto_detected, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    group_name = excluded.group_name,
                    group_description = excluded.group_description,
                    university_name = excluded.university_name,
                    university_confidence = excluded.university_confidence,
                    college_name = excluded.college_name,
                    department_name = excluded.department_name,
                    group_type = excluded.group_type,
                    academic_level = excluded.academic_level,
                    auto_detected = excluded.auto_detected,
                    updated_at = excluded.updated_at
            """, (chat_id, group_name, description, university_name, confidence,
                  college, department, group_type, academic_level,
                  auto_detected, now, now))
            conn.commit()
    
    def get_full_context(self, chat_id: int) -> Optional[Dict]:
        """Get complete context for a group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chat_id, group_name, group_description, university_name,
                       university_confidence, college_name, department_name,
                       group_type, academic_level, auto_detected,
                       created_at, updated_at
                FROM group_universities
                WHERE chat_id = ?
            """, (chat_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "chat_id": row[0],
                    "group_name": row[1],
                    "group_description": row[2],
                    "university_name": row[3],
                    "university_confidence": row[4],
                    "college_name": row[5],
                    "department_name": row[6],
                    "group_type": row[7],
                    "academic_level": row[8],
                    "auto_detected": bool(row[9]),
                    "created_at": row[10],
                    "updated_at": row[11]
                }
            return None
    
    def log_name_change(self, chat_id: int, old_name: str, new_name: str):
        """Log group name changes."""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO group_name_history (chat_id, old_name, new_name, changed_at)
                VALUES (?, ?, ?, ?)
            """, (chat_id, old_name, new_name, now))
            conn.commit()


# ============================================================================
# ENHANCED UNIVERSITY CONTEXT MANAGER
# ============================================================================

class UniversityContextManager:
    """Professional context manager with comprehensive features."""
    
    def __init__(self, db_path: str = "university_context.db"):
        self.db = DatabaseManager(db_path)
        self.extractor = ContextExtractor()
    
    def detect_from_group_info(self, group_name: str, group_description: str = None) -> Tuple[Optional[University], float]:
        """
        Detect university from both group name and description.
        
        Returns:
            Tuple of (university_or_None, confidence)
        """
        # Try name first (higher weight)
        uni_from_name, conf_name = SaudiUniversities.detect_university(group_name)
        
        # Try description
        uni_from_desc = None
        conf_desc = 0.0
        if group_description:
            uni_from_desc, conf_desc = SaudiUniversities.detect_university(group_description)
        
        # Combined detection logic
        if uni_from_name and conf_name >= 0.90:
            return uni_from_name, conf_name
        
        if uni_from_desc and conf_desc >= 0.90:
            return uni_from_desc, conf_desc
        
        # If both low confidence, return the better one
        if conf_name > conf_desc:
            return uni_from_name, conf_name
        else:
            return uni_from_desc, conf_desc
    
    def extract_group_context(self, group_name: str, group_description: str = None) -> Dict:
        """Extract comprehensive context from group info."""
        combined_text = group_name
        if group_description:
            combined_text += " " + group_description
        
        return self.extractor.extract_full_context(combined_text)
    
    def handle_new_group(self, chat_id: int, group_name: str, group_description: str = None) -> Tuple[bool, Optional[str], float]:
        """
        Handle bot addition to a new group.
        
        Returns:
            Tuple of (detected_successfully, university_name, confidence)
        """
        # Try detection
        university, confidence = self.detect_from_group_info(group_name, group_description)
        
        if university and confidence >= 0.80:
            # Extract additional context
            context = self.extract_group_context(group_name, group_description)
            
            # Save to database
            self.db.set_university(
                chat_id=chat_id,
                group_name=group_name,
                university_name=university.get_primary_name(),
                confidence=confidence,
                college=context["college"].name if context["college"] else None,
                department=context["department"].name if context["department"] else None,
                group_type=context["group_type"].value if context["group_type"] != GroupType.UNKNOWN else None,
                academic_level=context["academic_level"].value if context["academic_level"] != AcademicLevel.UNKNOWN else None,
                auto_detected=True,
                description=group_description
            )
            
            logger.info(f"Auto-detected {university.get_primary_name()} for {group_name} (confidence: {confidence:.2%})")
            return True, university.get_primary_name(), confidence
        else:
            logger.info(f"Could not auto-detect university for {group_name}")
            return False, None, confidence
    
    def handle_group_rename(self, chat_id: int, old_name: str, new_name: str):
        """Handle group title changes."""
        # Log the change
        self.db.log_name_change(chat_id, old_name, new_name)
        
        # Try to re-detect
        university, confidence = self.detect_from_group_info(new_name)
        
        if university and confidence >= 0.80:
            context = self.extract_group_context(new_name)
            self.db.set_university(
                chat_id=chat_id,
                group_name=new_name,
                university_name=university.get_primary_name(),
                confidence=confidence,
                college=context["college"].name if context["college"] else None,
                department=context["department"].name if context["department"] else None,
                group_type=context["group_type"].value if context["group_type"] != GroupType.UNKNOWN else None,
                academic_level=context["academic_level"].value if context["academic_level"] != AcademicLevel.UNKNOWN else None,
                auto_detected=True
            )
            logger.info(f"Re-detected university after rename: {university.get_primary_name()}")
    
    def should_process_message(self, chat_id: int, message_text: str, chat_type: str) -> Tuple[bool, str]:
        """
        Determine if a message should be processed.
        
        Returns:
            Tuple of (should_process, reason_or_context)
        """
        if chat_type == "private":
            return True, ""
        
        group_context = self.db.get_full_context(chat_id)
        
        if not group_context:
            return False, (
                "⚠️ لم يتم تحديد الجامعة لهذه المجموعة بعد.\n"
                "يمكن للمشرفين استخدام الأمر:\n"
                "/set_university اسم الجامعة"
            )
        
        # Check if message mentions another university
        mentioned_uni, confidence = SaudiUniversities.detect_university(message_text, confidence_threshold=0.70)
        
        if mentioned_uni and confidence >= 0.70 and mentioned_uni.get_primary_name() != group_context["university_name"]:
            return False, (
                f"❌ هذه المجموعة مخصصة لـ **{group_context['university_name']}** فقط.\n\n"
                f"لا يمكنني الإجابة عن أسئلة تخص **{mentioned_uni.get_primary_name()}** هنا.\n\n"
                "📌 يرجى:\n"
                "• طرح سؤالك في مجموعة الجامعة المعنية\n"
                "• أو مراسلتي في الخاص للإجابة عن أي جامعة"
            )
        
        return True, group_context
    
    def get_gemini_context(self, group_context: Dict) -> str:
        """Generate comprehensive Gemini context."""
        context_parts = [
            f"Current University:\n{group_context['university_name']}"
        ]
        
        if group_context.get('college_name'):
            context_parts.append(f"College:\n{group_context['college_name']}")
        
        if group_context.get('department_name'):
            context_parts.append(f"Department:\n{group_context['department_name']}")
        
        if group_context.get('group_type'):
            context_parts.append(f"Group Type:\n{group_context['group_type']}")
        
        if group_context.get('academic_level'):
            context_parts.append(f"Academic Level:\n{group_context['academic_level']}")
        
        context_parts.append("Chat Type:\nUniversity Group")
        context_parts.append(f"The Telegram group belongs to {group_context['university_name']}.")
        context_parts.append("Never answer according to any other Saudi university.")
        context_parts.append("If the user asks about another university, politely refuse.")
        context_parts.append("If the question is general and unrelated to university regulations, answer normally.")
        context_parts.append(f"If the question is university-specific, answer only according to {group_context['university_name']}.")
        
        return "\n\n".join(context_parts)


# ============================================================================
# BOT INTEGRATION (ENHANCED)
# ============================================================================

class BotIntegration:
    """Enhanced bot integration with comprehensive features."""
    
    def __init__(self, context_manager: UniversityContextManager):
        self.manager = context_manager
    
    async def handle_bot_added_to_group(self, chat_id: int, group_name: str, group_description: str = None):
        """Enhanced handler for bot addition."""
        detected, uni_name, confidence = self.manager.handle_new_group(
            chat_id, group_name, group_description
        )
        
        if detected:
            if confidence >= 0.95:
                return f"✅ تم اكتشاف الجامعة تلقائياً: **{uni_name}** (دقة عالية)"
            elif confidence >= 0.80:
                # Check if there's ambiguity
                university, _ = SaudiUniversities.detect_university(group_name)
                if university:
                    ambig_abbrs = [abbr for abbr in university.abbreviations 
                                  if abbr in SaudiUniversities.AMBIGUOUS_ABBREVIATIONS]
                    if ambig_abbrs:
                        other_unis = SaudiUniversities.get_ambiguous_abbreviation_info(ambig_abbrs[0])
                        return (
                            f"✅ تم اكتشاف: **{uni_name}**\n\n"
                            f"⚠️ لكن يوجد تشابه مع: {', '.join(other_unis)}\n"
                            "إذا كانت الجامعة خاطئة، استخدم:\n"
                            f"/set_university اسم الجامعة الصحيح"
                        )
                
                return f"✅ تم اكتشاف الجامعة: **{uni_name}**"
            
            return f"✅ تم اكتشاف الجامعة: **{uni_name}** (بثقة {confidence:.0%})"
        else:
            return (
                "👋 لم أتمكن من تحديد الجامعة تلقائياً.\n\n"
                "📌 استخدم: /set_university اسم الجامعة"
            )
    
    async def handle_set_university(self, chat_id: int, group_name: str, 
                                   university_name: str, is_admin: bool,
                                   group_description: str = None):
        """Enhanced set university handler."""
        if not is_admin:
            return "❌ هذا الأمر متاح للمشرفين فقط."
        
        if not university_name:
            return "❌ يرجى تحديد اسم الجامعة.\nمثال: /set_university جامعة الطائف"
        
        university, confidence = SaudiUniversities.detect_university(university_name)
        
        if university:
            # Extract context
            context = self.manager.extract_group_context(group_name, group_description)
            
            self.manager.db.set_university(
                chat_id=chat_id,
                group_name=group_name,
                university_name=university.get_primary_name(),
                confidence=1.0,  # Manual setting = 100% confidence
                college=context["college"].name if context["college"] else None,
                department=context["department"].name if context["department"] else None,
                group_type=context["group_type"].value if context["group_type"] != GroupType.UNKNOWN else None,
                academic_level=context["academic_level"].value if context["academic_level"] != AcademicLevel.UNKNOWN else None,
                auto_detected=False,
                description=group_description
            )
            
            return f"✅ تم تعيين الجامعة: **{university.get_primary_name()}**"
        else:
            return "❌ لم يتم التعرف على الجامعة. استخدم /list_universities"
    
    async def handle_message(self, chat_id: int, message_text: str, chat_type: str):
        """
        Enhanced message handler.
        
        Returns:
            Tuple of (should_send_to_gemini, context_or_message, is_error)
        """
        should_process, result = self.manager.should_process_message(
            chat_id, message_text, chat_type
        )
        
        if not should_process:
            return False, result, False
        
        if chat_type == "private":
            mentioned_uni, confidence = SaudiUniversities.detect_university(message_text)
            if mentioned_uni and confidence >= 0.70:
                context = self.manager.get_gemini_context({
                    "university_name": mentioned_uni.get_primary_name()
                })
            else:
                context = "You are a helpful assistant for Saudi university students."
            return True, context, False
        
        # Group chat with context
        group_context = result  # This is the full context dict
        context = self.manager.get_gemini_context(group_context)
        return True, context, False
    
    async def handle_group_rename(self, chat_id: int, old_name: str, new_name: str):
        """Handle group title changes."""
        self.manager.handle_group_rename(chat_id, old_name, new_name)
        # Could optionally send a notification about redetection
