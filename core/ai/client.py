import logging
import json
from pathlib import Path

from .providers import initialize_providers, ROOT_DIR
from .rag import WorldContextManager
from .prompts import generate_eh_system_prompt, generate_world_rules
from core.storage import load_conversations, save_conversations

try:
    import google.generativeai as genai
except ImportError:
    genai = None

import re
import time

logger = logging.getLogger("EH_Brain")

# JSON schema preamble injected at the TOP of the system prompt for party/group channels
PARTY_JSON_SCHEMA = """
### RESPONSE FORMAT (MANDATORY):
You MUST respond with a valid JSON array and NOTHING ELSE. No prose, no explanation outside the array.
Schema: [{"speaker": "CharacterName", "content": "Their dialogue or action text"}]
- Include 1-3 characters who would NATURALLY respond to the message. Not everyone must speak every turn.
- NEVER include King Kaelrath as a speaker.
- Keep each character's voice distinct and true to their personality.
- Actions go inside content as *italicised text*. Dialogue goes as plain text.
- Example: [{"speaker": "Talmarr", "content": "*glances at the door* Someone's coming."}]
"""

class EHClient:
    def __init__(self, thread_id="default", npc_name=None, model_gemini="gemini-2.0-flash", model_openai="gpt-4o", model_github="gpt-4o"):
        self.thread_id = str(thread_id)
        self.npc_name = npc_name
        self.eh_dir = ROOT_DIR / "EmberHeartReborn"
        self.world_manager = WorldContextManager(self.eh_dir)
        self.providers = initialize_providers(model_gemini, model_openai, model_github)

        self.ollama_client = self.providers["ollama_client"]
        self.github_client = self.providers["github_client"]
        self.openai_client = self.providers["openai_client"]
        self.model_ollama = self.providers["model_ollama"]
        self.model_github = self.providers["model_github"]
        self.model_openai = self.providers["model_openai"]
        self.model_gemini = self.providers["model_gemini"]
        self.keys = self.providers["keys"]

        self.system_prompt = generate_eh_system_prompt(self.eh_dir)
        if self.npc_name:
            self._apply_npc_override(self.npc_name)

        self.gemini_chat = None
        self.gemini_model = None
        self._init_gemini()

        # Load unified history
        all_conversations = load_conversations()
        if self.thread_id in all_conversations:
            self.unified_history = all_conversations[self.thread_id]
        else:
            self.unified_history = [{"role": "system", "content": self.system_prompt}]
            
        # Ensure the system prompt stays updated across loads (e.g., if NPC override was applied after thread creation)
        if self.unified_history and self.unified_history[0].get("role") == "system":
            self.unified_history[0]["content"] = self.system_prompt
            
        # Optional sync Gemini's memory if being used
        if self.gemini_chat and self.keys["GEMINI"]:
            # Rebuilding internal gemini memory array
            gemini_hist = []
            for msg in self.unified_history:
                 if msg["role"] == "user":
                      gemini_hist.append({"role": "user", "parts": [msg["content"]]})
                 elif msg["role"] == "assistant":
                      gemini_hist.append({"role": "model", "parts": [msg["content"]]})
            self.gemini_chat.history = gemini_hist

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
        if last.get("role") != "user" or last.get("content") != enhanced_message:
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
        reply = re.sub(r"^[A-Za-z]+\s*:\s*", "", reply) # Strip leading Name:
        
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
        reply = re.sub(r"^[A-Za-z]+\s*:\s*", "", reply)

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
        
        for i, entry in enumerate(self.unified_history):
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

    def _chat_ollama_json(self, message: str) -> str:
        """
        Calls Ollama with format='json' enforced at the API level.
        Returns raw text (should be a JSON string).
        """
        if not self.ollama_client:
            raise ValueError("Ollama not configured.")
        
        # Build the enhanced message with pulse/briefing context
        briefing = self.world_manager.get_sovereign_briefing()
        pulse = self.world_manager.get_narrative_pulse()
        rag_context = self.world_manager.get_relevant_context(message)
        enhanced_message = message
        if pulse: enhanced_message += pulse
        if briefing: enhanced_message += briefing
        if rag_context: enhanced_message += rag_context

        last = self.unified_history[-1] if self.unified_history else {}
        if last.get("role") != "user" or last.get("content") != enhanced_message:
            self.unified_history.append({"role": "user", "content": enhanced_message})
        self._trim_history(max_messages=8)

        # Use the raw httpx/requests approach via the openai compat client
        # Ollama openai-compat doesn't expose format=json, so we call via base URL directly
        import urllib.request
        import urllib.error
        ollama_base = self.providers.get("ollama_base", "http://localhost:11434")
        payload = json.dumps({
            "model": self.model_ollama,
            "messages": self.unified_history,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.85, "num_predict": 2048}
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
        logger.info(f"JSON response received from Ollama ({self.model_ollama})")
        return reply

    def chat(self, message: str) -> str:
        """
        Unified chat with priority fallback:
          1. Ollama (local Llama — primary)
          2. GitHub Models (cloud)
          3. Gemini (cloud)
          4. OpenAI (cloud)
        """
        errors = []

        if self.ollama_client:
            try:
                return self._chat_openai_compatible(self.ollama_client, self.model_ollama, message, "Ollama")
            except Exception as e:
                errors.append(f"Ollama: {e}")
                logger.error(f"Ollama failed. Details: {e}", exc_info=True)
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

    def chat_json(self, message: str) -> str:
        """
        JSON-mode chat for group/party channels.
        Tries Ollama native JSON format first, then falls back to standard chat().
        Always returns raw text (caller uses parse_response() to decode it).
        """
        try:
            return self._chat_ollama_json(message)
        except Exception as e:
            logger.warning(f"Ollama JSON mode failed ({e}), falling back to standard chat.")
            return self.chat(message)

    def parse_response(self, text: str) -> list:
        """
        Safely parses an AI response into a list of {speaker, content} dicts.
        Tries JSON first, falls back to legacy heuristic splitter.
        Always returns a list (may be empty).
        """
        if not text:
            return []
        
        # Step 1: Try to extract a JSON array from the response
        # Sometimes the model wraps JSON in markdown code fences
        text_stripped = text.strip()
        # Strip markdown code fences if present
        if text_stripped.startswith("```"):
            lines = text_stripped.split("\n")
            text_stripped = "\n".join(lines[1:-1]).strip()
        
        # Try parsing as JSON
        try:
            data = json.loads(text_stripped)
            if isinstance(data, list):
                results = []
                for item in data:
                    if isinstance(item, dict) and "speaker" in item and "content" in item:
                        speaker = str(item["speaker"]).strip()
                        content = str(item["content"]).strip()
                        if speaker and content:
                            results.append({"speaker": speaker, "content": content})
                if results:
                    logger.info(f"parse_response: JSON decoded {len(results)} block(s).")
                    return results
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Step 2: JSON failed — fall back to the legacy heuristic parser
        logger.warning("parse_response: JSON decode failed. Falling back to heuristic parser.")
        try:
            from core.formatting import parse_speaker_blocks
            from core.config import IDENTITIES
            raw_blocks = parse_speaker_blocks(text, IDENTITIES, set())
            return [{"speaker": b["speaker"], "content": b["content"]} for b in raw_blocks]
        except Exception as e:
            logger.error(f"parse_response: heuristic fallback also failed: {e}")
            # Last resort: return as a single DM block
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
