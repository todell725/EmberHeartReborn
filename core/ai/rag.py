import json
import re
import logging
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

        IGNORED_RAG_FILES = {
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
            "github_data_list"
        }

        for path in self.docs_dir.glob("*"):
            if path.is_file() and any(word in path.name.lower() for word in message_low.split()):
                if path.stem in IGNORED_RAG_FILES: continue
                
                if len(context_snippets) < 5: # Limit to avoid bloat
                    try:
                        content = path.read_text(encoding='utf-8')
                        clean_name = path.stem.replace('_', ' ').title()
                        context_snippets.append(scrub_meta_context(f"### Historical Record: {clean_name}\n{content[:500]}"))
                    except Exception as e:
                        logger.error(f"Error reading context file {path.name}: {e}")

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
        # Using a simple keyword match for item/spell names
        found_ref = 0
        for ref_key, ref_info in self.ref_index.items():
            if ref_key in message_low:
                # Update path logic: D&D Reference points relative to original root, so mapped to docs here
                ref_filename = Path(ref_info['path']).name
                ref_path = self.docs_dir / ref_filename
                
                # Check original if not in reborn docs
                if not ref_path.exists():
                     ref_path = self.eh_dir.parent / "EmberHeart" / ref_info['path']
                     
                if ref_path.exists():
                    content = ref_path.read_text(encoding='utf-8')
                    context_snippets.append(f"REFERENCE ({ref_info['title']}): {content[:800]}")
                    found_ref += 1
                if found_ref >= 3: break # Limit to 3 items to avoid context overflow

        if not context_snippets:
            return ""

        return scrub_meta_context("\n## ADDITIONAL WORLD INSIGHTS:\n" + "\n".join(context_snippets))
