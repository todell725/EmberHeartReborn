# Cult & Corruption Engine: EmberHeart
Version: 1.0

## 核心指标 (Core Metrics)
- **Cult Activity (0–10)**: Hidden infiltration level.
- **Corruption Index (0–10)**: Physical/spiritual rot in the settlement.

## 指标增长 (Deltas)
- **Growth**: Tremor Threat (>= 5), Low Morale, Critical Food.
- **Decay**: Council Unity (>= 7), Wards & Rituals, Conservation Actions.

## NPC 转化模型 (NPC Conversion)
- **Base Chance**: 0.5% per NPC per week.
- **Modifiers**: High fear, high cult activity, low morale.
- **Effect**: `cult_marked: true`. Morale drift, rumor distortion, event shifts.

## 决策门槛 (Decision Gates)
- Discovery of a `cult_marked` NPC triggers a **Tier 3 Decision Gate** (Exile/Execution/Prison).

#cult #corruption #hidden #emberheart
