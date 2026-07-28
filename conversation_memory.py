"""
conversation_memory.py

إدارة ذاكرة المحادثات لكل مستخدم.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque, Dict, List


class ConversationMemory:
    """
    يحتفظ بآخر عدد محدد من الرسائل لكل مستخدم.
    """

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages

        self._memory: Dict[int, Deque[dict]] = defaultdict(
            lambda: deque(maxlen=max_messages)
        )

    def add_user_message(self, user_id: int, message: str) -> None:
        self._memory[user_id].append(
            {
                "role": "user",
                "content": message,
            }
        )

    def add_assistant_message(self, user_id: int, message: str) -> None:
        self._memory[user_id].append(
            {
                "role": "assistant",
                "content": message,
            }
        )

    def get_history(self, user_id: int) -> List[dict]:
        return list(self._memory[user_id])

    def clear(self, user_id: int) -> None:
        self._memory[user_id].clear()


memory = ConversationMemory()
