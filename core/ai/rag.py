import json
import re
import logging
import math
import time
from collections import Counter
from pathlib import Path

logger = logging.getLogger("EH_Brain")

def scrub_meta_context(text: str) -> str:
    """
    Strips technical meta-context (Athena, Antigravity, workflows, etc.) 
    from retrieved world snippets to maintain immersion.
    """
    if not text: return ""
    
    # Meta Keywords to scrub (Case-insensitive)
    meta_keywords = [
        "Athena", "Antigravity", "managed workflow", "/managed", "/dm", 
        "simulation", "managed exit", "hibernated", "agent context", 
        "ingestion", "technical details", "bot", "setup phase", 
        "inter-galactic", "data pad", "workspace", "corpus",
        "Triple-Lock", "Triple Sowing", "Cortex", "Scribe", "Antigravity-Class",
        "Chronicle Weaver"
    ]
    
    for kw in meta_keywords:
        # Use regex to remove sentence/phrase containing the keyword if possible, 
        # or just replace the keyword. Here we'll do a simple case-insensitive replacement first.
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        text = pattern.sub("[REDACTED]", text)
        
    return text

_IGNORED_RAG_FILES = frozenset({
    "ADULT_RELATIONSHIP_CALIBRATION",
    "PARTY_RELATIONSHIP_ENGINE",
    "RELATIONSHIP_GRAPH_SPEC",
    "DM_RULES",
    "CULT_CORRUPTION_ENGINE",
    "EVENT_RULES",
    "FACTION_RULES",
    "PARTY_MECHANICS",
    "BOT_EXPANSION_PLAN",
    "VALIDATION_CHECKLIST",
    "PROMPT_INTERFACE",
    "NPC_AGENT_MODEL",
    "AUTO_TICK_PROTOCOL",
    "QUEST_BOTTLENECK_REPORT",
    "RUNTIME_RULESET",
    "decisions",
    "gap_analysis",
    "github_data_list",
    "github_data_list_utf8",
    "kaelrath_profile_patch",
})

_OOC_MARKERS = (
    "twitch channel data",
    "twitchclient-cdn",
    "schema.org",
    '"twitchchannel"',
    "display_name",
    "followers",
    "subscribers",
)

_BM25_INDEX_TTL = 300  # seconds; rebuild if older than this


class BM25Scorer:
    """Pure Python BM25 implementation for zero-dependency semantic retrieval."""
    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.documents = []
        self.df = Counter()
        self.doc_len = []
        self.avgdl = 0
        self.N = 0
        self.idf = {}

    def add_document(self, path: Path, content: str):
        tokens = self.tokenize(content)
        self.documents.append({'path': path, 'tokens': tokens, 'content': content})
        self.doc_len.append(len(tokens))
        for token in set(tokens):
            self.df[token] += 1

    def tokenize(self, text: str) -> list:
        return [t for t in re.findall(r'[a-z0-9_\-]+', text.lower()) if len(t) >= 4]

    def build(self):
        self.N = len(self.documents)
        if self.N == 0:
            self.avgdl = 0
            return
        self.avgdl = sum(self.doc_len) / self.N
        for token, df in self.df.items():
            self.idf[token] = math.log(1 + (self.N - df + 0.5) / (df + 0.5))

    def get_top_n(self, query: str, n=5) -> list:
        if self.N == 0:
            return []
            
        q_tokens = self.tokenize(query)
        if not q_tokens:
            return []
            
        scores = []
        for idx, doc in enumerate(self.documents):
            score = 0
            doc_tokens = doc['tokens']
            doc_len = self.doc_len[idx]
            term_freqs = Counter(doc_tokens)
            
            for token in q_tokens:
                if token not in self.idf: continue
                tf = term_freqs[token]
                num = tf * (self.k1 + 1)
                den = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                score += self.idf[token] * (num / den)
                
            # Boost score if query terms appear in the filename
            filename_tokens = self.tokenize(doc['path'].stem)
            for token in q_tokens:
                if token in filename_tokens:
                    score += self.idf.get(token, 1.5) * 2.0
                
            if score > 0:
                scores.append((score, doc))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scores[:n]]

class WorldContextManager:
    """Manages dynamic context injection from local EmberHeart knowledge."""
    def __init__(self, eh_dir: Path):
        self.eh_dir = eh_dir
        self.docs_dir = eh_dir / "docs"
        self.state_dir = eh_dir / "state"
        from core.config import CHARACTERS_DIR
        self.characters_dir = CHARACTERS_DIR
        self.settlement_path = self.state_dir / "SETTLEMENT_STATE.json"
        
        # Build keyword map from directory names instead of loading full JSON
        self.char_map = {} # ID -> Profile path
        if self.characters_dir.exists():
            for d in self.characters_dir.iterdir():
                if d.is_dir() and "_" in d.name:
                    char_id = d.name.split("_")[0]
                    self.char_map[char_id] = d / "profile.json"
        
        self.world_keys = ["stats", "state", "affairs", "situation", "kingdom", "settlement", "morale", "food", "quest", "deeds", "accomplishments"]
        self.party_keys = ["party", "inventory", "gear", "health", "hp", "worn"]
        # Reference Index
        self.ref_index = self._load_json(self.docs_dir / "DND_REFERENCE_INDEX.json")
        
        # Short-Term Memory Files
        self.journal_path = self.docs_dir / "CAMPAIGN_JOURNAL.md"
        self.deeds_path = self.state_dir / "QUEST_DEEDS.md"
        self.narrative_log_path = self.eh_dir / "state" / "NARRATIVE_LOG.md"

        # BM25 index (built once at startup, refreshed on TTL)
        self._bm25: BM25Scorer | None = None
        self._bm25_built_at: float = 0.0
        self._build_bm25_index()

    @property
    def settlement_data(self) -> dict:
        """B-23: Reload settlement data on access to ensure freshness."""
        return self._load_json(self.settlement_path) or {}

    def get_narrative_pulse(self) -> str:
        """Pulls the last 10 events from the global narrative pulse for continuity."""
        if not self.narrative_log_path.exists():
            return ""
            
        try:
            lines = self.narrative_log_path.read_text(encoding='utf-8').splitlines()
            if not lines: return ""
            
            # Last 10 lines
            recent = lines[-10:]
            return "\n## RECENT GLOBAL EVENTS (Cross-Channel):\n" + "\n".join(recent)
        except Exception as e:
            logger.error(f"Error reading narrative log: {e}")
            return ""

    def get_sovereign_briefing(self) -> str:
        """Pulls the most recent history for absolute awareness."""
        briefing = []
        
        if self.journal_path.exists():
            content = self.journal_path.read_text(encoding='utf-8')
            # Get latest session summary
            match = re.search(r"## (.*?) - Session.*?\n(.*?)(?=\n##|$)", content, re.S)
            if match:
                briefing.append(f"### LATEST SESSION: {match.group(1)}\n{match.group(2).strip()}")

        if self.deeds_path.exists():
            content = self.deeds_path.read_text(encoding='utf-8')
            # Get last 3 deeds
            deeds = re.findall(r"### (.*?)\n(>.*?)\n", content, re.S)
            if deeds:
                recent_deeds = "\n".join([f"- {d[0]}: {d[1].strip()}" for d in deeds[-3:]])
                briefing.append(f"### RECENT ACCOMPLISHMENTS:\n{recent_deeds}")

        if not briefing: return ""
        return scrub_meta_context("\n## RECENT CHRONICLE RECORDS:\n" + "\n".join(briefing))

    def _load_json(self, path: Path):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding='utf-8'))
            except Exception:
                return {}
        return {}

    def _resolve_reference_path(self, raw_path: str) -> Path | None:
        """Resolve indexed reference paths from legacy and reborn layouts."""
        raw = str(raw_path or "").strip().replace("\\", "/")
        if not raw:
            return None

        raw = raw.lstrip("./")
        candidates = []

        def add(path: Path):
            if path not in candidates:
                candidates.append(path)

        add(self.eh_dir / Path(raw))

        trimmed = raw
        for prefix in ("EmberHeartReborn/", "EmberHeart/"):
            if trimmed.lower().startswith(prefix.lower()):
                trimmed = trimmed[len(prefix):]
                break

        add(self.eh_dir / Path(trimmed))

        low = trimmed.lower()
        docs_marker = "/docs/"
        if docs_marker in low:
            idx = low.find(docs_marker)
            docs_rel = trimmed[idx + len(docs_marker):]
            add(self.docs_dir / Path(docs_rel))

        if low.startswith("docs/"):
            add(self.eh_dir / Path(trimmed))

        add(self.docs_dir / Path(trimmed).name)

        for path in candidates:
            if path.exists() and path.is_file():
                return path
        return None

    def _build_bm25_index(self) -> None:
        """Build (or rebuild) the BM25 retrieval index from docs_dir."""
        bm25 = BM25Scorer()
        if self.docs_dir.exists():
            for path in self.docs_dir.glob("*"):
                if not path.is_file() or path.stem in _IGNORED_RAG_FILES:
                    continue
                try:
                    content = path.read_text(encoding="utf-8")
                    if not any(m in content.lower() for m in _OOC_MARKERS):
                        bm25.add_document(path, content)
                except Exception as e:
                    logger.error("BM25 index: error reading %s: %s", path.name, e)
        bm25.build()
        self._bm25 = bm25
        self._bm25_built_at = time.time()
        logger.info("BM25 index built: %d documents indexed.", bm25.N)

    def _build_bm25_index_if_stale(self) -> None:
        """Rebuild the BM25 index if it is older than _BM25_INDEX_TTL seconds."""
        if self._bm25 is None or (time.time() - self._bm25_built_at) > _BM25_INDEX_TTL:
            self._build_bm25_index()

    def refresh_index(self) -> None:
        """Force an immediate rebuild of the BM25 index. Call after docs change."""
        self._build_bm25_index()

    def get_relevant_context(self, message: str) -> str:
        """Scan message for keywords and return relevant world snippets."""
        message_low = message.lower()
        context_snippets = []

        # 1. Check for Characters (On-demand loading)
        for char_id, profile_path in self.char_map.items():
            # Check for name/ID in message before loading full JSON
            # This is a bit tricky since we don't have names yet, but we can check the folder names from char_map
            # or just load the profile once per message (max 60 loads isn't huge, but let's be smarter)
            
            # Extract name from profile path/dir for quick check
            char_folder_name = profile_path.parent.name
            # folder is "ID_Name_Parts", let's split
            parts = char_folder_name.lower().split("_")
            
            # B-21: Bump threshold to 4+ chars to avoid false positives on "the", "red", "old", etc.
            if any(p in message_low for p in parts if len(p) > 4):
                # Load full profile for verification and sketch building
                try:
                    n = json.loads(profile_path.read_text(encoding='utf-8'))
                    name = n.get("name", "").lower()
                    
                    # More flexible match: check if name OR parts of name are in message
                    name_words = re.findall(r'\w+', name)
                    # B-21: Bump threshold to 4+ chars
                    if any(w in message_low for w in name_words if len(w) > 4) or char_id.lower() in message_low:
                        # Check Relationships
                        from core.relationships import relationship_manager
                        rel_data = relationship_manager.get_relationship("PC-01", char_id)
                        rel_labels = relationship_manager.get_status_labels(rel_data)
                        rel_text = ", ".join(rel_labels) if rel_labels else "Neutral"
                        
                        context_snippets.append(f"### Character Sketch: {n.get('name')}\nRole: {n.get('role', n.get('class'))}\nRelationship to You (Kaelrath): {rel_text}\nMotivation: {n.get('motivation', 'Unknown')}\nBio: {n.get('bio', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Error loading profile for {char_id}: {e}")

        # 2. Query cached BM25 Index for Docs
        self._build_bm25_index_if_stale()
        top_docs = self._bm25.get_top_n(message_low, n=4)
        for doc in top_docs:
            clean_name = doc['path'].stem.replace('_', ' ').title()
            context_snippets.append(scrub_meta_context(f"### Historical Record: {clean_name}\n{doc['content'][:800]}"))

        # 3. Check for World/Settlement Stats
        if any(k in message_low for k in self.world_keys):
            s_root = self.settlement_data.get("settlement", {})
            core = s_root.get("core_status", {})
            context_snippets.append(f"REALM STATUS: Morale: {core.get('morale', 'Stable')}, Food: {core.get('food_status', 'Adequate')}, Threat: {core.get('tremor_threat', 'Low')}")

        # 4. Check for Party
        if any(k in message_low for k in self.party_keys):
            party_summaries = []
            for char_id, profile_path in self.char_map.items():
                if char_id.startswith("PC-"):
                    try:
                        # Load profile for name, state for HP
                        profile = json.loads(profile_path.read_text(encoding='utf-8'))
                        state_path = profile_path.parent / "state.json"
                        hp = "Full"
                        if state_path.exists():
                            st = json.loads(state_path.read_text(encoding='utf-8'))
                            hp = st.get('hp_current', 'Full')
                        party_summaries.append(f"{profile.get('name')} (HP: {hp})")
                    except Exception:
                        pass
            if party_summaries:
                context_snippets.append(f"PARTY STATUS: {', '.join(party_summaries)}")

        # 5. Check for D&D Reference Matches (Spells/Items)
        found_ref = 0
        for ref_key, ref_info in self.ref_index.items():
            if ref_key in message_low:
                ref_path = self._resolve_reference_path(ref_info.get("path", ""))
                if ref_path:
                    content = ref_path.read_text(encoding='utf-8')
                    context_snippets.append(f"REFERENCE ({ref_info['title']}): {content[:800]}")
                    found_ref += 1
                if found_ref >= 3:
                    break  # Limit to 3 items to avoid context overflow

        if not context_snippets:
            return ""

        return scrub_meta_context("\n## ADDITIONAL WORLD INSIGHTS:\n" + "\n".join(context_snippets))



