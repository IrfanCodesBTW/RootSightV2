import asyncio
import json
import logging

import google.generativeai as genai

from ..config import settings

logger = logging.getLogger(__name__)

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    logger.warning("gemini_client.missing_api_key using configured fallback behavior")

model = genai.GenerativeModel(settings.GEMINI_MODEL)


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```", 2)
        if len(parts) >= 2:
            text = parts[1]
        text = text.replace("json", "", 1).strip()
    return text


async def generate(prompt: str, max_retries: int = 3) -> dict:
    if not prompt or not str(prompt).strip():
        raise ValueError("Prompt must be a non-empty string.")

    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,       # Low temp for structured reasoning
                    max_output_tokens=2048
                )
            )
            text = getattr(response, "text", None)
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Gemini response did not include text.")
            return json.loads(_strip_json_fences(text))
        except json.JSONDecodeError as e:
            logger.warning("gemini_client.invalid_json attempt=%s/%s error=%s", attempt + 1, max_retries, e)
            if attempt == max_retries - 1:
                raise ValueError(f"Gemini returned invalid JSON after {max_retries} attempts: {e}")
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.warning("gemini_client.request_failed attempt=%s/%s error=%s", attempt + 1, max_retries, e)
            if attempt == max_retries - 1:
                raise RuntimeError(f"Gemini request failed after {max_retries} attempts: {e}") from e
            await asyncio.sleep(2 ** attempt)
