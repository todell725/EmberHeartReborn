import json
import logging
import re
from pathlib import Path

logger = logging.getLogger("EH_Core")

# Standardized Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_DIR = ROOT_DIR / "state"
CHARACTERS_DIR = ROOT_DIR / "characters"

# D&D 5E XP Thresholds
XP_THRESHOLDS = {
    1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500, 6: 14000, 7: 23000, 8: 34000,
    9: 48000, 10: 64000, 11: 85000, 12: 100000, 13: 120000, 14: 140000,
    15: 165000, 16: 195000, 17: 225000, 18: 265000, 19: 305000, 20: 355000,
}

# Identity Registry Base
_DM_IDENTITY = {"name": "The Chronicle Weaver", "avatar": "https://i.imgur.com/pYIe6oM.png", "id": "DM-00"}

IDENTITIES = {
    "DM": _DM_IDENTITY,
    "DM-00": _DM_IDENTITY,
    "The Chronicle Weaver": _DM_IDENTITY,
    "STEWARD": {"name": "Royal Steward", "avatar": "https://i.imgur.com/4zYf4zD.png"},
    "SHADOW": {"name": "Your Shadow", "avatar": "https://i.imgur.com/u7yH8zW.png"},
    "NPC": {"name": "NPC", "avatar": "https://i.imgur.com/pYIe6oM.png"},
    "RUMORS": {"name": "The Rumor Mill", "avatar": "https://i.imgur.com/lO1nIOn.png"},
}

_IDENTITY_ID_RE = re.compile(r"\b(?:EH|PC|DM)-\d+\b", re.IGNORECASE)


def _register_identity_aliases(char_name: str, entry: dict):
    """Register common name aliases so model variants still resolve avatars/identities."""
    if not char_name:
        return

    clean_name = str(char_name).strip()
    if clean_name and clean_name not in IDENTITIES:
        IDENTITIES[clean_name] = entry

    # Remove quoted nicknames: Silvara "Silvy" -> Silvara
    no_quotes = re.sub(r'\s*".*?"\s*', ' ', clean_name).strip()
    no_quotes = re.sub(r'\s+', ' ', no_quotes)
    if no_quotes and no_quotes not in IDENTITIES:
        IDENTITIES[no_quotes] = entry

    # Remove bracketed IDs if they ever appear in names
    no_brackets = re.sub(r'\s*\[.*?\]\s*', ' ', clean_name).strip()
    no_brackets = re.sub(r'\s+', ' ', no_brackets)
    if no_brackets and no_brackets not in IDENTITIES:
        IDENTITIES[no_brackets] = entry

    # First-name alias: Vaelis Thorne -> Vaelis
    first_name = no_quotes.split()[0] if no_quotes else ""
    if first_name and first_name not in IDENTITIES:
        IDENTITIES[first_name] = entry


def normalize_identity_id(value: str) -> str:
    """Normalize identity IDs (EH-01/PC-02/DM-00) from free text."""
    if not value:
        return ""
    text = str(value).strip().upper()
    match = _IDENTITY_ID_RE.search(text)
    return match.group(0).upper() if match else ""


def resolve_identity(speaker: str = "", speaker_id: str = ""):
    """
    Resolve identity by ID first, then by name aliases.
    Returns (identity_dict_or_none, canonical_name, canonical_id).
    """
    # ID-first resolution
    canonical_id = normalize_identity_id(speaker_id or speaker)
    # Canonical DM identity: only DM-00 is valid in this world.
    if canonical_id.startswith("DM-") and canonical_id != "DM-00":
        canonical_id = "DM-00"

    if canonical_id and canonical_id in IDENTITIES and isinstance(IDENTITIES[canonical_id], dict):
        token = IDENTITIES[canonical_id]
        return token, str(token.get("name", "")).strip(), canonical_id

    # Name resolution
    name = str(speaker or "").strip()
    if not name:
        return None, "", ""

    # Remove common model wrappers
    name_clean = re.sub(r"\[[^\]]+\]", "", name)
    name_clean = re.sub(r"\b(?:EH|PC|DM)-?\d+\b", "", name_clean, flags=re.IGNORECASE)
    name_clean = re.sub(r"\s+", " ", name_clean).strip(' :-\t\n\r"')
    if not name_clean:
        return None, "", canonical_id

    token = IDENTITIES.get(name_clean)
    if isinstance(token, dict):
        return token, str(token.get("name", name_clean)).strip(), str(token.get("id", canonical_id or "")).upper()

    # Case-insensitive exact key match
    low = name_clean.lower()
    match_key = next((k for k in IDENTITIES if isinstance(k, str) and k.lower() == low), None)
    if match_key:
        token = IDENTITIES[match_key]
        if isinstance(token, dict):
            return token, str(token.get("name", name_clean)).strip(), str(token.get("id", canonical_id or "")).upper()

    # Fuzzy contains fallback
    fuzzy_key = next(
        (
            k for k in IDENTITIES
            if isinstance(k, str) and (low in k.lower() or k.lower() in low)
        ),
        None,
    )
    if fuzzy_key:
        token = IDENTITIES[fuzzy_key]
        if isinstance(token, dict):
            return token, str(token.get("name", name_clean)).strip(), str(token.get("id", canonical_id or "")).upper()

    return None, name_clean, canonical_id


def list_identity_roster(prefixes=None, exclude_ids=None):
    """Return sorted unique identity records: [{'id','name','avatar'}]."""
    prefixes = {str(p).upper() for p in (prefixes or [])}
    exclude_ids = {str(i).upper() for i in (exclude_ids or [])}

    unique = {}
    for key, value in IDENTITIES.items():
        if not isinstance(value, dict):
            continue
        identity_id = normalize_identity_id(value.get("id") or key)
        if not identity_id:
            continue
        if prefixes and not any(identity_id.startswith(p) for p in prefixes):
            continue
        if identity_id in exclude_ids:
            continue
        if identity_id not in unique:
            unique[identity_id] = {
                "id": identity_id,
                "name": str(value.get("name", "")).strip(),
                "avatar": value.get("avatar"),
            }

    return [unique[k] for k in sorted(unique.keys())]


def load_npc_identities():
    """Populates IDENTITIES with data from the individual character profile files."""
    if not CHARACTERS_DIR.exists():
        logger.warning(f"Characters directory not found: {CHARACTERS_DIR}")
        return

    try:
        for char_dir in CHARACTERS_DIR.iterdir():
            if not char_dir.is_dir():
                continue

            profile_path = char_dir / "profile.json"
            if not profile_path.exists():
                continue

            with open(profile_path, "r", encoding="utf-8") as f:
                npc = json.load(f)
                char_id = npc.get("id")
                char_name = npc.get("name")

                if char_id and char_name:
                    entry = {"name": char_name, "avatar": npc.get("avatar_url"), "id": char_id}
                    IDENTITIES[char_id] = entry
                    _register_identity_aliases(char_name, entry)

    except Exception as e:
        logger.error(f"Failed to load NPC identities: {e}")


# Populate on initial import
load_npc_identities()
