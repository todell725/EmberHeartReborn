# Cult Spread System
Version: 1.0
Purpose: Hidden corruption & infiltration simulation
Scope: Weekly tick
Integration: SETTLEMENT_STATE.json, PARTY_STATE.json, RUNTIME_RULESET.md

====================================================================
I. CORE VARIABLES
====================================================================

Global:
- corruption_index (0–10)
- deep_cult_activity (0–10)

Per NPC (hidden):
- corruption_exposure (0–100)
- cult_allegiance (0–100)
- latent_symptom_flag (boolean)

Per PC:
- corruption_susceptibility modifier
- cult_marked (boolean)

====================================================================
II. CORRUPTION INDEX (GLOBAL)
====================================================================

Represents ambient anomaly pressure.

Base increase sources:
+1 if tremor_threat >= 5
+1 if rare_metal_exposed == true
+1 if Shaft 3 opened
+1 if morale <= -5
+1 if deep_cult_activity >= 6

Base decrease sources:
-1 if Investigation mission succeeds
-1 if corruption_event resolved publicly
-1 if Talmarr detection + Silvy detection both active

Clamp 0–10.

Thresholds:

0–2 Dormant
3–4 Murmurs
5–6 Organized cells
7–8 Active sabotage
9–10 Open manifestation

====================================================================
III. CULT SPREAD MECHANIC
====================================================================

Each week:

For each NPC:
  ExposureChance = corruption_index × 2%

Modify ExposureChance by:
  +5% if fear > 50
  +5% if morale < -3
  +3% if unemployed
  +3% if injured
  -3% if council_unity >= 7
  -Talmarr cult_detection_bonus

If roll succeeds:
  corruption_exposure += 10–20

If corruption_exposure >= 50:
  latent_symptom_flag = true

If corruption_exposure >= 80:
  cult_allegiance increases

If cult_allegiance >= 60:
  NPC becomes active agent (hidden)

====================================================================
IV. ACTIVE AGENT EFFECTS
====================================================================

Per active agent:

+1% mine incident chance
+1% farm blight chance
+1 morale penalty every 2 weeks
+1 structural degradation chance per 4 weeks

Agents attempt:

- Resource theft
- Panic spreading
- Ritual preparation
- Sabotage of repairs

If corruption_index >= 7:
  agents may attempt coordinated action.

====================================================================
V. PC CORRUPTION RULES
====================================================================

Each PC has corruption_susceptibility.

Weekly roll if corruption_index >= 4:

Chance = corruption_index × 1%

Multiply by corruption_susceptibility.

If roll succeeds:
  Apply Corruption Mark (hidden flag)

Effects of mark:
- Occasional dream sequences
- Advantage on detecting anomalies
- Disadvantage on resisting cult influence
- Future awakening hooks

Silvy has higher susceptibility.
Mareth has lower.
Kaelrath moderate.
Talmarr reduced.

Tier 3 prompt required before permanent PC corruption.

====================================================================
VI. DETECTION SYSTEM
====================================================================

Detection Score =
  (Talmarr Survival/20)
+ (Silvy Influence/25)
+ (Investigation mission success bonus)

If DetectionScore >= corruption_index:
  Reveal one latent_symptom NPC.

Investigation mission required to confirm.

====================================================================
VII. RITUAL THRESHOLD EVENT
====================================================================

If:

- corruption_index >= 8
AND
- 3+ active agents
AND
- tremor_threat >= 6

Trigger: Ritual Attempt Event

This becomes a Major Mission.

Failure:
  tremor_threat +2
  structural_integrity -1 tier
  deep_cult_activity +2

Success:
  corruption_index -2
  legitimacy +10
  cult agents revealed

====================================================================
VIII. SHAFT 3 INTERACTION
====================================================================

Opening Shaft 3:

Immediately:
  corruption_index +2
  deep_cult_activity +2

Every week open:
  +1 corruption_index if depth increases

If corruption_index >= 9 and Shaft 3 open:
  Manifestation event possible.

Manifestation is Tier 4 user-gated.

====================================================================
IX. BALANCE SAFETY
====================================================================

Cult cannot:

- Destroy settlement without Tier 3 prompt
- Kill named NPC without Tier 3 prompt
- Permanently corrupt PC without Tier 3 prompt

Cult is pressure engine, not auto-loss mechanic.
