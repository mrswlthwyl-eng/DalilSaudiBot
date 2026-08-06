"""
Knowledge Manager v7.2 - Block Generic Sections
================================================
- MIN_SCORE = 50
- Blocks kfu_training_knowledge, kfu_external_opportunities, kfu_specific_info
- Better title handling
- Falls back to AI for weak/generic matches
"""

import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set


class KnowledgeManager:

    MIN_SCORE = 50
    MAX_RESULTS = 20
    MAX_CACHE_SIZE = 1000
    DEBUG = False

    # Sections to block from appearing in results
    BLOCKED_SECTIONS = {
        "kfu_training_knowledge",
        "kfu_external_opportunities",
        "kfu_specific_info",
    }

    FIELD_WEIGHTS = {
        "name": 5, "title": 5, "question": 5, "answer": 5,
        "keywords": 4, "tags": 4, "aliases": 2,
        "category": 3, "type": 3, "position": 3, "company": 3,
        "description": 2, "username": 2, "channel": 2,
        "phone": 2, "email": 2,
        "url": 1,
    }

    CONTENT_KEYS = {
        "url", "name", "title", "description", "tags",
        "category", "type", "username", "channel", "company",
        "position", "phone", "email", "question", "answer",
        "keywords", "aliases",
    }

    SECTION_TYPE_BONUS = {
        "colleges": 20, "deanships": 15, "programs": 12,
        "electronic_services": 10, "admission": 10, "calendar": 10,
        "contact": 8, "centers": 5, "administrations": 5,
        "telegram": 3, "news": 2, "posts": 2, "channels": 2,
        "training_opportunities": 2, "remote_jobs": 2,
    }

    INTENT_MAP = {
        "كلية": (["colleges"], 50), "كليات": (["colleges"], 50),
        "عمادة": (["deanships"], 50), "عمادات": (["deanships"], 50),
        "مركز": (["centers"], 40), "مراكز": (["centers"], 40),
        "برنامج": (["programs"], 40), "برامج": (["programs"], 40),
        "خدمة": (["electronic_services"], 40), "خدمات": (["electronic_services"], 40),
        "تقويم": (["calendar"], 40),
        "قبول": (["admission"], 40), "تسجيل": (["admission"], 40),
        "تدريب": (["telegram", "training_opportunities"], 35),
        "وظيفة": (["training_opportunities", "remote_jobs"], 35),
        "وظائف": (["training_opportunities", "remote_jobs"], 35),
        "قناة": (["telegram"], 35), "قنوات": (["telegram"], 35),
        "تلجرام": (["telegram"], 35), "تيليجرام": (["telegram"], 35),
        "هاتف": (["contact"], 40),
        "رقم": (["contact"], 35),
        "بريد": (["contact", "electronic_services"], 35),
        "إيميل": (["contact", "electronic_services"], 35),
        "ايميل": (["contact", "electronic_services"], 35),
        "منحة": (["scholarships"], 40), "منح": (["scholarships"], 40),
        "مكتبة": (["library"], 40),
        "بلاك": (["electronic_services"], 40),
        "blackboard": (["electronic_services"], 40),
        "دبلوم": (["programs", "diploma"], 40),
        "ماجستير": (["programs"], 40), "دكتوراه": (["programs"], 40),
        "بكالوريوس": (["programs"], 40),
        "سياسة": (["policies"], 35), "سياسات": (["policies"], 35),
        "تقرير": (["telegram"], 30), "تقارير": (["telegram"], 30),
        "نموذج": (["telegram"], 30), "نماذج": (["telegram"], 30),
        "معلومات": (["__info__"], 60), "تعريف": (["__info__"], 60),
        "نبذه": (["__info__"], 60), "نبذة": (["__info__"], 60),
        "رابط": (["__links__"], 60), "روابط": (["__links__"], 60),
        "موقع": (["__links__"], 60),
    }

    GREETINGS = {
        "السلام عليكم", "وعليكم السلام", "سلام", "هلا", "اهلا", "مرحبا",
        "صباح الخير", "صباح النور", "مساء الخير", "مساء النور",
        "ياهلا", "يا هلا", "حياك", "حياكم", "الله حي", "هلا بك",
        "hello", "hi", "hey",
    }

    QUESTION_WORDS = {
        "متى", "وين", "اين", "كيف", "كم", "ايش", "شنو", "ما", "هل",
        "عطني", "اعطني", "اريد", "ابي", "ابغى", "بغيت",
        "ممكن", "يفيد", "تقدر", "عندك", "تعرف",
    }

    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self._cache: Dict[str, dict] = {}
        self._aliases_map: Dict[str, str] = {}
        self._item_aliases: Dict[str, set] = {}
        self._search_cache: OrderedDict = OrderedDict()
        self._loaded = False

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

    def is_greeting(self, text: str) -> bool:
        normalized = self.normalize(text)
        words = set(normalized.split())
        for greeting in self.GREETINGS:
            greeting_norm = self.normalize(greeting)
            if greeting_norm in normalized or all(w in words for w in greeting_norm.split()):
                return True
        return False

    def is_just_university_name(self, text: str) -> bool:
        normalized = self.normalize(text)
        words = normalized.split()
        if len(words) <= 4:
            for alias in self._aliases_map:
                if alias and alias in normalized:
                    if not any(qw in words for qw in self.QUESTION_WORDS):
                        return True
        return False

    def load_database(self) -> None:
        if not self.knowledge_dir.exists():
            raise FileNotFoundError(f"Knowledge directory not found: {self.knowledge_dir.resolve()}")
        self._cache.clear()
        self._aliases_map.clear()
        self._item_aliases.clear()
        self._search_cache.clear()
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
                    self._aliases_map[self.normalize(alias)] = university_id
                self._aliases_map[self.normalize(data.get("name", ""))] = university_id
                self._aliases_map[self.normalize(data.get("short_name", ""))] = university_id
                self._collect_item_aliases(university_id, data)
            except json.JSONDecodeError as e:
                print(f"⚠️  Skipping {file_path.name}: invalid JSON — {e}")
            except Exception as e:
                print(f"⚠️  Error loading {file_path.name}: {e}")
        self._loaded = True
        print(f"✅ Knowledge Manager loaded {len(self._cache)} universities with {len(self._aliases_map)} aliases.")

    def _collect_item_aliases(self, university_id: str, data: Any) -> None:
        if university_id not in self._item_aliases:
            self._item_aliases[university_id] = set()
        if isinstance(data, dict):
            if "aliases" in data and isinstance(data["aliases"], list):
                for alias in data["aliases"]:
                    self._item_aliases[university_id].add(self.normalize(alias))
            for key, value in data.items():
                if key not in ("id",):
                    self._collect_item_aliases(university_id, value)
        elif isinstance(data, list):
            for item in data:
                self._collect_item_aliases(university_id, item)

    def reload_database(self) -> None:
        self.load_database()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def universities(self) -> List[str]:
        return list(self._cache.keys())

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

    def get_university_context_for_ai(self, university_id: str) -> str:
        data = self._cache.get(university_id)
        if not data:
            return ""
        parts = []
        name = data.get("name", "")
        city = data.get("city", "")
        website = data.get("info", {}).get("website", "")
        phone = data.get("contact", {}).get("phone", "")
        email = data.get("contact", {}).get("email", "")
        parts.append(f"الجامعة: {name}")
        if city: parts.append(f"المدينة: {city}")
        if website: parts.append(f"الموقع الرسمي: {website}")
        if phone: parts.append(f"رقم الهاتف: {phone}")
        if email: parts.append(f"البريد الإلكتروني: {email}")
        colleges = data.get("colleges", [])
        if colleges:
            college_names = [c.get("name", "") for c in colleges if c.get("name")]
            if college_names: parts.append(f"الكليات: {', '.join(college_names)}")
        deanships = data.get("deanships", [])
        if deanships:
            deanship_names = [d.get("name", "") for d in deanships if d.get("name")]
            if deanship_names: parts.append(f"العمادات: {', '.join(deanship_names)}")
        return "\n".join(parts)

    def _detect_intent(self, query_words: List[str]) -> Tuple[Optional[List[str]], int]:
        for word in query_words:
            if word in self.INTENT_MAP:
                return self.INTENT_MAP[word]
        return None, 0

    def _clean_query(self, user_text: str, university_id: str) -> List[str]:
        query = self.normalize(user_text)
        for alias in sorted(self._aliases_map, key=len, reverse=True):
            if alias and alias in query:
                query = query.replace(alias, "")
                break
        if university_id in self._item_aliases:
            for alias in sorted(self._item_aliases[university_id], key=len, reverse=True):
                if alias and alias in query:
                    query = query.replace(alias, "")
                    break
        stop_words = {
            "في", "عن", "ما", "هو", "هي", "هل", "وين", "اين", "ابي",
            "عطني", "اريد", "اريد", "بخصوص", "شنو", "ايش", "كيف", "متى",
            "لو", "سمحت", "تكفي", "تكفون", "ممكن", "بغيت", "ابغى", "ابغي",
        }
        words = [w.strip() for w in query.split() if len(w.strip()) > 1 and w.strip() not in stop_words]
        return words if words else []

    def _is_content_item(self, item: dict) -> bool:
        return bool(set(item.keys()) & self.CONTENT_KEYS)

    def _score_match(self, query_words: List[str], text: str) -> int:
        if not text: return 0
        text_norm = self.normalize(text)
        text_words = set(text_norm.split())
        score = 0
        full_phrase = " ".join(query_words)
        if full_phrase in text_norm: score += 20
        for qw in query_words:
            if qw in text_words: score += 10
            elif any(qw in tw for tw in text_words): score += 5
            elif any(tw in qw for tw in text_words): score += 3
        return score

    def _score_dict(self, query_words: List[str], item: dict) -> int:
        score = 0
        for key, value in item.items():
            if key in ("id", "score", "_"): continue
            weight = self.FIELD_WEIGHTS.get(key, 1)
            if isinstance(value, str): score += self._score_match(query_words, value) * weight
            elif isinstance(value, list):
                for v in value:
                    if isinstance(v, str): score += self._score_match(query_words, v) * weight
                    elif isinstance(v, dict): score += self._score_dict(query_words, v)
            elif isinstance(value, dict): score += self._score_dict(query_words, value)
        return score

    def _get_section_bonus(self, section_key: str) -> int:
        clean_key = section_key.split("/")[-1] if "/" in section_key else section_key
        return self.SECTION_TYPE_BONUS.get(clean_key, 0)

    def _cache_key(self, university_id: str, user_text: str) -> Tuple[str, str]:
        return (university_id, self.normalize(user_text))

    def _set_cache(self, key: Tuple[str, str], value: dict) -> None:
        if len(self._search_cache) >= self.MAX_CACHE_SIZE: self._search_cache.popitem(last=False)
        self._search_cache[key] = value

    def _get_cache(self, key: Tuple[str, str]) -> Optional[dict]:
        if key in self._search_cache:
            self._search_cache.move_to_end(key)
            return self._search_cache[key]
        return None

    # ============================================================
    # Main Search
    # ============================================================
    def search(self, user_text: str) -> dict:
        if not self._loaded: return {"found": False}
        if self.is_greeting(user_text): return {"found": False, "is_greeting": True}

        university_id = self.find_university(user_text)
        if not university_id: return {"found": False}

        if self.is_just_university_name(user_text):
            uni_data = self._cache.get(university_id, {})
            uni_name = uni_data.get("name", "الجامعة")
            return {
                "found": True, "is_just_name": True,
                "university": uni_name, "university_id": university_id,
                "title": uni_name,
                "answer": f"نعم، {uni_name}. تفضل، وش تحب تعرف عنها؟\n\nأقدر أساعدك في:\n• الكليات والتخصصات\n• العمادات والخدمات\n• القبول والتسجيل\n• التدريب التطبيقي\n• أي سؤال آخر",
                "url": uni_data.get("info", {}).get("website", ""), "section": "greeting",
            }

        ck = self._cache_key(university_id, user_text)
        cached = self._get_cache(ck)
        if cached is not None: return cached

        university_data = self._cache.get(university_id)
        if not university_data: return {"found": False}

        query_words = self._clean_query(user_text, university_id)
        if not query_words or all(len(w) < 2 for w in query_words):
            result = {"found": False}; self._set_cache(ck, result); return result

        target_sections, intent_bonus = self._detect_intent(query_words)

        if target_sections == ["__info__"]:
            info_data = university_data.get("info", {})
            description = info_data.get("description") or info_data.get("about") or ""
            if not description:
                name = university_data.get("name", "")
                city = university_data.get("city", "")
                website = info_data.get("website", "")
                description = f"{name} في {city}. الموقع: {website}"
            result = {
                "found": True, "title": university_data.get("name", ""),
                "answer": description, "url": info_data.get("website", ""),
                "section": "info", "university": university_data.get("name", university_id), "score": 100,
            }
            self._set_cache(ck, result); return result

        all_results: List[Tuple[int, dict]] = []
        scored_ids: Set[int] = set()

        if target_sections:
            for section_key in target_sections:
                if section_key in university_data:
                    self._deep_search_scored(query_words, university_data[section_key], section_key, all_results, scored_ids)
            all_results = [(s + intent_bonus, r) for s, r in all_results]
        else:
            self._deep_search_scored(query_words, university_data, "", all_results, scored_ids)

        if not all_results:
            result = {"found": False}; self._set_cache(ck, result); return result

        seen = set()
        unique_results = []
        for score, result in all_results:
            key = (result.get("section", ""), result.get("title", ""), result.get("url", ""))
            if key not in seen: seen.add(key); unique_results.append((score, result))

        all_results = unique_results
        all_results.sort(key=lambda x: x[0], reverse=True)
        all_results = all_results[:self.MAX_RESULTS]

        best_score, best_result = all_results[0]

        if best_score < self.MIN_SCORE:
            result = {"found": False}; self._set_cache(ck, result); return result

        best_result["university"] = university_data.get("name", university_id)
        best_result["score"] = best_score
        self._set_cache(ck, best_result)
        return best_result

    # ============================================================
    # Deep Search
    # ============================================================
    def _deep_search_scored(self, query_words, data, path, results, scored_ids):
        if isinstance(data, dict):
            item_id = id(data)
            
            # ✅ Check if this section should be blocked
            section_name = path.split("/")[-1] if "/" in path else path
            
            if path and self._is_content_item(data) and item_id not in scored_ids:
                # ✅ Block generic sections
                if section_name not in self.BLOCKED_SECTIONS:
                    scored_ids.add(item_id)
                    score = self._score_dict(query_words, data)
                    if score > 0:
                        section_key = path.split("/")[-1] if "/" in path else path
                        score += self._get_section_bonus(section_key)
                        results.append((score, self._item_to_result(path, data)))

            kw_data = data.get("keywords")
            if kw_data and item_id not in scored_ids:
                scored_ids.add(item_id)
                self._process_keywords(query_words, kw_data, data, results, scored_ids)

            for key, value in data.items():
                if key in ("id",): continue
                # ✅ Skip blocked sections entirely
                if key in self.BLOCKED_SECTIONS: continue
                new_path = f"{path}/{key}" if path else key
                self._deep_search_scored(query_words, value, new_path, results, scored_ids)

        elif isinstance(data, list):
            for item in data:
                self._deep_search_scored(query_words, item, path, results, scored_ids)
        elif isinstance(data, str) and data:
            score = self._score_match(query_words, data)
            if score > 0:
                results.append((score, self._string_to_result(path, data)))

    def _process_keywords(self, query_words, kw_data, parent_data, results, scored_ids):
        if isinstance(kw_data, dict):
            for kw_list in kw_data.values():
                if isinstance(kw_list, list):
                    for kw in kw_list:
                        if self._score_match(query_words, kw) > 5:
                            self._score_related_sections(query_words, parent_data, results, scored_ids)
                            break
        elif isinstance(kw_data, list):
            for kw in kw_data:
                if self._score_match(query_words, kw) > 5:
                    self._score_related_sections(query_words, parent_data, results, scored_ids)
                    break

    def _score_related_sections(self, query_words, parent_data, results, scored_ids):
        skip_keys = {"id", "aliases", "keywords", "name", "short_name", "city", "type"}
        for section_key, section_value in parent_data.items():
            if section_key in skip_keys: continue
            if section_key in self.BLOCKED_SECTIONS: continue
            if isinstance(section_value, list):
                for item in section_value:
                    if isinstance(item, dict) and id(item) not in scored_ids:
                        scored_ids.add(id(item))
                        s = self._score_dict(query_words, item)
                        if s > 0:
                            s += self._get_section_bonus(section_key)
                            results.append((s, self._item_to_result(section_key, item)))

    def _item_to_result(self, section_key: str, item: dict) -> dict:
        fallback = section_key.split("/")[-1] if "/" in section_key else section_key
        title = (
            item.get("name") or item.get("title") or item.get("question")
            or item.get("channel") or item.get("username")
            or item.get("company") or item.get("position")
            or item.get("description")
            or fallback
        )
        if not title or title == fallback:
            title = item.get("description") or fallback.replace("_", " ").title()
        url = item.get("url", "")
        description = item.get("description", "") or item.get("answer", "")
        answer = description if description and not description.startswith("http") else ""
        if not answer: answer = url
        return {"found": True, "section": fallback, "title": title, "answer": answer, "url": url}

    def _string_to_result(self, key: str, value: str) -> dict:
        section = key.split("/")[-1] if "/" in key else key
        is_url = value.startswith("http")
        return {
            "found": True, "section": section,
            "title": section.replace("_", " ").title(),
            "answer": value if not is_url else "",
            "url": value if is_url else "",
        }

    def get_section(self, university_id: str, section: str) -> Optional[Any]:
        data = self._cache.get(university_id)
        if data: return data.get(section)
        return None

    def list_universities(self) -> List[Dict[str, str]]:
        return [{"id": uid, "name": data.get("name", uid)} for uid, data in self._cache.items()]


_knowledge_instance: Optional[KnowledgeManager] = None


def get_knowledge_manager(knowledge_dir: str = "knowledge") -> KnowledgeManager:
    global _knowledge_instance
    if _knowledge_instance is None:
        _knowledge_instance = KnowledgeManager(knowledge_dir)
        _knowledge_instance.load_database()
    return _knowledge_instance
