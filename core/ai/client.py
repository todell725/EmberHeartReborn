import logging
from pathlib import Path
import google.generativeai as genai

from .providers import initialize_providers, ROOT_DIR
from .rag import WorldContextManager
from .prompts import generate_eh_system_prompt

logger = logging.getLogger("EH_Brain")

class EHClient:
    def __init__(self, model_gemini="gemini-3-flash-preview", model_openai="gpt-4o", model_github="gpt-4o"):
        self.eh_dir = ROOT_DIR / "EmberHeartReborn"
        self.world_manager = WorldContextManager(self.eh_dir)
        
        # Initialize structured providers
        self.providers = initialize_providers(model_gemini, model_openai, model_github)
        
        # Set instance variables from providers dictionary
        self.github_client = self.providers["github_client"]
        self.openai_client = self.providers["openai_client"]
        self.model_github = self.providers["model_github"]
        self.model_openai = self.providers["model_openai"]
        self.model_gemini = self.providers["model_gemini"]
        self.keys = self.providers["keys"]

        # Initialize System Prompt
        self.system_prompt = generate_eh_system_prompt(self.eh_dir)
        
        # Finish Gemini Initialization (requires system prompt)
        self.gemini_chat = None
        self.gemini_model = None
        if self.keys["GEMINI"]:
            self.gemini_model = genai.GenerativeModel(
                model_name=self.model_gemini,
                system_instruction=self.system_prompt,
                generation_config=genai.GenerationConfig(temperature=1.0, max_output_tokens=8192)
            )
            self.gemini_chat = self.gemini_model.start_chat(history=[])
        
        # Unified History (List of dicts for OpenAI/GitHub)
        self.unified_history = [{"role": "system", "content": self.system_prompt}]

    def _trim_history(self, max_messages: int = 10):
        """Keep the chat history lean to avoid token limits."""
        if len(self.unified_history) > max_messages + 1:
            self.unified_history = [self.unified_history[0]] + self.unified_history[-(max_messages):]

    def _chat_openai_compatible(self, client, model: str, message: str, provider_name: str) -> str:
        """Generic handler with RAG context injection."""
        if not client:
            raise ValueError(f"{provider_name} Client not configured.")
        
        # 1. Get RAG Context & Briefing
        briefing = self.world_manager.get_sovereign_briefing()
        rag_context = self.world_manager.get_relevant_context(message)
        enhanced_message = message + briefing + rag_context if (briefing or rag_context) else message

        # 2. History Management
        if not self.unified_history or self.unified_history[-1]["role"] != "user" or self.unified_history[-1]["content"] != enhanced_message:
             self.unified_history.append({"role": "user", "content": enhanced_message})
        
        self._trim_history(max_messages=8)

        response = client.chat.completions.create(
            model=model,
            messages=self.unified_history,
            temperature=1.0,
            max_tokens=4096
        )
        reply = response.choices[0].message.content
        self.unified_history.append({"role": "assistant", "content": reply})
        return reply

    def chat(self, message: str) -> str:
        """Unified chat with auto-fallback: GitHub -> Gemini -> OpenAI."""
        errors = []
        
        if self.github_client:
            try:
                return self._chat_openai_compatible(self.github_client, self.model_github, message, "GitHub")
            except Exception as e:
                error_str = str(e)
                if "413" in error_str or "too many tokens" in error_str.lower():
                    logger.warning("GitHub limit reached (413). Trimming further...")
                    self._trim_history(max_messages=4)
                logger.warning(f"GitHub failed: {e}. Falling back...")
                errors.append(f"GitHub: {e}")
        
        if self.gemini_chat:
            try:
                # Gemini handles long context better, but we still inject RAG for accuracy
                briefing = self.world_manager.get_sovereign_briefing()
                rag_context = self.world_manager.get_relevant_context(message)
                enhanced_message = message + briefing + rag_context if (briefing or rag_context) else message
                response = self.gemini_chat.send_message(enhanced_message)
                return response.text
            except Exception as e:
                logger.warning(f"Gemini failed: {e}. Falling back...")
                errors.append(f"Gemini: {e}")

        if self.openai_client:
            try:
                return self._chat_openai_compatible(self.openai_client, self.model_openai, message, "OpenAI")
            except Exception as e:
                logger.error(f"OpenAI Failed: {e}")
                errors.append(f"OpenAI: {e}")
                    
        error_summary = " | ".join(errors) if errors else "No providers configured."
        return f"❌ All Brains Failed. Details: {error_summary}"

    def clear_history(self):
        if self.gemini_chat:
            self.gemini_chat = self.gemini_model.start_chat(history=[])
        self.unified_history = [{"role": "system", "content": self.system_prompt}]
