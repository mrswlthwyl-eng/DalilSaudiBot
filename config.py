==========================================================

config.py

Dalili Saudi Bot

Professional Configuration

Version : 2.0.0

==========================================================

import os
from pathlib import Path

==========================================================

Project Information

==========================================================

PROJECT_NAME = "Dalili Saudi Bot"

PROJECT_NAME_AR = "دليلي الجامعي"

BOT_NAME = "دليلي الجامعي"

BOT_USERNAME = "@DalilSaudiBot"

VERSION = "2.0.0"

DEVELOPER_AR = "سديم للتقنيات الرقمية"

DEVELOPER_EN = "SADEEM Digital Technologies"

DEFAULT_LANGUAGE = "ar"

TIMEZONE = "Asia/Riyadh"

ENVIRONMENT = os.getenv(
"ENVIRONMENT",
"production"
)

==========================================================

Project Directories

==========================================================

BASE_DIR = Path(file).resolve().parent

DATA_DIR = BASE_DIR / "data"

KNOWLEDGE_DIR = BASE_DIR / "knowledge"

UNIVERSITIES_DIR = BASE_DIR / "universities"

CACHE_DIR = BASE_DIR / "cache"

LOGS_DIR = BASE_DIR / "logs"

BACKUP_DIR = BASE_DIR / "backups"

TEMP_DIR = BASE_DIR / "temp"

EXPORT_DIR = BASE_DIR / "exports"

MODELS_DIR = BASE_DIR / "models"

PROMPTS_DIR = BASE_DIR / "prompts"

==========================================================

Telegram

==========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = os.getenv("OWNER_ID")

BOT_ADMINS = []

==========================================================

AI Engine

==========================================================

PRIMARY_PROVIDER = "gemini"

AUTO_PROVIDER_SELECTION = True

AUTO_FALLBACK = True

AUTO_ROTATE_PROVIDER = True

SKIP_PROVIDER_IF_NO_API_KEY = True

SKIP_PROVIDER_IF_TIMEOUT = True

SKIP_PROVIDER_IF_RATE_LIMIT = True

SKIP_PROVIDER_IF_ERROR = True

ENABLE_PROVIDER_HEALTH_CHECK = True

ENABLE_PROVIDER_STATISTICS = True

AI_PRIORITY = [

"gemini",  

"openai",  

"claude",  

"deepseek",  

"qwen",  

"grok",  

"openrouter",  

"ollama",  

"mistral",  

"cohere",  

"perplexity"

]

==========================================================

API Keys

==========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

QWEN_API_KEY = os.getenv("QWEN_API_KEY")

GROK_API_KEY = os.getenv("GROK_API_KEY")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

COHERE_API_KEY = os.getenv("COHERE_API_KEY")

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

OLLAMA_HOST = os.getenv(
"OLLAMA_HOST",
"http://localhost:11434"
)

==========================================================

Default Models

==========================================================

GEMINI_MODEL = os.getenv(
"GEMINI_MODEL",
"gemini-3.6-flash"
)

OPENAI_MODEL = os.getenv(
"OPENAI_MODEL",
"gpt-5.5"
)

CLAUDE_MODEL = os.getenv(
"CLAUDE_MODEL",
"claude-sonnet-4"
)

DEEPSEEK_MODEL = os.getenv(
"DEEPSEEK_MODEL",
"deepseek-chat"
)

QWEN_MODEL = os.getenv(
"QWEN_MODEL",
"qwen-max"
)

GROK_MODEL = os.getenv(
"GROK_MODEL",
"grok-4"
)

OPENROUTER_MODEL = os.getenv(
"OPENROUTER_MODEL",
"openai/gpt-5.5"
)

MISTRAL_MODEL = os.getenv(
"MISTRAL_MODEL",
"mistral-large-latest"
)

COHERE_MODEL = os.getenv(
"COHERE_MODEL",
"command-r-plus"
)

PERPLEXITY_MODEL = os.getenv(
"PERPLEXITY_MODEL",
"sonar"
)

OLLAMA_MODEL = os.getenv(
"OLLAMA_MODEL",
"llama3"
)

==========================================================

AI Configuration

==========================================================

TEMPERATURE = 0.2

TOP_P = 0.95

TOP_K = 40

MAX_OUTPUT_TOKENS = 4096

REQUEST_TIMEOUT = 120

CONNECT_TIMEOUT = 30

READ_TIMEOUT = 120

MAX_RETRIES = 3

RETRY_DELAY = 2

ENABLE_STREAMING = False

ENABLE_CACHE = True

CACHE_TTL = 3600

MAX_CONTEXT_MESSAGES = 20

MAX_HISTORY_MESSAGES = 20

MAX_PROMPT_LENGTH = 50000

MAX_MESSAGE_LENGTH = 4000

==========================================================

Knowledge Base

==========================================================

USE_KNOWLEDGE_BASE = True

KNOWLEDGE_PRIORITY = [

"universities",  

"knowledge",  

"faq",  

"documents",  

"regulations",  

"training",  

"careers",  

"ai"

]

AUTO_UPDATE_KNOWLEDGE = False

USE_OFFICIAL_INFORMATION_PRIORITY = True

ENABLE_FAQ = True

ENABLE_REGULATIONS = True

ENABLE_STUDY_PLANS = True

ENABLE_TRAINING_DATA = True

ENABLE_SCHOLARSHIPS = True

ENABLE_DOCUMENTS = True

ENABLE_CAREERS = True

ENABLE_ADMISSIONS = True

ENABLE_ACADEMIC_CALENDAR = True

ENABLE_ELECTRONIC_SERVICES = True

ENABLE_POSTGRADUATE = True

ENABLE_TUITION_INFORMATION = True

ENABLE_CONTACT_INFORMATION = True

ENABLE_COLLEGES_INFORMATION = True

ENABLE_DEPARTMENTS_INFORMATION = True

ENABLE_CAMPUS_INFORMATION = True

==========================================================

University Detection

==========================================================

ENABLE_UNIVERSITY_DETECTION = True

AUTO_DETECT_FROM_MESSAGE = True

AUTO_DETECT_FROM_GROUP_NAME = True

AUTO_DETECT_FROM_GROUP_DESCRIPTION = True

AUTO_DETECT_FROM_USER_HISTORY = True

AUTO_DETECT_FROM_GROUP_SETTINGS = True

AUTO_DETECT_FROM_USERNAME = True

AUTO_DETECT_FROM_PROFILE = True

ASK_IF_UNIVERSITY_UNKNOWN = True

SAVE_USER_UNIVERSITY = True

SAVE_GROUP_UNIVERSITY = True

DEFAULT_UNIVERSITY = None

==========================================================

Telegram Behavior

==========================================================

REPLY_IN_PRIVATE = True

REPLY_IN_GROUPS = True

REPLY_TO_ALL_MESSAGES = True

REPLY_TO_REPLIES = True

REPLY_TO_MENTIONS_ONLY = False

SHOW_TYPING = True

DELETE_COMMAND_MESSAGES = False

ALLOW_FORWARD_MESSAGES = True

ALLOW_EDITED_MESSAGES = True

ALLOW_MEDIA = True

ALLOW_DOCUMENTS = True

ALLOW_PHOTOS = True

ALLOW_AUDIO = True

ALLOW_VIDEO = True

ALLOW_PDF = True

ALLOW_WORD = True

ALLOW_EXCEL = True

ALLOW_POWERPOINT = True

ALLOW_ZIP = False

ALLOW_RAR = False

==========================================================

Conversation Memory

==========================================================

ENABLE_MEMORY = True

SAVE_HISTORY = True

SAVE_USERS = True

SAVE_GROUPS = True

SAVE_LAST_PROVIDER = True

SAVE_LAST_MODEL = True

MAX_HISTORY = 20

MAX_MEMORY_DAYS = 30

AUTO_CLEAN_MEMORY = True

MEMORY_CLEANUP_INTERVAL = 86400

==========================================================

Search Configuration

==========================================================

ENABLE_SEARCH = True

SEARCH_TOP_RESULTS = 5

SEARCH_SIMILARITY_THRESHOLD = 0.75

SEARCH_MIN_SCORE = 0.50

SEARCH_IGNORE_CASE = True

SEARCH_USE_KEYWORDS = True

SEARCH_USE_SYNONYMS = True

==========================================================

JSON Files

==========================================================

USERS_FILE = DATA_DIR / "users.json"

GROUPS_FILE = DATA_DIR / "groups.json"

ALIASES_FILE = DATA_DIR / "aliases.json"

SETTINGS_FILE = DATA_DIR / "settings.json"

MEMORY_FILE = DATA_DIR / "memory.json"

SESSIONS_FILE = DATA_DIR / "sessions.json"

CACHE_FILE = DATA_DIR / "cache.json"

ANALYTICS_FILE = DATA_DIR / "analytics.json"

STATISTICS_FILE = DATA_DIR / "statistics.json"

PROVIDERS_FILE = DATA_DIR / "providers.json"

==========================================================

Knowledge Files

==========================================================

ADMISSIONS_FILE = KNOWLEDGE_DIR / "admissions.json"

MAJORS_FILE = KNOWLEDGE_DIR / "majors.json"

REGULATIONS_FILE = KNOWLEDGE_DIR / "regulations.json"

TRAINING_FILE = KNOWLEDGE_DIR / "training.json"

SCHOLARSHIPS_FILE = KNOWLEDGE_DIR / "scholarships.json"

GRADUATE_STUDIES_FILE = KNOWLEDGE_DIR / "graduate_studies.json"

ACADEMIC_CALENDAR_FILE = KNOWLEDGE_DIR / "academic_calendar.json"

ELECTRONIC_SERVICES_FILE = KNOWLEDGE_DIR / "electronic_services.json"

DOCUMENTS_FILE = KNOWLEDGE_DIR / "documents.json"

CAREERS_FILE = KNOWLEDGE_DIR / "careers.json"

FAQ_FILE = KNOWLEDGE_DIR / "faq.json"

COLLEGES_FILE = KNOWLEDGE_DIR / "colleges.json"

DEPARTMENTS_FILE = KNOWLEDGE_DIR / "departments.json"

UNIVERSITIES_INDEX_FILE = KNOWLEDGE_DIR / "universities.json"

CONTACTS_FILE = KNOWLEDGE_DIR / "contacts.json"

TUITION_FILE = KNOWLEDGE_DIR / "tuition.json"

SERVICES_FILE = KNOWLEDGE_DIR / "services.json"

==========================================================

Supported File Types

==========================================================

SUPPORTED_DOCUMENTS = [

".pdf",  

".doc",  

".docx",  

".ppt",  

".pptx",  

".xls",  

".xlsx",  

".txt",  

".csv",  

".json"

]

SUPPORTED_IMAGES = [

".jpg",  

".jpeg",  

".png",  

".webp"

]

SUPPORTED_AUDIO = [

".mp3",  

".wav",  

".ogg",  

".m4a"

]

==========================================================

Logging

==========================================================

ENABLE_LOGGING = True

LOG_LEVEL = "INFO"

LOG_TO_FILE = True

LOG_TO_CONSOLE = True

LOG_REQUESTS = True

LOG_RESPONSES = True

LOG_ERRORS = True

LOG_WARNINGS = True

LOG_AI_PROVIDER = True

LOG_AI_MODEL = True

LOG_RESPONSE_TIME = True

LOG_USER_ACTIVITY = True

LOG_GROUP_ACTIVITY = True

LOG_FILE_NAME = "dalili.log"

LOG_MAX_SIZE_MB = 20

LOG_BACKUP_COUNT = 10

==========================================================

Security

==========================================================

DEBUG = False

SAFE_MODE = True

HIDE_INTERNAL_ERRORS = True

ALLOW_SYSTEM_PROMPT_VIEW = False

ALLOW_PROMPT_EXPORT = False

ALLOW_DEBUG_COMMANDS = False

ALLOW_ADMIN_COMMANDS = True

ENABLE_INPUT_VALIDATION = True

ENABLE_OUTPUT_FILTERING = True

ENABLE_API_KEY_CHECK = True

ENABLE_REQUEST_SANITIZATION = True

BLOCK_EMPTY_MESSAGES = True

BLOCK_SPAM_MESSAGES = True

BLOCK_TOO_LONG_MESSAGES = True

BLOCK_UNKNOWN_FILE_TYPES = True

==========================================================

Cache

==========================================================

CACHE_ENABLED = True

CACHE_PROVIDER = "memory"

CACHE_MAX_SIZE = 1000

CACHE_EXPIRE_SECONDS = 3600

CACHE_CLEANUP_INTERVAL = 600

CACHE_AI_RESPONSES = True

CACHE_SEARCH_RESULTS = True

CACHE_KNOWLEDGE = True

CACHE_USERS = True

CACHE_GROUPS = True

==========================================================

Network

==========================================================

HTTP_TIMEOUT = 120

CONNECT_TIMEOUT = 30

READ_TIMEOUT = 120

WRITE_TIMEOUT = 120

POOL_TIMEOUT = 30

MAX_CONNECTIONS = 100

VERIFY_SSL = True

USER_AGENT = "DaliliSaudiBot/2.0"

FOLLOW_REDIRECTS = True

KEEP_ALIVE = True

==========================================================

Rate Limits

==========================================================

MAX_REQUESTS_PER_USER_PER_MINUTE = 30

MAX_REQUESTS_PER_GROUP_PER_MINUTE = 300

MAX_CONCURRENT_REQUESTS = 20

MAX_MESSAGE_LENGTH = 4000

MAX_PROMPT_LENGTH = 50000

MAX_FILE_SIZE_MB = 20

MAX_IMAGE_SIZE_MB = 10

MAX_DOCUMENT_SIZE_MB = 20

==========================================================

Sessions

==========================================================

SESSION_ENABLED = True

SESSION_TIMEOUT = 1800

SESSION_SAVE_CONTEXT = True

SESSION_AUTO_CLEAN = True

SESSION_MAX_PER_USER = 5

SESSION_RESTORE_AFTER_RESTART = True

==========================================================

Backup

==========================================================

BACKUP_ENABLED = True

BACKUP_INTERVAL_HOURS = 24

BACKUP_KEEP_DAYS = 30

BACKUP_COMPRESS = True

BACKUP_DATABASE = True

BACKUP_LOGS = True

BACKUP_KNOWLEDGE = True

BACKUP_DIRECTORY = BACKUP_DIR

==========================================================

Analytics

==========================================================

ENABLE_ANALYTICS = True

COUNT_USERS = True

COUNT_GROUPS = True

COUNT_MESSAGES = True

COUNT_AI_REQUESTS = True

COUNT_PROVIDER_USAGE = True

COUNT_MODEL_USAGE = True

COUNT_ERRORS = True

COUNT_RESPONSE_TIME = True

COUNT_SEARCHES = True

COUNT_FILE_UPLOADS = True

==========================================================

Feature Flags

==========================================================

ENABLE_IMAGE_ANALYSIS = False

ENABLE_DOCUMENT_ANALYSIS = False

ENABLE_WEB_SEARCH = False

ENABLE_TRANSLATION = False

ENABLE_CODE_ASSISTANT = False

ENABLE_SUMMARIZATION = True

ENABLE_TEXT_EXTRACTION = True

ENABLE_TABLE_ANALYSIS = True

ENABLE_SMART_ROUTING = True

ENABLE_PROVIDER_SWITCHING = True

ENABLE_CONTEXT_MEMORY = True

==========================================================

Future Features

==========================================================

ENABLE_RAG = False

ENABLE_VECTOR_DATABASE = False

ENABLE_EMBEDDINGS = False

ENABLE_AGENT_MODE = False

ENABLE_MULTI_AGENT = False

ENABLE_PLUGINS = False

ENABLE_API_SERVER = False

ENABLE_DASHBOARD = False

ENABLE_VOICE_CHAT = False

ENABLE_IMAGE_GENERATION = False

ENABLE_FINE_TUNING = False

==========================================================

Admin

==========================================================

ADMIN_IDS = []

SUPER_ADMIN_IDS = []

ALLOWED_GROUPS = []

BLOCKED_USERS = []

BLOCKED_GROUPS = []

READ_ONLY_GROUPS = []

==========================================================

Database

==========================================================

DATABASE_TYPE = "json"

DATABASE_URL = None

AUTO_CREATE_DATABASE = True

AUTO_SAVE_DATABASE = True

AUTO_SAVE_INTERVAL = 300

AUTO_BACKUP_DATABASE = True

==========================================================

Development

==========================================================

PRINT_STARTUP_INFO = True

PRINT_PROVIDER = True

PRINT_MODEL = True

PRINT_WARNINGS = True

AUTO_RELOAD = False

SHOW_DETAILED_ERRORS = False

ENABLE_PERFORMANCE_MONITOR = True

ENABLE_PROVIDER_BENCHMARK = True

ENABLE_DEBUG_TIMERS = False

==========================================================

AI Providers Configuration

==========================================================

AI_PROVIDERS = {

"gemini": {  
    "enabled": True,  
    "priority": 1,  
    "api_key": GEMINI_API_KEY,  
    "api_key_env": "GEMINI_API_KEY",  
    "model": GEMINI_MODEL,  
    "supports_stream": True,  
    "supports_images": True,  
    "supports_documents": True,  
    "supports_function_calling": True,  
    "supports_system_prompt": True,  
    "timeout": REQUEST_TIMEOUT,  
    "max_output_tokens": MAX_OUTPUT_TOKENS,  
},  

"openai": {  
    "enabled": True,  
    "priority": 2,  
    "api_key": OPENAI_API_KEY,  
    "api_key_env": "OPENAI_API_KEY",  
    "model": OPENAI_MODEL,  
    "supports_stream": True,  
    "supports_images": True,  
    "supports_documents": True,  
    "supports_function_calling": True,  
    "supports_system_prompt": True,  
    "timeout": REQUEST_TIMEOUT,  
    "max_output_tokens": MAX_OUTPUT_TOKENS,  
},  

"claude": {  
    "enabled": True,  
    "priority": 3,  
    "api_key": CLAUDE_API_KEY,  
    "api_key_env": "CLAUDE_API_KEY",  
    "model": CLAUDE_MODEL,  
    "supports_stream": True,  
    "supports_images": True,  
    "supports_documents": True,  
    "supports_function_calling": True,  
    "supports_system_prompt": True,  
    "timeout": REQUEST_TIMEOUT,  
    "max_output_tokens": MAX_OUTPUT_TOKENS,  
},  

"deepseek": {  
    "enabled": True,  
    "priority": 4,  
    "api_key": DEEPSEEK_API_KEY,  
    "api_key_env": "DEEPSEEK_API_KEY",  
    "model": DEEPSEEK_MODEL,  
    "supports_stream": True,  
    "supports_images": False,  
    "supports_documents": True,  
    "supports_function_calling": False,  
    "supports_system_prompt": True,  
    "timeout": REQUEST_TIMEOUT,  
    "max_output_tokens": MAX_OUTPUT_TOKENS,  
},  

"qwen": {  
    "enabled": True,  
    "priority": 5,  
    "api_key": QWEN_API_KEY,  
    "api_key_env": "QWEN_API_KEY",  
    "model": QWEN_MODEL,  
    "supports_stream": True,  
    "supports_images": True,  
    "supports_documents": True,  
    "supports_function_calling": True,  
    "supports_system_prompt": True,  
    "timeout": REQUEST_TIMEOUT,  
    "max_output_tokens": MAX_OUTPUT_TOKENS,  
},  

"grok": {  
    "enabled": True,  
    "priority": 6,  
    "api_key": GROK_API_KEY,  
    "api_key_env": "GROK_API_KEY",  
    "model": GROK_MODEL,  
    "supports_stream": True,  
    "supports_images": True,  
    "supports_documents": True,  
    "supports_function_calling": True,  
    "supports_system_prompt": True,  
    "timeout": REQUEST_TIMEOUT,  
    "max_output_tokens": MAX_OUTPUT_TOKENS,  
},  

"openrouter": {  
    "enabled": True,  
    "priority": 7,  
    "api_key": OPENROUTER_API_KEY,  
    "api_key_env": "OPENROUTER_API_KEY",  
    "model": OPENROUTER_MODEL,  
    "supports_stream": True,  
    "supports_images": True,  
    "supports_documents": True,  
    "supports_function_calling": True,  
    "supports_system_prompt": True,  
    "timeout": REQUEST_TIMEOUT,  
    "max_output_tokens": MAX_OUTPUT_TOKENS,  
},  

"ollama": {  
    "enabled": False,  
    "priority": 8,  
    "host": OLLAMA_HOST,  
    "model": OLLAMA_MODEL,  
    "supports_stream": True,  
    "supports_images": False,  
    "supports_documents": False,  
    "supports_function_calling": False,  
    "supports_system_prompt": True,  
    "timeout": REQUEST_TIMEOUT,  
    "max_output_tokens": MAX_OUTPUT_TOKENS,  
},  

"mistral": {  
    "enabled": True,  
    "priority": 9,  
    "api_key": MISTRAL_API_KEY,  
    "api_key_env": "MISTRAL_API_KEY",  
    "model": MISTRAL_MODEL,  
    "supports_stream": True,  
    "supports_images": False,  
    "supports_documents": True,  
    "supports_function_calling": True,  
    "supports_system_prompt": True,  
    "timeout": REQUEST_TIMEOUT,  
    "max_output_tokens": MAX_OUTPUT_TOKENS,  
},  

"cohere": {  
    "enabled": True,  
    "priority": 10,  
    "api_key": COHERE_API_KEY,  
    "api_key_env": "COHERE_API_KEY",  
    "model": COHERE_MODEL,  
    "supports_stream": True,  
    "supports_images": False,  
    "supports_documents": True,  
    "supports_function_calling": False,  
    "supports_system_prompt": True,  
    "timeout": REQUEST_TIMEOUT,  
    "max_output_tokens": MAX_OUTPUT_TOKENS,  
},  

"perplexity": {  
    "enabled": True,  
    "priority": 11,  
    "api_key": PERPLEXITY_API_KEY,  
    "api_key_env": "PERPLEXITY_API_KEY",  
    "model": PERPLEXITY_MODEL,  
    "supports_stream": True,  
    "supports_images": False,  
    "supports_documents": True,  
    "supports_function_calling": False,  
    "supports_system_prompt": True,  
    "timeout": REQUEST_TIMEOUT,  
    "max_output_tokens": MAX_OUTPUT_TOKENS,  
}

}

==========================================================

Prompt Configuration

==========================================================

SYSTEM_PROMPT_VERSION = "2.0"

USE_DYNAMIC_PROMPT = True

USE_CONTEXT_MEMORY = True

USE_GROUP_CONTEXT = True

USE_USER_CONTEXT = True

USE_CONVERSATION_HISTORY = True

USE_KNOWLEDGE_CONTEXT = True

USE_SEARCH_CONTEXT = True

PROMPT_MAX_CONTEXT = 10

==========================================================

Required Directories

==========================================================

REQUIRED_DIRECTORIES = [

DATA_DIR,  

KNOWLEDGE_DIR,  

UNIVERSITIES_DIR,  

CACHE_DIR,  

LOGS_DIR,  

BACKUP_DIR,  

TEMP_DIR,  

EXPORT_DIR,  

MODELS_DIR,  

PROMPTS_DIR,

]

==========================================================

Create Missing Directories

==========================================================

for directory in REQUIRED_DIRECTORIES:

directory.mkdir(  
    parents=True,  
    exist_ok=True  
)

==========================================================

Validate Environment

==========================================================

REQUIRED_ENVIRONMENT = [

"BOT_TOKEN",

]

OPTIONAL_AI_KEYS = [

"GEMINI_API_KEY",  

"OPENAI_API_KEY",  

"CLAUDE_API_KEY",  

"DEEPSEEK_API_KEY",  

"QWEN_API_KEY",  

"GROK_API_KEY",  

"OPENROUTER_API_KEY",  

"MISTRAL_API_KEY",  

"COHERE_API_KEY",  

"PERPLEXITY_API_KEY",

]

==========================================================

End Of Configuration

==========================================================
