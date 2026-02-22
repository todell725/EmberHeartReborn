import re

def sanitize_text(text: str) -> str:
    """Clean up 'smart' characters and common encoding artifacts for logs and Discord."""
    if not text: return ""
    # Smart Quotes & Apostrophes
    replacements = {
        "\u201c": '"', "\u201d": '"', # Double quotes
        "\u2018": "'", "\u2019": "'", # Single quotes
        "\u2014": "--", "\u2013": "-", # Dashes
        "\u2026": "..." # Ellipsis
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# Characters to NEVER parse as AI speakers (Prevents God-moding)
IGNORE_SPEAKERS = {"Kaelrath", "King Kaelrath", "The King", "Sovereign"}

def strip_god_moding(text: str) -> str:
    """
    Aggressively strips intra-paragraph god-moding narration.
    Removes sentences that describe the actions of Kaelrath/User.
    """
    if not text: return ""
    
    # 1. Preserve spacing by using a non-destructive split
    # We use capturing group for quotes to keep them in the parts list
    parts = re.split(r'(".*?")', text)
    
    # Patterns for god-moding (Third Person & Second Person)
    names = ["Kaelrath", "King Kaelrath", "The King", "Sovereign"]
    name_pattern = "|".join([re.escape(n) for n in names])
    
    # Sentence pattern: Starts with Name/You/Your, ends with punctuation.
    # We look for matches at the start of the string (ignoring whitespace) or following punctuation.
    gm_regex = re.compile(rf'(^\s*|[.!?]\s+)(?:{name_pattern}|You|Your)\b.*?[.!?](?=\s|$)', re.I)

    cleaned_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Narration: Apply regex to strip god-moding sentences
            # We strip sentences but try to keep the leading spaces for flow
            seg = part
            # Loop-replace to catch multiple sentences
            old_seg = ""
            while old_seg != seg:
                old_seg = seg
                seg = gm_regex.sub(r"\1", seg)
            cleaned_parts.append(seg)
        else:
            # Dialogue: Preserve as-is
            cleaned_parts.append(part)
            
    # Join and clean up double spaces/leading/trailing
    result = "".join(cleaned_parts)
    result = re.sub(r'\s+', ' ', result).strip()
    return result

def parse_speaker_blocks(text: str, identities: dict, ignore_headers: set) -> list:
    """
    Parses an AI response string for '**Name**: "Dialogue"' patterns 
    and yields distinct blocks of text assigned to specific identities.
    
    Args:
        text (str): The raw text from the LLM.
        identities (dict): The loaded identity registry.
        ignore_headers (set): Set of strings to ignore as headers rather than speakers.
        
    Returns:
        list of dict: [{"speaker": str, "identity": dict or None, "content": str}]
    """
    if not text: return []

    # Regex to find Speaker tags:
    pattern = r'(\*\*[ \t]*([^\n]*?)[ \t]*\*\*[ \t]*:[ \t]*)'
    text = sanitize_text(text)
    parts = re.split(pattern, text)

    blocks = []
    
    if len(parts) == 1:
        return [{"speaker": "DM", "identity": identities.get("DM"), "content": text}]

    current_speaker = "DM"
    buffer_text = ""
    
    if parts[0].strip():
        buffer_text += parts[0]

    i = 1
    while i < len(parts):
        if i + 2 >= len(parts): break
        
        raw_name = parts[i+1].strip().rstrip(":")
        segment_content = parts[i+2] 
        
        is_speaker = True
        
        # ID-Lock Protocol: Extract bracketed ID if present
        id_match = re.search(r'\[(EH-\d+|DM-\d+|PC-\d+)\]', raw_name)
        extracted_id = id_match.group(1) if id_match else None
        
        # Pre-clean the name for lookup (Strip leading/trailing brackets)
        lookup_name = raw_name.strip("[]").strip()
        
        known_identity = None
        if extracted_id and extracted_id in identities:
            known_identity = identities[extracted_id]
        elif lookup_name in identities:
            known_identity = identities[lookup_name]
        else:
            temp_name = re.sub(r'\s*\[.*?\]', '', lookup_name).strip()
            # Try to match parts of the name
            match = next((k for k in identities if k.lower() in temp_name.lower() or temp_name.lower() in k.lower()), None)
            if match: 
                known_identity = identities[match]

        if not known_identity:
            preceding_text = parts[i-1]
            if preceding_text and not preceding_text.rstrip(' ').endswith('\n') and preceding_text.strip():
                is_speaker = False

            if is_speaker and raw_name in ignore_headers:
                is_speaker = False
            
            if is_speaker and ("Agenda" in raw_name or "Notes" in raw_name or "State" in raw_name):
                is_speaker = False
                
            if is_speaker:
                word_count = len(raw_name.split())
                if word_count > 6: is_speaker = False 
                if word_count == 1 and raw_name.isupper(): is_speaker = False 
            
            if is_speaker and any(char.isdigit() for char in raw_name) and not extracted_id:
                is_speaker = False

            if is_speaker:
                clean_content = segment_content.strip()
                # Allow DM or Chronicle Weaver to narrate without quotes
                is_narrator = "DM" in lookup_name or "Chronicle" in lookup_name or "Weaver" in lookup_name
                if not is_narrator and not (clean_content.startswith('"') or clean_content.startswith('“') or clean_content.startswith('*')):
                     is_speaker = False

        if is_speaker:
            # SAVE PREVIOUS BLOCK (If not ignored)
            if buffer_text.strip():
                if current_speaker not in IGNORE_SPEAKERS:
                    # Resolve identity for previous speaker before saving block
                    token = identities.get(current_speaker)
                    if not token and current_speaker != "DM":
                        match = next((k for k in identities if k.lower() in current_speaker.lower()), None)
                        if match: 
                            token = identities[match]
                        else:
                            clean = re.sub(r'\s*\(.*?\)', '', current_speaker).strip()
                            if clean in identities: token = identities[clean]
                            else: token = {"name": current_speaker, "avatar": identities.get("NPC", {}).get("avatar")}
                    elif current_speaker == "DM":
                        token = identities.get("DM")

                    blocks.append({"speaker": current_speaker, "identity": token, "content": buffer_text.strip()})

            display_name = re.sub(r'\s*\[.*?\]', '', lookup_name).strip()
            current_speaker = display_name
            if known_identity: current_speaker = known_identity["name"]
            
            buffer_text = segment_content
            
        else:
            buffer_text += f"\n{parts[i]}{segment_content}"

        i += 3
        
    if buffer_text.strip():
        if current_speaker not in IGNORE_SPEAKERS:
            token = identities.get(current_speaker)
            if not token and current_speaker != "DM":
                match = next((k for k in identities if current_speaker.lower() in k.lower()), None)
                if match: token = identities[match]
                else: token = {"name": current_speaker, "avatar": identities.get("NPC", {}).get("avatar")}
            elif current_speaker == "DM":
                token = identities.get("DM")
                
            blocks.append({"speaker": current_speaker, "identity": token, "content": buffer_text.strip()})

    return blocks
