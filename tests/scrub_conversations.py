import json
import re
from pathlib import Path

CONV_PATH = Path(r"z:\DnD\EmberHeartReborn\state\CONVERSATIONS.json")

def scrub_conversations():
    if not CONV_PATH.exists():
        print("CONVERSATIONS.json not found.")
        return

    with open(CONV_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scrubbed_count = 0
    for thread_id, messages in data.items():
        if not messages:
            continue
        
        system_msg = messages[0]
        if system_msg.get("role") == "system":
            content = system_msg.get("content", "")
            
            # If this is an NPC role (starts with "You are [Name].")
            if "private, 1-on-1 direct message" in content:
                # Strip "Persona: The Chronicle Weaver" and everything after it
                # Strip "Core Dynamic: \"The Invisible DM\"" and everything after it
                
                original_content = content
                
                # Check for "The Chronicle Weaver"
                content = re.sub(r"## Persona: The Chronicle Weaver.*", "", content, flags=re.S)
                
                # Check for "The Invisible DM"
                content = re.sub(r"## Core Dynamic: \"The Invisible DM\".*", "", content, flags=re.S)
                
                # Double check for any residual "The Chronicle Weaver" in the text
                content = content.replace("The Chronicle Weaver", "The Sovereign's Advisor")
                
                if content != original_content:
                    system_msg["content"] = content.strip()
                    scrubbed_count += 1
                    print(f"Scrubbed thread {thread_id}")

    if scrubbed_count > 0:
        with open(CONV_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Total scrubbed: {scrubbed_count}")
    else:
        print("No threads needed scrubbing.")

if __name__ == "__main__":
    scrub_conversations()
