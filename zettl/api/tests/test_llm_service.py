from unittest.mock import AsyncMock, patch, MagicMock


async def test_generate_content_returns_string():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Generated text"))]

    with patch("app.services.llm_service.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = mock_response

        from app.services.llm_service import LLMService
        service = LLMService()

        result = await service.generate("Write a haiku")

        assert result == "Generated text"
        mock_completion.assert_called_once()
