# Protocol: EmberHeart Weekly Auto-Tick

When advancing the world state (typically during `/managed` or a session end), follow these deterministic steps to update `SETTLEMENT_STATE.json` and `NPC_STATE_FULL.json`.

## Step 1: Resource Balance
1. **Consumption**: Total Population (47) + Party (4) consumes FU.
   - Base consumption: 305 FU.
   - Party consumption: +20 FU.
2. **Production**:
    - Farming (9 LU): +260 FU.
    - Hunting (2 LU): +40 FU.
    - *Party Node Bonuses*: Apply multipliers from `PARTY_STATE.json` if assigned.
3. **Net Change**: Deduct from `food_stock_fu`.

## Step 2: Cult Spread (Weekly Roll)
- **Global**: Update `corruption_index` based on `CULT_SPREAD_SYSTEM.md` sources.
- **Per NPC**: Perform `ExposureChance` roll (corruption_index * 2%).
- **Exposure**: Success = +10-20 `corruption_exposure`.
- **Symptoms**: If `exposure` >= 50, set `latent_symptom_flag: true`.
- **Agents**: If `allegiance` >= 60, NPC becomes active agent.

## Step 3: Morale & Fear Update
- **IF** `food_stock_fu` deficit: Morale -2, Fear +6.
- **IF** active cult agents > 0: -1 Morale every 2 weeks.

## Step 4: Party Fatigue & Recovery
- **Mission**: +1 to +3 fatigue based on mission tier.
- **Node**: +1 fatigue per week.
- **Rest**: -2 fatigue per week.
- **Threshold**: If `fatigue` >= `threshold`, apply -1 to mission indices.

## Step 5: Tremor Escalation
... [Same as before] ...

## Step 6: Calendar Update
... [Same as before] ...

#protocol #managed #tick #logic
