import pytest
from unittest.mock import patch, AsyncMock
import json
from rootsight.backend.llm_clients.gemini_client import generate
from rootsight.backend.llm_clients.groq_client import format_json

@pytest.mark.asyncio
async def test_gemini_client_success():
    with patch("rootsight.backend.llm_clients.gemini_client.model.generate_content") as mock_generate:
        mock_response = AsyncMock()
        mock_response.text = '```json\n{"status": "ok"}\n```'
        # generate_content is synchronous in the SDK, but we wrap it in asyncio.to_thread in our client
        # Wait, the mock needs to return the object when called synchronously by the thread
        mock_generate.return_value = mock_response
        
        result = await generate("Test prompt")
        assert result == {"status": "ok"}

@pytest.mark.asyncio
async def test_gemini_client_retry_json_error():
    with patch("rootsight.backend.llm_clients.gemini_client.model.generate_content") as mock_generate:
        mock_bad = AsyncMock()
        mock_bad.text = 'Not a json string'
        
        mock_good = AsyncMock()
        mock_good.text = '{"status": "recovered"}'
        
        mock_generate.side_effect = [mock_bad, mock_good]
        
        # Patch sleep to avoid waiting during tests
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await generate("Test prompt")
            assert result == {"status": "recovered"}
            assert mock_generate.call_count == 2

@pytest.mark.asyncio
async def test_groq_client_success():
    with patch("rootsight.backend.llm_clients.groq_client.client.chat.completions.create") as mock_create:
        mock_msg = AsyncMock()
        mock_msg.message.content = '{"groq": "ok"}'
        
        mock_choice = AsyncMock()
        mock_choice.choices = [mock_msg]
        
        mock_create.return_value = mock_choice
        
        result = await format_json("Test prompt")
        assert result == {"groq": "ok"}

@pytest.mark.asyncio
async def test_gemini_client_failure_after_retries():
    with patch("rootsight.backend.llm_clients.gemini_client.model.generate_content", side_effect=RuntimeError("offline")) as mock_generate:
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError):
                await generate("Test prompt")
        assert mock_generate.call_count == 3

@pytest.mark.asyncio
async def test_groq_client_failure_after_retries():
    with patch("rootsight.backend.llm_clients.groq_client.client.chat.completions.create", side_effect=RuntimeError("offline")) as mock_create:
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError):
                await format_json("Test prompt")
        assert mock_create.call_count == 3
