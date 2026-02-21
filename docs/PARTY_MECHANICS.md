# Party Mechanics
Version: 1.0
Purpose: Defines how party missions affect the settlement simulation engine
Scope: Weekly resolution + event missions
Integration: RESOURCES_ENGINE.md, RESOURCE_SITES.md, RUNTIME_RULESET.md, FACTION_RULES.md

====================================================================
I. PARTY ROLE TYPES
====================================================================

Each week, each party member must be in one of three states:

1) Assigned to Node
2) On Mission
3) Resting / Recovery

No character may be in multiple states.

====================================================================
II. NODE ASSIGNMENT RULES
====================================================================

If assigned to a RESOURCE_SITE:

- Apply their node_bonuses from PARTY_STATE.json
- Apply skill-based multipliers (per SKILL_NODE_MAPPING.md)
- Reduce incident chance per incident_reduction_pp
- Reduce tool_wear if applicable

Node assignment consumes:
- 1 fatigue level per week (unless resting previous week)

If fatigue_level >= fatigue_threshold:
- Output multiplier reduced by 50%
- Injury chance +5%
- Morale penalty if collapse occurs

====================================================================
III. MISSION SYSTEM
====================================================================

A mission is triggered by:

- Event table entry
- Player decision
- Faction pressure escalation
- Cult anomaly detection
- Structural failure
- Open Call arc

MISSION TYPES:
- Resource Stabilization
- Threat Elimination
- Recon / Survey
- Diplomacy
- Structural Repair
- Investigation (cult/anomaly)

====================================================================
IV. MISSION RESOLUTION MODEL
====================================================================

Each mission has:

- Threat Rating (1–10)
- Complexity Rating (1–10)
- Time Cost (days or weeks)
- Risk Tier (1–4)

Party success is computed from:

Combat Index =
  (Average Level × 2)
  + Strongest Frontliner AC/HP factor
  + Spell utility presence
  + Special advantage (favored enemy, etc.)

Skill Index =
  Average of relevant enforced skills

Social Index =
  Average Influence + Tradecraft of involved PCs

Final Resolution Score =
  Combat + Skill + Social + situational modifiers
  vs
  Threat × 5

If score >= threshold:
  SUCCESS
If within 10%:
  Partial Success (costs applied)
If below threshold:
  Failure (penalties apply; Tier 3 prompt required for major harm)

====================================================================
V. LEGITIMACY REWARDS
====================================================================

Legitimacy gained per mission:

Minor mission: +2
Moderate mission: +5
Major mission: +10
Existential crisis: +20

Apply legitimacy_gain_multiplier per PC involved.

Example:
Kaelrath (1.15) + Silvy (1.20)
Major mission base +10
Average multiplier = 1.175
Final legitimacy gain = 11 or 12 (round)

====================================================================
VI. RESOURCE IMPACT TABLE
====================================================================

Resource Stabilization:
- +X FU, WU, or SU
- +Morale 1
- -Incident weight for 2 weeks

Threat Elimination:
- -Threat weight
- -Faction pressure
- +Militia alignment

Recon:
- Unlock hidden node
- Reduce future mission difficulty
- Detect cult activity

Diplomacy:
- Reduce faction pressure by 1–2
- Improve caravan yield
- Raise council unity

Structural Repair:
- Improve StructuralIntegrity one step
- Reduce tremor amplification
- Reduce collapse severity

Investigation:
- Reduce corruption_index
- Reveal cult agent
- Unlock hidden lore

====================================================================
VII. FATIGUE & INJURY
====================================================================

Each mission:
+1 fatigue (minor)
+2 fatigue (moderate)
+3 fatigue (major)

Rest week:
-2 fatigue

If fatigue >= threshold:
- -1 to all mission indices
- +5% injury risk

Injury tiers:
1) Light – disadvantage next week
2) Moderate – -2 HP until healed
3) Severe – Tier 3 prompt required

Medicine MU reduces severity tier by 1.

====================================================================
VIII. PANIC & MORALE INTERACTION
====================================================================

If morale < -3:
- Mission difficulty +1
- Panic chance +5%

Silvy morale_support:
- weekly_morale_floor_bonus = +1
- panic_dampening = -5%

Mareth:
- collapse_severity_reduction = 1 tier

====================================================================
IX. LEADERSHIP PROGRESSION
====================================================================

Legitimacy thresholds:

25 – Trusted Outsider
50 – Settlement Champion
70 – Council Influence
85 – De Facto Leader
95+ – Leadership Vote (Tier 4, user decision)

Influence skill accelerates persuasion checks.
Council unity affects vote success probability.
