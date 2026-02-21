# Runtime Ruleset: EmberHeart
Version: 1.0

## 周期模型 (Weekly Tick)
Each week corresponds to one deterministic update of the world state.

### 1. Food & Morale
- **Standard Consumption**: 305 Food Units (FU) per week.
- **Status Thresholds**:
    - **Stable**: >= 610 FU
    - **Low**: 305 - 609 FU (Morale -1/week, Fear +3)
    - **Critical**: < 305 FU (Morale -2/week, Fear +6, Unrest +15%)

### 2. Tremor & Threat
- **Hidden Scale**: 0–10. Current Level: 3.
- **Triggers**: Deep mining (Extraction depth) increases threat.
- **Escalation**:
    - **Level 5**: Structural damage risk.
    - **Level 7**: Creature emergence eligible.

### 3. Legitimacy System
- **Range**: 0–100.
- **Ranks**:
    - 25: Trusted Outsider
    - 50: Settlement Champion
    - 70: Council Influence (Legitimacy used to affect votes)
    - 85: De facto Leader

### 4. Faction Pressure
- **Range**: 0-20.
- **Reaction Thresholds**:
    - 7: Soft attention (scouts).
    - 10: Envoy/Ultimatum.
    - 14: Coercion/Sanctions.
    - 18: Direct Intervention.

### 5. Decision Gates (Human-in-the-loop)
- **Tier 2**: Prompt for moderate decisions.
- **Tier 3**: Always ask user for lethal/political outcomes or named NPC deaths.
- **Tier 4**: User-exclusive (War, sovereignty, leadership change).

### 6. Auto-Generation Protocol (DM Mode)
- **Trigger**: When new tracking needs arise (e.g., new colonies, fleets, or research projects).
- **Action**: Automatically generate the necessary JSON or Markdown files to track state.
- **Naming**: Use screaming snake case for file names (e.g., `NEW_COLONY_STATE.json`).
- **Inventory**: Link new files in `SETTLEMENT_STATE.json` inventory for easy access.

#rules #runtime #tick #emberheart
