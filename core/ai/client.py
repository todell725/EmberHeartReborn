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

try:
    import google.generativeai as genai
except ImportError:
    genai = None

import re
import time

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

# JSON schema preamble injected at the TOP of the system prompt for party/group channels
PARTY_JSON_SCHEMA = """
### RESPONSE FORMAT (MANDATORY):
You MUST respond with a valid JSON array and NOTHING ELSE. No prose, no explanation outside the array.
Schema: [{"speaker_id": "PC-02", "speaker": "Talmarr", "content": "Their dialogue or action text"}]
- Include 1-3 characters who would NATURALLY respond to the message. Not everyone must speak every turn.
- NEVER include King Kaelrath as a speaker.
- `speaker_id` is REQUIRED for each block and must match the roster IDs provided in context.
- `speaker` should be the canonical character name for that ID.
- Do NOT invent IDs. If an ID is unknown, choose a different character.
- Keep each character's voice distinct and true to their personality.
- Actions go inside content as *italicised text*. Dialogue goes as plain text.
- Example: [{"speaker_id": "PC-02", "speaker": "Talmarr", "content": "*glances at the door* Someone's coming."}]
"""

class EHClient:
    def __init__(self, thread_id="default", npc_name=None, model_gemini="gemini-2.0-flash", model_openai="gpt-4o", model_github="gpt-4o"):
        self.thread_id = str(thread_id)
        self.npc_name = npc_name
        self.eh_dir = ROOT_DIR 
        self.world_manager = WorldContextManager(self.eh_dir)
        self.providers = initialize_providers(model_gemini, model_openai, model_github)

        self.ollama_client = self.providers["ollama_client"]
        self.github_client = self.providers["github_client"]
        self.openai_client = self.providers["openai_client"]
        self.model_ollama = self.providers["model_ollama"]
        self.model_ollama_rp = self.providers.get("model_ollama_rp")
        self.model_ollama_reasoning = self.providers.get("model_ollama_reasoning")
        self.model_github = self.providers["model_github"]
        self.model_openai = self.providers["model_openai"]
        self.model_gemini = self.providers["model_gemini"]
        self.keys = self.providers["keys"]

        # JSON-mode tuning (used by PartyBrain/group channels)
        self.json_temperature = _env_float("OLLAMA_JSON_TEMPERATURE", 0.55)
        self.json_num_predict = _env_int("OLLAMA_JSON_NUM_PREDICT", 220)
        self.json_history_messages = _env_int("OLLAMA_JSON_HISTORY_MESSAGES", 5)
        self.json_include_pulse = _env_bool("OLLAMA_JSON_INCLUDE_PULSE", True)
        self.json_include_briefing = _env_bool("OLLAMA_JSON_INCLUDE_BRIEFING", True)
        self.json_include_rag = _env_bool("OLLAMA_JSON_INCLUDE_RAG", False)

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

        self.gemini_chat = None
        self.gemini_model = None
        self._init_gemini()

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
    def _init_gemini(self):
        """Initializes or re-initializes the Gemini model with the current system prompt."""
        if self.keys["GEMINI"] and genai:
            try:
                self.gemini_model = genai.GenerativeModel(
                    model_name=self.model_gemini,
                    system_instruction=self.system_prompt,
                    generation_config=genai.GenerationConfig(temperature=1.0, max_output_tokens=8192)
                )
                self.gemini_chat = self.gemini_model.start_chat(history=[])
                # Restore history if it exists
                if hasattr(self, 'unified_history') and len(self.unified_history) > 1:
                     gemini_hist = []
                     for msg in self.unified_history[1:]:
                          if msg["role"] == "user":
                               gemini_hist.append({"role": "user", "parts": [msg["content"]]})
                          elif msg["role"] == "assistant":
                               gemini_hist.append({"role": "model", "parts": [msg["content"]]})
                     self.gemini_chat.history = gemini_hist
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")

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
        
        # Re-init Gemini to apply the new system prompt instructions
        self._init_gemini()


    def _save_history(self):
        """Atomically saves this specific thread to disk."""
        all_conversations = load_conversations()
        all_conversations[self.thread_id] = self.unified_history
        save_conversations(all_conversations)

    def _trim_history(self, max_messages: int = 10):
        if len(self.unified_history) > max_messages + 1:
            self.unified_history = [self.unified_history[0]] + self.unified_history[-(max_messages):]
            self._save_history()

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

        self._trim_history(max_messages=8)

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
        
        self.unified_history.append({"role": "assistant", "content": reply})
        self._save_history()
        logger.info(f"Response received from {provider_name} ({model})")
        return reply

    def _chat_gemini(self, message: str) -> str:
        if not self.gemini_chat:
            raise ValueError("Gemini not configured.")
        briefing = self.world_manager.get_sovereign_briefing()
        pulse = self.world_manager.get_narrative_pulse()
        rag_context = self.world_manager.get_relevant_context(message)
        
        enhanced = message
        if pulse: enhanced += pulse
        if briefing: enhanced += briefing
        if rag_context: enhanced += rag_context
        
        response = self.gemini_chat.send_message(enhanced)
        
        reply = response.text
        # IMMERSION CLEANUP
        reply = re.sub(r"^\(.*?\)\s*", "", reply)
        # B-16: Identity-aware name stripping (matches _chat_openai_compatible)
        name_match = re.match(r"^([A-Za-z]+)\s*:\s*", reply)
        if name_match:
             potential_name = name_match.group(1)
             from ..config import IDENTITIES
             if any(potential_name.lower() in k.lower() for k in IDENTITIES):
                  reply = reply[name_match.end():]

        # Keep our unified memory in sync for the JSON save file
        last = self.unified_history[-1] if self.unified_history else {}
        if last.get("role") != "user" or last.get("content") != enhanced:
            self.unified_history.append({"role": "user", "content": enhanced})
        self.unified_history.append({"role": "assistant", "content": reply})
        self._trim_history(max_messages=8)
        self._save_history()
        logger.info(f"Response received from Gemini ({self.model_gemini})")
        return reply

    def clear_history(self):
        self.unified_history = [{"role": "system", "content": self.system_prompt}]
        self._save_history()
        if self.gemini_model and genai:
            self.gemini_chat = self.gemini_model.start_chat(history=[])
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
            # If Gemini is active, we just restart the chat with the new history
            if self.gemini_model and genai:
                self.gemini_chat = self.gemini_model.start_chat(history=[]) # Will rebuild on next send
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
        self._trim_history(max_messages=12) # Slightly larger window for rebuild
        self._save_history()
        if self.gemini_model and genai:
            self.gemini_chat = self.gemini_model.start_chat(history=[])
        logger.info(f"Thread {self.thread_id} rebuilt from {len(message_list)} messages.")

    def _chat_ollama_json(self, message: str, model: str = None) -> str:
        """
        Calls Ollama with format='json' enforced at the API level.
        Returns raw text (should be a JSON string).
        """
        if not self.ollama_client:
            raise ValueError("Ollama not configured.")

        # Build the enhanced message with optional context for speed tuning.
        briefing = self.world_manager.get_sovereign_briefing() if self.json_include_briefing else ""
        pulse = self.world_manager.get_narrative_pulse() if self.json_include_pulse else ""
        rag_context = self.world_manager.get_relevant_context(message) if self.json_include_rag else ""
        enhanced_message = message
        if pulse:
            enhanced_message += pulse
        if briefing:
            enhanced_message += briefing
        if rag_context:
            enhanced_message += rag_context

        last = self.unified_history[-1] if self.unified_history else {}
        if last.get("role") != "user" or last.get("content") != enhanced_message:
            self.unified_history.append({"role": "user", "content": enhanced_message})
        self._trim_history(max_messages=max(2, self.json_history_messages))

        # Ollama openai-compat does not expose format=json, so call native API directly.
        import urllib.request
        import urllib.error
        ollama_base = self.providers.get("ollama_base", "http://localhost:11434")
        payload = json.dumps({
            "model": model or self.model_ollama,
            "messages": self.unified_history,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": self.json_temperature,
                "num_predict": max(64, self.json_num_predict),
            },
        }).encode()
        req = urllib.request.Request(
            f"{ollama_base}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            reply = result["message"]["content"]

        self.unified_history.append({"role": "assistant", "content": reply})
        self._save_history()
        logger.info(
            "JSON response received from Ollama (%s) [num_predict=%s, temp=%s, rag=%s]",
            (model or self.model_ollama),
            self.json_num_predict,
            self.json_temperature,
            self.json_include_rag,
        )
        return reply

    def chat(self, message: str, model_type: str = "general") -> str:
        """
        Unified chat with priority fallback and model_type routing.
        model_type can be: "general", "rp", "reasoning"
        """
        errors = []

        if self.ollama_client:
            # Determine which Ollama model to use
            target_model = self.model_ollama
            if model_type == "rp" and self.model_ollama_rp:
                target_model = self.model_ollama_rp
            elif model_type == "reasoning" and self.model_ollama_reasoning:
                target_model = self.model_ollama_reasoning

            try:
                return self._chat_openai_compatible(self.ollama_client, target_model, message, "Ollama")
            except Exception as e:
                errors.append(f"Ollama ({target_model}): {e}")
                logger.error(f"Ollama failed for {target_model}. Details: {e}", exc_info=True)
                time.sleep(0.5)  # Brief jitter before fallback

        if self.github_client:
            try:
                return self._chat_openai_compatible(self.github_client, self.model_github, message, "GitHub")
            except Exception as e:
                errors.append(f"GitHub: {e}")
                logger.warning(f"GitHub Models failed: {e}")
                time.sleep(0.5)

        if self.gemini_chat:
            try:
                return self._chat_gemini(message)
            except Exception as e:
                errors.append(f"Gemini: {e}")
                logger.warning(f"Gemini failed: {e}")
                time.sleep(0.5)

        if self.openai_client:
            try:
                return self._chat_openai_compatible(self.openai_client, self.model_openai, message, "OpenAI")
            except Exception as e:
                errors.append(f"OpenAI: {e}")
                logger.warning(f"OpenAI failed: {e}")

        error_summary = " | ".join(errors)
        logger.error(f"CRITICAL: All AI providers failed. Summary: {error_summary}")
        raise RuntimeError(f"All AI providers failed: {error_summary}")

    def chat_json(self, message: str, model_type: str = "general") -> str:
        """
        JSON-mode chat for group/party channels.
        Tries Ollama native JSON format first, then falls back to standard chat().
        Always returns raw text (caller uses parse_response() to decode it).
        model_type can be: "general", "rp", "reasoning".
        """
        target_model = self.model_ollama
        if model_type == "rp" and self.model_ollama_rp:
            target_model = self.model_ollama_rp
        elif model_type == "reasoning" and self.model_ollama_reasoning:
            target_model = self.model_ollama_reasoning

        try:
            return self._chat_ollama_json(message, model=target_model)
        except Exception as e:
            logger.warning(f"Ollama JSON mode failed ({e}), falling back to standard chat.")
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
        logger.warning("parse_response: JSON decode failed. Falling back to heuristic parser.")
        try:
            from ..formatting import parse_speaker_blocks
            from ..config import IDENTITIES
            raw_blocks = parse_speaker_blocks(text, IDENTITIES, set())

            results = []
            for b in raw_blocks:
                speaker = str(b.get("speaker", "")).strip()
                content = str(b.get("content", "")).strip()
                token = b.get("identity") if isinstance(b.get("identity"), dict) else None
                speaker_id = str(token.get("id", "")).strip() if token else ""

                if not speaker or not content:
                    continue

                row = {"speaker": speaker, "content": content}
                if speaker_id:
                    row["speaker_id"] = speaker_id
                if token:
                    row["identity"] = token
                results.append(row)

            return results
        except Exception as e:
            logger.error(f"parse_response: heuristic fallback also failed: {e}")
            return [{"speaker": "DM", "content": text.strip()}]

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
        # If Gemini is active, we just restart the chat with the new history
        if self.gemini_model and genai:
            self.gemini_chat = self.gemini_model.start_chat(history=[]) # Rebuild on next send
        logger.info(f"Thread {self.thread_id} set to META-AWARE (Chronicle Weaver) mode.")



