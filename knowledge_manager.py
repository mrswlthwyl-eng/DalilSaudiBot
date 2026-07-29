"""
Knowledge Manager - Knowledge Base Engine
==========================================
Responsible for loading, caching, and searching university knowledge bases.
Acts as the brain for DalilSaudiBot's static knowledge queries.

Supports:
    - Dynamic loading of all JSON files in /knowledge
    - Smart search by aliases, sections, and keywords
    - Partial word matching for better accuracy
    - Fully extensible — no code changes needed for new universities or sections
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class KnowledgeManager:
    """
    Central knowledge engine for the bot.
    Loads all university JSON files from /knowledge into memory,
    and provides smart search capabilities.
    """

    def __init__(self, knowledge_dir: str = "knowledge"):
        """
        Initialize the Knowledge Manager.

        Args:
            knowledge_dir: Relative path to the folder containing JSON files.
        """
        self.knowledge_dir = Path(knowledge_dir)
        self._cache: Dict[str, dict] = {}  # university_id → data
        self._aliases_map: Dict[str, str] = {}  # alias → university_id
        self._loaded = False

    # ============================================================
    # Loading & Caching
    # ============================================================

    def load_database(self) -> None:
        """
        Load all JSON files from the knowledge directory into memory.
        Builds an alias map for fast university lookup.
        Called once at bot startup.
        """
        if not self.knowledge_dir.exists():
            raise FileNotFoundError(
                f"Knowledge directory not found: {self.knowledge_dir.resolve()}"
            )

        self._cache.clear()
        self._aliases_map.clear()

        json_files = list(self.knowledge_dir.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(
                f"No JSON files found in {self.knowledge_dir.resolve()}"
            )

        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                university_id = data.get("id")
                if not university_id:
                    print(f"⚠️  Skipping {file_path.name}: missing 'id' field")
                    continue

                self._cache[university_id] = data

                # Map all aliases → university_id
                for alias in data.get("aliases", []):
                    self._aliases_map[alias.lower()] = university_id

                # Also map the full name and short name
                self._aliases_map[data.get("name", "").lower()] = university_id
                self._aliases_map[data.get("short_name", "").lower()] = university_id

            except json.JSONDecodeError as e:
                print(f"⚠️  Skipping {file_path.name}: invalid JSON — {e}")
            except Exception as e:
                print(f"⚠️  Error loading {file_path.name}: {e}")

        self._loaded = True
        print(f"✅ Knowledge Manager loaded {len(self._cache)} universities "
              f"with {len(self._aliases_map)} aliases.")

    def reload_database(self) -> None:
        """
        Reload all JSON files from disk.
        Useful when new universities are added without restarting the bot.
        """
        self.load_database()

    @property
    def is_loaded(self) -> bool:
        """Check if the knowledge base has been loaded."""
        return self._loaded

    @property
    def universities(self) -> List[str]:
        """Return list of loaded university IDs."""
        return list(self._cache.keys())

    # ============================================================
    # University Lookup
    # ============================================================

    def find_university(self, query: str) -> Optional[str]:
        """
        Find a university ID by matching the query against aliases.

        Args:
            query: User's text that may contain a university name/alias.

        Returns:
            university_id if found, else None.
        """
        query_lower = query.lower()

        # Direct match
        if query_lower in self._aliases_map:
            return self._aliases_map[query_lower]

        # Partial match (query contains an alias, or alias contains query)
        for alias, uid in self._aliases_map.items():
            if query_lower in alias or alias in query_lower:
                return uid

        return None

    def get_university_data(self, university_id: str) -> Optional[dict]:
        """Retrieve the full data dict for a university ID."""
        return self._cache.get(university_id)

    # ============================================================
    # Smart Search Engine
    # ============================================================

    def search(self, user_text: str) -> dict:
        """
        Main search entry point.
        Extracts university and intent from user text, then searches
        the relevant sections.

        Args:
            user_text: The full user message.

        Returns:
            dict with keys: found, university, section, title, answer, url
            or {"found": False}
        """
        if not self._loaded:
            return {"found": False}

        # Step 1: Identify the university
        university_id = self.find_university(user_text)
        if not university_id:
            return {"found": False}

        university_data = self._cache.get(university_id)
        if not university_data:
            return {"found": False}

        # Step 2: Search all sections for matching content
        result = self._search_all_sections(user_text, university_data)
        if result:
            result["university"] = university_data.get("name", university_id)
            return result

        return {"found": False}

    def _search_all_sections(self, query: str, data: dict) -> Optional[dict]:
        """
        Iterate over all sections in the university data and search for
        matching content using keywords and text matching.

        Args:
            query: The user's question (lowercased for matching).
            data: The university data dict.

        Returns:
            A result dict if found, else None.
        """
        query_lower = query.lower()
        keywords_map = data.get("keywords", {})

        # Check each section
        for section_key, section_data in data.items():
            if section_key in ("id", "name", "short_name", "city", "type", "aliases"):
                continue

            result = self._search_section(
                query_lower, section_key, section_data, keywords_map
            )
            if result:
                return result

        return None

    def _search_section(
        self,
        query: str,
        section_key: str,
        section_data: Any,
        keywords_map: dict,
    ) -> Optional[dict]:
        """
        Search a single section for matching content.

        Handles: lists of dicts, dicts, and strings.
        """
        # 1. Check keywords for this section
        section_kw = keywords_map.get(section_key, [])
        for kw in section_kw:
            if kw.lower() in query:
                # Keyword matched — try to extract the best item
                return self._extract_best_item(
                    section_key, section_data, kw
                )

        # 2. Direct text search inside the section
        if isinstance(section_data, list):
            return self._search_list(query, section_key, section_data)

        elif isinstance(section_data, dict):
            return self._search_dict(query, section_key, section_data)

        elif isinstance(section_data, str) and section_data:
            # Simple string value (e.g., phone, email)
            query_words = query.split()
            if any(word in section_data.lower() for word in query_words):
                return {
                    "found": True,
                    "section": section_key,
                    "title": section_key.replace("_", " ").title(),
                    "answer": section_data,
                    "url": section_data if section_data.startswith("http") else "",
                }

        return None

    def _search_list(
        self, query: str, section_key: str, items: list
    ) -> Optional[dict]:
        """
        Search a list of items for a match using partial word matching.
        Each word in the query must appear somewhere in the item text.
        """
        query_words = query.split()

        for item in items:
            if isinstance(item, dict):
                # Collect all text values from the item
                name = item.get("name", "")
                title = item.get("title", "")
                description = item.get("description", "")
                category = item.get("category", "")
                username = item.get("username", "")
                company = item.get("company", "")
                position = item.get("position", "")

                # Combine all text fields into one searchable string
                item_text = (
                    f"{name} {title} {description} {category} "
                    f"{username} {company} {position}"
                ).lower()

                # Check if ALL query words appear somewhere in the item text
                if all(word in item_text for word in query_words):
                    return self._item_to_result(section_key, item)

            elif isinstance(item, str):
                if all(word in item.lower() for word in query_words):
                    return {
                        "found": True,
                        "section": section_key,
                        "title": item,
                        "answer": item,
                        "url": "",
                    }

        return None

    def _search_dict(
        self, query: str, section_key: str, data: dict
    ) -> Optional[dict]:
        """Search a dict for a match in keys or values."""
        query_words = query.split()
        # Check if any key name or value matches
        for key, value in data.items():
            if isinstance(value, str) and value:
                if any(word in key.lower() or word in value.lower() for word in query_words):
                    return {
                        "found": True,
                        "section": section_key,
                        "title": key.replace("_", " ").title(),
                        "answer": value if not value.startswith("http") else value,
                        "url": value if value.startswith("http") else "",
                    }
        return None

    def _extract_best_item(
        self, section_key: str, section_data: Any, keyword: str
    ) -> Optional[dict]:
        """Extract the most relevant item from a section after a keyword match."""
        if isinstance(section_data, list):
            for item in section_data:
                if isinstance(item, dict):
                    # Try to find the item most related to the keyword
                    name = item.get("name", "")
                    title = item.get("title", "")
                    item_text = f"{name} {title}".lower()
                    if keyword.lower() in item_text:
                        return self._item_to_result(section_key, item)
            # Fallback: return first item
            if section_data and isinstance(section_data[0], dict):
                return self._item_to_result(section_key, section_data[0])

        elif isinstance(section_data, dict):
            return {
                "found": True,
                "section": section_key,
                "title": section_key.replace("_", " ").title(),
                "answer": str(section_data),
                "url": "",
            }

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
        """Convert a dict item to a standardized search result."""
        title = (
            item.get("name")
            or item.get("title")
            or item.get("channel")
            or item.get("username")
            or item.get("company")
            or section_key.replace("_", " ").title()
        )
        url = item.get("url", "")
        description = item.get("description", "")
        answer = description or url or str(item)

        return {
            "found": True,
            "section": section_key,
            "title": title,
            "answer": answer,
            "url": url,
        }

    # ============================================================
    # Convenience Methods
    # ============================================================

    def get_section(self, university_id: str, section: str) -> Optional[Any]:
        """Retrieve a specific section from a university's data."""
        data = self._cache.get(university_id)
        if data:
            return data.get(section)
        return None

    def list_universities(self) -> List[Dict[str, str]]:
        """List all loaded universities with name and ID."""
        return [
            {"id": uid, "name": data.get("name", uid)}
            for uid, data in self._cache.items()
        ]

    def search_by_keyword(self, keyword: str) -> List[dict]:
        """
        Search all universities for a specific keyword.
        Returns a list of matching results.
        """
        results = []
        for uid, data in self._cache.items():
            kw_map = data.get("keywords", {})
            for section, keywords in kw_map.items():
                if keyword.lower() in [k.lower() for k in keywords]:
                    section_data = data.get(section)
                    if section_data:
                        result = self._extract_best_item(
                            section, section_data, keyword
                        )
                        if result:
                            result["university"] = data.get("name", uid)
                            results.append(result)
        return results


# ============================================================
# Singleton instance
# ============================================================
_knowledge_instance: Optional[KnowledgeManager] = None


def get_knowledge_manager(knowledge_dir: str = "knowledge") -> KnowledgeManager:
    """
    Get or create the singleton KnowledgeManager instance.

    Args:
        knowledge_dir: Path to the knowledge directory.

    Returns:
        The KnowledgeManager instance.
    """
    global _knowledge_instance
    if _knowledge_instance is None:
        _knowledge_instance = KnowledgeManager(knowledge_dir)
        _knowledge_instance.load_database()
    return _knowledge_instance


# ============================================================
# Example usage
# ============================================================
if __name__ == "__main__":
    km = KnowledgeManager("knowledge")
    km.load_database()

    print("\n" + "=" * 60)
    print("Loaded universities:")
    for uni in km.list_universities():
        print(f"  • {uni['name']} ({uni['id']})")

    print("\n" + "=" * 60)
    test_queries = [
        "جامعة الملك فيصل كلية إدارة الأعمال",
        "KFU كلية الهندسة",
        "الملك فيصل التقرير النهائي",
        "وين البلاك بورد حق جامعة الملك فيصل",
    ]

    for q in test_queries:
        print(f"\n🔍 Searching: '{q}'")
        result = km.search(q)
        if result.get("found"):
            print(f"   ✅ Found!")
            print(f"   University : {result.get('university')}")
            print(f"   Section    : {result.get('section')}")
            print(f"   Title      : {result.get('title')}")
            print(f"   URL        : {result.get('url')}")
        else:
            print(f"   ❌ Not found in knowledge base")
