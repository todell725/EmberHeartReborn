# EmberHeart Branching Decisions Reference

> **Version:** 2.0 — 58 quest database  
> This document covers all quests with meaningful branching outcomes, from flavor-only choices to permanent world-state changes.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Critical Decisions](#2-critical-decisions)
3. [All Branching Quests Reference](#3-all-branching-quests-reference)
4. [Branching Categories](#4-branching-categories)
5. [Optimization Guide](#5-optimization-guide)

---

## 1. Introduction

### How the Branching System Works

Every quest in EmberHeart ends with a `branching_outcomes` block in the database. This block defines two (occasionally three) possible resolution paths and their downstream consequences.

**Branching outcomes affect four systems:**

| System | How It's Affected |
|--------|------------------|
| **Settlement Stability** | Integer modifier (±1–5) to city structural health |
| **Settlement Morale** | Integer modifier (±1–5) to citizen well-being |
| **World State** | Named permanent effects persisting between sessions |
| **Future Quest Availability** | Some Epic-tier quests explicitly `unlocks` based on path choice |

**What branching does NOT do (by default):**  
Current Easy and Medium quests generally do *not* lock future quest access based on branching choice. The consequence is qualitative — the world looks different — but both paths leave the same quest chain accessible. Epic-tier quests are the exception.

### Multiple Playthrough Considerations

The branching system is designed around a *single continuous campaign* model, not discrete playthroughs. However, choices accumulate. A campaign where the party consistently chooses aggressive solutions (destroy every fabric entity, disperse the Sock Elemental, bleach the cult) creates a measurably different EmberHeart than one that befriends every entity encountered.

**Tone signature:** Aggressive playthroughs trend toward *higher stability, lower morale*. Protective/befriend playthroughs trend toward *lower stability, higher morale*. Neither is correct — they represent genuinely different EmberHearts.

---

## 2. Critical Decisions

These are the decisions with the highest downstream impact. DMs should give players clear information about the context before these turns and avoid railroading in either direction.

---

### Decision 1: The Glass-City Awakening — Three-Way Resolution

**Quest:** `SQ-EPIC-GLASS`  
**Turn:** Turn 18–20 (Phase 4: The Reckoning)  
**Emergency trigger:** Active Glass-City Awakening; the city has minutes before temporal cascade

**Context:**  
The players have navigated the Glass City's interior, met the Wraith Liss, and now face the final choice. The Glass City cannot be stopped from manifesting — the question is *how* it resolves.

#### Path A: Destroy the Convergence Point
> *Sever the dimensional anchor connecting Glass City and EmberHeart. The Glass City will dissipate.*

| Aspect | Effect |
|--------|--------|
| Settlement Stability | +3 (city is safe) |
| Settlement Morale | -2 (the Glass City's people perish) |
| World State | EmberHeart stabilises; North Ward clocks run correctly again |
| Lore cost | The Glass City's 200 years of warnings die with it |
| NPC outcome | Soli Yan survives; Liss disperses |
| Unlocks | None |

#### Path B: Merge the Cities
> *Allow the Glass City to phase into EmberHeart. Two populations, one city.*

| Aspect | Effect |
|--------|--------|
| Settlement Stability | -2 (integration chaos) |
| Settlement Morale | +3 (Glass City refugees survive) |
| World State | Doubled population; Glass City NPCs become permanent residents; North Ward becomes a dual-time zone |
| Lore gain | Access to Glass City's 200 years of Concordat research records |
| NPC outcome | Liss becomes a recurring NPC; Soli Yan is changed by the experience |
| Unlocks | Potential future content involving Glass City refugees |

#### Path C: Perfect Merge (Hidden Path)
> *Requires Soli Yan to have gained the `Chronal Sense` ability (Path B prerequisite loot from earlier in the quest). Perform a phased resonance merge that fully integrates both cities without structural chaos.*

| Aspect | Effect |
|--------|--------|
| Settlement Stability | +1 |
| Settlement Morale | +4 |
| World State | As Path B, but seamlessly integrated; Soli Yan becomes the first Chronal Warden |
| Bonus ability | Soli Yan grants party `Chronal Attunement` passive ability |
| Unlocks | High-tier content involving Soli Yan as a recurring ally |

**DM recommendation:** Path C should feel earned, not obvious. Only hint at its existence if the party explored thoroughly during Phases 1–3. Path A is narratively cleanest; Path B is emotionally richest; Path C is the completionist reward.

---

### Decision 2: The Bleach-Cult — Redirect or Disband

**Quest:** `EH_SQ_090`  
**Turn:** Turn 7 (Resolution)  
**Context:** Brother Pale's Bleach-Cult has been caught purifying fabric in the market district. Their activities are genuinely disruptive. But Brother Pale has demonstrable Warp-sensitivity — he can *feel* the Warp-Static in fabric — and his instinct (bleach neutralizes it) is accidentally correct.

#### Path A: Disband the Cult
> *Expose the cult's activities to city authority. Brother Pale is fined; the cult disperses.*

| Aspect | Effect |
|--------|--------|
| Market Ward Stability | +1 |
| Morale | -1 (Pale genuinely wanted to help) |
| World State | Concordat Warp-Silk cache under bleached district is eventually found by scavengers |
| NPC loss | Brother Pale as a recurring asset disappears |

#### Path B: Redirect the Cult
> *Explain Warp-Static to Brother Pale. Ask the cult to become Warp-Fabric Wardens — identifying Warp-Silk in the city and reporting it rather than destroying it.*

| Aspect | Effect |
|--------|--------|
| Market Ward Stability | No change |
| Morale | +2 (Pale achieves his purpose) |
| World State | Warp-Fabric Wardens become a minor civic institution; they report Warp-Silk discoveries to the party |
| NPC gain | **Brother Pale** becomes a recurring contact for Laundry thread investigation |
| Intel gain | Wardens discover 7 additional Warp-Silk deposits in Market Ward over following weeks |

**DM recommendation:** Path B is the stronger narrative choice. Brother Pale's sensitivity is a rare asset that is explicitly tied to later Laundry thread content. Redirecting the cult gives the party an early warning system for Warp-Silk phenomena.

---

### Decision 3: The Sock-Thief Elemental — Befriend or Disperse

**Quest:** `EH_SQ_091`  
**Turn:** Turn 7 (The Choice)  
**Context:** Lefty is a Warp-Static elemental formed from 300 stolen left socks. It is not malicious — it stole only *left* socks because it is building what it thinks will be a friend. It is lonely. It is also a minor dimensional hazard.

#### Path A: Befriend the Elemental
> *Provide Lefty with a proper home, a name, and voluntary contributions from Laundry Ward residents.*

| Aspect | Effect |
|--------|--------|
| Settlement Morale | +2 |
| World State | **Lefty** becomes Laundry Ward mascot; occasional ambient sock-disappearances continue; Lefty provides mild dimensional-disturbance warnings |
| Sock resolution | All 300 socks are returned except Lefty's core 12 |
| NPC gain | Lefty is available for future Laundry thread interactions |
| Lore function | Demonstrates Warp-Static can form sapient entities from accumulated material |

#### Path B: Disperse the Elemental
> *Unravel the Warp-Static field; the socks disintegrate back to their component materials.*

| Aspect | Effect |
|--------|--------|
| Settlement Stability | +1 (hazard removed) |
| Settlement Morale | -1 (children cry) |
| World State | 300 socks returned; no ongoing disappearances; Warp-Static vent sealed |
| Lore function | Still demonstrates the elemental-formation mechanism; Warp-Static dispersal noted in Corsairs' records |

**DM recommendation:** Befriending Lefty provides the better campaign experience. Lefty is designed as a recurring character with escalating utility. Dispersal is the cautious choice; befriending is the memorable one.

---

### Decision 4: The Stitched-Memories — Preserve or Neutralize

**Quest:** `EH_SQ_092`  
**Turn:** Turn 8 (Resolution)  
**Context:** The memory-quilts in Widow Tessaly's attic have been identified as Concordat Warp-Silk quilts containing the consciousness-echoes of their original weavers. They speak. They remember. They weep. The question is what to do with them.

#### Path A: Establish a Memory-Quilt Library
> *Work with Elder Whitmore to create a public archive. Residents can come to speak with the echoes of the dead.*

| Aspect | Effect |
|--------|--------|
| Morale | +4 (extraordinary; grief given form and dialogue) |
| Stability | -1 (dimensional bleed from active quilts increases slightly) |
| World State | **Memory-Quilt Library** becomes a civic institution; access to 12 named consciousness-echoes, all pre-Scourge |
| Lore gain | Party can question pre-Scourge citizens directly about Concordat operations |
| Vane connection | Quilt 7 contains a woman who knew young Aldric Vane personally |

#### Path B: Neutralize the Quilts
> *Treat with Warp-static suppressant. The echoes quiet. The quilts become ordinary memorial objects.*

| Aspect | Effect |
|--------|--------|
| Stability | +1 |
| Morale | -2 (Tessaly's goodbye with her husband is lost) |
| World State | Quilts returned as silent memorials; dimensional bleed resolved |
| Lore loss | Pre-Scourge witness testimony permanently unavailable |

**DM recommendation:** Path A is the significantly stronger choice from a campaign-depth perspective. The Memory-Quilt Library is one of the most valuable party assets, particularly for the Vermin thread's Vane investigation. The dimensional bleed cost is trivial. Neutralizing the quilts is a defensible cautious choice that the party will regret by mid-campaign.

---

### Decision 5: The Rat-Funeral — Honor or Investigate

**Quest:** `EH_SQ_073`  
**Turn:** Turn 8 (Final Resolution)  
**Context:** The players discover that the Concordat rats hold funeral ceremonies for their dead. The bodies are being arranged in specific patterns before burial. The patterns, upon investigation, are complex mana-routing diagrams. Do you allow the funeral to proceed as ritual, or interrupt it to study the diagram?

#### Path A: Allow the Funeral
> *Let the rats complete their ceremony. Observe respectfully.*

| Aspect | Effect |
|--------|--------|
| Morale | +2 (unexpected emotional weight) |
| NPC relationship | Rat society becomes cautiously non-hostile to the party |
| Intel | Partial diagram captured from memory/sketch; 60% accurate |
| World State | Rats remember this. Future Vermin-thread encounters have slightly reduced hostility |

#### Path B: Interrupt to Investigate
> *Capture the body diagram before it's buried. Full mana-routing schematic obtained.*

| Aspect | Effect |
|--------|--------|
| Stability | +1 (critical intelligence gained) |
| Morale | -1 |
| Intel | Full diagram captured; 100% accurate mana-routing schematic for the Reactivation Protocol's current phase |
| NPC relationship | Rat society becomes actively hostile; ambush risk in tunnel sub-basements increases |
| Cascades to | EH_SQ_074: The Copper-Plague encounters are harder |

**DM recommendation:** Path A is the more interesting choice and does not permanently lose the intelligence — the party can piece together the diagram over EH_SQ_074. Path B provides a significant tactical advantage at a relationship cost that matters in late Vermin thread encounters.

---

## 3. All Branching Quests Reference

| Quest ID | Title | Choice A | Choice B | A Unlocks | B Unlocks | Impact |
|----------|-------|----------|----------|-----------|-----------|--------|
| `SQ-EPIC-GLASS` | The Glass-City Awakening | Destroy convergence | Merge cities (+hidden C) | None | Refugee content | **Critical** |
| `EH_SQ_025` | The Weaver's Needle | Perfect save | Partial save | SQ-H-WEAVER (both) | SQ-H-WEAVER | **Major** |
| `EH_SQ_090` | The Bleach-Cult | Disband cult | Redirect as Wardens | None | Brother Pale NPC | **Major** |
| `EH_SQ_091` | The Sock-Thief Elemental | Befriend Lefty | Disperse elemental | Lefty NPC | None | **Major** |
| `EH_SQ_092` | The Stitched-Memories | Memory-Quilt Library | Neutralize quilts | Vane intel | None | **Major** |
| `EH_SQ_093` | The Fabric-Eater Moths | Destroy colony | Relocate colony | None | Relocated colony NPC | **Medium** |
| `EH_SQ_094` | The Living-Carpet | Relocate Unit 7 | Neutralize carpet | Unit 7 NPC | None | **Medium** |
| `EH_SQ_073` | The Rat-Funeral | Allow ceremony | Interrupt to study | Rat goodwill | Full schematic | **Medium** |
| `EH_SQ_074` | The Copper-Plague | Contain outbreak | Trace source first | Faster resolution | Vane contact | **Medium** |
| `EH_SQ_072` | The Squeaker-Box | Repair device | Keep broken | Translation bonus | Black market data | **Minor** |
| `EH_SQ_070` | The Rat-Prophet | Believe the prophet | Debunk the prophet | Prophet as informant | None | **Minor** |
| `EH_SQ_071` | Shadow-Hole Cartography | Map and report | Map and withhold | Official resource | Private leverage | **Minor** |

---

## 4. Branching Categories

### Major Decisions
These create persistent NPCs, permanently unlock intel assets, or alter the balance of a thread's investigation capacity. Both paths remain accessible in terms of future quests, but the qualitative experience of the campaign differs significantly.

**Signature:** One path creates something (a NPC, an institution, a relationship), the other path removes a possibility.

**Quests:** `EH_SQ_090`–`EH_SQ_092`, `EH_SQ_025`, `SQ-EPIC-GLASS`

### Medium Decisions
These affect settlement metrics (±1–3) and create or prevent ambient events in specific districts. They may produce minor NPC contacts but not major recurring figures.

**Signature:** Stability vs. Morale tradeoff; both paths feel like reasonable choices.

**Quests:** `EH_SQ_093`–`EH_SQ_094`, `EH_SQ_073`–`EH_SQ_074`

### Minor Decisions
These primarily affect tone and flavor. World state changes are minimal or short-lived. Both choices lead to essentially the same campaign trajectory.

**Signature:** The choice matters in the moment but the DM won't need to reference it again.

**Quests:** `EH_SQ_070`–`EH_SQ_072`

---

## 5. Optimization Guide

### Maximize Quest Access
To unlock every quest in the network with no-quest-left-behind goal:

1. Complete `SQ-02` + `SQ-28` simultaneously (both required for `SQ-05`)
2. Complete `EH_SQ_070` → `EH_SQ_071` → `EH_SQ_072` chain independently
3. Merge both Vermin sub-chains at `EH_SQ_073`
4. Complete Chronos through `EH_SQ_022` before attempting `SQ-EPIC-GLASS`
5. Complete both `EH_SQ_022` AND `SQ-04` for EPIC access

For Laundry: all five current quests are entry-point accessible simultaneously. Order by district for geographic efficiency: Market Ward first (`EH_SQ_090`, `EH_SQ_093`), then Lower Ward (`EH_SQ_091`, `EH_SQ_092`, `EH_SQ_094`).

### Completionist Branching Strategy

For a player wanting to see everything in a single campaign, prioritize **befriend/preserve** paths for Laundry thread entities. The NPCs created (Lefty, Brother Pale, the Memory-Quilt witnesses, Unit 7) are interconnected and reference each other in later content. Destroying them creates narrative gaps.

For `SQ-EPIC-GLASS`: Path C (Perfect Merge) is the completionist resolution. It requires:
- Exploring Phase 2 thoroughly to find the `Chronal Resonance Map`
- Keeping Soli Yan close during Phase 3 (do not take the shortcut path)
- Having 0 Chronal Stability failures entering Phase 4

### Multiple Playthrough Strategy

**Run 1 (Cautious):** Prioritize stability: Disperse Sock Elemental, Redirect Bleach-Cult (not Disband — too much intel loss), Neutralize quilts, Destroy Glass City. Produces a cleaner EmberHeart with fewer persistent supernatural entities but significantly less cross-thread intelligence.

**Run 2 (Empathetic):** Prioritize morale: Befriend Sock Elemental, Redirect Bleach-Cult, Establish Quilt Library, Perfect Merge Glass City. Produces a richer EmberHeart heavily annotated with recurring NPCs and historical testimony. The Concordat's purpose becomes clear much earlier.

**Run 3 (DM's Choice):** Mix based on party instincts. This is the most interesting run to observe. The branching system is calibrated so that there is no "wrong" pattern of choices — only different EmberHearts.

---

> *The goal is never optimization. EmberHeart is a city worth inhabiting. Make choices the characters would make.*
