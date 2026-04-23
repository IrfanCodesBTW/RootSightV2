import asyncio
import json
import logging
import re

import google.generativeai as genai

from .errors import LLMClientError
from ...utils.config import settings

logger = logging.getLogger(__name__)

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    logger.warning("gemini_client.missing_api_key using configured fallback behavior")

model = genai.GenerativeModel(settings.GEMINI_MODEL)


def strip_fences(text: str) -> str:
    """Remove markdown code fences from LLM output without corrupting inner content."""
    text = text.strip()
    # Match ```json ... ``` or ``` ... ``` blocks, extracting inner content
    pattern = r"^```(?:json|JSON)?\s*\n?(.*?)```\s*$"
    match = re.match(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def enforce_token_budget(text: str, max_tokens: int = 3000) -> str:
    max_chars = max_tokens * 4
    if len(text) > max_chars:
        logger.warning(f"[TOKEN] Truncated: {len(text)} → {max_chars} chars")
        return text[:max_chars]
    return text


async def generate(prompt: str, max_retries: int = 3) -> dict:
    """Call Gemini and return parsed JSON dict. Raises LLMClientError on failure."""
    if not prompt or not str(prompt).strip():
        raise ValueError("Prompt must be a non-empty string.")

    prompt = enforce_token_budget(prompt)

    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.2, max_output_tokens=2048),
            )
            text = getattr(response, "text", None)
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Gemini response did not include text.")
            return json.loads(strip_fences(text))
        except json.JSONDecodeError as e:
            logger.warning("gemini_client.invalid_json attempt=%s/%s error=%s", attempt + 1, max_retries, e)
            if attempt == max_retries - 1:
                raise LLMClientError("Gemini", f"Invalid JSON after {max_retries} attempts: {e}", e)
            await asyncio.sleep(2**attempt)
        except LLMClientError:
            raise
        except Exception as e:
            logger.warning("gemini_client.request_failed attempt=%s/%s error=%s", attempt + 1, max_retries, e)
            if attempt == max_retries - 1:
                raise LLMClientError("Gemini", f"Request failed after {max_retries} attempts: {e}", e)
            await asyncio.sleep(2**attempt)
