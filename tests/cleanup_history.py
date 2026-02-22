import json
from pathlib import Path
import re

history_path = Path(r"z:\DnD\EmberHeartReborn\state\CONVERSATIONS.json")

def clean_history():
    with open(history_path, 'r', encoding='utf-8') as f:
        history = json.load(f)

    # 1. Thread 1475260096723554466 (Weaver Meta) - RESET
    if "1475260096723554466" in history:
        print("Resetting Weaver Meta thread...")
        system_msg = history["1475260096723554466"][0]
        history["1475260096723554466"] = [system_msg]

    # 2. General Purge for Galactic Hallucination
    keywords = ["starship", "galactic", "colony ship", "Seed-Fleet", "universe", "galactic sanctuary", "Post-Scarcity"]
    
    for thread_id, messages in history.items():
        if thread_id == "test-reset-channel": continue
        
        cleaned_messages = []
        for msg in messages:
            content = msg.get("content", "")
            if any(key.lower() in content.lower() for key in keywords):
                print(f"Purging hallucination from thread {thread_id}: {content[:50]}...")
                continue
            cleaned_messages.append(msg)
        
        history[thread_id] = cleaned_messages

    # Atomic Save
    with open(history_path.with_suffix(".bak"), 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4)
        
    import os
    os.replace(history_path.with_suffix(".bak"), history_path)
    print("Cleanup Complete.")

if __name__ == "__main__":
    clean_history()
