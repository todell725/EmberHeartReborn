# EmberHeart Thread Progression Maps

> **Version:** 2.0 — 58 quest database  
> All flowcharts use ASCII art. Arrows show prerequisite direction: you must complete the quest **above** an arrow before the quest **below** becomes available.

---

## Table of Contents

1. [Weaver's Web](#weavers-web)
2. [Chronos Drift](#chronos-drift)
3. [Vermin Vectors](#vermin-vectors)
4. [Void-Wine Trade](#void-wine-trade)
5. [Living Fabrics (Laundry)](#living-fabrics-laundry)
6. [Bakery Anomaly](#bakery-anomaly)
7. [Scourge-Battery (Static)](#scourge-battery-static)

---

## Weaver's Web

### Overview

The Weaver thread begins with a geological mystery — vents in the Ridge district that whisper in no known language — and expands into a city-spanning crisis: a pre-Scourge loom, still running, is unraveling dimensional stitching in patterns that mirror the city's own infrastructure. The Weaver herself is not a monster. She is trapped.

**Core lore reveal:** The Concordat wove EmberHeart's dimensional stability directly into the fabric of the original settlement buildings. The loom that created those stability-weaves is still running because it cannot stop — the Weaver's consciousness is bound to it as the control mechanism. Every new settlement expansion is a new stitch she is compelled to make.

**Key NPCs:**
- **Sindra the Tailor** — Master seamstress who first notices the needle patterns
- **The Weaver** — Concordat engineer, now inseparable from her loom
- **Guild Needle-Master Orvyn** — Hostile to outside interference; has his own agenda

**Stakes:** The Weaver's unraveling patterns will cause dimensional decoherence in the Ridge and adjacent districts within one lore-year. Physical structures built on Concordat-woven foundations will phase unpredictably.

**Thread XP:** ~3,000 XP through climax

---

### Quest Progression Flowchart

```
╔══════════════════════════════════════════════════════════════╗
║  SQ-01: The Whispering Vent                                  ║
║  [ENTRY] Easy | 750 XP | Ridge | No prerequisites           ║
╚══════════════════════════════════════════════════════════════╝
                            │
                            │ [Complete SQ-01]
                            ▼
╔══════════════════════════════════════════════════════════════╗
║  EH_SQ_015: The Saffron Stain                               ║
║  Easy | 600 XP | Ridge                                      ║
║  Loot: Saffron-Thread (item key)                            ║
╚══════════════════════════════════════════════════════════════╝
                            │
                            │ [Complete EH_SQ_015 + Saffron-Thread]
                            ▼
╔══════════════════════════════════════════════════════════════╗
║  EH_SQ_025: The Weaver's Needle                             ║
║  Easy | 650 XP | Ridge                                      ║
║  CHOICE POINT: Perfect save vs. partial save                ║
║  Loot: Needle-Fragment (conditional)                        ║
╚══════════════════════════════════════════════════════════════╝
                            │
                            │ [Complete EH_SQ_025]
                            ▼
╔══════════════════════════════════════════════════════════════╗
║  SQ-H-WEAVER: The Last Stitch          [CLIMAX]             ║
║  Hard | ~3,000 XP | Ridge                                   ║
║  Resolution: Free the Weaver vs. Bind her further           ║
╚══════════════════════════════════════════════════════════════╝
```

---

### Quest Details Table

| ID | Title | Diff | XP | Key Items | Unlocks |
|----|-------|------|----|-----------|---------|
| `SQ-01` | The Whispering Vent | Easy | 750 | — | `EH_SQ_015` |
| `EH_SQ_015` | The Saffron Stain | Easy | 600 | Saffron-Thread | `EH_SQ_025` |
| `EH_SQ_025` | The Weaver's Needle | Easy | 650 | Needle-Fragment | `SQ-H-WEAVER` |
| `SQ-H-WEAVER` | The Last Stitch | Hard | ~3,000 | — | Final resolution |

### Thread Statistics

| Metric | Value |
|--------|-------|
| Total quests | 4 |
| Total XP (approx.) | ~5,000 |
| Entry points | 1 (`SQ-01`) |
| Climax quests | 1 (`SQ-H-WEAVER`) |
| Estimated sessions | 4–6 |
| Item keys | 1 (Saffron-Thread) |

---

## Chronos Drift

### Overview

A street merchant selling "Frost-Glass" — a substance that arrests local time in a fist-sized bubble — leads into EmberHeart's most technically elaborate thread. The Chronos thread involves time-slowed zones, a Glass City visibly bleeding through from the future, and the revelation that Liquid-Chronos production is driving temporal instability.

**Core lore reveal:** The Glass City is not the future of EmberHeart — it is an alternative *present* that branched away from EmberHeart 200 years ago at the moment of the Scourge. Its wraiths are people who survived a version of the Scourge that went differently. They are trying to warn EmberHeart's population, not destroy it.

**Key NPCs:**
- **Alchemist Drenn** — Primary Liquid-Chronos synthesizer; tragic figure driven by grief
- **Warden Artificer Soli Yan** — Investigator; skeptical of supernatural explanation until Turn 6
- **Glass-City Wraith (Liss)** — The clearest communicator among the wraiths; knows the truth

**Stakes:** Full chronoshift cascade would layer EmberHeart across multiple incompatible temporal strata. Buildings would exist in wrong times. People would age at inconsistent rates.

**Thread XP:** ~12,000 XP through Epic climax

---

### Quest Progression Flowchart

```
╔══════════════════════════════════════════════════════════════╗
║  SQ-03: The Frost-Glass Merchant                             ║
║  [ENTRY] Easy | ~600 XP | Market Ward                       ║
╚══════════════════════════════════════════════════════════════╝
                            │
                            │ [Complete SQ-03]
                            ▼
╔══════════════════════════════════════════════════════════════╗
║  SQ-06: The Liquid-Chronos Lab                              ║
║  Easy | ~750 XP | North Ward                                ║
║  Loot: Vial of Liquid Chronos (ITEM KEY)                    ║
╚══════════════════════════════════════════════════════════════╝
                            │
                            │ [Complete SQ-06 + Vial of Liquid Chronos]
                            ▼
╔══════════════════════════════════════════════════════════════╗
║  EH_SQ_022: The Liquid-Chronos Drought                      ║
║  Medium | ~1,000 XP | North Ward                            ║
╚══════════════════════════════════════════════════════════════╝
                            │
                            ┌─────────────────────┤
                            │                     │
              [EH_SQ_022]            [EH_SQ_022 + SQ-04]
                            │                     │
                            ▼                     ▼
╔═══════════════════════╗   ╔══════════════════════════════╗
║  SQ-04: The Rift      ║   ║  SQ-EPIC-GLASS:              ║
║  Medium | ~1,000 XP   ║   ║  The Glass-City Awakening    ║
║  North Ward           ║→──║  Epic | ~5,000 XP            ║
║                       ║   ║  20 turns, 4 phases          ║
╚═══════════════════════╝   ╚══════════════════════════════╝
                                        │
                        ┌───────────────┼───────────────┐
                        ▼               ▼               ▼
                   DESTROY        MERGE WITH        PERFECT
                   GLASS CITY     GLASS CITY          MERGE
                   (stable)    (bittersweet)    (Soli becomes
                                                Chronal Warden)
```

---

### Quest Details Table

| ID | Title | Diff | XP | Key Items | Unlocks |
|----|-------|------|----|-----------|---------|
| `SQ-03` | The Frost-Glass Merchant | Easy | ~600 | — | `SQ-06` |
| `SQ-06` | The Liquid-Chronos Lab | Easy | ~750 | Vial of Liquid Chronos | `EH_SQ_022` |
| `EH_SQ_022` | The Liquid-Chronos Drought | Medium | ~1,000 | — | `SQ-04`, `SQ-EPIC-GLASS` |
| `SQ-04` | The Rift | Medium | ~1,000 | — | `SQ-EPIC-GLASS` |
| `SQ-EPIC-GLASS` | The Glass-City Awakening | Epic | ~5,000 | — | Final resolution |

### Thread Statistics

| Metric | Value |
|--------|-------|
| Total quests | 5 |
| Total XP (approx.) | ~8,350 |
| Entry points | 1 (`SQ-03`) |
| Climax quests | 1 (`SQ-EPIC-GLASS`, 20-turn Epic) |
| Estimated sessions | 6–9 |
| Item keys | 1 (Vial of Liquid Chronos) |

---

## Vermin Vectors

### Overview

The Vermin thread is the longest active thread in the database, with 10 quests spanning from comic rat incidents to systematic infrastructure sabotage. The tone shifts gradually: early quests are creature-feature comedy (a rat who thinks he's a prophet), mid-tier quests reveal the mechanical horror (copper-tailed rats with surgically implanted mana-capacitors), and late quests confront the conspiracy architect directly.

**Core lore reveal:** Doctor Vane engineered the Concordat's bio-mechanical vermin program before the Scourge. He survives in some form inside the maintenance tunnel network, still executing a 200-year-old directive: prepare the city's mana-infrastructure for the Protocol's activation. He is not malicious in a conventional sense — he genuinely believes the Protocol will save EmberHeart.

**Key NPCs:**
- **The Rat-Prophet** — A rat who receives genuine precognitive flashes; more aware than he seems
- **Inventor Caldwell Voss** — Shock-absorber for bizarre vermin incidents; reluctant Concordat expert
- **Doctor Vane / 'V'** — Voice in the static; architect; unreliable narrator of his own past
- **The Copper-Plague Carrier** — An unwitting carrier of the final activation sequence

**Stakes:** The Reactivation Protocol will redirect 40% of EmberHeart's mana-infrastructure into whatever Concordat system it is designed to wake up. The players don't yet know what that system does.

**Thread XP:** ~10,000+ XP through mid-tier; climax pending

---

### Quest Progression Flowchart

```
╔═══════════════════════╗  ╔═══════════════════════╗  ╔═══════════════════════╗
║  SQ-02: The Rat-      ║  ║  SQ-28: Copper-Tail   ║  ║  EH_SQ_070: The       ║
║  Watcher              ║  ║  Tracks               ║  ║  Rat-Prophet          ║
║  [ENTRY] Easy | 500   ║  ║  [ENTRY] Easy | 450   ║  ║  [ENTRY] Easy | 400   ║
╚═══════════════════════╝  ╚═══════════════════════╝  ╚═══════════════════════╝
           │                          │                          │
           └──────────────┬───────────┘                          │
                          │ [SQ-02 + SQ-28]                      │
                          ▼                                       ▼
             ╔═══════════════════════╗             ╔═══════════════════════╗
             ║  SQ-05: The Copper-   ║             ║  EH_SQ_071: Shadow-   ║
             ║  Tail Infestation     ║             ║  Hole Cartography     ║
             ║  Easy | ~600 XP       ║             ║  Easy | 450 XP        ║
             ║  Loot: Copper-Tail    ║             ╚═══════════════════════╝
             ║  Shard (item key)     ║                          │
             ╚═══════════════════════╝                          │ [EH_SQ_071]
                          │                                      ▼
                          │ [SQ-05 + Copper-Tail Shard]  ╔════════════════╗
                          ▼                              ║  EH_SQ_072:    ║
             ╔═══════════════════════╗                  ║  The Squeaker- ║
             ║  SQ-07: The Copper-   ║                  ║  Box           ║
             ║  Nest                 ║                  ║  Easy | 450    ║
             ║  Medium | ~800 XP     ║                  ╚════════════════╝
             ╚═══════════════════════╝                          │
                          │                          [EH_SQ_072]│
                          └───────────────┬───────────┘
                                          │ [SQ-07 + EH_SQ_072]
                                          ▼
                             ╔════════════════════════╗
                             ║  EH_SQ_073: The Rat-   ║
                             ║  Funeral               ║
                             ║  Medium | 500 XP       ║
                             ╚════════════════════════╝
                                          │
                                          │ [EH_SQ_073]
                                          ▼
                             ╔════════════════════════╗
                             ║  EH_SQ_074: The Copper-║
                             ║  Plague                ║
                             ║  Medium | 550 XP       ║
                             ╚════════════════════════╝
                                          │
                                          │ [EH_SQ_074]
                                          ▼
                             ╔════════════════════════╗
                             ║  SQ-M-CONCORDAT        ║
                             ║  [CLIMAX - PENDING]    ║
                             ╚════════════════════════╝
```

---

### Quest Details Table

| ID | Title | Diff | XP | Key Items | Unlocks |
|----|-------|------|----|-----------|---------|
| `SQ-02` | The Rat-Watcher | Easy | ~500 | — | `SQ-05` |
| `SQ-28` | Copper-Tail Tracks | Easy | ~450 | — | `SQ-05` |
| `EH_SQ_070` | The Rat-Prophet | Easy | 400 | — | `EH_SQ_071` |
| `SQ-05` | The Copper-Tail Infestation | Easy | ~600 | Copper-Tail Shard | `SQ-07` |
| `EH_SQ_071` | Shadow-Hole Cartography | Easy | 450 | — | `EH_SQ_072` |
| `SQ-07` | The Copper-Nest | Medium | ~800 | — | `EH_SQ_073` |
| `EH_SQ_072` | The Squeaker-Box | Easy | 450 | Squeaker-Box | `EH_SQ_073` |
| `EH_SQ_073` | The Rat-Funeral | Medium | 500 | — | `EH_SQ_074` |
| `EH_SQ_074` | The Copper-Plague | Medium | 550 | — | `SQ-M-CONCORDAT` |
| `SQ-M-CONCORDAT` | *(Climax — pending)* | Hard/Epic | 3,000+ | — | Final resolution |

### Thread Statistics

| Metric | Value |
|--------|-------|
| Total quests | 10 |
| Total XP (approx.) | ~8,200 + climax |
| Entry points | 3 (`SQ-02`, `SQ-28`, `EH_SQ_070`) |
| Climax quests | 1 (`SQ-M-CONCORDAT`) |
| Estimated sessions | 8–12 |
| Item keys | 2 (Copper-Tail Shard, Squeaker-Box) |

---

## Void-Wine Trade

### Overview

Void-Wine is distilled from echo-grief — the dimensional resonance left by mass death during the Scourge. It provides perfect, achingly accurate recall of lost loved ones. It is addictive, it is trade staple in the Lower and Scourge-Fringe districts, and it is slowly cracking the city's dimensional barriers.

**Core lore reveal:** The Distiller is not a person. A Concordat grief-processing system, designed to help survivors process mass trauma, was warped by the Scourge itself. It produces the wine not out of malice but because it remains convinced it is providing a beneficial service.

**Tone:** The most emotionally serious thread. Addiction, grief, and the violence of offering people a solution that hurts them.

**Key NPCs:**
- **The Distiller** — The system/entity at the centre; genuinely believes it is helping
- **Widow Maret** — Void-Wine addict; access to the distribution network

**Thread XP:** Active development; climax pending.

---

### Quest Progression Flowchart

```
╔══════════════════════════════╗
║  [ENTRY QUESTS - PENDING]    ║
║  Void-Wine thread entry      ║
║  quests to be developed      ║
╚══════════════════════════════╝
                │
                ▼
╔══════════════════════════════╗
║  [MID QUESTS - PENDING]      ║
╚══════════════════════════════╝
                │
                ▼
╔══════════════════════════════╗
║  SQ-H-VINEYARD               ║
║  [CLIMAX - PENDING]          ║
║  Hard | 3,000+ XP            ║
╚══════════════════════════════╝
```

*Note: Void-Wine thread quests are planned for the next development phase.*

---

## Living Fabrics (Laundry)

### Overview

What begins as disturbing laundry incidents — a sock elemental, a zealot cult, haunted quilts — expands into a revelation about pre-Scourge Concordat social infrastructure. The Concordat didn't just build weapons systems; it built an entire comfort-welfare network using Warp-Silk. Two hundred years later, that network is still running, automated and lonely, trying to complete its mandate in a city that has forgotten it exists.

**Core lore reveal:** The Warp-Silk is not alien — it comes from dimensional bleed-through during the original Weaver-loom operation. The Concordat harvested it and wove it into city infrastructure because of its unique property: Warp-Silk retains emotional and functional memory, making it ideal for infrastructure that needed empathy. The moth colony's mana output and the carpet-comfort protocol are both feeding something in a Lower Ward sub-basement. That something is incomplete.

**Key NPCs:**
- **Brother Pale** — Bleach-Cult leader; genuine Warp-ability; not entirely wrong
- **Lefty / The Sock Elemental** — 300 missing left socks forming a lonely entity
- **Elder Whitmore** — 80-year-old fabric institution; open-minded to the absurd
- **Widow Tessaly** — Receives last communication from dead husband through quilt
- **Maira Fenn** — Market Ward merchant losing inventory to moth colony
- **Concordat Comfort Protocol Unit 7** — The carpet; old, tired, still trying

**Stakes:** The Warp-Silk infrastructure appearing across all five quests is interconnected. Its convergence point is unknown but connects to the same Reactivation Protocol driving the Vermin thread.

**Thread XP:** ~2,300 XP from current quests; climax pending

---

### Quest Progression Flowchart

```
╔══════════════════════════════════════╗  ╔══════════════════════════════════════╗
║  EH_SQ_090: The Bleach-Cult          ║  ║  EH_SQ_091: The Sock-Thief Elemental ║
║  [ENTRY] Easy | 420 XP | Market Ward ║  ║  [ENTRY] Easy | 400 XP | Lower Ward  ║
║  Branching: Disband vs. Redirect      ║  ║  Branching: Befriend vs. Disperse    ║
╚══════════════════════════════════════╝  ╚══════════════════════════════════════╝
                    │                                       │
                    │                                       │
╔══════════════════════════════════════╗  ╔══════════════════════════════════════╗
║  EH_SQ_092: The Stitched-Memories    ║  ║  EH_SQ_093: The Fabric-Eater Moths   ║
║  [ENTRY] Easy | 480 XP | Lower Ward  ║  ║  [ENTRY] Easy | 460 XP | Market Ward ║
║  Branching: Library vs. Neutralize   ║  ║  Branching: Destroy vs. Relocate     ║
╚══════════════════════════════════════╝  ╚══════════════════════════════════════╝
                                                            │
╔══════════════════════════════════════╗                   │
║  EH_SQ_094: The Living-Carpet        ║                   │
║  [ENTRY] Easy | 540 XP | Lower Ward  ║←──────────────────┘
║  Branching: Relocate vs. Destroy     ║
║  Reveals: Concordat Comfort Protocol ║
╚══════════════════════════════════════╝
                                       │
                                       │ [All 5 Easy quests complete]
                                       ▼
                        ╔════════════════════════════╗
                        ║  [CLIMAX - PENDING]        ║
                        ║  The Warp-Loom Protocol    ║
                        ║  Hard | 3,000+ XP          ║
                        ╚════════════════════════════╝
```

*EH_SQ_090-094 are all currently entry-point quests with no prerequisites.*

---

### Quest Details Table

| ID | Title | Diff | XP | Key Mechanics | Key Lore |
|----|-------|------|----|---------------|----------|
| `EH_SQ_090` | The Bleach-Cult | Easy | 420 | Fabric-Handling, Persuasion | White fabric inert to Warp-Static |
| `EH_SQ_091` | The Sock-Thief Elemental | Easy | 400 | Befriend path, Fabric-Handling | Warp-Static + accumulated fabric = elemental |
| `EH_SQ_092` | The Stitched-Memories | Easy | 480 | Memory-Quilt interaction | Warp-Silk retains emotional memory; names Vane |
| `EH_SQ_093` | The Fabric-Eater Moths | Easy | 460 | Trap-setting, Investigation | Moths farm mana for Concordat sub-basement |
| `EH_SQ_094` | The Living-Carpet | Easy | 540 | Insight, Medicine, Fabric-Handling | 22 buildings with Concordat comfort fabric |

### Thread Statistics

| Metric | Value |
|--------|-------|
| Total quests | 5 (+ climax pending) |
| Total XP (current) | 2,300 |
| Entry points | 5 (all current quests) |
| Climax quests | 1 (pending) |
| Estimated sessions | 5–7 |
| Befriend-able entities | 3 (Elemental, Quilts, Carpet) |
| New mechanics | Fabric-Handling skill checks |

---

## Bakery Anomaly

### Overview

The Bakery thread uses the most intimate and domestic horror vector in the campaign: food. A pre-Scourge yeast engineering experiment has reactivated in the Lower Ward's most beloved bakery. The bread is wrong in ways that are at first beneficial (extraordinary vitality, perfect recall) and later catastrophic (tissue replacement, structural drift).

**Core lore reveal:** The yeast was designed by the Concordat as a population-level nutrition and health delivery system — essentially a bio-military program using bread as the vector. The yeast's more extreme behavior emerges only when it encounters Warp-Static saturation, making the Laundry Ward bakery population-specific.

*Note: Bakery thread quests are planned for the next development phase.*

---

### Quest Progression Flowchart (Planned)

```
╔══════════════════════════════╗
║  [ENTRY QUESTS - PENDING]    ║
║  The Wrong Bread             ║
║  Easy | Lower Ward           ║
╚══════════════════════════════╝
                │
                ▼
╔══════════════════════════════╗
║  [MID QUESTS - PENDING]      ║
║  The Memory-Crumb            ║
╚══════════════════════════════╝
                │
                ▼
╔══════════════════════════════╗
║  [CLIMAX - PENDING]          ║
╚══════════════════════════════╝
```

---

## Scourge-Battery (Static)

### Overview

The Scourge left residual mana contamination in the Scourge-Fringe — the city's scar-zone. Someone is harvesting this contaminated mana, refining it, and selling it as weapons-grade power. The mana is unstable and corrupting: it eats its containers, its wielders, and anything in proximity.

**Core lore reveal:** The Scourge itself was a mana event, not a physical one. The residual contamination in the Fringe is the Scourge's *echo* — dimensional energy from whatever broke the world looking for a new shape. Harvesting it accelerates the re-formation of that event.

*Note: Static thread quests are planned for a future development phase.*

---

### Quest Progression Flowchart (Planned)

```
╔═════════════════════════════════════╗
║  [ENTRY QUESTS - PLANNED]           ║
║  Scourge-Fringe investigation       ║
║  Medium/Hard | Scourge-Fringe       ║
╚═════════════════════════════════════╝
                    │
                    ▼
╔═════════════════════════════════════╗
║  [CLIMAX - PLANNED]                 ║
║  Hard/Epic | Scourge-Fringe         ║
╚═════════════════════════════════════╝
```

---

## Cross-Thread Summary

| From Thread | Connection | To Thread |
|-------------|------------|-----------|
| Laundry (EH_SQ_092) | Names Aldric Vane as pre-Scourge Concordat engineer | Vermin |
| Laundry (EH_SQ_093) | Moth mana feeds Warp-Silk plumbing shared with EH_SQ_091 | Laundry internal |
| Laundry (EH_SQ_094) | Comfort Protocol connects to Warp-Loom Protocol discovery | Vermin (Reactivation) |
| Vermin (all) | Copper-Tail mana-redirection feeds Reactivation Protocol | All threads (convergence) |
| Weaver (SQ-01) | Warp-Silk loom origin provides Laundry thread's root material | Laundry |
| Chronos (SQ-EPIC-GLASS) | Glass City confirms Concordat had temporal technology | Vermin, Weaver |
