# EmberHeart Quest Network Guide

> **Version:** 2.0 — Updated for 220 quest database  
> **Maintained by:** DM Toolkit project  
> **Last updated:** 2026-02-20

---

## Table of Contents

1. [Overview](#1-overview)
2. [Getting Started](#2-getting-started)
3. [Prerequisites System](#3-prerequisites-system)
4. [Narrative Threads](#4-narrative-threads)
5. [Districts](#5-districts)
6. [Branching Outcomes](#6-branching-outcomes)
7. [Item-Locked Quests](#7-item-locked-quests)
8. [Tools and Scripts](#8-tools-and-scripts)
9. [FAQ](#9-faq)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Overview

The EmberHeart Quest Network is a **directed acyclic graph** (DAG) of side quests organized into *narrative threads* and *districts*. Quests have prerequisites that must be satisfied before the player party can access them, creating meaningful progression arcs that reward exploration and investment in specific storylines.

### How Prerequisite Chains Work

Every quest in the database can optionally require:
- **Completed quests** — specific quest IDs that must be finished first
- **Inventory items** — unique loot dropped by earlier quests
- **District reputation** — standing with a specific ward's faction
- **Status effects** — active modifiers on the party

This creates natural gates. The **Vermin** thread's deepest quests won't appear until the player has investigated early rat incidents, so the horror of the Concordat conspiracy lands with proper weight.

### How Threads and Districts Organize Content

**Threads** are narrative storylines that run across multiple quests. Each thread has its own protagonist NPCs, a central mystery, and a climax quest. Threads are largely independent — completing the **Weaver** thread has no bearing on accessing **Chronos** quests — but several quests contain *cross-thread lore reveals* that reward players pursuing multiple storylines.

**Districts** are physical locations within EmberHeart. A quest's district determines its ambient setting and which NPC factions are relevant. Some high-tier quests require the player to have visited or earned reputation in specific districts.

---

## 2. Getting Started

### Finding Entry-Point Quests

Entry-point quests have **no prerequisites** — they are accessible immediately when a new game begins. The easiest way to find them programmatically:

```python
from quest_api import QuestAPI, PlayerState
api = QuestAPI()
entries = api.get_entry_quests()
for q in entries:
    print(q["id"], q["title"], q["thread"])
```

Key entry quests to know:
| ID | Title | Thread | District |
|----|-------|--------|----------|
| `SQ-01` | The Whispering Vent | Weaver | Ridge |
| `SQ-02` | The Rat-Watcher | Vermin | Lower Ward |
| `SQ-03` | The Frost-Glass Merchant | Chronos | Market Ward |
| `SQ-28` | Copper-Tail Tracks | Vermin | Lower Ward |
| `EH_SQ_090` | The Bleach-Cult | Laundry | Market Ward |
| `EH_SQ_091` | The Sock-Thief Elemental | Laundry | Lower Ward |

### Understanding Difficulty Tiers

| Tier | XP Range | Expected Party Level | Description |
|------|----------|---------------------|-------------|
| **Easy** | 300–600 | 1–3 | Investigation + light combat, clear hooks |
| **Medium** | 700–1200 | 4–6 | Multiple encounter types, meaningful choices |
| **Hard** | 1500–3000 | 7–10 | Serious consequences, branching paths |
| **Epic** | 5000+ | 11+ | Climax events, permanent world changes |

### Reading Prerequisites

A quest's `prerequisites` field looks like this:

```json
{
    "quests_completed":    ["SQ-02", "SQ-28"],
    "items_required":      ["Copper-Tail Shard"],
    "district_reputation": { "Lower Ward": 3 },
    "status_effects":      []
}
```

All conditions must be satisfied simultaneously. If a player has completed `SQ-02` but lacks the `Copper-Tail Shard`, the quest remains locked.

> **Legacy note:** Older quests use `"prerequisites": "None"`. The API and validator both handle this correctly.

---

## 3. Prerequisites System

### quests_completed

A list of quest IDs that must be in the player's completed set. These form the *spine* of the progression chain.

```python
# Check if a specific quest is accessible
ok, missing = api.can_access_quest("EH_SQ_073", player)
if not ok:
    print("Missing requirements:", missing)
```

Chains can be arbitrarily deep. The `SQ-EPIC-GLASS` quest, for example, sits at the end of the Chronos thread's longest chain. Use `get_prerequisite_chain()` to see the full path:

```python
chain = api.get_prerequisite_chain("SQ-EPIC-GLASS")
print(" -> ".join(chain))
# SQ-03 -> SQ-06 -> EH_SQ_022 -> SQ-04 -> SQ-EPIC-GLASS
```

### items_required

Specific named items that must appear in the player's inventory. These items are exclusively obtained from loot tables of earlier quests in the same thread, creating a concrete reward loop.

**Example:** `EH_SQ_022` (The Liquid-Chronos Drought) requires a `Vial of Liquid Chronos`, which only drops from `SQ-06`. This enforces narrative order: you must *experience* the liquid-chronos phenomenon before you can investigate its drought.

To find where an item comes from:
```python
sources = api.get_loot_sources("Vial of Liquid Chronos")
for q in sources:
    print(q["id"], q["title"])
```

### district_reputation

An integer gate on faction standing. Values are set by the DM based on player actions. Example:

```json
"district_reputation": { "High Ward": 5 }
```

This blocks access until the player has achieved reputation level 5 in the High Ward. Reputation is tracked externally (not in this database).

### status_effects

Active flags on the party — curses, blessings, or narrative states. Currently limited use in the Easy tier but appears in Medium and Hard quests to create optional "hidden" quest paths.

---

## 4. Narrative Threads

### Weaver's Web

**Central mystery:** The fabric of reality in the Weaver District is tearing. Pattern-silk from a pre-Scourge loom is unraveling the city's dimensional stability, one stitch at a time.

**Tone:** Folk horror meets craftsperson tragedy. The Weaver is not a villain — she is bound to a loom she can never leave.

**Key NPCs:** The Tailor Sindra, the spirit bound in the stitch-work, the Guild of Needles.

**Stakes:** If the loom is not resolved, the Weaver District will phase out of dimensional alignment with the rest of EmberHeart within two years.

**Entry quest:** `SQ-01` (The Whispering Vent)  
**Climax quest:** `SQ-H-WEAVER` (The Last Stitch)

---

### Chronos Drift

**Central mystery:** Liquid-Chronos — a substance that slows local time — is being synthesized illegally, used by the desperate to pause grief and aging. The synthesis process is accelerating temporal instability in the North Ward, where a Glass City from 200 years in the future is becoming visible through rifts.

**Tone:** Time-horror meets addiction tragedy. Temporal collapse as the slow tragedy of people trying to escape the present.

**Key NPCs:** Alchemist Drenn, the Glass-City Wraith, Warden Artificer Soli Yan.

**Stakes:** The Glass City's full manifestation would cause a temporal cascade across EmberHeart, potentially slicing the city into incompatible temporal layers.

**Entry quest:** `SQ-03` (The Frost-Glass Merchant)  
**Climax quest:** `SQ-EPIC-GLASS` (The Glass-City Awakening) — 20 turns, Epic tier

---

### Vermin Vectors

**Central mystery:** The city's rat population has been weaponized. Pre-Scourge bio-mechanical implants in the rats are directing them to sabotage mana-infrastructure, mapping attack patterns against city systems, and collecting intelligence. The architect: Doctor Vane, possibly a 200-year-old Concordat engineer.

**Tone:** Conspiracy thriller meets body horror. Comedy in the individual rat incidents; profound dread in the systemic picture.

**Key NPCs:** Doctor Vane (voice only, until later), Inventor Caldwell Voss, the Squeaker-Box.

**Stakes:** The rats are executing a Reactivation Protocol — trying to wake something dormant beneath the city by redirecting its mana-infrastructure.

**Entry quests:** `SQ-02` (The Rat-Watcher), `SQ-28` (Copper-Tail Tracks), `EH_SQ_070` (The Rat-Prophet)  
**Climax quest:** `SQ-M-CONCORDAT`

---

### Void-Wine Trade

**Central mystery:** A substance called Void-Wine is being distilled from echo-grief — the dimensional resonance left by mass death during the Scourge. Those who drink it experience perfect recall of loved ones lost. It is deeply addictive. It is accelerating dimensional bleed.

**Tone:** Substance-horror meets grief study. The most emotionally direct of the threads.

**Key NPCs:** The nameless Distiller, the Grieving Widow faction, the smuggling network.

**Stakes:** Mass Void-Wine consumption is creating dimensional pressure that could crack the Scourge-Fringe's quarantine.

**Entry quest:** Relevant Void-Wine thread quests  
**Climax quest:** `SQ-H-VINEYARD`

---

### Living Fabrics

**Central mystery:** Specific fabrics — Warp-Silk, woven in dimensional bleed-through — are animating. What begins as haunted laundry reveals a pre-Scourge Concordat welfare program still running after 200 years, an espionage communications network embedded in memorial quilts, and a massive probability-manipulation field being woven in a Lower Ward sub-basement.

**Tone:** Horror-comedy. Absurd premises executed with sincerity. The comedy is in the premise; the horror is in the implications.

**Key NPCs:** The Sock Elemental (Lefty), Elder Whitmore, Widow Tessaly, Concordat Comfort Protocol Unit 7.

**Stakes:** The pre-Scourge Warp-Silk infrastructure connects to the same Concordat Reactivation Protocol driving the Vermin thread.

**Entry quests:** `EH_SQ_090`–`EH_SQ_091` (no prerequisites)  
**Climax quest:** Pending

---

### Bakery Anomaly

**Central mystery:** Something is wrong with the bread. A pre-Scourge bio-engineering experiment in yeast has reactivated, creating loaves that extend life, induce visions, or — in dangerous batches — slowly replace human tissue with something else.

**Tone:** Body horror meets domestic comedy. The most quotidian horror vector possible.

**Entry quests:** Bakery-thread quests  
**Climax quest:** Pending

---

### Scourge-Battery

**Central mystery:** Someone is harvesting residual mana from the Scourge-Fringe — the scar-zone where the original Scourge struck — and converting it into weapons. The energy is inherently unstable and corrupting.

**Tone:** War-horror meets ecological tragedy. The Scourge-Fringe as a wound the city refuses to stop picking at.

**Entry quests:** Scourge-Battery thread quests  
**Climax quest:** Pending

### Thread Interconnections

Several threads share lore infrastructure:

| Connection | Details |
|------------|---------|
| Vermin + Laundry | Both connect to Concordat Reactivation Protocol; Warp-Silk plumbing feeds moth mana into Laundry Ward infrastructure |
| Vermin + Stitched-Memories | Pre-Scourge memory-quilts name Doctor Vane as a young Concordat engineer |
| Chronos + Glass City | Glass City wraiths carry memories of a Concordat that had temporal technology |
| All threads | The Reactivation Protocol appears as background detail across all threads, hinting at a single convergence point |

**Recommended play order:** Weaver → Vermin (early quests) → Laundry → Vermin (mid quests) → Chronos → Epic cross-thread content.

---

## 5. Districts

### Lower Ward

The oldest part of EmberHeart, built over the original Concordat residential district. Decay, improvised infrastructure, and a tight community that's learned to live with weirdness. The Laundry Ward — a sub-region of the Lower Ward — is the centre of Warp-Silk activity.

**Primary threads:** Vermin, Laundry, Void-Wine  
**Notable quests:** The Rat-Funeral, The Stitched-Memories, The Living-Carpet

### North Ward

Clockwork district. Mana-powered timekeeping infrastructure. Temporal bleed from the Chronos thread is most visible here — clocks run wrong, shadows fall at incorrect angles.

**Primary threads:** Chronos  
**Notable quests:** Chronos-thread mid-tier

### Ridge

The frontier edge of EmberHeart, built on geothermal vents. First contact with unknown phenomena from outside the city. Entry point for the Weaver thread.

**Primary threads:** Weaver  
**Notable quests:** SQ-01 (The Whispering Vent)

### High Ward

Trade hub and political centre. The wealthiest district; also the most vulnerable to sophisticated infrastructure attack. Copper-Tail mana-sabotage is most damaging here.

**Primary threads:** Vermin (later quests), Standalone political quests  
**Notable quests:** The Squeaker-Box (EH_SQ_072)

### Market Ward

The commercial heart of EmberHeart. High foot traffic, active guild presence, and the boutique Silk Promenade. Fabric-Eater Moths operate here.

**Primary threads:** Laundry, Vermin (Copper-Plague)  
**Notable quests:** The Bleach-Cult (EH_SQ_090), The Fabric-Eater Moths (EH_SQ_093), The Copper-Plague (EH_SQ_074)

### Scourge-Fringe

The quarantined scar-zone. High danger, high reward. Few casual quests here — content is primarily Hard and Epic tier.

**Primary threads:** Scourge-Battery, Expedition  
**Notable quests:** Expedition-tier quests

### Expedition

Quests that take the party entirely outside EmberHeart's walls. Rare; reserved for climax-tier and Epic content.

---

## 6. Branching Outcomes

Most quests offer two primary paths at resolution, tracked in the `branching_outcomes` field:

```json
"branching_outcomes": {
    "befriend_elemental": {
        "description": "Give the sock elemental a home and a purpose",
        "effects":     { "settlement_morale": 3 },
        "unlocks":     [],
        "consequences": {
            "permanent_effect": "Sock Elemental becomes Laundry Ward mascot",
            "ambient_hazard":   "Occasional left-sock disappearances continue"
        }
    },
    "disperse_elemental": {
        "description": "Unravel the elemental, dispersing the Warp-Static",
        "effects":     { "settlement_stability": 1 },
        "unlocks":     [],
        "consequences": { "ambient_hazard": "300 socks returned to owners" }
    }
}
```

**Effects** modify global settlement metrics:  
- `settlement_stability` — structural integrity of the city's systems  
- `settlement_morale` — citizen well-being and crime rate  

**Unlocks** reference quest IDs made available by this choice (currently used in Epic tier).

**Permanent effects** are narrative mutations to the world that the DM should track between sessions.

---

## 7. Item-Locked Quests

Quests requiring specific items from earlier loot tables:

| Quest ID | Title | Required Item | Source Quest |
|----------|-------|---------------|-------------|
| `EH_SQ_022` | The Liquid-Chronos Drought | Vial of Liquid Chronos | `SQ-06` |
| `EH_SQ_073` | The Rat-Funeral | *(No item req — quest req only)* | — |
| `EH_SQ_074` | The Copper-Plague | *(No item req — quest req only)* | — |

> **Note:** Item requirements are the least common prerequisite type in the current database. Most gates are quest-completion requirements.

---

## 8. Tools and Scripts

### validate_quest_network.py

Run validation checks on the entire quest database before a session.

```bash
# From EmberHeart root directory
python scripts/validate_quest_network.py

# Custom database path
python scripts/validate_quest_network.py --json docs/SIDE_QUESTS_DB.json
```

**Checks performed:**
- Duplicate quest IDs
- Missing required fields
- Invalid difficulty / thread / district values
- Broken prerequisite chains (missing quest IDs)
- Circular dependencies (via DFS)
- Orphaned quests (unreachable)
- Broken branching_outcomes.unlocks references
- Item prerequisite traceability

**Exit codes:** `0` = pass, `1` = errors found.

---

### quest_api.py

Programmatic query interface for tooling and DM prep.

```bash
# Run demo output
python scripts/quest_api.py
```

```python
from quest_api import QuestAPI, PlayerState

api    = QuestAPI()   # loads docs/SIDE_QUESTS_DB.json
player = PlayerState(
    completed_quests={"SQ-01", "SQ-02"},
    inventory={"Copper-Tail Shard"},
)

# What can this player access right now?
available = api.get_available_quests(player)

# Check a specific quest
ok, missing = api.can_access_quest("EH_SQ_073", player)

# Thread progression
progression = api.get_thread_progression("Vermin")
# Returns: {"entry": [...], "mid": [...], "advanced": [...], "climax": [...]}

# Find what drops a specific item
sources = api.get_loot_sources("Squeaker-Box")

# Search quests by keyword
results = api.search_quests("copper tail")

# Get database statistics
stats = api.get_statistics()
```

---

### visualize_network.py

Generates PNG graphs of quest relationships. Requires `pip install networkx matplotlib`.

```bash
# Text report only (no matplotlib needed)
python scripts/visualize_network.py --report

# Full network PNG
python scripts/visualize_network.py --full

# Single thread
python scripts/visualize_network.py --thread Vermin

# Single district
python scripts/visualize_network.py --district "Lower Ward"

# Everything
python scripts/visualize_network.py --all
```

**Output files** (saved to `docs/`):
- `quest_network_full.png` — all quests, coloured by difficulty
- `quest_network_{thread}.png` — thread-specific, hierarchical layout
- `quest_flowchart_{thread}.png` — strict flowchart with ID + title + difficulty
- `quest_network_{district}.png` — district map, coloured by thread
- `quest_network_report.txt` — text statistics

---

## 9. FAQ

**Q: Can I complete quests out of thread order?**  
A: Only if you can meet the prerequisites another way. Most prerequisites are quest-completion requirements, so the natural play order is the required order within a thread. Across threads, there's no ordering requirement.

**Q: What happens if I fail a quest?**  
A: Quest failure typically applies the `risk_matrix.penalty` — usually a settlement stability or morale hit. Failed quests remain in your available queue and can be attempted again unless the narrative permanently closes them (Epic tier only).

**Q: Do branching outcomes lock out content?**  
A: Currently, branching outcomes primarily affect *world state* (settlement metrics, ambient hazards, NPC availability) rather than locking future quests. The exception is Epic-tier choices on `SQ-EPIC-GLASS`, where the Destroy vs. Merge vs. Perfect-Merge paths have permanently different world consequences.

**Q: How does the Squeaker-Box item work across quests?**  
A: The Squeaker-Box (EH_SQ_072 loot) is referenced in EH_SQ_074 as providing bonus translation ability. Its presence in inventory gives a +2 Intel bonus on Concordat chitter-code checks in subsequent Vermin quests. It's not a hard prerequisite, but its possession is extremely useful.

**Q: What is settlement stability vs. settlement morale?**  
A: *Stability* measures the city's structural/systemic health (infrastructure, safety, governance). *Morale* measures citizen well-being and social cohesion. Low stability creates mechanical hazards; low morale creates social hazards (crime, unrest, NPC hostility).

**Q: Are there quests with no combat?**  
A: All quests have at least one combat option in their turn structure, but several (particularly Laundry thread) can be resolved entirely through social/investigation/Fabric-Handling skill checks if the player chooses the befriend path.

**Q: Can the Sock Elemental (EH_SQ_091) die?**  
A: If dispersed (destroy path), yes — permanently. If befriended, it becomes a recurring NPC (Lefty) who can appear in future Laundry Ward content. The DM should track this outcome.

**Q: What is Doctor Vane?**  
A: Unknown canonically. The Vermin thread establishes that he was a young Concordat Division Seven bio-engineer before the Scourge (200+ years ago), currently names himself 'V' in transmissions, speaks pre-Scourge Common with native fluency, and operates from deep within the city's Concordat maintenance tunnel network. Whether he is alive, preserved, uploaded, or a title passed down is left deliberately ambiguous.

**Q: How many quests are in the database?**  
A: As of the current version, 220 quests are present. Use `python scripts/quest_api.py` for an up-to-date count.

**Q: What's the maximum XP from completing all side quests?**  
A: Run `api.get_statistics()["total_xp"]` for the current total. As of version 2.0, this exceeds 246,370 XP across all threads.

---

## 10. Troubleshooting

### Validator reports "circular dependency"
This means Quest A requires Quest B, which requires Quest A. Run the validator to identify the cycle, then edit one quest's `prerequisites.quests_completed` to break it.

### Validator reports "orphaned quest"
A quest's prerequisites include a quest ID that doesn't exist in the database. Either the prerequisite quest was removed, or the ID has a typo. The validator will name both the orphaned quest and the missing prerequisite.

### quest_api.py can't find the database
Ensure you're running from the EmberHeart root directory (`z:\DnD\EmberHeart`) or pass `--json` with the full path. The API also searches relative to its own script location.

### visualize_network.py produces no PNGs
Install matplotlib: `pip install matplotlib`. The script will still produce the text report without it.

### A quest doesn't appear in `get_available_quests()`
Check: (1) Is the quest already in `player.completed_quests`? (2) Does it have prerequisites you haven't met? Use `can_access_quest(quest_id, player)` to get the exact list of unmet requirements.

### Legend items overlap on full network graph
The full network with 50+ quests can become visually dense. Use `--thread` or `--district` for cleaner focused graphs.

### JSON parse error from SIDE_QUESTS_DB.json
Run the validator; it will report the exact JSON error. Common causes: trailing commas, unescaped quotes in narrative text, or encoding issues in non-ASCII characters. The database uses `ensure_ascii=False` in the insertion scripts, so high-unicode characters should be valid.
