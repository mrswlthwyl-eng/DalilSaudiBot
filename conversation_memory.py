"""
conversation_memory.py - Ultimate Memory System
================================================
- Per-user conversation history with smart expiration
- Context summarization for long conversations
- Multi-turn understanding
- Auto cleanup for inactive users
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional


class ConversationMemory:
    """
    Advanced conversation memory system.
    
    Features:
    - Stores last N messages per user (default: 30 = 15 turns)
    - Auto-expires conversations after TTL (default: 2 hours)
    - Provides context summary for AI
    - Tracks conversation state for continuity
    """

    def __init__(
        self,
        max_messages: int = 30,      # 15 turns (user + assistant)
        ttl_minutes: int = 120,      # 2 hours before auto-clear
    ):
        self.max_messages = max_messages
        self.ttl_seconds = ttl_minutes * 60

        self._memory: Dict[int, Deque[dict]] = defaultdict(
            lambda: deque(maxlen=max_messages)
        )
        self._last_activity: Dict[int, float] = {}
        self._user_university: Dict[int, str] = {}    # Track which university user is asking about
        self._user_topic: Dict[int, str] = {}          # Track current topic

    # ============================================================
    # Core Methods
    # ============================================================

    def add_user_message(self, user_id: int, message: str) -> None:
        """Add a user message to the conversation history."""
        self._touch(user_id)
        self._memory[user_id].append({
            "role": "user",
            "content": message,
        })

    def add_assistant_message(self, user_id: int, message: str) -> None:
        """Add an assistant response to the conversation history."""
        self._touch(user_id)
        self._memory[user_id].append({
            "role": "assistant",
            "content": message,
        })

    def get_history(self, user_id: int) -> List[dict]:
        """
        Get conversation history for a user.
        Auto-cleans if expired.
        """
        self._clean_if_expired(user_id)
        return list(self._memory[user_id])

    def clear(self, user_id: int) -> None:
        """Clear all memory for a user."""
        self._memory[user_id].clear()
        self._last_activity.pop(user_id, None)
        self._user_university.pop(user_id, None)
        self._user_topic.pop(user_id, None)

    # ============================================================
    # Smart Context Methods
    # ============================================================

    def set_university(self, user_id: int, university_name: str) -> None:
        """Remember which university the user is asking about."""
        self._user_university[user_id] = university_name

    def get_university(self, user_id: int) -> Optional[str]:
        """Get the university the user is currently asking about."""
        return self._user_university.get(user_id)

    def set_topic(self, user_id: int, topic: str) -> None:
        """Remember the current topic of conversation."""
        self._user_topic[user_id] = topic

    def get_topic(self, user_id: int) -> Optional[str]:
        """Get the current conversation topic."""
        return self._user_topic.get(user_id)

    def get_context_summary(self, user_id: int) -> str:
        """
        Build a short context summary for the AI.
        Helps the AI understand what the user is talking about.
        """
        history = self.get_history(user_id)
        if not history:
            return ""

        university = self._user_university.get(user_id)
        topic = self._user_topic.get(user_id)

        parts = []
        if university:
            parts.append(f"المستخدم يسأل عن: {university}")
        if topic:
            parts.append(f"الموضوع الحالي: {topic}")

        # Add last 3 exchanges for immediate context
        recent = history[-6:]  # Last 3 turns
        if recent:
            parts.append("آخر المحادثة:")
            for msg in recent:
                role = "المستخدم" if msg["role"] == "user" else "المساعد"
                content = msg["content"][:100]  # First 100 chars
                parts.append(f"  {role}: {content}...")

        return "\n".join(parts)

    def detect_topic_from_history(self, user_id: int) -> Optional[str]:
        """
        Auto-detect the conversation topic from recent messages.
        """
        history = self.get_history(user_id)
        if not history:
            return None

        # Check last user message for topic clues
        last_user_msgs = [m for m in history if m["role"] == "user"]
        if not last_user_msgs:
            return None

        last_msg = last_user_msgs[-1]["content"].lower()

        # Simple topic detection
        topic_keywords = {
            "تدريب": "التدريب التطبيقي",
            "تقرير": "التقارير",
            "نموذج": "النماذج",
            "كلية": "الكليات",
            "قبول": "القبول والتسجيل",
            "تسجيل": "القبول والتسجيل",
            "عمادة": "العمادات",
            "بلاك بورد": "الخدمات الإلكترونية",
            "موقع": "الموقع الإلكتروني",
            "رقم": "معلومات الاتصال",
            "معلومات": "معلومات عامة",
        }

        for keyword, topic in topic_keywords.items():
            if keyword in last_msg:
                return topic

        return None

    # ============================================================
    # Maintenance
    # ============================================================

    def _touch(self, user_id: int) -> None:
        """Update last activity timestamp."""
        self._last_activity[user_id] = time.time()

    def _clean_if_expired(self, user_id: int) -> None:
        """Clear memory if conversation has expired."""
        last = self._last_activity.get(user_id)
        if last and (time.time() - last) > self.ttl_seconds:
            self.clear(user_id)

    def cleanup_inactive(self, max_inactive_minutes: int = 360) -> int:
        """
        Remove conversations inactive for longer than max_inactive_minutes.
        Returns number of cleaned conversations.
        """
        now = time.time()
        max_inactive_seconds = max_inactive_minutes * 60
        to_remove = []

        for user_id, last_time in self._last_activity.items():
            if now - last_time > max_inactive_seconds:
                to_remove.append(user_id)

        for user_id in to_remove:
            self.clear(user_id)

        return len(to_remove)

    # ============================================================
    # Stats
    # ============================================================

    def get_stats(self, user_id: int) -> dict:
        """Get statistics about a user's conversation."""
        history = self.get_history(user_id)
        user_msgs = sum(1 for m in history if m["role"] == "user")
        assistant_msgs = sum(1 for m in history if m["role"] == "assistant")

        return {
            "total_messages": len(history),
            "user_messages": user_msgs,
            "assistant_messages": assistant_msgs,
            "turns": min(user_msgs, assistant_msgs),
            "university": self._user_university.get(user_id),
            "topic": self._user_topic.get(user_id),
            "last_activity": self._last_activity.get(user_id, 0),
            "expired": self._is_expired(user_id),
        }

    def _is_expired(self, user_id: int) -> bool:
        """Check if a conversation has expired."""
        last = self._last_activity.get(user_id)
        if last:
            return (time.time() - last) > self.ttl_seconds
        return True


# ============================================================
# Global Instance
# ============================================================
memory = ConversationMemory(
    max_messages=30,    # 15 complete turns
    ttl_minutes=120,    # 2 hours
)
