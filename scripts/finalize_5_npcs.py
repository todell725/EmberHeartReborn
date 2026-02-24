
import json
import shutil
from pathlib import Path

root = Path(r"z:\DnD\EmberHeartReborn")
char_root = root / "characters"
pics_dir = root / "Character Pics"

# Data from User Cards
npc_data = {
    "EH-53_Commander_Vex": {
        "id": "EH-53",
        "name": "Commander Vex",
        "race": "Human",
        "role": "Ace Pilot / Captain of the Resonance",
        "status": "Blade-Sworn",
        "avatar_url": "./Commander Vex.png",
        "description": "A human woman with a slight, agile build. She wears a specialized pilot's flight suit of dark leather. Her hair is shorn short, and her eyes are intense and focused.",
        "motivation": "To ensure no one else loses their home to the void.",
        "bio": "Captain of the Resonance, a Sovereign Corvette. She is a resonance pilot who coordinates fleet maneuvers through a direct neural-harmonic interface."
    },
    "EH-54_Grand_Marshal_Malakor": {
        "id": "EH-54",
        "name": "Grand Marshal Malakor",
        "race": "Human",
        "role": "Head of the Sovereign Military (Former Regent)",
        "status": "Grand-Marshal / Blade-Brother",
        "avatar_url": "./Grand Marshal Malakor.png",
        "description": "A stern man in imposing, heavy black armor adorned with the Sovereign's crest. He has piercing gray eyes and a close-cropped beard. His presence is commanding and disciplined.",
        "motivation": "To be the unbreakable shield and the righteous blade of the Bread-King.",
        "bio": "Once the iron-fisted ruler of the Concordat. Now serves as the ultimate military authority under High-Sovereign Kaelrath."
    },
    "EH-55_Elder_Thorne": {
        "id": "EH-55",
        "name": "Elder Thorne",
        "race": "Tiefling",
        "role": "Councilor / Lead Signal Analyst",
        "status": "Sacredbound",
        "avatar_url": "./Elder Thorne.png",
        "description": "An elderly Tiefling with faded blue skin and smooth, worn horns. He wears simple, earthen-toned robes and carries a staff made from a gnarled mountain root.",
        "motivation": "To decode the cosmic resonance behind the Seekers' tracking signal.",
        "bio": "A spiritual and technical advisor on the Council. He specializes in tracking and analyzing high-frequency cosmic signals."
    },
    "EH-56_Queen_Elara": {
        "id": "EH-56",
        "name": "Queen Elara",
        "race": "High Elf",
        "role": "Councilor (Former Matriarch of Valemere)",
        "status": "Devoted-Architect",
        "avatar_url": "./Queen Elara.png",
        "description": "A High Elf of ethereal beauty, wearing robes of woven emerald and silver. Her hair flows like liquid moonlight, and she wears a circlet of living wood.",
        "motivation": "The preservation of the planet's soul and ancient memories.",
        "bio": "Former Matriarch of the Valemere nature-states. She now oversees the architectural and ecological preservation of the colony."
    },
    "EH-57_Rix_the_Scavenger": {
        "id": "EH-57",
        "name": "Rix (The Scavenger)",
        "race": "Human (Void-Marked)",
        "role": "Survivor of the Star-Shrike",
        "status": "Cooperative-Informant",
        "avatar_url": "./Rix (The Scavenger).png",
        "description": "A young man with patches of faintly glowing 'void-scars' on his neck and hands. He wears a tattered scavenger's jumpsuit and is highly alert.",
        "motivation": "Revenge for his crew.",
        "bio": "A scavenger pilot rescued from the void. After being healed by Silvara and comforted by the colony, he acts as an informant for the ridge."
    }
}

# Image source mapping (where they are currently)
image_map = {
    "Commander Vex.png": pics_dir / "Commander Vex.png",
    "Grand Marshal Malakor.png": pics_dir / "Grand Marshal Malakor.png",
    "Queen Elara.png": char_root / "EH-45_Elara_Moonwhisper" / "Queen Elara.png",
    "Elder Thorne.png": char_root / "EH-47_Valerius_Thorne" / "Elder Thorne.png",
    "Rix (The Scavenger).png": char_root / "EH-52_Zael" / "Rix (The Scavenger).png"
}

# 1. Move Images and Create Profiles
for folder_name, data in npc_data.items():
    folder_path = char_root / folder_name
    pic_name = [k for k, v in npc_data.items() if v['name'] == data['name'] or v['name'].startswith(data['name'])][0] # Helper
    # Correction: pic_name is the key in image_map
    possible_keys = [k for k in image_map.keys() if data['name'] in k or (data['name'].split(' ')[-1] in k and len(data['name'].split(' ')) > 1)]
    # Use explicit keys
    if "Vex" in data['name']: actual_pic = "Commander Vex.png"
    elif "Malakor" in data['name']: actual_pic = "Grand Marshal Malakor.png"
    elif "Elara" in data['name']: actual_pic = "Queen Elara.png"
    elif "Thorne" in data['name']: actual_pic = "Elder Thorne.png"
    elif "Rix" in data['name']: actual_pic = "Rix (The Scavenger).png"
    
    src = image_map[actual_pic]
    dst = folder_path / actual_pic
    
    if src.exists():
        print(f"Moving {actual_pic} -> {folder_name}")
        shutil.move(src, dst)
        
    print(f"Creating profile.json for {folder_name}")
    with open(folder_path / "profile.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# 2. Restore Old Avatars for the Mismatched Folders
restore_map = {
    "EH-45_Elara_Moonwhisper": "https://cdn.discordapp.com/attachments/1473540819146244218/1473556652627067065/image0.jpg?ex=69989e53&is=69974cd3&hm=06367c6f44c32327942302a1bb21ddbff9b33ba19f30ad569f64af4ded896080&",
    "EH-47_Valerius_Thorne": "https://cdn.discordapp.com/attachments/1473540819146244218/1473556763923189788/image0.jpg?ex=69989e6d&is=69974ced&hm=865fa5564748f61bc4f0d68ab3318415d0d4cb4111c22649330b9cb90d3005fd&",
    "EH-52_Zael": "https://cdn.discordapp.com/attachments/1473540819146244218/1473556251366658078/image0.jpg?ex=69989df3&is=69974c73&hm=6812dd7d500d50125d04f5100902afc9ea44b68c27df81390b961acf62dc13ed&"
}

for folder, url in restore_map.items():
    p_path = char_root / folder / "profile.json"
    if p_path.exists():
        data = json.loads(p_path.read_text(encoding='utf-8'))
        data['avatar_url'] = url
        with open(p_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Restored avatar for {folder}")
