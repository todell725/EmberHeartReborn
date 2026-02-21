# NPC Agent Model: EmberHeart
Version: 1.0

## NPC 状态属性 (Attributes)
- **Loyalty (0–100)**: Allegiance to the settlement/player.
- **Fear (0–100)**: Driven by food status, tremors, and events.
- **Influence (0–10)**: Weight of their voice in politics.
- **Grievance (0–10)**: Cumulative dissatisfaction.
- **Ambition (0–10)**: Drive for power or change.
- **Faction Lean**: -5 to +5 across major factions.
- **Status**: active, injured, missing, dead.

## 影响力等级 (Influence Scale)
- **Council**: 8–10
- **Specialists/Captain**: 5–8
- **Militia/Miners**: 2–4
- **Laborers**: 1–2

## 变动逻辑 (Update Logic)
- **Loyalty**: Affected by morale, food status, and legitimacy.
- **Fear**: Affected by tremors, event severity, and security.

## 叛逃阈值 (Defection)
- If Loyalty <= 20 and Fear >= 60, defection or sabotage event becomes eligible (Moderate).

#npcs #agents #politics #emberheart
