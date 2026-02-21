import json
import re
import logging
from pathlib import Path

logger = logging.getLogger("EH_Brain")

class WorldContextManager:
    """Manages dynamic context injection from local EmberHeart knowledge."""
    def __init__(self, eh_dir: Path):
        self.eh_dir = eh_dir
        self.docs_dir = eh_dir / "docs"
        self.state_dir = eh_dir / "state"
        
        raw_npc_data = self._load_json(self.state_dir / "NPC_STATE_FULL.json")
        self.npc_data = raw_npc_data.get("npcs", []) if isinstance(raw_npc_data, dict) else raw_npc_data
        
        self.party_data = self._load_json(self.state_dir / "PARTY_STATE.json")
        self.settlement_data = self._load_json(self.state_dir / "SETTLEMENT_STATE.json")
        
        # Build keywords for faster matching
        self.npc_names = {n.get("name", "").lower(): n for n in self.npc_data if isinstance(n, dict) and n.get("name")}
        self.world_keys = ["stats", "kingdom", "settlement", "morale", "food", "quest", "deeds", "accomplishments"]
        self.party_keys = ["party", "inventory", "gear", "health", "hp", "worn"]
        
        # Reference Index
        self.ref_index = self._load_json(self.docs_dir / "DND_REFERENCE_INDEX.json")
        
        # Short-Term Memory Files
        self.journal_path = self.docs_dir / "CAMPAIGN_JOURNAL.md"
        self.deeds_path = self.state_dir / "QUEST_DEEDS.md"

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
        return "\n## SOVEREIGN BRIEFING (Core Awareness):\n" + "\n".join(briefing)

    def _load_json(self, path: Path):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding='utf-8'))
            except:
                return {}
        return {}

    def get_relevant_context(self, message: str) -> str:
        """Scan message for keywords and return relevant world snippets."""
        message_low = message.lower()
        context_snippets = []

        # 1. Check for NPCs (Name Match OR Bio/Connection Match)
        for n in self.npc_data:
            if not isinstance(n, dict): continue
            name = n.get("name", "").lower()
            bio = n.get("bio", "").lower()
            conn = n.get("connection", "").lower()
            
            if name and name in message_low or (bio and any(word in message_low for word in name.split())) or (conn and any(word in message_low for word in name.split())):
                # If specific NPC name is mentioned, or words from its name appear in context
                npc_id = n.get('id', '??')
                context_snippets.append(f"NAME: {n.get('name')} [ID: {npc_id}] | ROLE: {n.get('role', n.get('class'))} | MOTIVATION: {n.get('motivation', 'Unknown')}\nBIO: {n.get('bio', bio[:200])}")

        # 2. Check for File Matches (e.g., KAELRATH_PROFILE_PATCH.md)
        for path in self.docs_dir.glob("*"):
            if path.is_file() and any(word in path.name.lower() for word in message_low.split()):
                if len(context_snippets) < 5: # Limit to avoid bloat
                    try:
                        content = path.read_text(encoding='utf-8')
                        context_snippets.append(f"FILE ({path.name}): {content[:500]}")
                    except Exception as e:
                        logger.error(f"Error reading context file {path.name}: {e}")

        # 3. Check for World/Settlement Stats
        if any(k in message_low for k in self.world_keys):
            core = self.settlement_data.get("core_status", {})
            context_snippets.append(f"REALM STATUS: Morale: {core.get('morale')}, Food: {core.get('food_status')}, Threat: {core.get('tremor_threat')}")

        # 4. Check for Party
        if any(k in message_low for k in self.party_keys):
            party_sum = ", ".join([f"{p.get('name')} (HP: {p.get('hp_current', 'Full')})" for p in self.party_data if isinstance(p, dict)])
            context_snippets.append(f"PARTY STATUS: {party_sum}")

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

        return "\n## NEW WORLD KNOWLEDGE (Injected Context):\n" + "\n".join(context_snippets)
