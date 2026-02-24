
import os
import re

source_dir = r"z:\DnD\EmberHeartReborn\docs\reference\gamebooks"
target_dir = r"z:\DnD\EmberHeartReborn\docs\reference\gamebooks_md"

def normalize(name):
    if not name: return ""
    # Only splitext if it's a file with a known extension
    # But these are either dirs or .md files.
    # Better: just remove .md or .pdf explicitly if they exist at the end.
    name = re.sub(r'\.(md|pdf|docx|txt|djvu)$', '', name, flags=re.I)
    
    # Handle common suffixes in gamebooks_md
    name = name.replace("_djvu", "").replace("_text", "").replace("_lcp", "")
    # Remove all punctuation
    return re.sub(r'[^a-z0-9]', '', name.lower())

sources = os.listdir(source_dir)
targets = os.listdir(target_dir)

target_norms = {}
for t in targets:
    norm = normalize(t)
    if norm not in target_norms:
        target_norms[norm] = []
    target_norms[norm].append(t)

missing = []
for s in sources:
    s_norm = normalize(s)
    if s_norm not in target_norms:
        # Check if maybe the dot or something else is missing
        # Some sources have .pdf in the dir name
        alt_norm = normalize(s.replace(".pdf", ""))
        if alt_norm not in target_norms:
             missing.append(s)

print(f"Total Sources: {len(sources)}")
print(f"Total Unique Targets (base): {len(target_norms)}")
print(f"\nMissing Conversions ({len(missing)}):")
for m in sorted(missing):
    print(f"- {m}")
