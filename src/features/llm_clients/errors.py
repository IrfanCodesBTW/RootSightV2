"""Shared error types and utilities for LLM clients."""

import logging
import re

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Raised when an LLM client request fails after all retries."""

    def __init__(self, client_name: str, message: str, cause: Exception | None = None):
        self.client_name = client_name
        super().__init__(f"[{client_name}] {message}")
        if cause:
            self.__cause__ = cause


def strip_fences(text: str) -> str:
    """Remove markdown code fences from LLM output without corrupting inner content.

    Handles edge cases:
    - Empty string
    - Fences with any language tag (```json, ```python, ```bash, etc.)
    - Fences without newlines after the tag
    - Nested fences (only strips outermost)
    """
    if not text or not text.strip():
        return ""

    text = text.strip()

    # Match ```<optional-lang> ... ``` blocks, extracting inner content
    # Supports any language tag (json, python, bash, etc.) or no tag
    pattern = r"^```(?:\w+)?\s*\n?(.*?)```\s*$"
    match = re.match(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return text


def enforce_token_budget(text: str, max_tokens: int = 3000) -> str:
    """Truncate text to fit within a token budget (approximated at 4 chars/token).

    Raises ValueError if truncation would remove >80% of content.
    """
    if not text:
        return ""

    max_chars = max_tokens * 4
    if len(text) > max_chars:
        removed_pct = (len(text) - max_chars) / len(text) * 100
        if removed_pct > 80:
            logger.error(
                "enforce_token_budget.excessive_truncation original=%d max=%d removed_pct=%.1f%%",
                len(text),
                max_chars,
                removed_pct,
            )
            raise ValueError(
                f"Token budget truncation would remove {removed_pct:.0f}% of content "
                f"({len(text)} chars → {max_chars} chars). "
                f"Input is too large for max_tokens={max_tokens}."
            )
        logger.warning(
            "enforce_token_budget.truncated original=%d max=%d removed_pct=%.1f%%",
            len(text),
            max_chars,
            removed_pct,
        )
        return text[:max_chars]
    return text
