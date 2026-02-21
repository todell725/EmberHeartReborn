# 🌌 EmberHeart Bot Expansion Plan: Deep Dive Suggestion (v1.0)

Based on a deep-dive analysis of the **Eleventh Age** simulation, the `SlayerEngine`, and the `QuestEngine`, here are 10 proposed features to transform the Discord bot into a living interface for the Emberheart Sovereignty.

---

## 🏗️ 1. Idle Fleet Operations (Shadow Missions)
*   **Source**: [FLEET_REGISTRY.json](file:///c:/Users/todd/agent-bookish-train/EmberHeart/docs/FLEET_REGISTRY.json)
*   **Concept**: Deploy your "Seed Sonde" or "Spark Frigates" on real-world timers to explore neighbor systems.
*   **Command**: `!fleet dispatch [Ship] [Target]`
*   **Mechanic**: Recon missions reduce "Fog of War" in [NEIGHBOR_SYSTEM_STATE.json](file:///c:/Users/todd/agent-bookish-train/EmberHeart/docs/NEIGHBOR_SYSTEM_STATE.json) and generate unique loot in real-time.

## 🏛️ 2. The Steward’s Council (NPC Interaction)
*   **Source**: [NPC_STATE_FULL.json](file:///c:/Users/todd/agent-bookish-train/EmberHeart/docs/NPC_STATE_FULL.json)
*   **Concept**: Use the bot to "summon" key NPCs (like Councilman Vane) for a dynamic conversation.
*   **Command**: `!summon [NPC_Name]`
*   **Mechanic**: The bot uses Webhook impersonation and the `EHClient` brain to simulate the NPC's specific personality and current corruption level for a 5-minute interaction window.

## 💓 3. Sovereignty Heartbeat (Automated Weekly Tick)
*   **Source**: [auto_tick.py](file:///c:/Users/todd/agent-bookish-train/EmberHeart/scripts/auto_tick.py)
*   **Concept**: Stop manual ticks. Sync the world's progression to a real-world weekly schedule.
*   **Mechanic**: Every Wednesday morning, the bot announces the **"Weekly Proclamation"**: Economy updates, morale shifts, and randomized cult rumors from the simulation.

## 🚨 4. Corruption Alert System (Live Intrigue)
*   **Source**: [CULT_CORRUPTION_ENGINE.md](file:///c:/Users/todd/agent-bookish-train/EmberHeart/docs/CULT_CORRUPTION_ENGINE.md)
*   **Concept**: If the `corruption_index` reaches a threshold, the bot sends an "Emergency Alert" to the channel.
*   **Mechanic**: Players must use a command (e.g., `!purge` or `!investigate`) to handle the threat before the next "Tick", or risk losing an NPC to the cult.

## ⚒️ 5. Artifact Fabrication (Idle Crafting)
*   **Source**: [ECONOMY_ENGINE.md](file:///c:/Users/todd/agent-bookish-train/EmberHeart/docs/ECONOMY_ENGINE.md)
*   **Concept**: Spend your massive surpluses of Ore (`OU`) and Metal (`M2U`) to build custom gear.
*   **Command**: `!forge [Blueprint]`
*   **Mechanic**: Crafting takes 12-48 hours. The bot tracks progress and adds the final item to [PARTY_EQUIPMENT.json](file:///c:/Users/todd/agent-bookish-train/EmberHeart/docs/PARTY_EQUIPMENT.json) upon completion.

## 🛋️ 6. Downtime Assignments
*   **Source**: [PARTY_STATE.json](file:///c:/Users/todd/agent-bookish-train/EmberHeart/docs/PARTY_STATE.json)
*   **Concept**: Assign party members to specific city nodes (e.g., "Kaelrath assigned to the Warden Forges").
*   **Mechanic**: While assigned, the character gains unique "Downtime XP" and provides a passive buff to the town (e.g., -5% build time or +2 Morale).

## 📊 7. Live Economic Ledger
*   **Source**: [SETTLEMENT_STATE.json](file:///c:/Users/todd/agent-bookish-train/EmberHeart/docs/SETTLEMENT_STATE.json)
*   **Concept**: A more granular `!stats` command that shows "Projected Growth" and current "Resource Burn."
*   **Visual**: Uses table formatting to show how the "Golden Age" abundance is being distributed.

## 📜 8. The Chronicle Archive (RAG Search)
*   **Source**: [QUEST_DEEDS.md](file:///c:/Users/todd/agent-bookish-train/EmberHeart/docs/QUEST_DEEDS.md)
*   **Concept**: Query the history of the campaign directly.
*   **Command**: `!history [Topic/Keyword]`
*   **Mechanic**: The AI DM summarizes every deed, campaign log, and decision related to that keyword, bridging the gap between sessions.

## 🗺️ 9. Sector Radar (Dynamic Map)
*   **Source**: [RESOURCES_ENGINE.md](file:///c:/Users/todd/agent-bookish-train/EmberHeart/docs/RESOURCES_ENGINE.md)
*   **Concept**: A text-based ASCII map or dynamic image generation of the current sector.
*   **Command**: `!map`
*   **Mechanic**: Shows your current fleet locations, active resource nodes, and discovered neighbor systems.

## 🐉 10. Sovereign Hunts (Boss Slaying)
*   **Source**: [IDLE_SLAYER_DB.json](file:///c:/Users/todd/agent-bookish-train/EmberHeart/docs/IDLE_SLAYER_DB.json)
*   **Concept**: Massive "World Bosses" that appear once per month.
*   **Mechanic**: Requires the user to coordinate multiple "Party Slots" or specific fleet support to take down within a real-time window.

---
> [!TIP]
> **Priority Suggestion**: Start with **#3 (Weekly Tick)** and **#5 (Fabrication)**. They bridge the gap between "Endless Wealth" and "Actionable Progression" most effectively.
