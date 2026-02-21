# Open Call Trigger
Version: 1.0
Purpose: Defines initial crisis that triggered request for outside aid

====================================================================
I. PRE-CAMPAIGN STATE
====================================================================

- tremor_threat: 3
- structural_integrity: FRACTURED
- mine_depth_level: 2
- caravans_missed: 0
- corruption_index: 1

But:

Hidden Variable:
- Subsurface anomaly probability rising.

====================================================================
II. TRIGGER EVENT: "The Breathing Stone"
====================================================================

Event occurs 2 weeks before party arrival.

At Shaft 2:

Miners report:
- Stone vibrating rhythmically
- Heat spike in lower tunnel
- Faint whispering in cracks

Incident:
- Partial collapse
- 2 injured
- 1 missing miner (unconfirmed death)
- Ore output reduced -25% temporarily

Immediate Effects:
- tremor_threat +1
- council_unity -1
- morale -1
- deep_cult_activity +1 (hidden)

====================================================================
III. COUNCIL RESPONSE
====================================================================

Garric (mine foreman faction):
- Wants deeper excavation to prove vein worth.

Shrine Keeper:
- Calls it a sign.

Refugees:
- Fear instability.

Militia:
- Overextended.

Vote passes narrowly:
- Send open request for outside help.

====================================================================
IV. OPEN CALL CONTENT
====================================================================

Distributed to:
- Caravan routes
- Waystations
- Regional shrines
- Mercenary networks

Message summary:

"Emberheart seeks capable hands. 
Mine instability, tremors, and rising unrest.
Payment in silver and ore share.
Room and standing offered to those who save us."

====================================================================
V. PARTY ENTRY CONDITION
====================================================================

When party accepts Open Call:

Set:
- open_call_posted = true
- adventurer_arrival = true
- legitimacy begins at 5 instead of 0

Upon arrival:
- Immediate Minor Mission offered:
  Inspect Shaft 2 instability
  OR
  Stabilize frightened workers

====================================================================
VI. HIDDEN TRUTH (DO NOT REVEAL WITHOUT INVESTIGATION)
====================================================================

Shaft 2 depth interacts with sealed Shaft 3 pocket.

Breathing Stone is not magical ore.

It is structural membrane.

Mining increases tremor_threat at accelerated rate once depth 3 reached.

Cult activity seeds begin at corruption_index >= 4.
