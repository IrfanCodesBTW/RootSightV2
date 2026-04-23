import pytest
from unittest.mock import patch, AsyncMock
from src.features.llm_clients.gemini_client import generate
from src.features.llm_clients.groq_client import format_json
from src.features.llm_clients.errors import LLMClientError, strip_fences, enforce_token_budget


# ── strip_fences tests ──────────────────────────────────────────────────────────


def test_strip_fences_empty():
    assert strip_fences("") == ""
    assert strip_fences("   ") == ""


def test_strip_fences_no_fences():
    assert strip_fences('{"key": "value"}') == '{"key": "value"}'


def test_strip_fences_json():
    assert strip_fences('```json\n{"key": "value"}\n```') == '{"key": "value"}'


def test_strip_fences_python():
    assert strip_fences('```python\nprint("hello")\n```') == 'print("hello")'


def test_strip_fences_no_language_tag():
    assert strip_fences('```\n{"key": "value"}\n```') == '{"key": "value"}'


def test_strip_fences_no_newline_after_tag():
    result = strip_fences('```json{"key": "value"}```')
    assert '{"key": "value"}' in result


# ── enforce_token_budget tests ───────────────────────────────────────────────────


def test_enforce_token_budget_short_text():
    assert enforce_token_budget("hello", 100) == "hello"


def test_enforce_token_budget_empty():
    assert enforce_token_budget("", 100) == ""


def test_enforce_token_budget_truncates():
    text = "a" * 5000
    result = enforce_token_budget(text, max_tokens=1000)
    assert len(result) == 4000  # 1000 * 4 chars/token


def test_enforce_token_budget_raises_on_extreme_truncation():
    text = "a" * 100000
    with pytest.raises(ValueError, match="remove"):
        enforce_token_budget(text, max_tokens=100)


# ── Gemini client tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_gemini_client_success():
    with patch("src.features.llm_clients.gemini_client.model.generate_content") as mock_generate:
        mock_response = AsyncMock()
        mock_response.text = '```json\n{"status": "ok"}\n```'
        mock_generate.return_value = mock_response

        result = await generate("Test prompt")
        assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_gemini_client_retry_json_error():
    with patch("src.features.llm_clients.gemini_client.model.generate_content") as mock_generate:
        mock_bad = AsyncMock()
        mock_bad.text = "Not a json string"

        mock_good = AsyncMock()
        mock_good.text = '{"status": "recovered"}'

        mock_generate.side_effect = [mock_bad, mock_good]

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await generate("Test prompt")
            assert result == {"status": "recovered"}
            assert mock_generate.call_count == 2


@pytest.mark.asyncio
async def test_gemini_client_failure_after_retries():
    with patch(
        "src.features.llm_clients.gemini_client.model.generate_content", side_effect=RuntimeError("offline")
    ) as mock_generate:
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(LLMClientError):
                await generate("Test prompt")
        assert mock_generate.call_count == 3


# ── Groq client tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_groq_client_success():
    with patch("src.features.llm_clients.groq_client.client.chat.completions.create") as mock_create:
        mock_msg = AsyncMock()
        mock_msg.message.content = '{"groq": "ok"}'

        mock_choice = AsyncMock()
        mock_choice.choices = [mock_msg]

        mock_create.return_value = mock_choice

        result = await format_json("Test prompt")
        assert result == {"groq": "ok"}


@pytest.mark.asyncio
async def test_groq_client_failure_returns_none():
    with patch(
        "src.features.llm_clients.groq_client.client.chat.completions.create", side_effect=RuntimeError("offline")
    ) as mock_create:
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await format_json("Test prompt")
            assert result is None
        assert mock_create.call_count == 3
