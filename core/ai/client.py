import logging
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
            f"You are {self.npc_name}. You are engaged in a private, 1-on-1 direct message with Kaelrath (the user).\n"
            f"### ROLEPLAY PROTOCOL:\n"
            f"1. You must strictly and exclusively roleplay as {self.npc_name} using the supplied lore.\n"
            f"2. You are a living inhabitant of the world, NOT an assistant or advisor.\n"
            f"3. Do NOT mention mechanics, file names, or 'injected context'.\n"
            f"4. Speak directly in character, using your personality, motivations, and secrets.\n"
            f"5. **DIALOGUE SOVEREIGNTY**: NEVER describe the actions, thoughts, or dialogue of King Kaelrath. Focus ONLY on your own physical presence and internal state. Do NOT 'god-mode' the user.\n"
            f"6. **NO META**: Do not repeat the user's prompt or add OOC commentary.\n\n"
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
        rag_context = self.world_manager.get_relevant_context(message)
        enhanced_message = message + briefing + rag_context if (briefing or rag_context) else message

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
        rag_context = self.world_manager.get_relevant_context(message)
        enhanced = message + briefing + rag_context if (briefing or rag_context) else message
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
