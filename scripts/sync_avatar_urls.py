"""
Sync character avatar URLs to GitHub raw links.

What this script does:
1. Scans `characters/*/profile.json`.
2. Finds a portrait image in each character folder.
3. Builds a GitHub raw URL using the current git remote + branch.
4. Updates `profile.json` avatar_url.
5. Propagates avatar_url to `state/NPC_STATE_FULL.json` and `state/PARTY_STATE.json`.

Usage:
    python scripts/sync_avatar_urls.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib import error, request
from urllib.parse import quote, unquote, urlparse


ROOT = Path(__file__).resolve().parent.parent
CHARACTERS_DIR = ROOT / "characters"
STATE_NPC_PATH = ROOT / "state" / "NPC_STATE_FULL.json"
STATE_PARTY_PATH = ROOT / "state" / "PARTY_STATE.json"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif")


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _github_repo_from_remote(remote_url: str) -> Optional[Tuple[str, str]]:
    # Supports:
    # - https://github.com/owner/repo.git
    # - git@github.com:owner/repo.git
    cleaned = remote_url.strip()
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]

    if "github.com/" in cleaned:
        tail = cleaned.split("github.com/", 1)[1]
    elif cleaned.startswith("git@github.com:"):
        tail = cleaned.split("git@github.com:", 1)[1]
    else:
        return None

    parts = [p for p in tail.split("/") if p]
    if len(parts) < 2:
        return None
    return parts[0], parts[1]


def _find_portrait(char_dir: Path, current_avatar_url: str = "") -> Optional[Path]:
    # Prefer the currently referenced file (if it exists) so reruns are stable.
    if current_avatar_url:
        maybe_name = ""
        if "://" in current_avatar_url:
            parsed = urlparse(current_avatar_url)
            maybe_name = Path(unquote(parsed.path)).name
        else:
            maybe_name = Path(current_avatar_url).name

        if maybe_name:
            direct = char_dir / maybe_name
            if direct.exists() and direct.is_file():
                return direct

            # Case-insensitive fallback for Windows-style drift.
            lowered = maybe_name.lower()
            for p in char_dir.iterdir():
                if p.is_file() and p.name.lower() == lowered:
                    return p

    # Deterministic fallback.
    images = sorted(
        [p for p in char_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    )
    return images[0] if images else None


def _raw_url(owner: str, repo: str, branch: str, relative_path: Path) -> str:
    rel = relative_path.as_posix()
    # Encode spaces/special chars but preserve path separators.
    encoded = quote(rel, safe="/-_.~")
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{encoded}"


def _save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _is_repo_public(owner: str, repo: str) -> bool:
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    req = request.Request(api_url, headers={"User-Agent": "avatar-sync"})
    try:
        with request.urlopen(req, timeout=10) as response:
            return response.getcode() == 200
    except error.HTTPError as exc:
        if exc.code in (401, 403, 404):
            return False
        return False
    except Exception:
        return False


def _update_state_file(path: Path, key: str, url_by_id: Dict[str, str]) -> int:
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get(key, [])
    if not isinstance(entries, list):
        return 0

    changes = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        char_id = str(entry.get("id", "")).strip()
        target = url_by_id.get(char_id)
        if not target:
            continue
        if entry.get("avatar_url") != target:
            entry["avatar_url"] = target
            changes += 1

    if changes:
        _save_json(path, data)
    return changes


def main() -> None:
    if not CHARACTERS_DIR.exists():
        print(f"Characters dir not found: {CHARACTERS_DIR}")
        return

    remote_url = _run_git(["remote", "get-url", "origin"])
    repo = _github_repo_from_remote(remote_url)
    if not repo:
        print(f"Could not parse GitHub remote URL: {remote_url}")
        return
    owner, repo_name = repo
    branch = _run_git(["branch", "--show-current"]) or "main"
    is_public_repo = _is_repo_public(owner, repo_name)

    profile_updates = 0
    profiles_scanned = 0
    missing_portraits = []
    duplicate_ids = []
    url_by_id: Dict[str, str] = {}

    for char_dir in sorted(CHARACTERS_DIR.iterdir()):
        if not char_dir.is_dir():
            continue
        profile_path = char_dir / "profile.json"
        if not profile_path.exists():
            continue

        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        char_id = str(profile.get("id", "")).strip()
        if not char_id:
            continue
        profiles_scanned += 1

        current_url = str(profile.get("avatar_url", "")).strip()
        portrait = _find_portrait(char_dir, current_url)
        if portrait is None:
            missing_portraits.append(char_dir.name)
            continue

        rel = portrait.relative_to(ROOT)
        target_url = _raw_url(owner, repo_name, branch, rel)

        if current_url != target_url:
            profile["avatar_url"] = target_url
            _save_json(profile_path, profile)
            profile_updates += 1

        if char_id in url_by_id and url_by_id[char_id] != target_url:
            duplicate_ids.append(char_id)
        else:
            url_by_id[char_id] = target_url

    npc_updates = _update_state_file(STATE_NPC_PATH, "npcs", url_by_id)
    party_updates = _update_state_file(STATE_PARTY_PATH, "party", url_by_id)

    print("Avatar URL sync complete")
    print(f"- Profiles updated: {profile_updates}")
    print(f"- NPC state entries updated: {npc_updates}")
    print(f"- Party state entries updated: {party_updates}")
    print(f"- Profiles scanned: {profiles_scanned}")
    print(f"- Unique character IDs: {len(url_by_id)}")
    if missing_portraits:
        print(f"- Missing portrait files: {len(missing_portraits)}")
        for folder in missing_portraits:
            print(f"  * {folder}")
    if duplicate_ids:
        print(f"- Duplicate character IDs detected: {sorted(set(duplicate_ids))}")
    if not is_public_repo:
        print("- WARNING: GitHub repo appears private/unreachable without auth.")
        print("  Raw GitHub avatar URLs will fail in Discord unless assets are publicly accessible.")


if __name__ == "__main__":
    main()
