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
        id_match = re.search(r'\[(EH-\d+|DM-\d+)\]', raw_name)
        extracted_id = id_match.group(1) if id_match else None
        
        known_identity = None
        if extracted_id and extracted_id in identities:
            known_identity = identities[extracted_id]
        elif raw_name in identities:
            known_identity = identities[raw_name]
        else:
            temp_name = re.sub(r'\s*\[.*?\]', '', raw_name).strip()
            match = next((k for k in identities if k.lower() in temp_name.lower()), None)
            if match: 
                known_identity = identities[match]
            else:
                clean_name = re.sub(r'\s*\(.*?\)', '', temp_name).strip()
                if clean_name in identities:
                     known_identity = identities[clean_name]

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
            
            if is_speaker and any(char.isdigit() for char in raw_name): is_speaker = False

            if is_speaker:
                clean_content = segment_content.strip()
                if not (clean_content.startswith('"') or clean_content.startswith('“') or clean_content.startswith('*')):
                     is_speaker = False

        if is_speaker:
            if buffer_text.strip():
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

            display_name = re.sub(r'\s*\[.*?\]', '', raw_name).strip()
            current_speaker = display_name
            if known_identity: current_speaker = known_identity["name"]
            
            buffer_text = segment_content
            
        else:
            buffer_text += f"\n{parts[i]}{segment_content}"

        i += 3
        
    if buffer_text.strip():
        token = identities.get(current_speaker)
        if not token and current_speaker != "DM":
            match = next((k for k in identities if current_speaker.lower() in k.lower()), None)
            if match: token = identities[match]
            else: token = {"name": current_speaker, "avatar": identities.get("NPC", {}).get("avatar")}
        elif current_speaker == "DM":
            token = identities.get("DM")
            
        blocks.append({"speaker": current_speaker, "identity": token, "content": buffer_text.strip()})

    return blocks
