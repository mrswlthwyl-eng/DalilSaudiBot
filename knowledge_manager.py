"""
Knowledge Manager v5.2 - Production Ready Search Engine
========================================================
Fixed: title fallback, nested dict scoring, deduplication, result limit,
phrase bonus, section type bonus.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class KnowledgeManager:
    """
    Central knowledge engine for the bot.
    Loads all university JSON files from /knowledge into memory,
    and provides smart, scored deep search capabilities.
    """

    MIN_SCORE = 10
    MAX_RESULTS = 20
    DEBUG = False

    FIELD_WEIGHTS = {
        "name": 5, "title": 5, "question": 5, "answer": 5,
        "keywords": 4, "tags": 4,
        "category": 3, "type": 3, "position": 3, "company": 3,
        "description": 2, "username": 2, "channel": 2,
        "phone": 2, "email": 2,
        "url": 1,
    }

    # Bonus points for matching specific section types
    SECTION_TYPE_BONUS = {
        "colleges": 20,
        "deanships": 15,
        "programs": 12,
        "electronic_services": 10,
        "admission": 10,
        "calendar": 10,
        "contact": 8,
        "centers": 5,
        "administrations": 5,
        "telegram": 3,
        "news": 2,
        "posts": 2,
        "channels": 2,
        "training_opportunities": 2,
        "remote_jobs": 2,
    }

    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self._cache: Dict[str, dict] = {}
        self._aliases_map: Dict[str, str] = {}
        self._search_cache: Dict[str, dict] = {}
        self._loaded = False

    # ============================================================
    # Text Normalization
    # ============================================================

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ى', 'ي')
        text = text.replace('ة', 'ه')
        text = re.sub(r'[؟?،,.:;()\[\]{}/\\\-_«»""'']', ' ', text)
        text = text.lower()
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # ============================================================
    # Loading & Caching
    # ============================================================

    def load_database(self) -> None:
        if not self.knowledge_dir.exists():
            raise FileNotFoundError(
                f"Knowledge directory not found: {self.knowledge_dir.resolve()}"
            )

        self._cache.clear()
        self._aliases_map.clear()
        self._search_cache.clear()

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

                for alias in data.get("aliases", []):
                    self._aliases_map[self.normalize(alias)] = university_id

                self._aliases_map[self.normalize(data.get("name", ""))] = university_id
                self._aliases_map[self.normalize(data.get("short_name", ""))] = university_id

            except json.JSONDecodeError as e:
                print(f"⚠️  Skipping {file_path.name}: invalid JSON — {e}")
            except Exception as e:
                print(f"⚠️  Error loading {file_path.name}: {e}")

        self._loaded = True
        print(f"✅ Knowledge Manager loaded {len(self._cache)} universities "
              f"with {len(self._aliases_map)} aliases.")

    def reload_database(self) -> None:
        self.load_database()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def universities(self) -> List[str]:
        return list(self._cache.keys())

    # ============================================================
    # University Lookup
    # ============================================================

    def find_university(self, query: str) -> Optional[str]:
        query_norm = self.normalize(query)
        if query_norm in self._aliases_map:
            return self._aliases_map[query_norm]
        for alias, uid in self._aliases_map.items():
            if query_norm in alias or alias in query_norm:
                return uid
        return None

    def get_university_data(self, university_id: str) -> Optional[dict]:
        return self._cache.get(university_id)

    # ============================================================
    # Query Cleaning
    # ============================================================

    def _clean_query(self, user_text: str) -> List[str]:
        query = self.normalize(user_text)

        for alias in sorted(self._aliases_map, key=len, reverse=True):
            if alias and alias in query:
                query = query.replace(alias, "")
                break

        stop_words = {
            "في", "عن", "ما", "هو", "هي", "هل", "وين", "اين", "ابي", "ابي",
            "عطني", "اريد", "اريد", "بخصوص", "شنو", "ايش", "كيف", "متى",
            "لو", "سمحت", "تكفي", "تكفون", "ممكن", "بغيت", "ابغى", "ابغي",
            "the", "is", "of", "in", "for", "what", "where", "how", "a", "an",
        }

        words = [
            w.strip()
            for w in query.split()
            if len(w.strip()) > 1 and w.strip() not in stop_words
        ]

        return words if words else [query.strip()]

    # ============================================================
    # Match Scoring
    # ============================================================

    def _score_match(self, query_words: List[str], text: str) -> int:
        if not text:
            return 0

        text_norm = self.normalize(text)
        text_words = set(text_norm.split())
        score = 0

        # Bonus for full phrase match
        full_phrase = " ".join(query_words)
        if full_phrase in text_norm:
            score += 20

        for qw in query_words:
            if qw in text_words:
                score += 10
            elif any(qw in tw for tw in text_words):
                score += 5
            elif any(tw in qw for tw in text_words):
                score += 3

        return score

    def _score_dict(self, query_words: List[str], item: dict) -> int:
        score = 0

        for key, value in item.items():
            if key in ("id", "aliases", "score", "_"):
                continue

            weight = self.FIELD_WEIGHTS.get(key, 1)

            if isinstance(value, str):
                score += self._score_match(query_words, value) * weight

            elif isinstance(value, list):
                for v in value:
                    if isinstance(v, str):
                        score += self._score_match(query_words, v) * weight
                    elif isinstance(v, dict):
                        score += self._score_dict(query_words, v)

            elif isinstance(value, dict):
                # ✅ Recurse into nested dicts
                score += self._score_dict(query_words, value)

        return score

    # ============================================================
    # Section Type Bonus
    # ============================================================

    def _get_section_bonus(self, section_key: str) -> int:
        """Get bonus points for matching a specific section type."""
        clean_key = section_key.split("/")[-1] if "/" in section_key else section_key
        return self.SECTION_TYPE_BONUS.get(clean_key, 0)

    # ============================================================
    # Deep Search with Scoring
    # ============================================================

    def search(self, user_text: str) -> dict:
        """Main search with query caching."""
        if not self._loaded:
            return {"found": False}

        cache_key = self.normalize(user_text)
        if cache_key in self._search_cache:
            if self.DEBUG:
                print(f"📦 Cache hit: {cache_key}")
            return self._search_cache[cache_key]

        university_id = self.find_university(user_text)
        if not university_id and len(self._cache) == 1:
            university_id = next(iter(self._cache))
        if not university_id:
            return {"found": False}

        university_data = self._cache.get(university_id)
        if not university_data:
            return {"found": False}

        query_words = self._clean_query(user_text)

        if self.DEBUG:
            print(f"🔍 Query: {user_text}")
            print(f"   Words: {query_words}")

        all_results: List[Tuple[int, dict]] = []
        self._deep_search_scored(query_words, university_data, "", all_results)

        if not all_results:
            result = {"found": False}
            self._search_cache[cache_key] = result
            return result

        # ✅ Deduplicate results
        seen = set()
        unique_results = []
        for score, result in all_results:
            key = (result.get("section", ""), result.get("title", ""), result.get("url", ""))
            if key not in seen:
                seen.add(key)
                unique_results.append((score, result))

        all_results = unique_results

        # Sort by score descending
        all_results.sort(key=lambda x: x[0], reverse=True)

        # ✅ Limit results
        all_results = all_results[:self.MAX_RESULTS]

        best_score, best_result = all_results[0]

        if best_score < self.MIN_SCORE:
            result = {"found": False}
            self._search_cache[cache_key] = result
            return result

        best_result["university"] = university_data.get("name", university_id)
        best_result["score"] = best_score

        if self.DEBUG:
            print(f"   ✅ Best: {best_result['title']} (score={best_score})")

        self._search_cache[cache_key] = best_result
        return best_result

    def _deep_search_scored(
        self,
        query_words: List[str],
        data: Any,
        path: str,
        results: List[Tuple[int, dict]],
    ) -> None:
        """Recursively search all data, score every dict, collect results."""
        if isinstance(data, dict):
            score = self._score_dict(query_words, data)
            if score > 0:
                # Add section type bonus
                section_key = path.split("/")[-1] if "/" in path else path
                score += self._get_section_bonus(section_key)

                result = self._item_to_result(path, data)
                results.append((score, result))

            # Keywords: search ALL sections dynamically
            if "keywords" in data:
                kw_data = data["keywords"]
                if isinstance(kw_data, dict):
                    for kw_key, kw_list in kw_data.items():
                        if isinstance(kw_list, list):
                            for kw in kw_list:
                                kw_score = self._score_match(query_words, kw)
                                if kw_score > 5:
                                    for section_key, section_value in data.items():
                                        if section_key in (
                                            "id", "aliases", "keywords",
                                            "name", "short_name", "city", "type"
                                        ):
                                            continue
                                        if isinstance(section_value, list):
                                            for item in section_value:
                                                if isinstance(item, dict):
                                                    s = self._score_dict(query_words, item)
                                                    if s > 0:
                                                        r = self._item_to_result(section_key, item)
                                                        results.append((s, r))

            # Recurse into all values
            for key, value in data.items():
                if key in ("id", "aliases"):
                    continue
                new_path = f"{path}/{key}" if path else key
                self._deep_search_scored(query_words, value, new_path, results)

        elif isinstance(data, list):
            for item in data:
                self._deep_search_scored(query_words, item, path, results)

        elif isinstance(data, str) and data:
            score = self._score_match(query_words, data)
            if score > 0:
                result = self._string_to_result(path, data)
                results.append((score, result))

    def _item_to_result(self, section_key: str, item: dict) -> dict:
        """Convert a dict item to a standardized search result."""
        # ✅ Safe fallback with explicit parentheses
        fallback = section_key.split("/")[-1] if "/" in section_key else section_key

        title = (
            item.get("name")
            or item.get("title")
            or item.get("question")
            or item.get("channel")
            or item.get("username")
            or item.get("company")
            or item.get("position")
            or fallback
        )
        url = item.get("url", "")
        description = item.get("description", "") or item.get("answer", "")
        answer = description if description and not description.startswith("http") else ""
        if not answer:
            answer = url

        return {
            "found": True,
            "section": fallback,
            "title": title,
            "answer": answer,
            "url": url,
        }

    def _string_to_result(self, key: str, value: str) -> dict:
        section = key.split("/")[-1] if "/" in key else key
        is_url = value.startswith("http")
        return {
            "found": True,
            "section": section,
            "title": section.replace("_", " ").title(),
            "answer": value if not is_url else "",
            "url": value if is_url else "",
        }

    # ============================================================
    # Convenience Methods
    # ============================================================

    def get_section(self, university_id: str, section: str) -> Optional[Any]:
        data = self._cache.get(university_id)
        if data:
            return data.get(section)
        return None

    def list_universities(self) -> List[Dict[str, str]]:
        return [
            {"id": uid, "name": data.get("name", uid)}
            for uid, data in self._cache.items()
        ]


# ============================================================
# Singleton
# ============================================================
_knowledge_instance: Optional[KnowledgeManager] = None


def get_knowledge_manager(knowledge_dir: str = "knowledge") -> KnowledgeManager:
    global _knowledge_instance
    if _knowledge_instance is None:
        _knowledge_instance = KnowledgeManager(knowledge_dir)
        _knowledge_instance.load_database()
    return _knowledge_instance
