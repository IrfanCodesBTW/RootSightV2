import asyncio
import json
import logging

from groq import Groq

from ...utils.config import settings

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.GROQ_API_KEY)


def strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


def enforce_token_budget(text: str, max_tokens: int = 3000) -> str:
    max_chars = max_tokens * 4
    if len(text) > max_chars:
        logger.warning(f"[TOKEN] Truncated: {len(text)} → {max_chars} chars")
        return text[:max_chars]
    return text


async def format_json(prompt: str, max_retries: int = 3) -> dict:
    if not prompt or not str(prompt).strip():
        raise ValueError("Prompt must be a non-empty string.")

    prompt = enforce_token_budget(prompt)

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
            return json.loads(strip_fences(content))
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
