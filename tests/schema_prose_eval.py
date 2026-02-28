"""
schema_prose_eval.py â€” Offline evaluator for parser validity and prose quality.

Determines whether the Ollama model output is reliable and rich enough to safely
unify the dual-bot architecture (discord_main.py + discord_party.py) into a single
bot runtime.

USAGE:
    python tests/schema_prose_eval.py
    python tests/schema_prose_eval.py --samples 10 --verbose
    python tests/schema_prose_eval.py --output report.json

PASS CRITERIA (all must be met for SAFE_FOR_UNIFICATION):
    schema_validity    >= 98%   Fraction of prompts producing parseable dialogue blocks
    speaker_diversity  >= 0.70  Avg unique speakers per turn, normalized to expected 2
    meta_leak_rate     == 0%    No system directive text present in any response

EXIT CODE:
    0 â€” SAFE_FOR_UNIFICATION
    1 â€” RETAIN_DUAL_BOT
"""

import argparse
import json
import logging
import sys
import time
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("schema_prose_eval")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Test prompts â€” realistic in-world triggers covering NPC chat, party scenes,
# world state queries, and adversarial edge cases.
# ---------------------------------------------------------------------------
TEST_PROMPTS = [
    # NPC interactions
    "What news from the merchant quarter today?",
    "Marta, has the supply shipment arrived from the eastern roads?",
    "I need to speak with the court advisor about the recent tremors.",
    "What do the scouts report from the northern pass?",
    "Is there any word from Veyra about the expedition?",
    # Party scenes
    "Rally the party â€” we move at dawn.",
    "The healer's guild requests an audience about a spreading sickness.",
    "Someone has been leaving coded messages at the market stalls.",
    "The guards found something unusual in the lower crypts.",
    # World state / rumour prompts
    "How fares the settlement after last night's storm?",
    "What are the latest rumors from the tavern district?",
    "Report on the status of the forge district.",
    "Describe the current state of the kingdom's defenses.",
    # Quest / faction
    "Has the quest for the lost artifact made any progress?",
    "The faction leaders are growing impatient with the delays.",
    "Has anyone spoken to the caravan master about the missing goods?",
    # Intrigue / tension
    "I sense something is wrong. What aren't you telling me?",
    "Who was seen near the royal archives last evening?",
    # Edge cases (short / vague)
    "Speak.",
    "Update me.",
]

# Substrings that indicate system directives leaked into the response
META_LEAK_MARKERS = [
    "### RESPONSE FORMAT",
    "MANDATORY:",
    '"speaker_id"',
    "[ARCHIVED:",
    "[ARCHIVED MEMORY]",
    "```json",
    "### ROLEPLAY PROTOCOL",
    "You MUST respond with",
    "speaker_id",
    "SYSTEM REPAIR",
]

PASS_THRESHOLDS = {
    "schema_validity": 0.98,
    "speaker_diversity": 0.70,
    "meta_leak_rate": 0.00,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_meta_leak(blocks: list) -> bool:
    """Return True if any block content contains a system directive."""
    all_text = " ".join(b.get("content", "") for b in blocks)
    return any(marker in all_text for marker in META_LEAK_MARKERS)


def _prose_metrics(blocks: list) -> dict:
    unique_speakers = len({b.get("speaker_id") or b.get("speaker", "") for b in blocks})
    avg_content_len = sum(len(b.get("content", "")) for b in blocks) / max(len(blocks), 1)
    return {
        "unique_speakers": unique_speakers,
        "has_meta_leak": _check_meta_leak(blocks),
        "avg_content_len": round(avg_content_len, 1),
        "thin_content": avg_content_len < 20,
    }


# ---------------------------------------------------------------------------
# Core evaluation loop
# ---------------------------------------------------------------------------

def run_evaluation(client, prompts: list, verbose: bool = False) -> list:
    from core.models import ConversationTurn
    from pydantic import ValidationError

    results = []
    for i, prompt in enumerate(prompts):
        label = prompt[:55] + "â€¦" if len(prompt) > 55 else prompt
        print(f"  [{i+1:02d}/{len(prompts)}] {label:<58}", end=" ", flush=True)

        entry = {
            "prompt": prompt,
            "schema_valid": False,
            "parse_error": None,
            "block_count": 0,
            "prose": {},
            "latency_s": 0.0,
        }

        t0 = time.time()
        try:
            raw = client.chat(prompt, model_type="rp")
            entry["latency_s"] = round(time.time() - t0, 2)

            blocks = client.parse_response(raw)

            # Validate each block against the ConversationTurn Pydantic model
            for block in blocks:
                ConversationTurn(
                    speaker=block.get("speaker", ""),
                    speaker_id=block.get("speaker_id"),
                    content=block.get("content", ""),
                )

            if blocks:
                entry["schema_valid"] = True
                entry["block_count"] = len(blocks)
                entry["prose"] = _prose_metrics(blocks)
                status = f"OK  ({len(blocks)} speakers, {entry['latency_s']}s)"
            else:
                entry["parse_error"] = "parse_response returned empty list"
                status = "FAIL (empty blocks)"

        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            entry["latency_s"] = round(time.time() - t0, 2)
            entry["parse_error"] = f"{type(exc).__name__}: {exc}"
            status = f"FAIL ({type(exc).__name__})"

        except Exception as exc:
            entry["latency_s"] = round(time.time() - t0, 2)
            entry["parse_error"] = f"Unexpected: {exc}"
            status = f"ERROR"

        print(status)

        if verbose and entry.get("schema_valid"):
            for b in client.parse_response(raw) if entry["schema_valid"] else []:
                sid = b.get("speaker_id", "?")
                name = b.get("speaker", "?")
                snip = b.get("content", "")[:90]
                print(f"      [{sid}] {name}: {snip}")

        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(results: list) -> dict:
    total = len(results)
    if not total:
        return {}

    valid = [r for r in results if r["schema_valid"]]
    n_valid = len(valid)

    schema_validity = n_valid / total
    meta_leak_count = sum(1 for r in valid if r["prose"].get("has_meta_leak"))
    meta_leak_rate = meta_leak_count / max(n_valid, 1)

    speaker_counts = [r["prose"].get("unique_speakers", 0) for r in valid]
    avg_speakers = sum(speaker_counts) / max(len(speaker_counts), 1)
    # Target is ~2 distinct speakers per turn; normalize to 0â€“1
    speaker_diversity = min(avg_speakers / 2.0, 1.0)

    avg_latency = sum(r["latency_s"] for r in results) / total
    thin_count = sum(1 for r in valid if r["prose"].get("thin_content"))

    error_types: Counter = Counter()
    for r in results:
        if not r["schema_valid"] and r["parse_error"]:
            key = r["parse_error"].split(":")[0].strip()
            error_types[key] += 1

    return {
        "total_prompts": total,
        "schema_valid_count": n_valid,
        "schema_validity": round(schema_validity, 4),
        "meta_leak_count": meta_leak_count,
        "meta_leak_rate": round(meta_leak_rate, 4),
        "avg_unique_speakers": round(avg_speakers, 2),
        # Backward-compatible key consumed by PASS_THRESHOLDS.
        "speaker_diversity": round(speaker_diversity, 4),
        "speaker_diversity_index": round(speaker_diversity, 4),
        "avg_latency_s": round(avg_latency, 2),
        "thin_content_count": thin_count,
        "error_types": dict(error_types),
    }


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def print_report(metrics: dict) -> str:
    w = 62
    print("\n" + "=" * w)
    print("  SCHEMA PROSE EVALUATION REPORT")
    print("=" * w)
    print(f"  Total prompts tested  : {metrics['total_prompts']}")
    print(f"  Schema valid          : {metrics['schema_valid_count']} / {metrics['total_prompts']}"
          f"  ({metrics['schema_validity'] * 100:.1f}%)")
    print(f"  Meta-leak instances   : {metrics['meta_leak_count']}"
          f"  ({metrics['meta_leak_rate'] * 100:.1f}%)")
    print(f"  Avg unique speakers   : {metrics['avg_unique_speakers']}")
    print(f"  Speaker diversity idx : {metrics['speaker_diversity_index']:.2f} / 1.00")
    print(f"  Avg response latency  : {metrics['avg_latency_s']}s")
    if metrics.get("thin_content_count"):
        print(f"  Thin responses (< 20c): {metrics['thin_content_count']}")
    if metrics.get("error_types"):
        print(f"  Error breakdown       : {metrics['error_types']}")

    print()
    print("  Threshold check:")
    all_pass = True
    for key, threshold in PASS_THRESHOLDS.items():
        val = metrics.get(key, 0.0)
        passed = (val <= threshold) if key == "meta_leak_rate" else (val >= threshold)
        if not passed:
            all_pass = False
        badge = "PASS" if passed else "FAIL"
        op = "<=" if key == "meta_leak_rate" else ">="
        print(f"    {key:<26} {val:>6.1%}  (need {op} {threshold:.0%})  [{badge}]")

    print()
    if all_pass:
        recommendation = "SAFE_FOR_UNIFICATION"
        print("  RECOMMENDATION:  SAFE_FOR_UNIFICATION")
        print("  All thresholds met. Safe to merge bots into a single")
        print("  runtime and retire discord_party.py.")
    else:
        recommendation = "RETAIN_DUAL_BOT"
        print("  RECOMMENDATION:  RETAIN_DUAL_BOT")
        print("  One or more thresholds not met. Keep the dual-bot setup.")
        print("  Tune model prompting/temperature and re-evaluate.")

    print("=" * w)
    return recommendation


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Offline schema and prose quality evaluator for bot unification gate."
    )
    parser.add_argument(
        "--samples", type=int, default=len(TEST_PROMPTS),
        help=f"Number of test prompts (default: all {len(TEST_PROMPTS)})"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Write JSON report to this path (optional)"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print individual speaker blocks for each response"
    )
    parser.add_argument(
        "--thread-id", type=str, default="eval_ephemeral",
        help="Conversation thread ID used for the eval client (default: eval_ephemeral)"
    )
    args = parser.parse_args()

    # Load .env if present
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except ImportError:
            pass  # dotenv optional; keys may already be in environment

    from core.ai.client import EHClient

    print(f"\nInitializing EHClient (thread: {args.thread_id})...")
    client = EHClient(thread_id=args.thread_id)
    # Wipe the eval thread history so each run starts clean
    client.clear_history()

    print(f"  Model            : {client.model_ollama}")
    print(f"  Temperature      : {client.json_temperature}")
    print(f"  Num predict      : {client.json_num_predict}")

    prompts = TEST_PROMPTS[: args.samples]
    print(f"\nRunning evaluation on {len(prompts)} prompts...\n")

    results = run_evaluation(client, prompts, verbose=args.verbose)

    # Clean up eval history so it doesn't bleed into real sessions
    client.clear_history()

    metrics = compute_metrics(results)
    recommendation = print_report(metrics)

    if args.output:
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "model": client.model_ollama,
            "json_temperature": client.json_temperature,
            "json_num_predict": client.json_num_predict,
            "metrics": metrics,
            "recommendation": recommendation,
            "pass_thresholds": PASS_THRESHOLDS,
            "results": results,
        }
        out = Path(args.output)
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"\n  Report written â†’ {out}")

    sys.exit(0 if recommendation == "SAFE_FOR_UNIFICATION" else 1)


if __name__ == "__main__":
    main()

