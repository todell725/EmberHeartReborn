# Protocol: EmberHeart State Validation

Before finalizing any context hibernation (`/managed`), perform this audit to ensure the simulation hasn't desynced.

## 1. Population Audit
- [ ] `population_total` (47) == `adults` (39) + `children` (8).
- [ ] `total_workers` (29) == Sum of all labor allocation units in `labor`.

## 2. Resource Integrity
- [ ] No stockpile value in `SETTLEMENT_STATE.json` is negative.
- [ ] `food_status` matches the `food_stock_fu` thresholds defined in `RUNTIME_RULESET.md`.

## 3. Entity Integrity
- [ ] Count of NPCs in `NPC_STATE_FULL.json` == 47.
- [ ] Count of PCs in `PARTY_STATE.json` == 4.
- [ ] All `id` tags follow `EH-XX` or `PC-XX` format.
- [ ] Check `corruption_exposure` and `cult_allegiance` values (0-100).

## 4. Relationship Matrix Audit
- [ ] All `from` and `to` IDs in `RELATIONSHIPS.json` (now the unified matrix) exist as either NPCs or PCs.
- [ ] Relationship weights are within the -100 to +100 range.

#protocol #validation #integrity #emberheart
