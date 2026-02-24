Claude’s Plan
EmberHeartReborn Roadmap Review + My Roadmap
Review of Existing Roadmap
The existing roadmap (roadmap.md + Codex Plan.md) is architecturally sound. The consensus approach — JSON canonical state, SQLite read cache, async event queue, BM25 RAG, and a gated unification decision — is the right call. It avoids over-engineering while solving real bottlenecks.

What's Strong
Security-first ordering is correct
The queue/producer-consumer pattern is the right fix for Discord race conditions
BM25 over ChromaDB is pragmatic and appropriate for this scale
Phase gates with measurable exit criteria is mature planning
The Schema Prose test before unification is smart — avoids "JSON lobotomy"
Conversation sliding window (keep 15, compact at 20) is well-calibrated
Gaps and Issues
1. Numbering Inconsistency
roadmap.md uses Phase 1-4; Codex Plan.md uses Phase 0-4 (Security is "Phase 0"). Small but will cause confusion during execution — pick one convention and stick to it.

2. Secrets Are a NOW Issue, Not a Phase 0 Issue
Both documents treat the exposed .env as a Phase 0 task. This is wrong. Live Google, OpenAI, GitHub Copilot, and Discord tokens are in the tracked .env right now. Those tokens should be rotated immediately — before planning, before coding, before anything else. If they were ever pushed to a remote, assume they've been scraped.

3. Avatar Hosting Has No Destination
The Discord CDN expiry bug is identified correctly, but neither document says where to host 62 NPC avatars. GitHub raw URLs work but have content size limits and break on repo renames. This needs a concrete hosting decision before Phase 0 closes.

4. No Atomic Write / Backup Strategy
The roadmap introduces a StateCoordinator to serialize writes, but doesn't address what happens if the bot crashes mid-write. The campaign state (NPC relationships, quest completions, party gold) is irreplaceable. A JSON file half-written by a crashed process will silently corrupt a campaign session. Solution: atomic writes (write to .tmp, rename on success) + periodic timestamped backups before any mutation batch.

5. The Global Mutation Worker is a Bottleneck
The Codex Plan specifies "one global mutation worker for all state-changing operations." This means a 15-second Ollama call for !combat blocks !forge and !shop behind it. For a multi-player session this is noticeable. Per-engine mutation queues (or at minimum separating AI-dependent vs. pure-math writes) would be more practical.

6. No Mocking Strategy for AI Tests
Test cases mention JSON validation loop tests, but if Ollama is down or slow, the test suite becomes non-deterministic. The plan needs a fixture/mock layer for Ollama responses so tests pass in CI without a live model.

7. Graceful Shutdown Not Mentioned
When the bot is stopped (SIGTERM, Ctrl+C), in-flight queue tasks should drain before exit. Otherwise a mid-session shutdown corrupts state. This belongs in Phase 2 alongside the queue implementation.

8. No Observability Plan
When Ollama returns 503 at 2am during a live session, there's no mention of structured logging, alerting, or health checks. A simple log-to-file with log rotation and a /ping Discord admin command would catch failures before players notice.

My Roadmap
Structurally identical to the existing plan but with the above gaps filled in.

Phase 0 (RIGHT NOW, Before Any Code): Token Rotation
Do this before touching code.

Rotate Discord bot token (main + party bot)
Rotate OpenAI API key
Rotate Google Gemini API key
Revoke GitHub Copilot token
Create .env.example with placeholder values
Add .env to .gitignore and verify it's untracked
If repo has ever been pushed to remote: git history scrub (BFG or git-filter-repo)
Exit gate: git status shows .env untracked; token rotation confirmed in each provider's dashboard.

Phase 1: Security Hygiene + Quick Wins (Before Architecture Changes)
Avatar hosting decision — Pick a permanent host for 62 NPC avatars (self-hosted, R2, or a dedicated GitHub repo for assets). Update all profile.json avatar URLs. Add an audit script that fails startup if any avatar URL is a Discord CDN attachment.
Import hygiene — Remove sys.path.insert(0, ...) from brain.py and brain_party.py; normalize to core.* imports.
Atomic writes — Wrap all json.dump() calls in storage.py to write to .tmp then os.replace(). Add pre-write backup copy to state/backups/ with timestamp and retain last 5.
Structured logging — Add a single core/logger.py module using Python's standard logging with rotating file handler. Replace ad-hoc print() calls with log.info/warning/error. This costs almost nothing and is invaluable later.
Exit gate: No tracked .env; no Discord CDN avatar URLs; no sys.path hacks; all writes are atomic; structured log output visible on bot startup.

Phase 2: Typed State + Coordinator
Pydantic models in core/models.py — CharacterProfile, CharacterState, QuestRecord, ConversationTurn, ConversationThread, NarrativeEvent, StateMutation
StateCoordinator in core/state_store.py — Route all canonical writes through it; rebuild SQLite in-memory read model on startup
Migrate write callsites — quest_engine, shop_engine, forge_engine, tick_engine, combat_engine, relationships.py, world.py, rules.py
AI test mocking — Add tests/fixtures/ollama_responses/ directory with JSON fixtures; wrap AI calls behind an interface that can be swapped for a fixture loader in tests
Exit gate: No direct uncoordinated file writes remain; malformed payloads fail fast at validation; quest lookup latency improves; test suite passes without a live Ollama instance.

Phase 3: Concurrency + Queue (Revised from Codex)
Per-channel narrative queues (same as Codex) — strict in-channel ordering
Per-engine mutation queues (revised from global) — Separate queues for AI-dependent operations (brain, brain_party) vs. pure-math operations (forge, shop, economy). This prevents a 15s Ollama call from blocking item crafting.
Graceful shutdown — Register SIGTERM/SIGINT handlers that stop accepting new tasks, drain the queue, and flush state before exit
Queue limits + stale-drop via env vars (EH_QUEUE_MAX_PER_CHANNEL, EH_QUEUE_STALE_SECONDS)
Admin health command — /eh-health Discord command (owner-only) that reports queue depths, last Ollama ping, and bot uptime
Exit gate: Zero corruption under synthetic concurrent events; per-channel order preserved; graceful shutdown confirmed; p95 acknowledge < 1s.

Phase 4: Memory, Retrieval, and Validation Loop
(Same as Codex Plan — it's good.)

Conversation compaction — Keep 15 raw turns, compact at 20 by summarizing oldest 5 into a narrative memory block
BM25 RAG — Chunk-level lexical retrieval in core/ai/rag.py; strict context-size cap; no ChromaDB
JSON validate→repair→fallback loop — validate → one Ollama repair attempt → graceful degradation; keep parse_speaker_blocks() as fallback until Phase 5 gate
Exit gate: Bounded conversation growth; deterministic retrieval cap; invalid JSON auto-recovers in one retry ≥95% of fixtures; test suite fully green.

Phase 5: Optional Unification Gate
(Same as Codex Plan.)

Build scripts/eval/schema_prose_eval.py — offline evaluator for schema vs. freeform prose quality
Threshold: JSON validity ≥ 98% AND prose quality ≥ 4.0/5
If pass: Merge discord_main.py + discord_party.py, retire parse_speaker_blocks() regex path
If fail: Keep dual-bot, document the threshold and re-evaluate after model upgrade
Critical Files
File	Phase	Change
.env / .gitignore	Phase 0	Untrack .env; rotate all secrets
characters/*/profile.json	Phase 1	Avatar URL migration
core/storage.py	Phase 1	Atomic writes + backups
core/logger.py	Phase 1	New — structured logging
cogs/brain.py, brain_party.py	Phase 1	Remove sys.path hacks
core/models.py	Phase 2	New — Pydantic models
core/state_store.py	Phase 2	New — StateCoordinator + SQLite read model
engines/*.py	Phase 2	Migrate write callsites
core/engine_queue.py	Phase 3	New — per-channel + per-engine queues
core/ai/client.py	Phase 4	Conversation compaction + JSON validate loop
core/ai/rag.py	Phase 4	BM25 chunk retrieval
discord_main.py + discord_party.py	Phase 5 (conditional)	Merge if prose gate passes
Verification Strategy
Phase 0: git status shows .env untracked; dashboard token invalidation confirmed
Phase 1: Startup audit script catches any Discord CDN URLs; write a file, kill process mid-write, verify no corruption
Phase 2: pytest tests/ passes without live Ollama; malformed JSON payload raises Pydantic error at boot
Phase 3: Synthetic stress test (1,000 concurrent events) shows zero state corruption
Phase 4: Conversation file stays bounded after 25+ exchanges; BFG fixture test ≥95% recovery rate
Phase 5: Prose evaluator script run against gemma3:12b and mythomax benchmarks