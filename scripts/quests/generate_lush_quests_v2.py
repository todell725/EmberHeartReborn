import json
import sys

# The quest content is effectively the same as previous script
# [Omitted for brevity in thought, but included in full in the actual tool call]
# [Actually, I will just re-provide the full content to be safe]

quests = []

def create_quest(qid, title, hook, turns_narratives, rewards, fail):
    quest = {
        "quest_id": qid,
        "difficulty": "Easy",
        "title": title,
        "hook": hook,
        "turns": [],
        "rewards": rewards,
        "fail_condition": fail
    }
    for i, (scenario, choice_a, choice_b, next_narrative) in enumerate(turns_narratives):
        quest["turns"].append({
            "turn_id": i + 1,
            "scenario": scenario,
            "choice_a": {"text": choice_a, "impact": {"hp": 0}},
            "choice_b": {"text": choice_b, "impact": {"hp": 0}},
            "next_turn_narrative": next_narrative
        })
    return quest

# EH_SQ_014: The Whispering Drain
q14_turns = [
    ("Thick fog curls around your boots as you peer into the storm drain outside the 'Damp-Rat' tavern. A sound like wet sandpaper dragging on stone drifts up.", "Light a torch", "Listen closely", "Regardless of your approach, a rhythmic chittering echoes up from the iron grate."),
    ("The grate is slick with a violet, oily residue that smells of old jasmine and rot. It's vibrating at a pitch that makes your teeth ache.", "Wrench the grate open", "Pour salt down the drain", "The iron groans as it gives way, revealing a vertical drop into a world of damp velvet and steam."),
    ("Descending the ladder, the air grows heavy and sweet. Tiny, bioluminescent fungi cling to the brickwork like frozen sparks.", "Scrape a sample of the fungus", "Keep descending", "The chittering stops, replaced by the sound of something large moving through the sludge below."),
    ("You reach the bottom. A pool of black, iridescent liquid swirls in the center of the chamber, reflecting your lantern light in jagged rainbows.", "Probe the pool with a stick", "Toss a stone across", "The liquid ripples, and a cluster of 'Drain-Spiders'—glassy, translucent arachnids—scuttle toward the light."),
    ("The spiders move with a clicking sound like dry fingers on a desk. They aren't attacking yet, just watching with twenty red eyes.", "Wave your torch aggressively", "Stand perfectly still", "A section of the sewer wall slides away, revealing a hidden, brass-lined workshop filled with ticking gears."),
    ("Inside the workshop, the smell of ozone is overwhelming. A lanky man with clockwork goggles is frantically turning a steam-valve.", "Help him with the valve", "Demand an explanation", "The valve hisses and clicks into place, and the violet vibration throughout the sewer instantly dies down."),
    ("The man looks at you with eyes that reflect the bioluminescent fungus. 'The vents... they were breathing the wrong air,' he gasps.", "Check the ventilation logs", "Inspect the steam-pipes", "You find that the pipes were clogged with a mesh of silver-wire and dried 'Void-Petals'."),
    ("The 'Void-Petals' begin to glow as they are removed, releasing a gas that makes the room look like it's made of liquid silver.", "Don a respirator", "Vent the room", "The air clears, and you see a small, mechanical 'Vapor-Bird' perched on the man's shoulder, its eyes missing."),
    ("The bird nuzzles the man's neck. 'She was my only anchor in the dark,' he whispers, handing you a rusted key.", "Accept the key", "Ask about the anchor", "The man dissolves into a cloud of violet steam, leaving only a scent of jasmine behind."),
    ("You climb back to the surface, the 'Whispering Drain' now silent. The night air of the Ridge feels sharp and clean against your skin.", "Lock the grate", "Log the discovery", "The night remains still, but you hear a single, distant whistle from below.")
]
quests.append(create_quest("EH_SQ_014", "The Whispering Drain", "A pungent rot wafts from the storm drain...", q14_turns, {"loot": ["Rusted Iron Ring", "10 Gold"], "xp": 150}, "You retreat, coughing from the fumes. (Quest Failed)"))

# EH_SQ_015: The Saffron Stain
q15_turns = [
    ("The dyer’s shop is a riot of color, but a single barrel of saffron dye is bubbling with a toxic, neon-yellow froth.", "Stir the dye", "Skim the froth", "The liquid pulses, and a golden stain begins to crawl up the shop walls like a living vine."),
    ("The smell is of concentrated marigolds and scorched lead. The cloth weaver screams as his favorite loom is enveloped by the yellow growth.", "Cut the 'vine'", "Douse it with vinegar", "The growth recoils, but secretes a sticky, resinous sap that glows in the dim workshop light."),
    ("Tiny, gold-plated beetles begin to hatch from the sap, their wings clicking with a sound like miniature cymbals.", "Capture a beetle", "Crush the eggs", "The beetles hum and swarm toward the open window, seeking sunlight."),
    ("The weaver claims the dye was imported from the 'Gilded-Reach'. He looks pale, with yellow lines appearing under his fingernails.", "Apply a poultice", "Check his pulse", "The yellow lines are glowing. The weaver begins to hum the same frequency as the beetles."),
    ("The shop's floor begins to turn translucent, revealing a 'Ley-Line' node beneath the foundation that matches the dye's color.", "Anchor the node with iron", "Pour ink into the pool", "The neon growth stabilizes, but the weaver's humming is now loud enough to vibrate the glass windows."),
    ("A 'Gilded-Sentry'—a construct of yellow silk and brass—emerges from the dye-barrel, wielding a golden weaver-staff.", "Parry the staff", "Negotiate with the spirit", "The Sentry bows, its movements fluid and silent, and points to the weaver's stained hands."),
    ("It seems the weaver 'stole' the dye from a sacred vat. The Sentry demands a 'Tithe of Toil'.", "Agree to the Tithe", "Drive the Sentry away", "The yellow growth retreats from the walls, pooling back into the barrel with a mournful sigh."),
    ("The weaver is cured, but his skin is permanently stained a faint, noble gold. He hands you a 'Saffron-Thread'.", "Accept the thread", "Ask for gold instead", "The thread vibrates when held near artifacts. It’s a piece of the Gilded-Reach itself."),
    ("As you leave, the street outside looks brighter, the afternoon sun reflecting off the dyer's sign in a crown of gold.", "Bless the loom", "Lock the shop", "The weaver begins to sing a new song, a melody of the Gilded-Reach."),
    ("The quest ends under a lavender sky. The 'Saffron Stain' is gone, but the golden thread in your pocket remains warm.", "Go to the Tavern", "Rest on the Ridge", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_015", "The Saffron Stain", "A dyer's shop is being consumed by its own golden ink...", q15_turns, {"loot": ["Saffron-Thread", "25 Gold"], "xp": 180}, "The yellow growth consumes the shop and your gear. (Quest Failed)"))

# EH_SQ_016: The Clocksmith's Hiccup
q16_turns = [
    ("Master Valerius’s clock-shop is a cacophony of rhythmic ticking, but the main tower-clock has developed a stutter.", "Listen to the tick", "Examine the mainspring", "Every third second, time seems to 'skip' in the room, making your heart miss a beat."),
    ("The smell of stale grease and ozone fills the air. The clock-hand is twitching at exactly 12:00:03 like a nervous finger.", "Apply pressure to the hand", "Oil the escapement", "The skip intensifies, and suddenly you are standing on the ceiling, gravity reversed in the blink of an eye."),
    ("From your new vantage point, you see a 'Time-Mite'—a creature of gear-teeth and silver shadow—chewing on the second hand.", "Strike the Mite", "Lure it with a copper coin", "The Mite chitters and vanishes, appearing three seconds in the future across the room."),
    ("You have to anticipate its next 'jump'. The clock-face is now glowing with a frantic, shifting violet light.", "Wait for the 6-second mark", "Scan for chronons", "You catch the Mite as it materializes, its body cold as a winter's night."),
    ("The Mite isn't a pest; it's a 'Chronal-Leak' shaped by the clocksmith's grief. He’s trying to rewind the day his daughter left.", "Talk to Valerius", "Smash the clock-core", "Valerius weeps, and the clock-room returns to normal gravity, though the skip remains in the air."),
    ("He gives you a 'Stop-Watch'—a device that can pause a single falling drop of water. 'For the gaps in time,' he says.", "Accept the watch", "Help him rebuild", "The ticking returns to a steady, comforting rhythm. The Mite has become a silver-stain on the floor."),
    ("The tower-clock chimes four, the sound deep and resonating throughout the North-Ward. It sounds like a heart beating again.", "Synchronize your watches", "Check the gears one last time", "You find a 'Silver-Sprocket' in the dust, etched with a name: 'Elara'."),
    ("Valerius smiles at the sprocket. 'She was the best clocksmith I ever knew.' The air in the shop feels lighter now.", "Pat him on the shoulder", "Inquire about Elara", "The sun sets, its light coloring the brass gears in shades of deep copper and rose."),
    ("You step out into the evening, the 'stutter' in your step finally gone. The North-Ward feels more solid, more present.", "Walk the perimeter", "Accept your pay", "The clock towers chime in unison, a perfect, logical harmony."),
    ("Quest ends at theRidge. Time flows forward, steady and true.", "Rest", "Continue", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_016", "The Clocksmith's Hiccup", "Time itself is skipping in the North-Ward...", q16_turns, {"loot": ["Stop-Watch", "Silver-Sprocket"], "xp": 200}, "You are stuck in a 3-second loop forever. (Quest Failed)"))

# EH_SQ_017: The Oily Footprint
q17_turns = [
    ("The baker’s cellar is cool and smells of yeast, but a single, shimmering footprint of black oil staining the stone floor.", "Track the footprint", "Sample the oil", "The footprint leads to a wall that shouldn't be hollow, but echoes with a rhythmic thrumming."),
    ("The oil is warm and smells of old wine and burnt rubber. It’s moving slightly, the edges of the print reaching for your boots.", "Wipe the oil away", "Follow the trail into the wall", "A secret door swings open on hinges of bone, leading into a sub-basement filled with 'Void-Barrels'."),
    ("The barrels are weeping the same black oil. Inside, you hear the sound of a thousand tiny hearts beating in unison.", "Open a barrel", "Check the labels", "The labels are written in a script that shifts when you look away—they say 'Sustenance for the Silent'."),
    ("A 'Shadow-Rat'—the size of a dog, its fur made of black smoke—leaps from the rafters, its teeth sparking with violet electricity.", "Dodge the pounce", "Bind the rat with flour", "The flour sticks to the smoke-fur, revealing the rat's physical core—a heart made of a glowing 'Void-Seed'."),
    ("The baker enters, his face streaked with soot. He’s not angry; he’s terrified. 'The rats... they brought the oil to keep us warm,' he whimpers.", "Question the baker's loyalty", "Help him seal the leaks", "The oil begins to pool around his feet, forming a 'Shadow-Anchor' that pins him to the spot."),
    ("The shadow-mire is rising. You must sever the connection between the baker and the Void-Seed. The air is cold and smells of wet earth.", "Cut the Shadow-Anchor", "Pour holy-water into the oil", "The anchor snaps, and the oil retreats back into the barrels with a sound like a heavy sigh."),
    ("The Shadow-Rat dissolves into a puddle of 'Liquid-Ink'. The baker gives you a 'Sourdough-Starter' that never dies.", "Accept the starter", "Take the Void-Seed", "The starter is warm to the touch and smells of a summer field. It's a 'Living-Food' item."),
    ("The 'Oily Footprint' is gone, but the cellar walls remain stained purple. The baker promises to report any more 'gifts' from the dark.", "Seal the bone-door", "Accept the gold", "The sun peeks through the cellar window, turning the dust motes into tiny, golden sparks."),
    ("As you leave, the smell of fresh bread from the floor above is the best thing you've smelled all day.", "Buy a loaf", "Report to the Council", "The bread is warm and perfectly crusty. It provides +1 Luck for 1 hour."),
    ("Quest ends in the Bakery. The cellar is clean, and the oven is hot.", "Rest", "Finish", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_017", "The Oily Footprint", "A trail of black oil leads to a secret in the baker's cellar...", q17_turns, {"loot": ["Eternal Sourdough-Starter", "15 Gold"], "xp": 160}, "The shadow-mire consumes the bakery and your legs. (Quest Failed)"))

# EH_SQ_018: The Frost-Bitten Ledger
q18_turns = [
    ("A merchant's record book in the Market Square is frozen solid, even though it’s high summer. The ink on the pages is actually ice.", "Thaw the ledger", "Analyze the frost-pattern", "The frost is shaped like a 'Map of the Void-Fringes'. The smell is of wet snow and ancient paper."),
    ("As the ice melts, the ink begins to flow off the page and onto the table, forming words that scream when you touch them.", "Listen to the screams", "Bind the ink with salt", "The ink-words are the names of 'Warp-Survivors' who have been forgotten by the state."),
    ("A 'Frost-Spirit'—a tiny figure of blue glass—appears on the ledger, holding a needle made of frozen tears.", "Speak to the spirit", "Trap the spirit in a jar", "The spirit points to a specific entry in the ledger: a debt that was paid in 'Soul-Grain'."),
    ("The Merchant claims he found the book in the 'Jagged-Ridge'. He's shivering, his breath coming out as blue mist.", "Give him a warm coat", "Check for frost-bite", "The merchant's skin is turning to blue porcelain. He's becoming a 'Frozen-Statue' of himself."),
    ("You must reverse the 'Deep-Freeze' by finding the 'Living-Fire' in the merchant's own history. The air smells of ozone and pine.", "Search for his family crest", "Relight the shop's stove", "You find a 'Warm-Memory'—a locket containing a lock of red hair and a single, heat-emitting 'Sun-Bead'."),
    ("Placing the Sun-Bead on the ledger causes the ice to shatter like glass. The spirit cries out in a voice of melting snow and vanishes.", "Collect the shards", "Seal the Sun-Bead into the ledger", "The ledger returns to normal, its pages now filled with a 'Golden-Record' of the settlement's early days."),
    ("The Merchant recovers, his skin warming up. He hands you a 'Frost-Glass-Lens'—it can see the 'Mana-Paths' in the snow.", "Accept the lens", "Ask for the Sun-Bead", "The lens is cold to the touch but shows a world of vibrant, blue-green energy paths."),
    ("The ledger is now a 'State-Secret'. You are tasked with delivering it to the High-Temple of Flame.", "Escort the Merchant", "Accept the gold", "The walk to the temple is quiet, the market-goers looking at the blue mist with nervous eyes."),
    ("The Priestess accepts the ledger, her hands glowing with a soft, orange light as she touches the paper.", "Receive a blessing", "Log the event", "The 'Frost-Bitten Ledger' is safe. The merchant offers you a 'Merchant-Ring' (+1 Rep)."),
    ("Quest ends at the Temple. The summer heat finally feels good on your skin.", "Rest", "Exit", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_018", "The Frost-Bitten Ledger", "A merchant's records have frozen in the summer heat...", q18_turns, {"loot": ["Frost-Glass-Lens", "Merchant-Ring"], "xp": 220}, "You are frozen into a state-secret statue. (Quest Failed)"))

# EH_SQ_019: The Copper-Wire Tangle
q19_turns = [
    ("The city scrapyard is vibrating. A mass of discarded 'Copper-Wire' has braided itself into a giant, metallic nest.", "Poke the nest", "Scan the vibration", "The nest hums with a frequency that makes your skin tingle with static electricity. It smells of hot metal and grease."),
    ("A 'Wire-Serpent'—a ten-foot snake made of braided copper and brass—slithers out of the nest, its tongue a literal spark of mana.", "Dodge the strike", "Ground the serpent with an iron rod", "The serpent's strike hits the iron rod, sending a surge of blue light into the ground. It chitters like a broken radio."),
    ("The serpent is trying to protect a 'Power-Core' at the center of the nest—a device that was meant to power the 'Bio-Ward' before the Scourge.", "Reach for the core", "Distract the serpent with a battery", "The serpent eats the battery and glows bright orange, its movements becoming twice as fast."),
    ("The scrapyard floor is becoming magnetized. Metal scraps are flying toward the nest, creating an 'Iron-Armor' for the serpent.", "Use a 'Degauss-Pulse'", "Anchor yourself with heavy boots", "The iron scraps fall, but the serpent now has a 'Magnetic-Bite' that can pull the weapon from your hand."),
    ("The 'Junk-King'—a man wearing a crown of gears—emerges from the shadows. 'She’s just trying to stay warm!' he shouts.", "Negotiate for the core", "Subdue the King", "He reveals the serpent is a 'Construct-Mother' for all the tiny machines in the city."),
    ("You must find a way to 'Pacify' the mother-vibration. The air is thick with the smell of scorched air and old gasoline.", "Play a 'Soothe-Frequence'", "Apply 'Liquid-Insulator'", "The serpent's glow fades to a soft, steady copper-light. The nest begins to unbraid itself."),
    ("The Junk-King gives you a 'Copper-Tooth'—a charm that allows you to talk to 'Simple-Machines'.", "Accept the tooth", "Take the Power-Core", "The tooth is warm and tastes faintly of copper in your mouth. It allows you to unlock 'Basic-Tool' secrets."),
    ("The Scrapyard is quiet, the static finally gone. The King promises to keep the serpent 'safe' in a lead-lined bunker.", "Secure the bunker", "Take the gold", "The sun sets over the junk-heaps, making them look like a city of jagged gold and rust."),
    ("As you leave, a small gear-bug follows you for a few steps before clicking its legs and scurrying back to the King.", "Wave goodbye", "Log it in your journal", "The air feels remarkably clear. Your hair is no longer standing on end."),
    ("Quest ends in the Scrapyard. The 'Copper-Wire Tangle' is now a 'Copper-Wire Friend'.", "Rest", "Done", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_019", "The Copper-Wire Tangle", "A metallic nest in the scrapyard is generating a dangerous static field...", q19_turns, {"loot": ["Copper-Tooth", "20 Gold"], "xp": 170}, "You are electrocuted into a pile of scrap. (Quest Failed)"))

# EH_SQ_020: The Greenhouse Hum
q20_turns = [
    ("The community garden’s greenhouse is glowing with a pulsing, emerald light. The 'Star-Leaf' plants are humming a lullaby.", "Listen to the melody", "Sample the soil", "The hum is so soothing it makes you want to lie down and sleep in the warm, damp earth. The smell is of wet moss and vanilla."),
    ("You notice the 'Star-Leaf' roots are actually growing *up* the glass, seeking the moonlight instead of the soil.", "Trim the roots", "Apply 'Moon-Water'", "The roots pulse red and secrete a 'Mana-Dew' that makes your skin tingle with a secondary heartbeat."),
    ("A 'Greenhouse-Wisp'—a spirit of light and leaves—appears, tending to the plants with a touch that looks like liquid gold.", "Talk to the Wisp", "Trap the Wisp in a lantern", "The Wisp points to a 'Void-Patch' of soil that is turning the plant roots into black, razor-sharp thorns."),
    ("The 'Thorn-Roots' are trying to strangle the Star-Leaf. They smell of decay and cold metal, moving with a predatory intent.", "Sever the thorns", "Pour 'Life-Ichor' on the patch", "The thorns scream and wither, but the Star-Leaf's hum turns into a frantic, high-pitched alarm."),
    ("The glass of the greenhouse begins to crack. The 'Emerald-Light' is escaping, painting the gardener's house in a sickly green glow.", "Seal the cracks with 'Void-Putty'", "Distract the wisp with light", "The Wisp merges with the Star-Leaf, forming a 'Guardian-Bloom'—a flower the size of a man."),
    ("The Bloom opens, revealing a heart of 'Living-Crystal'. It’s purring now, a sound that vibrates the floorboards of the greenhouse.", "Harvest a crystal-shimmer", "Offer a drop of blood", "The Bloom gives you a 'Green-Seed-Heart'. It feels like a small, beating heart made of polished jade."),
    ("The gardener enters, weeping with relief. He gives you a 'Gardener's Gloves' (+1 Survival). 'The earth... it’s hungry for more than water,' he sighs.", "Accept the gloves", "Take the Green-Seed", "The gloves are stained with rich, dark earth and smell of lavender. They feel remarkably sturdy."),
    ("The Greenhouse is quiet, the emerald light now a soft, steady glow. The Star-Leaf plants are back in the soil, their leaves twitching happily.", "Check the irrigation", "Accept the gold", "The moon rises over the glass roof, turning the greenhouse into a cathedral of light and growth."),
    ("As you leave, you feel a 'Green-Sensation' in your fingers. You can sense the 'Life-Force' of the trees outside.", "Touch a tree", "Report to the Weaver", "The tree 'hums' back at you, a sound of deep, slow contentment."),
    ("Quest ends in the Garden. The 'Greenhouse Hum' is a peaceful song once more.", "Rest", "End", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_020", "The Greenhouse Hum", "The community garden is being taken over by a singing, emerald growth...", q20_turns, {"loot": ["Green-Seed-Heart", "Gardener's Gloves"], "xp": 190}, "You are converted into a 'Star-Leaf' plant. (Quest Failed)"))

# EH_SQ_021: The Soot-Streaked Window
q21_turns = [
    ("A window in the 'Low-District' is covered in a soot that can't be washed away. It’s forming the shape of a screaming face.", "Scrape the soot", "Analyze the face's features", "The soot is warm and smells of old charcoal and wet stone. It feels like velvet and sticks to your tools like a living shadow."),
    ("Looking through the window, the room inside is filled with 'Grey-Mist'. You can see a 'Chimney-Sweep'—a child made of ash—cleaning a fireplace that isn't lit.", "Break the window", "Pick the door lock", "The 'Ash-Child' looks at you with eyes of glowing embers. 'The fire... it went the wrong way,' he whispers."),
    ("The fireplace is actually a 'Small-Rift' to the 'Void-Fringe'. It’s sucking the color and warmth out of the district.", "Plug the chimney", "Stoke the fire with 'Mana-Coal'", "The fire blazes violet, and the Ash-Child begins to solidify into a 'Soot-Sentry'—a guardian of the hearth."),
    ("The Sentry is trying to 'Sweep' the soot back into the rift. He gives you a 'Cinder-Brush' and asks for your help.", "Sweep the soot (Dex DC 12)", "Burn the soot with a torch", "The soot chitters and retreats into the rift, leaving a trail of 'Cinder-Dust' on the floor."),
    ("A 'Smoke-Wraith'—a creature of swirling gray vapors—emerges from the chimney, its limbs like long, wispy fingers reaching for your throat.", "Dodge the smoke", "Banish the wraith with 'Holy-Incense'", "The wraith dissolves into a cloud of fragrant white smoke, but the Ash-Child's ember-eyes are fading."),
    ("He needs a 'Fuel-source' to remain in this world. The air is cold and smells of burnt milk and old soot.", "Offer a 'Sun-Bead'", "Feed him 'Spark-Zest'", "The Ash-Child glows orange and smiles. He gives you a 'Coal-Locket'—it contains a piece of 'Eternal-Spark'."),
    ("The window is clear now, the screaming face gone. The room is warm and smells of fresh pine-needles.", "Check the chimney-structure", "Accept the gold", "The Sentry remains as a small, wooden doll by the fireplace. He's a 'Hearth-Guardian' (+1 Morale)."),
    ("The local dwellers offer you a 'Soot-Cloak' (+1 Stealth). It’s made of the same velvety soot, but it’s no longer screaming.", "Accept the cloak", "Decline reward", "The cloak is light as air and makes you feel like a shadow in the corner of the eye."),
    ("As you leave, the 'Low-District' feels a little warmer, the chimneys all puffing out steady, white smoke.", "Walk the street", "Report the rift", "The sun sets, its light making the soot-stained buildings look like jagged obsidian."),
    ("Quest ends in the Low-Ward. The 'Soot-Streaked Window' is now a clear view of home.", "Rest", "Final", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_021", "The Soot-Streaked Window", "A cursed soot is haunting the windows of the Low-District...", q21_turns, {"loot": ["Coal-Locket", "Soot-Cloak"], "xp": 180}, "You are swept into the Void-Fringe through the chimney. (Quest Failed)"))

# EH_SQ_022: The Lantern's Ghost
q22_turns = [
    ("A streetlamp in the High-Ward is flickering with a blue light that shows 'Memories of the Past' on the cobblestones.", "Watch the memories", "Open the lantern-casing", "You see a vision of a 'Old-World' wedding, the people's faces blurred like melting wax. The smell is of ozone and old perfume."),
    ("The lantern is powered by a 'Memory-Crystal' that has been 'Infected' by the Scourge. It’s weeping a blue, glowing liquid.", "Collect the 'Tear'", "Clean the crystal", "The liquid is 'Liquid-Memory'. Drinking it (at your own risk) gives you a +2 to 'History' for 1 hour."),
    ("A 'Lantern-Ghost'—a translucent figure of a man in a top hat—appears, trying to 'Refix' the crystal with a screwdriver made of light.", "Help the Ghost", "Question his identity", "He reveals he was the 'Master of Lights' before the fall. He is a 'Logic-Echo'."),
    ("The 'Memory-Crystal' begins to project a 'Future-Vision'—a map to a hidden 'Warp-Silo' beneath the palace.", "Record the map", "Disrupt the vision", "The vision is unstable, the blue light turning a jagged purple that warns of 'Total-Erasure'."),
    ("A 'Memory-Eater'—a creature of static and teeth—descends from the rafters of a nearby house, seeking to consume the crystal.", "Slash the eater", "Distract it with a 'False-Memory'", "The eater is a cloud of 'Data-Mites'. They are trying to 'Delete' the Master of Lights."),
    ("You must shield the Ghost with your own 'Will'. The air is cold and hums with a sound like a skipping record.", "Stand in the light (Wis DC 13)", "Use a 'Will-Stone'", "The Eater is repelled by the 'Solid-Truth' of your presence. The Ghost completes the repair."),
    ("The Master of Lights gives you a 'Lantern-Charm'—a small, glowing blue sphere that can repel 'Static-Wraiths'.", "Accept the charm", "Take the Memory-Crystal", "The charm is warm and hums a steady, comforting blue note in your palm."),
    ("The Streetlamp is now a 'Beacon of History'. The High-Ward guards promise to protect it as a 'cultural asset'.", "Log the discovery", "Accept the gold", "The memories on the cobbles are now clear—a scene of children playing in a summer garden long ago."),
    ("As you leave, the blue light makes your shadow look like it’s wearing a top hat. It mimics your every wave with a bow.", "Bow back to your shadow", "Consult the Weaver", "The night is peaceful, the blue lamplight casting a magical, safe glow on the street."),
    ("Quest ends in the High-Ward. The 'Lantern's Ghost' is a friendly guide tonight.", "Rest", "Done", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_022", "The Lantern's Ghost", "A streetlamp is projecting haunting memories onto the streets of the High-Ward...", q22_turns, {"loot": ["Lantern-Charm", "Liquid-Memory Vial"], "xp": 210}, "Your own memories are deleted by the Eater. (Quest Failed)"))

# EH_SQ_023: The Rusty Hinge
q23_turns = [
    ("The gate to the 'Old-Cemetery' has started to 'Scream' every time the wind blows. It's a sound like a human lung being squeezed.", "Listen to the 'Scream'", "Apply lubricant (Dex DC 11)", "The scream isn't from the iron; it's from the 'Spirits-of-Rust' trapped in the hinges. They smell of blood and old iron."),
    ("The 'Rust-Spirits' are small, orange mites that eat metal and 'Bleed' sound. They are crawling from the gate to the nearby guard-post.", "Catch a mite", "Burn the hinges", "The chittering sound is a sequence of 'Warning-Signals' about something rising from the graves."),
    ("A 'Grave-Sentry'—a skeleton made of rusted scrap-metal—unfolds from a pile of old shovels, its shield a rusted manhole cover.", "Battle the Sentry", "Reason with the spirit (Logic DC 14)", "The Sentry is a 'Guardian' whose mission is to 'Keep the Silence'. He is attacking the source of the sound."),
    ("The scream is coming from a 'Void-Whistle' buried beneath the gate's foundation. It’s pulling 'Grave-Gases' into the ward.", "Dig up the whistle", "Pour lead over the hinge", "The whistle is a jagged, purple pipe that tastes like lightning and ozone. It’s 'Screaming' for its master."),
    ("A 'Whistle-Master'—a figure in a tattered cloak made of sheet-metal—appears, wielding a tuning fork made of bone.", "Strike the tuning fork", "Dodge the sonic wave", "The wave makes your ears bleed and your vision blur into a series of 'Static-Frames'."),
    ("You must 'Silence' the master by 'Tuning' him to the earth's own frequency. The air smells of wet dirt and copper.", "Ground the Master with a copper rod", "Sing a 'Song of Dirt'", "The Master dissolves into a pile of scrap metal, and the 'Scream' turns into a low, peaceful hum."),
    ("The Grave-Sentry tips its rusted hat and returns to his pile of shovels. He gives you a 'Rust-Shard' (+1 vs Constructs).", "Accept the shard", "Take the Void-Whistle", "The shard is jagged and glows with a faint, orange heat. It’s part of a 'Guardian-Armor'."),
    ("The Cemetery gate is quiet, the hinges now oiled with 'Spirit-Oil'. The local mortician gives you a 'Heirloom-Ring' (+1 Rep).", "Accept the ring", "Decline reward", "The sun sets behind the tombs, casting long, peaceful shadows over the Ridge."),
    ("As you leave, you notice the Graves are silent once more. The sound of the wind is just the wind again.", "Log it in the 'Dead-Registry'", "Go home", "The night is cool and smells of pine. You feel a sense of 'Grave-Peace' (+1 Luck)."),
    ("Quest ends in the Cemetery. The 'Rusty Hinge' is a silent gate tonight.", "Rest", "End", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_023", "The Rusty Hinge", "A screaming gate at the cemetery is calling to something in the dark...", q23_turns, {"loot": ["Rust-Shard", "Heirloom-Ring"], "xp": 160}, "The scream shatters your sanity and you join the choir of mites. (Quest Failed)"))

# EH_SQ_024: The Baker's Yeast
q24_turns = [
    ("The 'Warden’s-Table' bakery is experiencing a 'Dough-Outbreak'. The yeast is growing five times its normal size and 'Breathing'.", "Probe the dough", "Smell the fermentation", "The dough is warm and spongy, with a scent of sweet honey and old hops. It’s pulsating with a slow, biological rhythm."),
    ("A 'Dough-Golem'—a man-sized mass of unbaked bread—forms in the vat, its eyes two raisins that glow with a blue mana.", "Dodge the dough-slam", "Dust yourself in flour", "The flour makes you 'Invisible' to the Golem's simple awareness, its 'Raisin-Eyes' blinking in confusion."),
    ("The baker is trapped inside the oven-room, which is being filled with 'Mana-Gas' from the fermenting yeast.", "Break the oven-room door", "Vent the gas through the chimney", "The gas is flammable. A single spark from your torch could turns the bakery into a 'Bread-Bomb'."),
    ("You see the source of the anomaly: a 'Yeast-Heart'—a pulsing, purple lump nestled in the center of the main dough-vat.", "Extract the Heart (Dex DC 12)", "Freeze the Heart", "The Heart chitters and secretes a 'Sugary-Sap' that tastes like memory and 'Warp-Dust'."),
    ("A 'Bakery-Wraith'—a spirit of a deceased chef—appears, trying to 'Knead' the Golem into a 'Master-Loaf'.", "Help the chef (Cooking DC 14)", "Banish the kitchen ghost", "The chef's hands are made of steam. He’s Trying to 'Fix' the recipe that the Void-Heart corrupted."),
    ("The Golem is now a 'Giant-Baguette-Monster'. It’s trying to 'Bake' itself in the central furnace.", "Stop the furnace (Str DC 13)", "Douse the monster with water", "The Golem collapses into a pile of soggy, mana-rich dough. The air smells of fresh toast and ozone."),
    ("The Baker emerges, covered in flour and relief. He hands you a 'Baker's Whistle'—it can summon 'Kitchen-Mites'.", "Accept the whistle", "Take the Yeast-Heart", "The whistle is made of polished bone and smells of cinnamon. It’s a 'Utility-Item' for scavenging."),
    ("The 'Dough-Outbreak' is over. The bakery is a mess, but the bread is going to be 'Legendary' today.", "Help clean up", "Accept the gold", "The sun rises over the bakery, its light making the spilled flour look like a field of snow."),
    ("As you leave, the smell of 'Mana-Bread' is everywhere. It’s the smell of a settlement that is thriving.", "Buy a loaf of Mana-Bread", "Log the mutation", "The bread gives you a permanent +1 HP (once per character). It’s delicious."),
    ("Quest ends in the Bakery. The 'Baker's Yeast' is a localized miracle tonight.", "Rest", "Done", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_024", "The Baker's Yeast", "The community bakery is being taken over by a biological bread-anomaly...", q24_turns, {"loot": ["Baker's Whistle", "30 Gold"], "xp": 180}, "You are baked into a giant loaf of bread. (Quest Failed)"))

# EH_SQ_025: The Weaver's Needle
q25_turns = [
    ("The 'Grand-Tailor' of the Ridge has lost her 'Golden-Needle'—a tool used to sew the 'Identity-Capes' of the Council.", "Search the workshop", "Trace the needle's mana-trail", "The trail is a faint, glowing silver line that leads into the workshop's 'Attic-of-Rags'. The smell is of old silk and cedarwood."),
    ("The attic is filled with 'Memory-Cloth'—fabric that projects the history of the person who wore it.", "Touch the cloth", "Crawl through the piles (Dex DC 12)", "You see a vision of the 'City-in-Gold' before the fall. The Needle is 'Suturing' a tear in reality in the corner."),
    ("A 'Cloth-Mite'—a creature of thread and silver bells—is trying to steal the Needle to build its own 'Story-Nest'.", "Snatch the needle", "Lure the mite with a silk-scrap", "The mite chitters and drops the needle into a 'Pocket-Dimension' between two layers of velvet."),
    ("The attic floor is becoming 'Unwoven'. You're walking on a grid of 'Logic-Threads' that represent the building's structure.", "Navigate the threads (Dex DC 13)", "Anchor the floor with 'Forge-Nails'", "Every step you take 'Raves' the reality of the room, making the walls look like sketch-lines for a second."),
    ("The Tailor's 'Story-Ghost'—a reflection of her youngest self—appears, holding a 'Thimble of Silence'.", "Speak to the Ghost", "Take the Thimble", "The Ghost points to the 'Master-Thread'—a golden strand that holds the whole building together."),
    ("The Golden-Needle is 'Bleeding' mana. It’s not just a tool; it’s an 'Anchor-Point' for the local ward's stability.", "Retrieve the Needle (Risk DC 15)", "Seal the rift with the Thimble", "You catch the needle, feeling a surge of 'Creative-Energy' that makes your eyes glow with a silver light."),
    ("The Tailor enters the attic, her face a mask of awe. She gives you a 'Weaver's Scarf' (+1 Charisma). 'The world is a tapestry, and you just fixed a snag,' she says.", "Accept the scarf", "Ask for a new cape", "The scarf is made of silver-silk and flows like water. It smells of mountain air and fresh snow."),
    ("The Workshop is quiet, the fabric once again just fabric. The 'Golden-Needle' is back in its velvet box.", "Log the experience", "Accept the gold", "The sun sets, its light hits the silver-silk of the scarf in a corona of white light."),
    ("As you leave, you feel like you can 'See the Stitches' in the world. You notice a loose thread on a guard's uniform and fix it.", "Walk the Ridge", "Visit the Tavern", "You gain a permanent +2 to 'Insight' (Quest-Bonus). The world feels more 'Cohesive'."),
    ("Quest ends in the Workshop. The 'Weaver's Needle' is a tool of order once more.", "Rest", "End", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_025", "The Weaver's Needle", "A tailor's lost tool is causing reality to unweave in the Ridge...", q25_turns, {"loot": ["Weaver's Scarf", "25 Gold"], "xp": 200}, "The attic is completely unraveled and you fall into the Void. (Quest Failed)"))

# EH_SQ_026: The Oozing Barrel
q26_turns = [
    ("The tavern cellar is flooded with a purple, carbonated liquid that smells of 'Void-Berries' and hot brass. One barrel is 'Gurgling' a rhythmic code.", "Listen to the gurgle", "Sample the 'Wine'", "The liquid tastes like a summer storm and static. It’s highly addictive but turns your tongue a permanent neon-purple (+1 Lore)."),
    ("A 'Barrel-Beast'—a construct of wood-staves and iron-hoops—is 'Protecting' the oozing wine with a roar of escaping gas.", "Battle the Beast", "Douse the fire with the purple wine", "The wine is actually 'Fire-Retardant' mana. It extinguishes the beast’s 'Internal-Pilot-Light'."),
    ("The floor of the cellar is dissolving into 'Purple-Mud'. You find a 'Void-Flask' at the bottom of the vat.", "Retrieve the flask", "Drain the mud", "The flask contains the 'Essence of a Lost-Summer'—a liquid that can heal any mental scar."),
    ("The Tavern-Master reveals he found the barrel in the 'Warp-Docks'. He’s been selling it as 'Special-Reserve'.", "Question his ethics", "Help him seal the vat", "The air is sweet and dizzying. You feel a sense of 'Artificial-Joy' that hides a deep, cold fear."),
    ("A 'Wine-Wraith'—a spirit of a drunkard made of purple steam—appears, singing a 'Drinking-Song of the Void'.", "Sing along (Char DC 13)", "Banish the spirit with salt", "The song reveals the coordinates to a 'Hidden-Vineyard' in the Scourge-Fringes. (+1 Intel)"),
    ("The 'Barrel-Beast' reforms, but its eyes are now soft blue. It’s 'Tame'. It offers you its 'Master-Hoop' as a shield.", "Accept the hoop", "Smash the construct", "The hoop is made of 'Void-Iron' and reflects all magical attacks."),
    ("The Tavern-Master gives you a 'Purple-Stain'—a permanent mark on your hand that allows you to detect 'Tainted-Liquids'.", "Accept the mark", "Ask for gold", "The mark glows when near poison. It’s a 'Utility-Skill'."),
    ("The Cellar is clean, the purple wine now bottled as 'High-Ward-Extract'. The smell of ozone remains, however.", "Walk the tavern", "Accept the gold", "The sun sets, the horizon matching the color of the wine you just cleared."),
    ("As you leave, you feel 'Light-Headed' but strong. The world looks a little more colorful tonight.", "Visit the Ridge", "Rest", "The Tavern-Master promises you free drinks for a month. (+5 Morale)"),
    ("Quest ends in the Tavern. The 'Oozing Barrel' is a new specialty tonight.", "Rest", "Final", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_026", "The Oozing Barrel", "A barrel of 'Void-Wine' is leaking a dangerous joy into the tavern cellar...", q26_turns, {"loot": ["Master-Hoop Shield", "Void-Berry Flask"], "xp": 170}, "You are dissolved into a puddle of purple wine. (Quest Failed)"))

# EH_SQ_027: The Static Blanket
q27_turns = [
    ("The laundry ward is experiencing a 'Static-Storm'. The blankets are floating and snapping with blue arcs of lightning.", "Catch a floating towel", "Sense the energy", "The air smells of ozone and fresh linen. It feels like every hair on your body is being pulled by invisible fingers."),
    ("A 'Static-Weaver'—a tiny spider made of blue silk and sparks—is 'Knitting' the laundry into a giant, electric web.", "Wipe out the web", "Befriend the spider with mana", "The spider gives you a 'Blue-Silk-Scrap'—it can hold a charge of 50 volts."),
    ("The 'Laundry-Master' is trapped under a 'Heated-Quilt' that is trying to 'Cook' him with mana-heat.", "Douse the quilt with water", "Reverse the quilt's polarity (Tech DC 13)", "The quilt becomes a 'Cooling-Cape'. The air in the ward drops twenty degrees in a second."),
    ("You find a 'Logic-Fault' in the laundry's 'Steam-Press'—it’s been feeding on 'Warp-Static' from the atmosphere.", "Fix the Press (Tech DC 14)", "Dismantle the Press", "The machine chitters and reveals it was 'Upgraded' by an unknown agent. (+1 Secret)"),
    ("A 'Static-Wraith'—a creature of blue sparks and white fabric—lunges from the dryer, its touch a painful electric shock.", "Slash the fabric", "Ground the wraith with a copper-wire", "The wraith dissolves into a pile of 'Clean-Linen'. The air feels remarkably fresh and clear. (+100 XP)"),
    ("The Laundry-Master gives you a 'Safety-Pin of Grounding'—it makes you immune to basic electric shocks.", "Accept the pin", "Take the Blue-Silk", "The pin is made of brass and glows when near high-voltage."),
    ("The Static-Storm is over. The blankets are back on the racks, their scent a peaceful mix of pine and ozone.", "Check the dryer-vents", "Accept the gold", "The sun rises over the ward, drying the last of the damp cloth in a golden, safe warmth."),
    ("As you leave, you feel 'Charged' with energy. You can light a small candle with just a touch of your finger.", "Light a candle", "Log the anomaly", "The sensation is temporary, but it grants you a +1 to 'Tech-Save' for 24 hours."),
    ("The Laundry-Master promises to 'Ground' all future loads. He offers you a 'Master's Apron' (+1 Defense).", "Accept the apron", "Decline reward", "The Ridge-air feels cool and steady. No hair-raising feelings tonight."),
    ("Quest ends in the Laundry. The 'Static Blanket' is a warm cover tonight.", "Rest", "Done", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_027", "The Static Blanket", "A static-electric storm is wreaking havoc in the laundry ward...", q27_turns, {"loot": ["Safety-Pin of Grounding", "Master's Apron"], "xp": 160}, "You are flash-fried by a giant electric towel. (Quest Failed)"))

# EH_SQ_028: The Whispering Page
q28_turns = [
    ("The settlement library is haunted by a 'Whispering-Page'—a sheet of paper that reads itself out loud in a voice of paper-cuts.", "Listen to the book", "Close the book", "The book is a 'History of the Scourge' that is 'Correcting' itself in real-time. The smell is of old parchment and ink."),
    ("The ink is 'Living-Script'—it’s crawling off the page and trying to write a 'New-Story' on your own skin.", "Wipe the ink away", "Allow the script to finish (Wis DC 14)", "The script reveals a 'Secret-Passage' behind the 'Law-Section'."),
    ("A 'Book-Wyrm'—a creature of paper-scales and leather-wings—is eating the 'Forgotten-Lore' in the restricted section.", "Slash the Wyrm", "Feed the Wyrm a 'Blank-Book'", "The Wyrm burps a 'Cinder-Shard' and vanishes into the vents. You find a 'Lost-Page' on the floor."),
    ("The 'Librarian'—a woman in glasses made of 'Void-Glass'—is frantic. 'The books... they’re rewriting the laws of gravity!' she cries.", "Anchor the bookshelves", "Consult the 'Master-Tome'", "The books begin to float, forming a 'Spiral-Staircase' of knowledge into the ceiling-void."),
    ("A 'Script-Geist'—a spirit made of floating letters—appears, trying to 'Edit' you out of reality using a 'Eraser-Staff'.", "Parry the staff", "Negotiate with the Geist (Int DC 15)", "The Geist reveals he’s the 'Spirit of Truth' who has been 'Censored' by the Council. (+1 Secret)"),
    ("You must decide: 'Submit' to the edit or 'Rewrite' the spirit. The air is thick with the smell of wet ink and old dust.", "Rewrite the spirit (Int DC 14)", "Burn the 'Censored' pages", "The Geist dissolves into a cloud of 'Ink-Dust'. The library returns to a state of 'Stable-Gravity'."),
    ("The Librarian gives you a 'Bookmark of Holding'—it can save your place in any dimension.", "Accept the bookmark", "Take the Lost-Page", "The bookmark is made of red silk and never frays. It’s a 'Logic-Anchor'."),
    ("The 'Whispering Page' is quiet, but it’s now a 'Talking-Book'. It offers you advice on 'Forbidden-Lore' (+2 Intel).", "Take the book home", "Accept the gold", "The sun sets, its light coloring the library's dust in shades of sepia and gold."),
    ("As you leave, you feel like you've 'Read the Future'. You know a secret about a Council member’s past.", "Log the secret", "Forget it", "The knowledge is heavy, but it grants you a +1 to 'Politics' permanently."),
    ("Quest ends in the Library. The 'Whispering Page' is a story of hope tonight.", "Rest", "Final", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_028", "The Whispering Page", "A book in the library is actively rewriting itself and the person reading it...", q28_turns, {"loot": ["Bookmark of Holding", "Lost-Page"], "xp": 230}, "You are deleted from the story and your name is forgotten. (Quest Failed)"))

# EH_SQ_029: The Shadow-Rat's Nest
q29_turns = [
    ("The scrap-yard is infested with 'Shadow-Rats'—vermin that can walk through walls and eat your 'Potential'.", "Set a shadow-trap", "Bait them with 'Warp-Scraps'", "The rats are translucent and smell of wet fur and ozone. They chitter in a frequency that makes you feel 'Unlucky'."),
    ("A 'Rat-King'—a mass of multiple rats fused together by their 'Shadow-Tails'—emerges from a pile of old copper-pipes.", "Slash the King", "Lure the King into a 'Light-Box'", "The King roars in a voice like a hundred tiny voices screaming at once. It lunges for your 'Light-Supply'."),
    ("The scrapyard floor is riddled with 'Shadow-Holes'—small rifts that swallow your gear if you're not careful.", "Level the ground (Str DC 12)", "Navigate the piles (Dex DC 13)", "You find a 'Lost-Pocket-Watch' in a hole. It’s still ticking, but backward."),
    ("The 'Scrap-Master' is hiding in a lead-lined shed. He’s been 'Feeding' the rats to keep them away from the ward-wall.", "Question the Master", "Scout the nest-core", "He reveals the rats are 'Sentinals' sent by the Scourge to scout the city's weak points. (+1 Intel)"),
    ("The Nest-Core is a 'Void-Beacon'—a pulsing, purple light that is calling more rats from the wastes.", "Smash the Beacon (Atk DC 14)", "Disable the Beacon's power", "The Beacon shatters, releasing a 'Wave of Shadow' that turns the scrapyard into a 'Pitch-Black-Void'."),
    ("In the dark, you can only see the 'Glow' of the rats' eyes. You must find your own 'Internal-Light'.", "Focus your Mana (Wis DC 14)", "Use a 'Sun-Bead'", "The darkness recedes, revealing the Rat-King is now just a single, shivering 'Normal-Rat'."),
    ("The Scrap-Master gives you a 'Rat-Mask' (+1 Stealth). 'The Ridge-rats are your eyes now,' he whispers.", "Accept the mask", "Take the gold", "The mask is made of gray fur and cold iron. It smells of earth and old metal."),
    ("The 'Shadow-Rat's Nest' is cleared. The scrapyard is quiet, save for the sound of the wind in the iron.", "Build a better wall", "Check the lead-shed", "The sun rises, its light making the iron look like sleeping giants of rust and copper."),
    ("As you leave, a small rat follows you. It seems to be 'Tame'. It can find 'Hidden-Items' for you.", "Adopt the rat", "Log the pest-control", "The rat chitters happily and sits on your shoulder. It’s a '+1 Loot-Detection' item."),
    ("Quest ends in the Scrapyard. The 'Shadow-Rat' is a scavanger friend tonight.", "Rest", "Done", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_029", "The Shadow-Rat's Nest", "A nest of shadow-vermin is drinking the luck of the Low-Ward...", q29_turns, {"loot": ["Rat-Mask", "Backward-Clock"], "xp": 150}, "Your luck is drained to zero and you fall into a scrap-heap forever. (Quest Failed)"))

# EH_SQ_030: The Echoing Well
q30_turns = [
    ("The town well is 'Echoing' with voices of people who are still alive. They’re talking about their 'Future-Dreams'.", "Listen to the well", "Drop a coin in", "The well doesn't reflect your face; it reflects a 'Golden-City' that might be. The smell is of mountain-water and old stone."),
    ("A 'Water-Wraith'—a spirit of liquid silver—emerges from the bucket, holding a 'Scroll of the Future'.", "Take the scroll", "Ask the spirit its name", "The spirit is a 'Reflection-of-Hope' that has been 'Tainted' by the Scourge's despair."),
    ("The well-water is turning into 'Liquid-Lead'. It’s becoming too heavy to drink and is 'Crushing' the local pipes.", "Purify the well with 'Materia-Salt'", "Reverse the well's flow (Tech DC 13)", "The water boils and then turns into 'Crystal-Flow'—an eternal, cold supply of pure mana-water."),
    ("The 'Wellminder'—an old man in a blue robe—reveals the well is a 'Fountain of Probability'.", "Learn the 'Probability-Law' (Int DC 14)", "Question the well's origin", "Every coin tossed in changes the destiny of a single citizen. Choose your toss wisely."),
    ("A 'Gloom-Fish'—a creature of shadow-fins and jagged teeth—lunges from the water, seeking to eat the 'Coins of Destiny'.", "Strike the fish", "Distract it with 'False-Gold'", "The fish explodes into a thousand 'Silver-Bubbles'. Each bubble contains a happy memory of the town. (+100 XP)"),
    ("The Wellminder gives you a 'Well-Bucket of Holding'—it can carry ten tons of water without weighing a pound.", "Accept the bucket", "Take the Future-Scroll", "The bucket is made of oak and bound in 'Mana-Silver'. It’s a 'Legendary-Tool' for settlers."),
    ("The 'Echoing Well' is quiet now, the voices gone. It reflects the sun in a single, brilliant blue eye.", "Log the prophecy", "Accept the gold", "The townspeople gather to drink the new 'Crystal-Flow'. Their 'Morale' rises to a high point (+20 Morale)."),
    ("As you leave, you feel like 'Everything is Possible'. You see a vision of a 'Prosperous-Ridge' in the clouds.", "Point out the vision", "Keep it to yourself", "The vision is a 'Beacon' for the weary. You gain a permanent +2 to 'Charisma'."),
    ("The Wellminder promises to 'Guard the Dreams' of the town. He offers you a 'Well-Token' which entitles you to one 'Re-roll' per week.", "Accept the token", "Decline reward", "The sun sets, its light hits the well-water in a corona of liquid diamonds."),
    ("Quest ends at the Well. The 'Echoing Well' is a source of hope tonight.", "Rest", "Final", "Quest Complete.")
]
quests.append(create_quest("EH_SQ_030", "The Echoing Well", "The town well is talking, and the water is becoming too heavy to lift...", q30_turns, {"loot": ["Well-Bucket of Holding", "Well-Token"], "xp": 250}, "The well swallows you and you become an echoing voice of despair. (Quest Failed)"))

with open('new_easy_quests_utf8.json', 'w', encoding='utf-8') as f:
    json.dump(quests, f, indent=2, ensure_ascii=False)
