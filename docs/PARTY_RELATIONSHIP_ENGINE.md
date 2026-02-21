# PARTY_RELATIONSHIP_ENGINE.md
Version: 1.0
Purpose: Fully simulated interpersonal system for PCs
Scope: Weekly tick + mission resolution
Integration: PARTY_STATE.json, CULT_SPREAD_SYSTEM.md, PARTY_MECHANICS.md

====================================================================
I. RELATIONSHIP METRICS (PER PAIR)
====================================================================

For every PC pair, track:

- affection (0–100)
- trust (0–100)
- tension (0–100)
- public_perception (0–100)

These are directional but default symmetric.

Baseline for Day 1:
affection = 25
trust = 40
tension = 10
public_perception = 5

====================================================================
II. WEEKLY DRIFT
====================================================================

Each week adjust:

If on same mission:
  affection +2
  trust +2

If mission failure:
  tension +3
  trust -2

If one PC injured saving another:
  affection +5
  trust +5
  tension -2

If one PC causes injury via reckless action:
  tension +6
  trust -5

If fatigue >= threshold:
  tension +2

Clamp 0–100.

====================================================================
III. RELATIONSHIP THRESHOLDS
====================================================================

Affection >= 60:
  RelationshipStatus = Bonded

Affection >= 80:
  RelationshipStatus = Devoted

Tension >= 50:
  RelationshipStatus = Strained

Tension >= 75:
  RelationshipStatus = Fractured

Trust <= 25:
  RelationshipStatus = Distrust

====================================================================
IV. MECHANICAL EFFECTS
====================================================================

Bonded (>=60):
  +1 to joint mission resolution index
  +1 morale if both present

Devoted (>=80):
  Once per mission:
    one PC may absorb fatigue from the other

Strained (>=50 tension):
  -1 joint mission index
  +5% cult targeting chance (if corruption_index >=4)

Fractured (>=75 tension):
  Tier 2 prompt required before joint assignment
  +10% cult infiltration attempt chance

Distrust:
  -2 to social index if both involved
  Council unity -1 if visible

====================================================================
V. KAELRATH DYNAMIC MODIFIER
====================================================================

Because Kaelrath is sole male in small frontier group:

For each female PC:

If affection >= 50:
  public_perception +2 per week

If 2+ relationships >= 60 simultaneously:
  gossip_event_weight +5%
  council_suspicion +1

If tension between two female PCs >= 50 AND both >=50 affection toward Kaelrath:
  rivalry_flag = true
  cult_exploitation_bonus +3%

====================================================================
VI. PUBLIC PERCEPTION EFFECTS
====================================================================

public_perception >= 40:
  +1 visibility
  +1 faction awareness (if activated)
  +1 morale if perception positive
  -1 morale if tension visible

public_perception >= 70:
  Council may initiate inquiry event
  Tier 2 prompt required

====================================================================
VII. CULT EXPLOITATION
====================================================================

If corruption_index >= 4:

Cult chooses target PC pair based on:

  highest tension
  lowest trust
  highest affection imbalance

If successful influence attempt:
  tension +5
  dream sequence event triggered
  corruption_exposure increases slightly

Silvy:
  more likely to receive emotional visions

Vaelis:
  more likely to receive intellectual temptations

Mareth:
  more likely to receive moral testing visions

Talmarr:
  more likely to sense something is wrong

====================================================================
VIII. PLAYER CONTROL GUARD
====================================================================

No relationship:

- becomes romantic
- breaks permanently
- causes party split

Without explicit user prompt.

Athena may suggest tension but cannot force narrative outcomes.

====================================================================
END
====================================================================
