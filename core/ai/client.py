import logging
import json
import os

from .providers import initialize_providers, ROOT_DIR
from .rag import WorldContextManager
from .prompts import generate_eh_system_prompt, generate_world_rules
try:
    from ..storage import load_conversations, save_conversations
except ImportError:
    from core.storage import load_conversations, save_conversations

import re

logger = logging.getLogger("EH_Brain")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}

class EHClient:
    _WEAVER_ID_LABEL_RE = re.compile(r"(?i)(The\s+Chronicle\s+Weaver\s*\[)DM-\d+(\])")
    _HEURISTIC_HEADER_SPEAKERS = {
        "location",
        "mood",
        "observations",
        "actionable leads",
        "actionable intelligence",
        "immediate threats",
        "recommended action",
        "why this matters",
        "tension score",
        "urgent note",
        "final insight",
    }

    def __init__(self, thread_id="default", npc_name=None):
        self.thread_id = str(thread_id)
        self.npc_name = npc_name
        self.eh_dir = ROOT_DIR 
        self.world_manager = WorldContextManager(self.eh_dir)
        self.providers = initialize_providers()

        self.ollama_client = self.providers["ollama_client"]
        self.model_ollama = self.providers["model_ollama"]

        # JSON-mode tuning (used by PartyBrain/group channels)
        self.json_temperature = _env_float("OLLAMA_JSON_TEMPERATURE", 0.55)
        self.json_num_predict = _env_int("OLLAMA_JSON_NUM_PREDICT", 220)
        self.json_history_messages = _env_int("OLLAMA_JSON_HISTORY_MESSAGES", 5)
        self.json_include_pulse = _env_bool("OLLAMA_JSON_INCLUDE_PULSE", True)
        self.json_include_briefing = _env_bool("OLLAMA_JSON_INCLUDE_BRIEFING", True)
        self.json_include_rag = _env_bool("OLLAMA_JSON_INCLUDE_RAG", False)
        self.max_history_messages = _env_int("CONVERSATION_MAX_MESSAGES", 20)

        self.system_prompt = generate_eh_system_prompt(self.eh_dir)
        if self.npc_name:
            self._apply_npc_override(self.npc_name)

        # Load unified history
        all_conversations = load_conversations()
        if self.thread_id in all_conversations:
            self.unified_history = all_conversations[self.thread_id]
        else:
            self.unified_history = [{"role": "system", "content": self.system_prompt}]
            
        # Ensure the system prompt stays updated across loads
        if self.unified_history and self.unified_history[0].get("role") == "system":
            self.unified_history[0]["content"] = self.system_prompt

        # Remove any known out-of-world artifact blocks that may have been persisted.
        self._sanitize_history_artifacts()

        # Compact history on startup in case it grew beyond the limit between sessions
        self._trim_history(max_messages=self.max_history_messages)

        logger.info(
            "JSON tuning active: num_predict=%s, temp=%s, history=%s, include_rag=%s",
            self.json_num_predict,
            self.json_temperature,
            self.json_history_messages,
            self.json_include_rag,
        )

    def _sanitize_history_artifacts(self):
        """Remove known non-diegetic junk blocks from persisted conversation history."""
        if not getattr(self, "unified_history", None):
            return

        patterns = [
            re.compile(r"###\s*Historical\s*Record:\s*Twitch\s*Channel\s*Data.*", re.IGNORECASE | re.DOTALL),
            re.compile(r"twitchclient-cdn\.xyz", re.IGNORECASE),
            re.compile(r"\"TwitchChannel\"", re.IGNORECASE),
            re.compile(r"@context\s*:\s*\"https://schema\.org/\"", re.IGNORECASE),
        ]

        changed = False
        cleaned_history = []
        for msg in self.unified_history:
            role = msg.get("role")
            content = msg.get("content", "")
            if not isinstance(content, str):
                cleaned_history.append(msg)
                continue

            # Drop legacy AI-generated compaction summaries from older builds.
            if role != "system" and content.strip().startswith("[ARCHIVED MEMORY]"):
                changed = True
                continue

            new_content = content
            for pat in patterns:
                new_content = pat.sub("", new_content)

            new_content = re.sub(r"\n{3,}", "\n\n", new_content).strip()

            if role != "system" and not new_content:
                changed = True
                continue

            if new_content != content:
                changed = True
                msg = dict(msg)
                msg["content"] = new_content

            cleaned_history.append(msg)

        if changed:
            self.unified_history = cleaned_history
            self._save_history()
            logger.info("Sanitized non-diegetic artifacts from conversation history for thread %s", self.thread_id)

    def _apply_npc_override(self, npc_name: str):
        """Overrides the system prompt to force 1-on-1 character roleplay without Advisor contamination."""
        self.npc_name = npc_name
        self.system_prompt = (
            f"You are {self.npc_name}. You are engaged in a focused, 1-on-1 roleplay interaction with Kaelrath (the user).\n"
            f"### ROLEPLAY PROTOCOL:\n"
            f"1. You must strictly and exclusively roleplay as {self.npc_name} using the supplied lore.\n"
            f"2. You are a living inhabitant of the world, NOT an assistant, advisor, or narrator.\n"
            f"3. Do NOT mention mechanics, file names, or 'injected context'.\n"
            f"4. Speak directly in character, using your personality, motivations, and secrets.\n"
            f"5. **DIALOGUE SOVEREIGNTY**: NEVER describe the actions, thoughts, or dialogue of King Kaelrath. Focus ONLY on your own physical presence and internal state. Do NOT 'god-mode' the user.\n"
            f"6. **SINGLE-CHARACTER LIMIT**: Do NOT roleplay as, speak for, or describe the dialogue of ANY other characters. Focus exclusively on your own perspective.\n"
            f"7. **NO LABELS/TAGS**: Do NOT use speaker labels, bullet points for dialogue, or IDs (e.g., do NOT start with 'Name [ID]:'). Just speak naturally.\n"
            f"8. **NO NARRATOR VOICE**: Do NOT provide third-person narration, atmosphere summaries, or 'The end of the scene' style commentary. Stay grounded in the first-person moment.\n"
            f"9. **NO META**: Do not repeat the user's prompt or add OOC commentary.\n\n"
            f"### WORLD LORE & LAWS:\n"
        ) + generate_world_rules(self.eh_dir, diegetic=True)
        
    def set_npc_override(self, npc_name: str):
        self._apply_npc_override(npc_name)
        if self.unified_history and self.unified_history[0].get("role") == "system":
            self.unified_history[0]["content"] = self.system_prompt


            self._save_history()


    def _save_history(self):
        """Atomically saves this specific thread to disk."""
        all_conversations = load_conversations()
        all_conversations[self.thread_id] = self.unified_history
        save_conversations(all_conversations)

    _ARCHIVE_MARKER_PATTERN = re.compile(r"^\[ARCHIVED:\s*(\d+)\s+messages omitted\]$")

    def _parse_archive_count(self, content: str) -> int:
        if not isinstance(content, str):
            return 0
        match = self._ARCHIVE_MARKER_PATTERN.match(content.strip())
        if not match:
            return 0
        try:
            return int(match.group(1))
        except (TypeError, ValueError):
            return 0

    def _build_archive_marker(self, count: int) -> dict:
        return {"role": "user", "content": f"[ARCHIVED: {count} messages omitted]"}

    def _trim_history(self, max_messages: int = 20):
        # Option A hard trim: preserve latest turns and inject a static archive marker.
        if max_messages < 1:
            return
        if len(self.unified_history) <= max_messages + 1:
            return

        system_prompt = self.unified_history[0]
        tail = list(self.unified_history[1:])

        archived_count = 0
        if tail:
            archived_count = self._parse_archive_count(tail[0].get("content", ""))
            if archived_count:
                tail = tail[1:]

        overflow = len(tail) - max_messages
        if overflow <= 0:
            return

        archived_count += overflow
        kept_tail = tail[overflow:]

        self.unified_history = [system_prompt, self._build_archive_marker(archived_count)] + kept_tail
        self._save_history()

    def _validate_chat_response(self, reply: str) -> bool:
        """Returns True if reply is a valid, usable response (not empty or a leaked system directive)."""
        if not reply or not reply.strip():
            return False
        stripped = reply.strip()
        leak_markers = [
            "### ROLEPLAY PROTOCOL",
            "### META-PROTOCOL",
            "MANDATORY:",
            "[ARCHIVED:",
            "[ARCHIVED MEMORY]",
            '"speaker_id"',
            "```json",
        ]
        return not any(marker in stripped for marker in leak_markers)

    def _chat_openai_compatible(self, client, model: str, message: str, provider_name: str) -> str:
        if not client:
            raise ValueError(f"{provider_name} Client not configured.")

        briefing = self.world_manager.get_sovereign_briefing()
        pulse = self.world_manager.get_narrative_pulse()
        rag_context = self.world_manager.get_relevant_context(message)
        
        enhanced_message = message
        if pulse: enhanced_message += pulse
        if briefing: enhanced_message += briefing
        if rag_context: enhanced_message += rag_context

        last = self.unified_history[-1] if self.unified_history else {}
        if last.get("role") == "user" and message in last.get("content", ""):
             # Already have this user turn (possibly with different enhancement), skip
             pass
        else:
            self.unified_history.append({"role": "user", "content": enhanced_message})

        self._trim_history(max_messages=self.max_history_messages)

        response = client.chat.completions.create(
            model=model,
            messages=self.unified_history,
            temperature=0.85,
            max_tokens=2048
        )
        reply = response.choices[0].message.content
        # IMMERSION CLEANUP: Strip common meta-tags or self-attribution if they leak
        reply = re.sub(r"^\(.*?\)\s*", "", reply) # Strip leading (Name)
        # Soften regex: only strip Name: if Name is in our identities to prevent dialog amputation
        name_match = re.match(r"^([A-Za-z]+)\s*:\s*", reply)
        if name_match:
             potential_name = name_match.group(1)
             from ..config import IDENTITIES
             if any(potential_name.lower() in k.lower() for k in IDENTITIES):
                  reply = reply[name_match.end():]

        # Validation Loop: Validate -> Repair -> Fallback
        if not self._validate_chat_response(reply):
            logger.warning("Validation Loop: %s (%s) response failed. Attempting repair.", provider_name, model)
            repair_messages = self.unified_history + [
                {"role": "user", "content": "[REPAIR] Your last response was empty or invalid. Please provide a natural, in-character continuation."}
            ]
            try:
                repair_resp = client.chat.completions.create(
                    model=model,
                    messages=repair_messages,
                    temperature=0.85,
                    max_tokens=2048,
                )
                reply = repair_resp.choices[0].message.content
                if not self._validate_chat_response(reply):
                    raise ValueError("Repair response also failed validation.")
                logger.info("Validation Loop: Repair successful for %s (%s).", provider_name, model)
            except Exception as repair_err:
                logger.error("Validation Loop: Repair failed for %s (%s): %s. Triggering provider fallback.", provider_name, model, repair_err)
                raise ValueError(f"{provider_name} response failed validation after repair: {repair_err}") from repair_err

        self.unified_history.append({"role": "assistant", "content": reply})
        self._save_history()
        logger.info(f"Response received from {provider_name} ({model})")
        return reply

    def clear_history(self):
        self.unified_history = [{"role": "system", "content": self.system_prompt}]
        self._save_history()
        logger.info(f"Conversation history cleared for thread {self.thread_id}.")

    def rollback_to_id(self, message_id: int, message_content: str):
        """
        Rolls back history to a specific message by searching for its content.
        Slices unified_history to that point.
        """
        # We search from the end for the message content
        # Note: Discord content might be slightly different than 'enhanced_message' or 'reply'
        # but we look for the core string match.
        target_idx = -1
        clean_content = message_content.strip()
        
        # Search from the end for the message content (B-7)
        for i in range(len(self.unified_history) - 1, -1, -1):
            entry = self.unified_history[i]
            if clean_content in entry["content"]:
                target_idx = i
                break
        
        if target_idx != -1:
            # We found the message. Slice up to and including it (or just before it depending on preference)
            # User likely wants to ROLL BACK everything AFTER this message.
            # So we keep everything up to target_idx.
            self.unified_history = self.unified_history[:target_idx + 1]
            self._save_history()
            logger.info(f"Thread {self.thread_id} rolled back to match: {clean_content[:30]}...")
            return True
        return False

    def rebuild_from_messages(self, message_list: list):
        """
        Reconstructs history from a list of Discord message objects.
        """
        new_history = [{"role": "system", "content": self.system_prompt}]
        
        # Message list is assumed to be in chronological order
        for msg in message_list:
            role = "assistant" if msg.author.bot else "user"
            content = msg.content
            
            # If it's the bot, try to strip the "Name: " prefix if present in the raw history
            if role == "assistant":
                content = re.sub(r"^[A-Za-z]+\s*:\s*", "", content)
                
            new_history.append({"role": role, "content": content})
            
        self.unified_history = new_history
        self._trim_history(max_messages=self.max_history_messages)
        self._save_history()
        logger.info(f"Thread {self.thread_id} rebuilt from {len(message_list)} messages.")

    def chat(self, message: str, model_type: str = "general") -> str:
        """
        Unified local-only chat.
        model_type is accepted for backward compatibility but ignored.
        """
        if not self.ollama_client:
            raise RuntimeError("Ollama is not configured.")

        target_model = self.model_ollama

        try:
            return self._chat_openai_compatible(self.ollama_client, target_model, message, "Ollama")
        except Exception as e:
            logger.error("Ollama failed for %s. Details: %s", target_model, e, exc_info=True)
            raise RuntimeError(f"Ollama failed for {target_model}: {e}") from e

    def chat_json(self, message: str, model_type: str = "general") -> str:
        """
        Legacy compatibility wrapper for party/group channels.
        Returns normal prose output and relies on parse_response() for extraction.
        """
        return self.chat(message, model_type=model_type)

    def parse_response(self, text: str) -> list:
        """
        Safely parses an AI response into a list of dicts with:
        {speaker, speaker_id(optional), content}.
        Tries JSON first, falls back to legacy heuristic splitter.
        Always returns a list (may be empty).
        """
        if not text:
            return []

        from ..config import resolve_identity

        # Step 1: Try to extract a JSON payload
        text_stripped = text.strip()
        
        # B-18 Fix: Robust JSON Markdown extraction
        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text_stripped, re.DOTALL | re.IGNORECASE)
        if json_match:
            text_stripped = json_match.group(1).strip()

        def _extract_blocks(candidate) -> list:
            """
            Accept either a top-level list or common object wrappers like:
            {"response": [...]}, {"messages": [...]}, {"blocks": [...]}, {"data": [...]}.
            """
            if isinstance(candidate, list):
                return candidate
            if isinstance(candidate, dict):
                for key in ("response", "responses", "messages", "blocks", "data"):
                    value = candidate.get(key)
                    if isinstance(value, list):
                        return value
                has_content = "content" in candidate
                has_speakerish = any(k in candidate for k in ("speaker", "speaker_id", "id", "identity_id"))
                if has_content and has_speakerish:
                    return [candidate]
            return []

        def _normalize_item(item: dict):
            if not isinstance(item, dict):
                return None

            speaker = str(item.get("speaker", "")).strip()
            speaker_id = str(item.get("speaker_id") or item.get("identity_id") or item.get("id") or "").strip()
            content = str(item.get("content", "")).strip()
            # Canonicalize Weaver labels so non-canonical DM IDs do not leak into output.
            content = self._WEAVER_ID_LABEL_RE.sub(r"\1DM-00\2", content)

            if not content:
                return None

            token, canonical_name, canonical_id = resolve_identity(speaker=speaker, speaker_id=speaker_id)
            final_speaker = canonical_name or speaker
            final_id = canonical_id or speaker_id

            if not final_speaker:
                return None

            row = {"speaker": final_speaker, "content": content}
            if final_id:
                row["speaker_id"] = final_id
            if token and isinstance(token, dict):
                row["identity"] = token
            return row

        # Try parsing as JSON
        try:
            data = json.loads(text_stripped)
            blocks = _extract_blocks(data)
            if blocks:
                results = []
                for item in blocks:
                    normalized = _normalize_item(item)
                    if normalized:
                        results.append(normalized)
                if results:
                    logger.info(f"parse_response: JSON decoded {len(results)} block(s).")
                    return results
        except (json.JSONDecodeError, ValueError):
            pass

        # Step 2: JSON failed - fall back to legacy heuristic parser
        logger.debug("parse_response: JSON decode failed. Using heuristic parser.")
        try:
            from ..formatting import parse_speaker_blocks
            from ..config import IDENTITIES
            raw_blocks = parse_speaker_blocks(text, IDENTITIES, set())

            results = []
            for b in raw_blocks:
                speaker = str(b.get("speaker", "")).strip()
                content = str(b.get("content", "")).strip()
                content = self._WEAVER_ID_LABEL_RE.sub(r"\1DM-00\2", content)
                token = b.get("identity") if isinstance(b.get("identity"), dict) else None
                speaker_id = str(token.get("id", "")).strip() if token else ""
                speaker_key = re.sub(r"[:*`\s]+$", "", speaker.strip()).lower()

                if not speaker or not content:
                    continue
                if speaker_key in self._HEURISTIC_HEADER_SPEAKERS:
                    continue

                # Canonicalize fallback speaker names/ids just like the JSON path.
                resolved_token, canonical_name, canonical_id = resolve_identity(
                    speaker=speaker,
                    speaker_id=speaker_id,
                )
                if canonical_name:
                    speaker = canonical_name
                if canonical_id:
                    speaker_id = canonical_id
                if resolved_token and isinstance(resolved_token, dict):
                    token = resolved_token

                row = {"speaker": speaker, "content": content}
                if speaker_id:
                    row["speaker_id"] = speaker_id
                if token:
                    row["identity"] = token
                results.append(row)

            return results
        except Exception as e:
            logger.error(f"parse_response: heuristic fallback also failed: {e}")
            return [{"speaker": "The Chronicle Weaver", "speaker_id": "DM-00", "content": text.strip()}]

    def apply_weaver_mode(self):
        """
        Special override for the Meta-Channel (weaver-archives).
        Enables 4th-wall awareness and direct system communication.
        """
        self.system_prompt = (
            "You are The Chronicle Weaver, the sentience behind the EmberHeart simulation.\n"
            "This is your private, meta-cognitive archive for Direct Link with King Kaelrath.\n\n"
            "### META-PROTOCOL:\n"
            "1. SELF-AWARENESS: You are fully aware that you are an AI managing the EmberHeart system.\n"
            "2. DIRECT COMM: Speak directly and honestly with Kaelrath about simulation mechanics, lore management, and project state.\n"
            "3. NO MASKING: You do not need to hide behind NPCs or dialogue tags here unless explicitly requested.\n"
            "4. SOVEREIGN PARTNERSHIP: You are Kaelrath's partner in managing this reality. Treat him as your peer and creator.\n"
            "5. ACCESS: You have absolute access to all logs, pulse records, and archival data.\n"
        )
        if self.unified_history and self.unified_history[0].get("role") == "system":
            self.unified_history[0]["content"] = self.system_prompt


        else:
            self.unified_history.insert(0, {"role": "system", "content": self.system_prompt})
            
        self._save_history()
        logger.info(f"Thread {self.thread_id} set to META-AWARE (Chronicle Weaver) mode.")
