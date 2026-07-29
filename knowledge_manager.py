"""
Knowledge Manager - Knowledge Base Engine
==========================================
Responsible for loading, caching, and searching university knowledge bases.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class KnowledgeManager:
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self._cache: Dict[str, dict] = {}
        self._aliases_map: Dict[str, str] = {}
        self._loaded = False

    def load_database(self) -> None:
        if not self.knowledge_dir.exists():
            raise FileNotFoundError(f"Knowledge directory not found: {self.knowledge_dir.resolve()}")

        self._cache.clear()
        self._aliases_map.clear()

        json_files = list(self.knowledge_dir.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(f"No JSON files found in {self.knowledge_dir.resolve()}")

        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                university_id = data.get("id")
                if not university_id:
                    print(f"⚠️  Skipping {file_path.name}: missing 'id' field")
                    continue

                self._cache[university_id] = data

                for alias in data.get("aliases", []):
                    self._aliases_map[alias.lower()] = university_id

                self._aliases_map[data.get("name", "").lower()] = university_id
                self._aliases_map[data.get("short_name", "").lower()] = university_id

            except json.JSONDecodeError as e:
                print(f"⚠️  Skipping {file_path.name}: invalid JSON — {e}")
            except Exception as e:
                print(f"⚠️  Error loading {file_path.name}: {e}")

        self._loaded = True
        print(f"✅ Knowledge Manager loaded {len(self._cache)} universities with {len(self._aliases_map)} aliases.")

    def reload_database(self) -> None:
        self.load_database()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def find_university(self, query: str) -> Optional[str]:
        query_lower = query.lower()
        if query_lower in self._aliases_map:
            return self._aliases_map[query_lower]
        for alias, uid in self._aliases_map.items():
            if query_lower in alias or alias in query_lower:
                return uid
        return None

    def search(self, user_text: str) -> dict:
        if not self._loaded:
            return {"found": False}

        university_id = self.find_university(user_text)
        if not university_id:
            return {"found": False}

        university_data = self._cache.get(university_id)
        if not university_data:
            return {"found": False}

        result = self._search_all_sections(user_text, university_data)
        if result:
            result["university"] = university_data.get("name", university_id)
            return result

        return {"found": False}

    def _search_all_sections(self, query: str, data: dict) -> Optional[dict]:
        query_lower = query.lower()
        keywords_map = data.get("keywords", {})

        for section_key, section_data in data.items():
            if section_key in ("id", "name", "short_name", "city", "type", "aliases"):
                continue

            result = self._search_section(query_lower, section_key, section_data, keywords_map)
            if result:
                return result

        return None

    def _search_section(self, query: str, section_key: str, section_data: Any, keywords_map: dict) -> Optional[dict]:
        section_kw = keywords_map.get(section_key, [])
        for kw in section_kw:
            if kw.lower() in query:
                return self._extract_best_item(section_key, section_data, kw)

        if isinstance(section_data, list):
            return self._search_list(query, section_key, section_data)
        elif isinstance(section_data, dict):
            return self._search_dict(query, section_key, section_data)
        elif isinstance(section_data, str) and section_data:
            if any(word in section_data.lower() for word in query.split()):
                return {
                    "found": True,
                    "section": section_key,
                    "title": section_key.replace("_", " ").title(),
                    "answer": section_data,
                    "url": section_data if section_data.startswith("http") else "",
                }

        return None

    def _search_list(self, query: str, section_key: str, items: list) -> Optional[dict]:
        """Search a list of dicts/strings for matching content."""
        query_words = query.split()

        for item in items:
            if isinstance(item, dict):
                # جمع كل النصوص في العنصر
                name = item.get("name", "")
                title = item.get("title", "")
                description = item.get("description", "")
                category = item.get("category", "")
                item_text = f"{name} {title} {description} {category}".lower()

                # إذا تطابقت أي كلمة من السؤال مع النص
                if any(word in item_text for word in query_words):
                    return self._item_to_result(section_key, item)

            elif isinstance(item, str):
                if any(word in item.lower() for word in query_words):
                    return {
                        "found": True,
                        "section": section_key,
                        "title": item,
                        "answer": item,
                        "url": "",
                    }

        return None

    def _search_dict(self, query: str, section_key: str, data: dict) -> Optional[dict]:
        query_words = query.split()
        for key, value in data.items():
            if isinstance(value, str) and value:
                if any(word in key.lower() or word in value.lower() for word in query_words):
                    return {
                        "found": True,
                        "section": section_key,
                        "title": key.replace("_", " ").title(),
                        "answer": value,
                        "url": value if value.startswith("http") else "",
                    }
        return None

    def _extract_best_item(self, section_key: str, section_data: Any, keyword: str) -> Optional[dict]:
        if isinstance(section_data, list):
            for item in section_data:
                if isinstance(item, dict):
                    name = item.get("name", "")
                    title = item.get("title", "")
                    if keyword.lower() in f"{name} {title}".lower():
                        return self._item_to_result(section_key, item)
            if section_data and isinstance(section_data[0], dict):
                return self._item_to_result(section_key, section_data[0])
        elif isinstance(section_data, str) and section_data:
            return {
                "found": True,
                "section": section_key,
                "title": section_key.replace("_", " ").title(),
                "answer": section_data,
                "url": section_data if section_data.startswith("http") else "",
            }
        return None

    def _item_to_result(self, section_key: str, item: dict) -> dict:
        title = (
            item.get("name")
            or item.get("title")
            or item.get("channel")
            or item.get("username")
            or section_key.replace("_", " ").title()
        )
        url = item.get("url", "")
        description = item.get("description", "")
        answer = description or url

        return {
            "found": True,
            "section": section_key,
            "title": title,
            "answer": answer,
            "url": url,
        }


_knowledge_instance: Optional[KnowledgeManager] = None


def get_knowledge_manager(knowledge_dir: str = "knowledge") -> KnowledgeManager:
    global _knowledge_instance
    if _knowledge_instance is None:
        _knowledge_instance = KnowledgeManager(knowledge_dir)
        _knowledge_instance.load_database()
    return _knowledge_instance
