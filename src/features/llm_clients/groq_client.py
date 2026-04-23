import asyncio
import json
import logging
from typing import Optional

from groq import Groq

from .errors import strip_fences, enforce_token_budget
from ...utils.config import settings

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.GROQ_API_KEY)

# Re-export shared utilities for backward compatibility
__all__ = ["format_json", "strip_fences", "enforce_token_budget"]


async def format_json(prompt: str, max_retries: int = 3) -> Optional[dict]:
    """Call Groq and return parsed JSON dict, or None on failure after retries."""
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
                max_tokens=1024,
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
                logger.error("groq_client.exhausted_retries returning None")
                return None
            await asyncio.sleep(2**attempt)
        except Exception as e:
            # Detect rate-limit or server errors for backoff logging
            err_str = str(e).lower()
            is_retryable = any(code in err_str for code in ("429", "503", "rate", "quota", "resource_exhausted"))
            if is_retryable:
                logger.warning(
                    "groq_client.rate_limited attempt=%s/%s error=%s backoff=%ss",
                    attempt + 1,
                    max_retries,
                    e,
                    2**attempt,
                )
            else:
                logger.warning("groq_client.request_failed attempt=%s/%s error=%s", attempt + 1, max_retries, e)
            if attempt == max_retries - 1:
                logger.error("groq_client.exhausted_retries returning None")
                return None
            await asyncio.sleep(2**attempt)
    return None
