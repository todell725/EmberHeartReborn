# EmberHeart Reborn Roadmap v2 (Execution-Ready, Gated)

## Brief Summary
1. Stabilize and harden runtime behavior without changing player-facing command semantics.
2. Keep JSON as canonical state, add in-memory SQLite as a read cache, and serialize all writes through a coordinator.
3. Reduce AI failure and latency risk using bounded memory, lexical retrieval, and validate-repair-fallback JSON handling.
4. Keep dual-bot unification as an optional final gate based on measured prose quality and schema reliability.

## Locked Architecture Decisions
1. Canonical state remains JSON files.
2. SQLite is in-memory read model only and is rebuilt at startup.
3. Concurrency uses per-channel narrative queues and one global mutation queue.
4. Retrieval uses pure-Python lexical ranking (BM25-style), not vector DB.
5. `parse_speaker_blocks()` remains as fallback until unification gate passes.

## Important Public APIs / Interfaces / Types
1. Add env knobs in `.env.example`: `EH_QUEUE_MAX_PER_CHANNEL`, `EH_QUEUE_STALE_SECONDS`, `EH_HISTORY_RAW_KEEP`, `EH_HISTORY_COMPACT_TRIGGER`, `EH_HISTORY_SUMMARIZE_BATCH`, `EH_RAG_TOP_K`, `EH_RAG_MAX_CHARS`.
2. Add typed models in [core/models.py](/z:/DnD/EmberHeartReborn/core/models.py): `CharacterProfile`, `CharacterState`, `QuestRecord`, `ConversationTurn`, `ConversationThread`, `NarrativeEvent`, `StateMutation`.
3. Add storage interfaces in [core/state_store.py](/z:/DnD/EmberHeartReborn/core/state_store.py): `JsonCanonicalStore`, `SQLiteReadModel`, `StateCoordinator`.
4. Add queue APIs in [core/engine_queue.py](/z:/DnD/EmberHeartReborn/core/engine_queue.py): `enqueue_narrative`, `enqueue_mutation`, `start_workers`, `stop_workers`.
5. Migrate [state/CONVERSATIONS.json](/z:/DnD/EmberHeartReborn/state/CONVERSATIONS.json) to `{system, summary, turns}` thread format with backward-compatible read logic in [core/ai/client.py](/z:/DnD/EmberHeartReborn/core/ai/client.py).

## Phase Plan With Gates

### Phase 0: Security + Hygiene (1-2 days)
1. Rotate all active tokens and invalidate previous values.
2. Add secret scan tooling in [scripts/security](/z:/DnD/EmberHeartReborn/scripts/security) and ops docs in [docs/OPERATIONS.md](/z:/DnD/EmberHeartReborn/docs/OPERATIONS.md).
3. Remove runtime `sys.path.insert(...)` from [cogs/brain.py](/z:/DnD/EmberHeartReborn/cogs/brain.py) and [cogs/brain_party.py](/z:/DnD/EmberHeartReborn/cogs/brain_party.py); normalize imports to `core.*`.
4. Fix mojibake in user-facing logs/messages in [discord_party.py](/z:/DnD/EmberHeartReborn/discord_party.py), [core/storage.py](/z:/DnD/EmberHeartReborn/core/storage.py), and related cogs.
5. Exit gate: no tracked `.env`; no high-risk findings in scans; bot startup/smoke tests still pass.

### Phase 1: Typed State + Coordinator (3-4 days)
1. Introduce Pydantic domain models in [core/models.py](/z:/DnD/EmberHeartReborn/core/models.py).
2. Introduce `StateCoordinator` in [core/state_store.py](/z:/DnD/EmberHeartReborn/core/state_store.py) and route canonical writes through it.
3. Migrate write callsites in [engines/quest_engine.py](/z:/DnD/EmberHeartReborn/engines/quest_engine.py), [engines/shop_engine.py](/z:/DnD/EmberHeartReborn/engines/shop_engine.py), [engines/forge_engine.py](/z:/DnD/EmberHeartReborn/engines/forge_engine.py), [engines/tick_engine.py](/z:/DnD/EmberHeartReborn/engines/tick_engine.py), [engines/combat_engine.py](/z:/DnD/EmberHeartReborn/engines/combat_engine.py), [core/relationships.py](/z:/DnD/EmberHeartReborn/core/relationships.py), [cogs/world.py](/z:/DnD/EmberHeartReborn/cogs/world.py), and [cogs/rules.py](/z:/DnD/EmberHeartReborn/cogs/rules.py).
4. Build startup JSON-to-SQLite read-model bootstrap for high-frequency reads.
5. Exit gate: no direct uncoordinated writes remain; malformed payloads fail fast with clear validation errors; quest lookup median latency improves by at least 50%.

### Phase 2: Queueing + Concurrency Control (4-6 days)
1. Add per-channel narrative workers for strict in-channel ordering.
2. Add one global mutation worker for all state-changing operations.
3. Update [cogs/brain.py](/z:/DnD/EmberHeartReborn/cogs/brain.py) and [cogs/brain_party.py](/z:/DnD/EmberHeartReborn/cogs/brain_party.py) to enqueue tasks and immediately acknowledge via typing state; send explicit queue notice only when backlog is high.
4. Enforce queue limits and stale-drop behavior using env defaults.
5. Standardize degraded timeout/error responses across both bots.
6. Exit gate: zero corruption under 1,000 concurrent synthetic events; per-channel order preserved; p95 ack start < 1s.

### Phase 3: Memory, Retrieval, and Validation Loop (3-4 days)
1. Implement conversation compaction in [core/ai/client.py](/z:/DnD/EmberHeartReborn/core/ai/client.py): keep 15 raw turns, compact when hitting 20 by summarizing oldest 5.
2. Replace filename-match retrieval in [core/ai/rag.py](/z:/DnD/EmberHeartReborn/core/ai/rag.py) with chunk-level lexical retrieval and strict context-size cap.
3. Add unified JSON loop in [core/ai/client.py](/z:/DnD/EmberHeartReborn/core/ai/client.py): validate -> one repair attempt -> graceful fallback.
4. Keep fallback parsing path in [core/formatting.py](/z:/DnD/EmberHeartReborn/core/formatting.py) active until Phase 4 decision.
5. Exit gate: bounded conversation growth; deterministic retrieval cap; invalid JSON auto-recovers in one retry for at least 95% fixtures.

### Phase 4: Optional Unification Gate (2-3 days)
1. Build offline evaluator in [scripts/eval/schema_prose_eval.py](/z:/DnD/EmberHeartReborn/scripts/eval/schema_prose_eval.py).
2. Compare dual-bot vs strict schema output on validity and prose quality.
3. Unification threshold: JSON validity >= 98% and prose quality >= 4.0/5 on benchmark set.
4. If pass, merge [discord_main.py](/z:/DnD/EmberHeartReborn/discord_main.py) and [discord_party.py](/z:/DnD/EmberHeartReborn/discord_party.py), then retire regex-heavy critical path.
5. If fail, keep dual-bot architecture and backlog targeted improvements.

## Test Cases And Scenarios
1. Security regression scan: tracked files + git history.
2. Type validation tests for malformed quest/character/inventory payloads.
3. Mutation stress tests across quest/shop/forge/tick/relationships writes.
4. Queue order tests with interleaved multi-channel message streams.
5. Backpressure tests for queue overflow and stale event handling.
6. Conversation migration tests from legacy list format to new thread object.
7. Retrieval precision tests with stopwords and lore-targeted prompts.
8. JSON validation-loop tests with intentionally broken model outputs.
9. Avatar durability tests ensuring no expiring Discord attachment URLs in profiles.
10. End-to-end gameplay smoke tests for command/routing regressions.

## Assumptions And Defaults
1. Player-facing command names and channel behavior remain unchanged through Phases 0-3.
2. JSON stays canonical for this roadmap.
3. SQLite remains in-memory only for this version.
4. No heavy vector/ML dependencies are introduced.
5. Secret exposure is treated as possible; token rotation is mandatory.
6. Existing fallback parser is intentionally retained until schema-prose quality proves safe.
