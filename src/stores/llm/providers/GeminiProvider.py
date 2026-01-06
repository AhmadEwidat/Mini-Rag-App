from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums  # reuse simple role names (system/user/assistant)
from google import genai
import logging


class GeminiProvider(LLMInterface):

    def __init__(self, api_key: str,
                       default_input_max_characters: int = 1000,
                       default_generation_max_output_tokens: int = 1000,
                       default_generation_temperature: float = 0.1):

        self.api_key = api_key

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None

        # google-genai client
        self.client = genai.Client(api_key=self.api_key)

        # Reuse OpenAI-style enums to be compatible with existing chat_history building
        self.enums = OpenAIEnums
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()

    def _flatten_chat_history(self, chat_history: list) -> str:
        if not chat_history:
            return ""
        # Join prior messages into a simple preamble; Gemini supports system instructions separately,
        # but for simplicity we prepend them to the user content.
        parts = []
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content")
            if not content:
                continue
            parts.append(f"[{role}] {content}")
        return "\n".join(parts)

    def generate_text(self, prompt: str, chat_history: list = [], max_output_tokens: int = None,
                      temperature: float = None):

        if not self.client:
            self.logger.error("Gemini client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model for Gemini was not set")
            return None

        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        # Prepare a single prompt string from history + current prompt
        preamble = self._flatten_chat_history(chat_history)
        full_contents = f"{preamble}\n[ user ] {self.process_text(prompt)}" if preamble else self.process_text(prompt)

        try:
            response = self.client.models.generate_content(
                model=self.generation_model_id,
                contents=full_contents,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                }
            )
        except Exception as exc:
            self.logger.exception("Gemini generate_text failed: %s", exc)
            return None

        try:
            return getattr(response, "text", None)
        except Exception:
            return None

    def embed_text(self, text: str, document_type: str = None):

        if not self.client:
            self.logger.error("Gemini client was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embedding model for Gemini was not set")
            return None

        try:
            # google-genai embeddings
            result = self.client.models.embed_content(
                model=self.embedding_model_id,
                content=self.process_text(text),
            )
        except Exception as exc:
            self.logger.exception("Gemini embed_text failed: %s", exc)
            return None

        # The result typically contains a dict with embeddings.values
        try:
            values = None
            if hasattr(result, "embedding") and hasattr(result.embedding, "values"):
                values = result.embedding.values
            elif isinstance(result, dict):
                # defensive fallback
                values = result.get("embedding", {}).get("values")
            return values
        except Exception:
            return None

    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": self.process_text(prompt)
        }








