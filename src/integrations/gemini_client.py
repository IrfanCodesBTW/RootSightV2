"""
RootSight — Gemini LLM Client

Wraps the Google GenAI SDK with retry logic, structured output,
and token tracking.
"""

from __future__ import annotations
import json
import time
from typing import Optional, Type

from google import genai
from google.genai import types
from pydantic import BaseModel

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("integrations.gemini")


class GeminiClient:
    """
    Wrapper around the Google GenAI SDK for structured LLM calls.

    Features:
        - Retry with exponential backoff
        - Structured JSON output via response_schema
        - Token usage tracking
    """

    def __init__(self):
        if not settings.has_gemini_key:
            logger.warning("No Gemini API key configured — LLM calls will fail")
            self._client = None
        else:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = settings.GEMINI_MODEL
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        response_schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.3,
    ) -> dict | str:
        """
        Generate a response from Gemini.

        Args:
            prompt: The user prompt to send.
            system_instruction: System-level instruction for the model.
            response_schema: Optional Pydantic model to enforce structured JSON output.
            temperature: Generation temperature (lower = more deterministic).

        Returns:
            Parsed dict if response_schema is provided, otherwise raw text string.

        Raises:
            RuntimeError: If all retry attempts fail.
        """
        if not self.is_available:
            raise RuntimeError("Gemini client not initialized — check GEMINI_API_KEY")

        config_kwargs = {"temperature": temperature}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if response_schema:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema

        config = types.GenerateContentConfig(**config_kwargs)

        last_error = None
        for attempt in range(1, settings.LLM_RETRY_ATTEMPTS + 1):
            try:
                logger.info(f"Gemini call attempt {attempt}/{settings.LLM_RETRY_ATTEMPTS}")
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=config,
                )

                # Track tokens
                if response.usage_metadata:
                    self._total_input_tokens += response.usage_metadata.prompt_token_count or 0
                    self._total_output_tokens += response.usage_metadata.candidates_token_count or 0

                text = response.text
                if response_schema:
                    return json.loads(text)
                return text

            except Exception as e:
                last_error = e
                delay = settings.LLM_RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(f"Gemini call failed (attempt {attempt}): {e}. Retrying in {delay}s...")
                if attempt < settings.LLM_RETRY_ATTEMPTS:
                    time.sleep(delay)

        raise RuntimeError(f"Gemini call failed after {settings.LLM_RETRY_ATTEMPTS} attempts: {last_error}")

    @property
    def token_usage(self) -> dict:
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
        }


# Module-level singleton
gemini_client = GeminiClient()
