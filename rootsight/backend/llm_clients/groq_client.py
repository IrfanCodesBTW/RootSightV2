import asyncio
import json
import logging

from groq import Groq

from ..config import settings

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.GROQ_API_KEY)


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```", 2)
        if len(parts) >= 2:
            text = parts[1]
        text = text.replace("json", "", 1).strip()
    return text


async def format_json(prompt: str, max_retries: int = 3) -> dict:
    if not prompt or not str(prompt).strip():
        raise ValueError("Prompt must be a non-empty string.")

    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=settings.GROQ_MODEL,
                temperature=0.1,
                max_tokens=1024
            )
            choices = getattr(response, "choices", [])
            if not choices:
                raise ValueError("Groq response did not include choices.")
            content = getattr(choices[0].message, "content", None)
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Groq response did not include message content.")
            return json.loads(_strip_json_fences(content))
        except json.JSONDecodeError as e:
            logger.warning("groq_client.invalid_json attempt=%s/%s error=%s", attempt + 1, max_retries, e)
            if attempt == max_retries - 1:
                raise ValueError(f"Groq returned invalid JSON after {max_retries} attempts: {e}")
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.warning("groq_client.request_failed attempt=%s/%s error=%s", attempt + 1, max_retries, e)
            if attempt == max_retries - 1:
                raise RuntimeError(f"Groq request failed after {max_retries} attempts: {e}") from e
            await asyncio.sleep(2 ** attempt)
