This roadmap synthesizes the core directives from roadmap.md, Codex Plan.md, and Claude’s Plan.md. It prioritizes immediate security, moves into structural stability, and concludes with a performance-based "gate" for the final bot unification.
Phase 0: Emergency Security & Asset Hardening
Based on Claude and Codex’s "NOW" priority.
• The Secret Scrub: Immediately rotate all API keys (Google, OpenAI, GitHub). Tracked .env files in git history mean these keys are compromised. Replace with a clean .env.example.
• Avatar Migration: Move NPC avatars out of Discord’s temporary CDN. Re-host them as permanent assets in a /assets folder or via GitHub Raw URLs to prevent broken profile images.
• Import Hygiene: Delete sys.path.insert(0, ...) hacks in brain_party.py. Use standard absolute imports to prevent circular dependency crashes.
Phase 1: The "Local-First" Data Engine
Based on the consensus to keep JSON canonical but improve performance.
• The Read Model (SQLite): Implement an in-memory SQLite database that builds at startup. High-frequency lookups (NPC stats, relationships) query this RAM-cache, while the "Source of Truth" remains your human-readable JSON files.
• Atomic Async Writes: Replace standard json.dump with aiofiles and an "Atomic Write" pattern (write to temp file \rightarrow rename). This prevents a crash from corrupting your entire campaign save file.
• Pydantic Enforcement: Create core/models.py. Every Quest, Character, and Inventory item must pass a Pydantic check before being processed. This catches "invisible" data bugs before they reach the AI.
Phase 2: Concurrency & Narrative Flow
Based on Codex’s Event-Driven architecture and Claude’s latency fixes.
• The Narrative Queue: Implement a Producer/Consumer queue. When a player speaks, the bot acknowledges the event immediately and adds it to a per-channel queue. This stops "Race Conditions" where the AI responds to the same trigger twice.
• Conversation Compaction: Stop CONVERSATIONS.json from growing infinitely. Implement a sliding window: keep the last 15 turns as raw text, and compact anything older into a "Summary Block" to keep LLM context windows lean and fast.
• Async I/O Audit: Audit the brain.py loop. Any synchronous time.sleep() or json.load() calls must be moved to asyncio threads to prevent the entire Discord bot from "freezing" while the AI thinks.
Phase 3: AI Reliability (The Validation Loop)
Based on the "Synthesis" section of roadmap.md.
• BM25 Retrieval (Lite-RAG): Instead of a heavy Vector DB, use a pure-Python lexical search (BM25) to grab the most relevant lore snippets for the current scene.
• The Repair Loop: Standardize AI calls into a three-step process:
1. Generate (LLM)
2. Validate (Pydantic check)
3. Repair/Fallback (If JSON is broken, ask the LLM to fix it once; if it fails again, use a safe narrative fallback).
Phase 4: The Unification Gate
The final decision point for merging discord_main.py and discord_party.py.
• The "Prose vs. Schema" Benchmark: Conduct an offline test. Force your local model (Ollama) to narrate complex scenes strictly inside JSON schemas.
• The Fork in the Road:
• IF PROSE REMAINS HIGH: Merge the bots, adopt strict JSON outputs, and delete the complex parse_speaker_blocks() regex code.
• IF PROSE BECOMES ROBOTIC: Keep the dual-bot split and the heuristic (regex) parser to preserve the "human" feel of the roleplay.
Critical Execution Order
1. Security/Assets (Do this today)
2. Pydantic Models (Define your data)
3. SQLite/Async I/O (Speed up the engine)
4. The Unification Gate (Simplify the code only if it doesn't hurt the story)