# 🧶 Quest Network Synthesis: Plot Interlocks & Narrative Chains

This document logs the deep-dive analysis of the EmberHeart side quest database (220 entries) as per the `/ultrathink` protocol. It maps recurring themes, NPC threads, and logical "Lock & Key" progression points to prepare for a 500-quest catalog expansion.

## 🏮 Phase 1: Core Axioms & Regional Clusters

Analysis of the `SIDE_QUESTS_DB.json` reveals three primary "Conflict Hubs" where multiple quests naturally converge:

### 1. The Lower Ward / Low-District (The "Rot" Cluster)
*   **Quests**: `SQ-07`, `EH_SQ_014`, `EH_SQ_021`, `EH_SQ_026`, `EH_SQ_029`.
*   **Plot Points**: Structural decay, "Void-Wine" black market, shadow-vermin infestations.
*   **Interlock Opportunity**: `EH_SQ_026` (Void-Wine leak in tavern cellar) could be a prerequisite for `SQ-07` (The Poisoned Well), suggesting the "Void-Wine" is actually a byproduct of the well's toxin.

### 2. The North-Ward / High-Steampunk (The "Entropy" Cluster)
*   **Quests**: `SQ-16`, `SQ-29`, `EH_SQ_016`, `EH_SQ_022`.
*   **Plot Points**: Temporal skips, memory projection through streetlamps, weeping walls.
*   **Interlock Opportunity**: `EH_SQ_016` (Clocksmith's Hiccup) should be a prerequisite for `EH_SQ_022` (The Lantern's Ghost). The "time skip" in the ward is what allowed the memories from the Lantern to bypass the standard flow of time.

### 3. The Ridge / Peripheral Wards (The "Invasion" Cluster)
*   **Quests**: `SQ-02`, `SQ-15`, `SQ-30`, `EH_SQ_020`.
*   **Plot Points**: Silica-Vents, Star-Ivy, Scourge-fog.
*   **Interlock Opportunity**: `SQ-15` (Glass-Lung Sickness) is the aftermath of `SQ-30` (The Fog-Watcher's Lantern) failing. If the lantern isn't fixed, the sickness spreads.

---

---

## 🧵 Phase 2: Recurring NPC & Faction Threads

### Thread A: The Weaver’s Web (Reality Unweaving)
*   **Quests**: `SQ-01` (Easy), `EH_SQ_015` (Easy), `EH_SQ_025` (Easy).
*   **Key Items**: `Weaver's Ritual Notebook`, `Saffron-Thread`, `Weaver's Needle`.
*   **Plot**: A hidden lineage or cult ("The Weaver of the Deep") is attempting to unweave the reality of Emberheart using silk infused with Void-energy.
*   **Lock Suggestion**: `EH_SQ_025` should be a prerequisite for a future Hard quest `SQ-H-WEAVER` where the player must "re-stitch" a localized reality collapse.

### Thread B: Subterranean Leakage (The "Ink" Trade)
*   **Quests**: `SQ-07` (Easy), `EH_SQ_014` (Easy), `EH_SQ_017` (Easy), `EH_SQ_026` (Easy).
*   **Key Items**: `Spider-Root Extract`, `Void-Wine`, `Eternal Sourdough-Starter`.
*   **Plot**: The sewers are leaking "Liquid-Ink" and "Void-Gall" from a much deeper layer. The "Silk-Hand" gang (`SQ-07`) and local bakers (`EH_SQ_017`) are unwittingly using these as ingredients.
*   **Lock Suggestion**: Completing `EH_SQ_026` (Oozing Barrel) unlocks `SQ-07` (The Poisoned Well).

### Thread C: Chronos Drift (The North-Ward Hiccup)
*   **Quests**: `SQ-06` (Medium), `EH_SQ_016` (Easy), `EH_SQ_018` (Easy).
*   **Key Items**: `Liquid Chronos`, `Stop-Watch`, `Silver-Sprocket`.
*   **Plot**: The North-Ward is physically "skipping" in time due to the usage of pre-Scourge "Sol-Crystals". The "Chronal-Leaks" take the form of Time-Mites.
*   **Lock Suggestion**: `EH_SQ_016` (Clocksmith's Hiccup) is a mandatory key to see the `SQ-06` (Glass Sentry) investigation.

### Thread D: Vermin Vectors (The Rat King's Legacy)
*   **Quests**: `SQ-02` (Easy), `SQ-04` (Medium), `SQ-28` (Easy), `EH_SQ_029` (Easy).
*   **Key Items**: `Rat-Mask`, `Concordat ID Ring`, `Band of the Tides`.
*   **Plot**: Rodents aren't just pests; they are bio-mechanical vectors for the Scourge. "Copper-Tails" eat mana-wiring, while "Shadow-Rats" drink the luck of the Low-Ward.
*   **Lock Suggestion**: Finding the `Concordat ID Ring` in `SQ-28` unlocks the "Political" side of the Rat King mystery in `SQ-04`.

---

## 🔒 Phase 3: The "Lock & Key" Progression Plan

To make the library immersive, we will implement **Narrative Gates**:

1.  **District Credibility**: You cannot see `!medium` quests in the *Lower Ward* until you have completed at least 3 `!easy` quests in that same district.
2.  **Item-Based Unlocks**: Certain "Grandmaster" adventures will require you to HAVE a specific item (like the `Weaver's Needle`) in your `!loot` to甚至 start the quest.
3.  **Branching Consequences**: Completing `SQ-09` (Bandit King's Toll) by *arresting* the King unlocks one set of Hard quests, while *taking the bribe* unlocks a completely different (and darker) set.

---

## 🧪 Phase 4: Future Plot Point Extraction

To reach 100 quests per tier, we should expand these "Hooks":
*   **The Laundry Ward (`EH_SQ_027`)**: Could lead to a whole subplot about "Living Fabrics" and "Mimic Cloth."
*   **The Bakery Anomaly (`EH_SQ_024`)**: Could escalate into a biological warfare plot.
*   **The Static Field (`EH_SQ_019`)**: Could be the first hint of a "Scourge-Battery" being built by the Ridge-Lords.

**Next Step**: Transform this analysis into logic flags within `SIDE_QUESTS_DB.json` (using the `prerequisites` field) once the user approves the specific chains.
