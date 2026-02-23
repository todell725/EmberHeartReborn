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

def test_split(text):
    # Updated regex: [ \t]* ensures we don't bridge newlines
    pattern = r'(\*\*[ \t]*([^\n]*?)[ \t]*\*\*[ \t]*:[ \t]*)'
    text = sanitize_text(text)
    parts = re.split(pattern, text)
    print(f"Parts count: {len(parts)}")
    for i in range(1, len(parts), 3):
        raw_name = parts[i+1].strip().rstrip(":")
        
        # ID-Lock Test
        id_match = re.search(r'\[(EH-\d+|DM-\d+)\]', raw_name)
        extracted_id = id_match.group(1) if id_match else "NONE"
        display_name = re.sub(r'\s*\[.*?\]', '', raw_name).strip()
        
        print(f"Match: {repr(raw_name)}")
        print(f"  -> Extracted ID: {extracted_id}")
        print(f"  -> Display Name: {display_name}")

# Test case with IDs
test_narrative = """The Council gathers in the shadow of the Spire.

**Marta Hale [EH-01]**: "Food reserves are at 80%."

**Veyra Wynstone (Knight-Captain) [EH-03]**: "The perimeter is secure, for now."

The **Blade of the Beholder** hums with anticipation.
"""

print("--- TESTING SPLIT ---")
test_split(test_narrative)
