"""
Provider Manager v8.0 - Production Ready ✅
طبقة إدارة موحدة لمزودات الذكاء الاصطناعي
Thread-Safe | قابل للتوسع | إدارة نظيفة للموارد | دعم Conversation History

التسلسل: Gemini (4 Keys) → Mistral → OpenRouter

يعتمد على:
    - google-genai (المكتبة الحديثة) — Client مستقل لكل مفتاح
    - httpx
    - python-dotenv

الاستخدام:
    from provider_manager import get_manager
    manager = get_manager()
    response = await manager.get_response(
        system_prompt=SYSTEM_PROMPT,
        history=history,        # List[Dict[str, str]]
        user_prompt=user_text,
    )
    await manager.shutdown()
"""

from __future__ import annotations

import os
import time
import uuid
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

# ============================================================
# الإعدادات العامة
# ============================================================
@dataclass(frozen=True)
class Config:
    COOLDOWN_DURATION: int = 300
    MAX_RETRIES: int = 2
    BASE_RETRY_DELAY: float = 1.0
    MAX_RETRY_DELAY: float = 10.0
    REQUEST_TIMEOUT: float = 60.0
    GEMINI_MODEL: str = "gemini-flash-lite-latest"
    MISTRAL_MODEL: str = "mistral-small-latest"
    OPENROUTER_MODEL: str = "openai/gpt-oss-20b:free"
    GEMINI_KEYS: tuple = (
        "GEMINI_API_KEY",
        "GEMINI_API_KEY_2",
        "GEMINI_API_KEY_3",
        "GEMINI_API_KEY_4",
    )
    MISTRAL_KEY: str = "MISTRAL_API_KEY"
    OPENROUTER_KEY: str = "OPENROUTER_API_KEY"
    FALLBACK_MESSAGE: str = (
        "حدثت مشكلة مؤقتة في خدمات الذكاء الاصطناعي، "
        "يرجى المحاولة مرة أخرى بعد قليل."
    )

config = Config()


# ============================================================
# التسجيل (Logger)
# ============================================================
logger = logging.getLogger("ProviderManager")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        '%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(h)


# ============================================================
# الاستثناءات
# ============================================================
class ProviderError(Exception):
    pass

class TemporaryProviderError(ProviderError):
    pass

class PermanentProviderError(ProviderError):
    pass

class QuotaExceededError(TemporaryProviderError):
    pass

class RateLimitError(TemporaryProviderError):
    pass

class ResourceExhaustedError(TemporaryProviderError):
    pass

class ServiceUnavailableError(TemporaryProviderError):
    pass

class NetworkError(TemporaryProviderError):
    pass

class TimeoutError(NetworkError):
    pass

class AuthenticationError(PermanentProviderError):
    pass

class ContentFilteredError(PermanentProviderError):
    pass


# ============================================================
# سياق الطلب
# ============================================================
@dataclass
class RequestContext:
    system_prompt: str
    user_prompt: str
    history: List[Dict[str, str]] = field(default_factory=list)
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    start_time: float = field(default_factory=time.time)
    provider_name: str = ""
    model_name: str = ""
    key_label: str = ""
    attempts: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def elapsed_ms(self) -> float:
        return (time.time() - self.start_time) * 1000


# ============================================================
# مزود أساسي
# ============================================================
class BaseProvider(ABC):
    def __init__(self, name: str, model: str, priority: int = 0):
        self.name = name
        self.model = model
        self.priority = priority
        self._cooldown_until: float = 0.0

    def is_available(self) -> bool:
        return time.time() >= self._cooldown_until

    def set_cooldown(self, duration: int = None):
        self._cooldown_until = time.time() + (duration or config.COOLDOWN_DURATION)

    def reset_cooldown(self):
        self._cooldown_until = 0.0

    @abstractmethod
    async def _call_api(self, ctx: RequestContext) -> str:
        pass

    async def generate(self, ctx: RequestContext) -> str:
        last_error = None
        for attempt in range(config.MAX_RETRIES + 1):
            ctx.attempts = attempt + 1
            try:
                return await asyncio.wait_for(
                    self._call_api(ctx),
                    timeout=config.REQUEST_TIMEOUT
                )
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"{self.name}: timeout")
            except NetworkError as e:
                last_error = e
            except TemporaryProviderError:
                raise
            except PermanentProviderError:
                raise
            except Exception as e:
                last_error = TemporaryProviderError(str(e))

            if attempt < config.MAX_RETRIES:
                delay = min(config.BASE_RETRY_DELAY * (2 ** attempt), config.MAX_RETRY_DELAY)
                await asyncio.sleep(delay)

        raise last_error

    def get_key_label(self) -> str:
        return "default"

    async def shutdown(self):
        pass


# ============================================================
# Gemini (google-genai - Client مستقل لكل مفتاح)
# ============================================================
class GeminiProvider(BaseProvider):
    """
    مزود Google Gemini مع 4 مفاتيح وتدوير تلقائي
    يستخدم google-genai (Client مستقل لكل مفتاح - لا Global State)
    """

    def __init__(self, api_keys: List[str]):
        super().__init__(name="Gemini", model=config.GEMINI_MODEL, priority=0)
        self._api_keys = [k.strip() for k in api_keys if k and k.strip()]
        if not self._api_keys:
            raise ValueError("لا توجد مفاتيح Gemini صالحة")
        self._current_index = 0
        self._key_cooldowns: Dict[int, float] = {}
        self._lock = asyncio.Lock()
        self._clients: Dict[int, Any] = {}

    def get_key_label(self) -> str:
        return f"Key {self._current_index + 1}"

    def _clean_cooldowns(self):
        now = time.time()
        for i in list(self._key_cooldowns):
            if now >= self._key_cooldowns[i]:
                del self._key_cooldowns[i]

    def refresh_availability(self):
        self._clean_cooldowns()

    def is_available(self) -> bool:
        self._clean_cooldowns()
        return any(i not in self._key_cooldowns for i in range(len(self._api_keys)))

    def _get_or_create_client(self, key_index: int) -> Any:
        if key_index not in self._clients:
            from google import genai
            self._clients[key_index] = genai.Client(api_key=self._api_keys[key_index])
        return self._clients[key_index]

    async def _call_api(self, ctx: RequestContext) -> str:
        self._clean_cooldowns()
        available = [i for i in range(len(self._api_keys)) if i not in self._key_cooldowns]
        if not available:
            raise ResourceExhaustedError("كل مفاتيح Gemini في تهدئة")

        last_error = None
        for key_index in available:
            async with self._lock:
                if key_index in self._key_cooldowns:
                    continue
                self._current_index = key_index

            ctx.key_label = self.get_key_label()
            try:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None, self._sync_call, key_index, ctx
                )
                return result
            except TemporaryProviderError as e:
                async with self._lock:
                    self._key_cooldowns[key_index] = time.time() + config.COOLDOWN_DURATION
                last_error = e
            except PermanentProviderError:
                raise

        raise last_error or ResourceExhaustedError("فشلت كل مفاتيح Gemini")

    def _build_contents(self, ctx: RequestContext) -> list:
        """بناء محتوى المحادثة مع التاريخ لـ Gemini"""
        contents = []

        for message in ctx.history:
            role = message.get("role", "user")
            text = message.get("content", "")

            if not text:
                continue

            if role == "assistant":
                contents.append({
                    "role": "model",
                    "parts": [{"text": text}],
                })
            else:
                contents.append({
                    "role": "user",
                    "parts": [{"text": text}],
                })

        # إضافة رسالة المستخدم الحالية
        contents.append({
            "role": "user",
            "parts": [{"text": ctx.user_prompt}],
        })

        return contents

    def _sync_call(self, key_index: int, ctx: RequestContext) -> str:
        client = self._get_or_create_client(key_index)
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=self._build_contents(ctx),
                config={
                    "system_instruction": ctx.system_prompt,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                },
            )
        except Exception as e:
            self._classify_error(e)

        if not response.candidates:
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                raise ContentFilteredError(str(response.prompt_feedback.block_reason))
            raise TemporaryProviderError("استجابة فارغة")

        try:
            return response.text
        except ValueError:
            raise ContentFilteredError("تعذر استخراج النص")

    def _classify_error(self, error: Exception):
        msg = str(error).lower()
        if any(k in msg for k in ("429", "quota", "exceeded")):
            raise QuotaExceededError(str(error))
        if "rate" in msg and "limit" in msg:
            raise RateLimitError(str(error))
        if "resource" in msg and "exhausted" in msg:
            raise ResourceExhaustedError(str(error))
        if "timeout" in msg or "timed out" in msg:
            raise TimeoutError(str(error))
        if "network" in msg or "connection" in msg:
            raise NetworkError(str(error))
        if "unavailable" in msg or "overloaded" in msg:
            raise ServiceUnavailableError(str(error))
        if "auth" in msg or "api key" in msg or "invalid" in msg:
            raise AuthenticationError(str(error))
        if "safety" in msg or "blocked" in msg:
            raise ContentFilteredError(str(error))
        raise TemporaryProviderError(str(error))


# ============================================================
# مزود HTTP عام (Mistral + OpenRouter)
# ============================================================
class HttpProvider(BaseProvider):
    def __init__(self, name: str, model: str, api_key: str, base_url: str, priority: int = 0):
        super().__init__(name=name, model=model, priority=priority)
        self._api_key = api_key.strip()
        self._base_url = base_url
        self._client: Optional["httpx.AsyncClient"] = None
        self._client_lock = asyncio.Lock()

    async def _get_client(self) -> "httpx.AsyncClient":
        if self._client is None:
            async with self._client_lock:
                if self._client is None:
                    import httpx
                    self._client = httpx.AsyncClient(
                        timeout=config.REQUEST_TIMEOUT,
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        }
                    )
        return self._client

    def _build_messages(self, ctx: RequestContext) -> list:
        """بناء رسائل المحادثة مع التاريخ لـ Mistral/OpenRouter"""
        messages = [
            {
                "role": "system",
                "content": ctx.system_prompt,
            }
        ]

        # إضافة التاريخ
        messages.extend(ctx.history)

        # إضافة رسالة المستخدم الحالية
        messages.append({
            "role": "user",
            "content": ctx.user_prompt,
        })

        return messages

    async def _call_api(self, ctx: RequestContext) -> str:
        import httpx
        client = await self._get_client()
        try:
            resp = await client.post(
                self._base_url,
                json={
                    "model": self.model,
                    "messages": self._build_messages(ctx),
                    "temperature": 0.7,
                    "max_tokens": 8192,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            self._classify_http_error(e)
        except httpx.TimeoutException:
            raise TimeoutError(f"{self.name}: timeout")
        except httpx.NetworkError:
            raise NetworkError(f"{self.name}: network error")

    def _classify_http_error(self, error: "httpx.HTTPStatusError") -> None:
        s = error.response.status_code
        if s == 429:
            raise RateLimitError(f"{self.name}: 429")
        if s in (500, 502, 503, 504):
            raise ServiceUnavailableError(f"{self.name}: {s}")
        if s in (401, 403):
            raise AuthenticationError(f"{self.name}: {s}")
        raise TemporaryProviderError(f"{self.name}: HTTP {s}")

    async def shutdown(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info(f"[{self.name}] تم إغلاق AsyncClient")


# ============================================================
# Mistral
# ============================================================
class MistralProvider(HttpProvider):
    def __init__(self, api_key: str):
        super().__init__(
            name="Mistral",
            model=config.MISTRAL_MODEL,
            api_key=api_key,
            base_url="https://api.mistral.ai/v1/chat/completions",
            priority=1
        )


# ============================================================
# OpenRouter
# ============================================================
class OpenRouterProvider(HttpProvider):
    def __init__(self, api_key: str):
        super().__init__(
            name="OpenRouter",
            model=config.OPENROUTER_MODEL,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1/chat/completions",
            priority=2
        )


# ============================================================
# ProviderManager (Singleton)
# ============================================================
class ProviderManager:
    _instance: Optional["ProviderManager"] = None

    def __new__(cls) -> "ProviderManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._providers: List[BaseProvider] = []
        self._load_providers()
        self._providers.sort(key=lambda p: p.priority)
        self._initialized = True

        logger.info(f"تم تحميل {len(self._providers)} مزودات")
        for i, p in enumerate(self._providers):
            logger.info(f"  {i+1}. {p.name} | {p.model} | priority={p.priority}")

    def _load_providers(self) -> None:
        keys = []
        for name in config.GEMINI_KEYS:
            v = os.getenv(name, "").strip()
            if v:
                keys.append(v)
        if keys:
            self._providers.append(GeminiProvider(keys))

        mk = os.getenv(config.MISTRAL_KEY, "").strip()
        if mk:
            self._providers.append(MistralProvider(mk))

        ok = os.getenv(config.OPENROUTER_KEY, "").strip()
        if ok:
            self._providers.append(OpenRouterProvider(ok))

        if not self._providers:
            raise RuntimeError("لم يتم تحميل أي مزود")

    def add_provider(self, provider: BaseProvider) -> None:
        self._providers.append(provider)
        self._providers.sort(key=lambda p: p.priority)

    async def get_response(
        self,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        user_prompt: str = "",
    ) -> str:
        ctx = RequestContext(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            history=history or [],
        )
        logger.info(
            f"[{ctx.request_id}] طلب | "
            f"sys:{len(system_prompt)} "
            f"user:{len(user_prompt)} "
            f"history:{len(ctx.history)}"
        )

        for p in self._providers:
            if isinstance(p, GeminiProvider):
                p.refresh_availability()

        for provider in self._providers:
            if not provider.is_available():
                continue

            ctx.provider_name = provider.name
            ctx.model_name = provider.model
            ctx.key_label = provider.get_key_label()

            t0 = time.time()
            try:
                result = await provider.generate(ctx)
                dt = (time.time() - t0) * 1000
                logger.info(
                    f"[{ctx.request_id}] OK | {provider.name} | "
                    f"{provider.model} | {ctx.key_label} | "
                    f"attempts={ctx.attempts} | {dt:.0f}ms"
                )
                return result
            except TemporaryProviderError as e:
                dt = (time.time() - t0) * 1000
                ctx.errors.append(f"{provider.name}: {e}")
                logger.warning(f"[{ctx.request_id}] TEMP | {provider.name}: {e} | {dt:.0f}ms")
                if not isinstance(provider, GeminiProvider):
                    provider.set_cooldown()
            except PermanentProviderError as e:
                dt = (time.time() - t0) * 1000
                ctx.errors.append(f"{provider.name}: {e}")
                logger.error(f"[{ctx.request_id}] PERM | {provider.name}: {e} | {dt:.0f}ms")
            except Exception as e:
                dt = (time.time() - t0) * 1000
                ctx.errors.append(f"{provider.name}: {e}")
                logger.error(f"[{ctx.request_id}] ERR | {provider.name}: {e} | {dt:.0f}ms")

        logger.error(f"[{ctx.request_id}] FAIL | " + "; ".join(ctx.errors))
        return config.FALLBACK_MESSAGE

    async def shutdown(self) -> None:
        logger.info("جاري إغلاق جميع المزودات...")
        for provider in self._providers:
            await provider.shutdown()
        logger.info("تم إغلاق جميع المزودات")


# ============================================================
# helper
# ============================================================
def get_manager() -> ProviderManager:
    return ProviderManager()
