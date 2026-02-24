import re


def sanitize_text(text: str) -> str:
    """Clean up 'smart' characters and common encoding artifacts for logs and Discord."""
    if not text:
        return ""

    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2014": "--",
        "\u2013": "-",
        "\u2026": "...",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _extract_name_ids(text: str) -> list[tuple[str, str]]:
    pattern = r"(\*\*[ \t]*([^\n]*?)[ \t]*\*\*[ \t]*:[ \t]*)"
    parts = re.split(pattern, sanitize_text(text))

    rows = []
    for i in range(1, len(parts), 3):
        raw_name = parts[i + 1].strip().rstrip(":")
        id_match = re.search(r"\[(EH-\d+|DM-\d+)\]", raw_name)
        extracted_id = id_match.group(1) if id_match else "NONE"
        display_name = re.sub(r"\s*\[.*?\]", "", raw_name).strip()
        rows.append((display_name, extracted_id))
    return rows


def test_split():
    test_narrative = """The Council gathers in the shadow of the Spire.

**Marta Hale [EH-01]**: "Food reserves are at 80%."

**Veyra Wynstone (Knight-Captain) [EH-03]**: "The perimeter is secure, for now."

The **Blade of the Beholder** hums with anticipation.
"""

    rows = _extract_name_ids(test_narrative)
    assert rows == [
        ("Marta Hale", "EH-01"),
        ("Veyra Wynstone (Knight-Captain)", "EH-03"),
    ]
