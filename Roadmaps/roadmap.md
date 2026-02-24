# EmberHeart Reborn: Modernization Roadmap

A synthesized architectural gameplan derived from three distinct AI reviews (Ultrathink, Codex, and Gemini 3.1). This roadmap prioritizes **reliability at scale** while explicitly maintaining your **local-first, narrative-driven** design philosophy.

---

## The Consensus Breakdown
The four models had different focus areas but overwhelmingly agreed on the structural bottlenecks:
* **The Friend (Data):** Emphasized solving file I/O bottlenecks with SQLite, bloat with Vector Search, and fragility with Pydantic type hinting.
* **Codex (Operations):** Flagged critical security flaws, import hygiene, and the need for an async event queue to prevent Discord race conditions.
* **Gemini (Unification):** Advocated for an Event-Driven Architecture to decouple Discord from AI math, and strict Pydantic JSON schemas to unify the dual-bot setup.
* **Claude 4.6 (Performance & Longevity):** Identified silent latency killers (sync I/O in async loops), long-term state explosions (infinite conversation history), and ephemeral asset bugs (Discord CDN expiry).

---

## Phase 1: Security, Hygiene, and Stability (Immediate Action)
These are non-negotiable fixes before the repository is made public or the campaign scales further.

- [ ] **The GitHub Safety Wipe (Codex):** Sanitize the live [.env](file:///z:/DnD/EmberHeartReborn/.env) file, replace it with [.env.example](file:///c:/Users/todd/agent-bookish-train/.env.example), and add [.env](file:///z:/DnD/EmberHeartReborn/.env) to [.gitignore](file:///z:/DnD/EmberHeartReborn/.gitignore) to prevent scraping of Google, OpenAI, and GitHub tokens.
- [ ] **Discord Avatar CDN Expiry (Claude 4.6):** Move character avatars off Discord CDN attachments. These URLs expire after 24-48 hours. Host them permanently (e.g., GitHub raw URLs) so character webhooks don't return broken images.
- [ ] **Import Hygiene (Codex):** Remove `sys.path.insert(0, ...)` hacks in [brain_party.py](file:///z:/DnD/EmberHeartReborn/cogs/brain_party.py) and enforce standard relative/absolute imports to prevent refactor breakage.
- [ ] **Type-Hinted Internal Data (Friend):** Implement Pydantic `BaseModel` classes for internal game structures (e.g., [Quest](file:///z:/DnD/EmberHeartReborn/cogs/quests.py#8-65), [Character](file:///z:/DnD/EmberHeartReborn/cogs/characters.py#9-417), `Weapon`). This catches dictionary key errors (like the [inventory](file:///z:/DnD/EmberHeartReborn/cogs/economy.py#21-48) bug) instantly during engine boot rather than mid-combat.

---

## Phase 2: State Management & Concurrency (The Architecture Shift)
These steps solve the two biggest structural vulnerabilities: synchronous file locking and Discord event loop blocking.

- [ ] **The "aiofiles" / Cache Fix (Claude 4.6):** 
  - *Problem:* `json.load()` calls reading 2.2MB files ([SIDE_QUESTS_DB.json](file:///z:/DnD/EmberHeartReborn/docs/SIDE_QUESTS_DB.json)) synchronously will freeze the Discord event loop during gameplay.
  - *Solution:* Cache the massive quest DB in memory at startup. For other I/O, switch to `aiofiles` or strictly use the asynchronous thread delegation you built.
- [ ] **The In-Memory SQLite Cache (Synthesis):** 
  - *Problem:* Iterating across 61 JSON files to calculate world state is slow and locks files.
  - *Solution:* Keep JSON as the "Source of Truth" on disk for human readability. At startup, load all state into a fast `sqlite3` memory database. Route all engine queries (`SELECT * FROM characters`) through RAM, and fire asynchronous writes back to the JSON files when stats change.
- [ ] **The Async Event Queue (Codex & Gemini):** 
  - *Problem:* Discord events run in parallel. Calling `!shop` and whispering an NPC simultaneously can overwrite the same file, and waiting 15 seconds for Ollama hangs the bot.
  - *Solution:* Implement a strict Producer/Consumer pattern for the main narrative channel. Discord pushes messages to an `asyncio.Queue` and immediately replies "acknowledged." A background Engine Worker pulls one message at a time, calculates the math, hits the AI, and renders the webhook. This makes the bot completely race-condition-proof.
- [ ] **Sliding Window Conversation Pruning (Claude 4.6):** 
  - *Problem:* [CONVERSATIONS.json](file:///z:/DnD/EmberHeartReborn/state/CONVERSATIONS.json) grows infinitely. Eventually, it will crash the context window or run out of RAM.
  - *Solution:* Keep the last 15 raw exchanges per channel. When it hits 20, summarize the oldest 5 into a dense "narrative memory" block and append it to the system prompt, rolling the window forward.

---

## Phase 3: The AI & Context Refactor (The RAG / Validation Shift)
As the "Eleventh Age" produces massive amounts of lore, the system prompt must be optimized.

- [ ] **Lightweight Semantic RAG (Ultrathink):** 
  - *Problem:* Appending monolithic campaign journals into the prompt destroys token processing speeds.
  - *Solution:* Do *not* implement ChromaDB, as it introduces gigabytes of PyTorch bloat. Instead, use a pure Python BM25 semantic search index. Retrieve only the 3 specific paragraphs of lore relevant to the user's current query.
- [ ] **The Validation Loop (Codex):** 
  - *Standardize the wrapper:* `Validate → Repair Attempt → Degrade Gracefully`. If Ollama hallucinated its JSON structure, Pydantic catches it, feeds the error back to Ollama automatically ("You missed a comma"), and if it fails again, falls back to a canned response.

---

## Phase 4: The Final Unification (Optional)
The ultimate goal proposed by Gemini is to merge [discord_main.py](file:///z:/DnD/EmberHeartReborn/discord_main.py) and [discord_party.py](file:///z:/DnD/EmberHeartReborn/discord_party.py) by forcing all AI output into structured JSON.

- [ ] **The "Schema Prose" Test (Synthesis):**
  - *The Danger:* Forcing RP models (like `mythomax_13b`) to strictly output `{"narration": "..."}` often causes a "JSON Lobotomy" where the prose becomes robotic. 
  - *The Action:* Write an offline script forcing the base model (`gemma3:12b`) to narrate a tavern brawl inside a Pydantic schema. 
- [ ] **Execute Unification:**
  - *If the prose is excellent:* Delete the brittle [parse_speaker_blocks()](file:///z:/DnD/EmberHeartReborn/core/formatting.py#112-224) regex pipeline, adopt strict Pydantic outputs, and unify the dual-bot split into a single application.
  - *If the prose degrades:* Keep the current [parse_speaker_blocks()](file:///z:/DnD/EmberHeartReborn/core/formatting.py#112-224) heuristic parser to allow the LLM to output freeform Markdown, preserving the immersion of the campaign.
