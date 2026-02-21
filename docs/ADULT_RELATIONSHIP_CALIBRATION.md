# ADULT_RELATIONSHIP_CALIBRATION.md
Version: 1.0
Tone: Mature (Non-Explicit)
Integration: PARTY_RELATIONSHIP_ENGINE.md, CULT_SPREAD_SYSTEM.md

====================================================================
I. INTIMACY LAYER (ADULT TONE)
====================================================================

New metric per pair:

- intimacy (0–100)

Baseline Day 1: 10

Intimacy increases when:
+5 shared high-risk mission survival
+3 private vulnerability scene
+2 after fatigue-rest conversation
+5 if affection >= 60 and trust >= 60
+10 if explicit user-confirmed romantic progression

Intimacy decreases when:
-4 betrayal
-3 public embarrassment
-5 if tension >= 60 for 2+ weeks

Clamp 0–100.

====================================================================
II. INTIMACY THRESHOLDS
====================================================================

>= 30  Emotional closeness
>= 50  Romantic bond
>= 70  Physical relationship implied (fade-to-black)
>= 85  Exclusive bond (if mutually chosen by user)

====================================================================
III. MECHANICAL EFFECTS
====================================================================

Emotional Closeness:
  +1 morale if both present in settlement

Romantic Bond:
  +1 joint mission index
  -2 tension drift per week
  +2 public_perception growth

Physical Relationship (implied):
  +2 morale if settlement stable
  +5 visibility
  +3 gossip_weight
  +2 cult exploitation chance if jealousy present

Exclusive Bond:
  Other PCs' affection toward Kaelrath decreases -2 per week
  jealousy_weight +5%

====================================================================
IV. JEALOUSY ENGINE
====================================================================

If Kaelrath intimacy >= 50 with 2+ PCs:

For each involved PC:
  jealousy_index = (affection - trust) + (intimacy imbalance)

If jealousy_index >= 20:
  tension +3 per week
  cult_exploitation_bonus +2%

If jealousy_index >= 40:
  rivalry_flag = true
  public_perception +5
  council_suspicion +1

Tier 2 prompt required before permanent rivalry.

====================================================================
V. POWER DYNAMICS
====================================================================

If legitimacy >= 50 and Kaelrath bonded:

Public perception shifts from romance to:
  "political alliance"

If legitimacy >= 70 and multiple bonds exist:
  settlement whispers increase
  council may question leadership impartiality

====================================================================
VI. CULT MANIPULATION (ADULT PSYCHOLOGICAL)
====================================================================

Cult may attempt:

- Emotional isolation
- Erotic dream manipulation (non-explicit)
- Suggest betrayal
- Offer exclusive power tied to intimacy
- Shame-based corruption

Silvy:
  Targeted through emotional longing

Vaelis:
  Targeted through intellectual seduction

Mareth:
  Targeted through redemption temptation

Talmarr:
  Targeted through fear of abandonment

Kaelrath:
  Targeted through dominance / legacy temptation

All corruption attempts require Tier 3 prompt before permanent damage.

====================================================================
VII. BOUNDARIES
====================================================================

No:
- Explicit sexual content
- Non-consensual outcomes
- Forced romantic progression
- Pregnancy simulation
- Graphic content

All escalation requires user confirmation.

====================================================================
END
====================================================================
