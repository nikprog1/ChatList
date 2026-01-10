"""
UNIT тесты для модуля network.py (API Providers, RequestManager).
"""

import pytest
import respx
import httpx
from unittest.mock import patch, MagicMock
from network import (
    APIProvider, OpenAIProvider, DeepSeekProvider, GroqProvider,
    OpenRouterProvider, CustomProvider, RequestManager
)
from models import Model


@pytest.fixture
def sample_model_with_key():
    """Создание тестовой модели с API-ключом."""
    model = Model(
        id=1,
        name='test-model',
        api_url='https://api.test.com/v1/chat/completions',
        api_id='TEST_API_KEY',
        provider_type='openai',
        is_active=1
    )
    # Мокаем get_api_key для этой модели
    model.get_api_key = lambda: 'test-api-key-12345'
    return model


@pytest.fixture
def sample_model_without_key():
    """Создание тестовой модели без API-ключа."""
    model = Model(
        id=2,
        name='test-model-no-key',
        api_url='https://api.test.com/v1/chat/completions',
        api_id='TEST_API_KEY',
        provider_type='openai',
        is_active=1
    )
    # Мокаем get_api_key для этой модели
    model.get_api_key = lambda: None
    return model


@pytest.mark.unit
class TestAPIProvider:
    """Тесты для базового класса APIProvider."""
    
    def test_api_provider_is_abstract(self):
        """Тест, что APIProvider - абстрактный класс."""
        with pytest.raises(TypeError):
            APIProvider()


@pytest.mark.unit
class TestOpenAIProvider:
    """Тесты для OpenAIProvider."""
    
    def test_get_headers(self, sample_model_with_key):
        """Тест формирования заголовков для OpenAI."""
        provider = OpenAIProvider()
        headers = provider.get_headers(sample_model_with_key)
        
        assert 'Authorization' in headers
        assert headers['Authorization'] == 'Bearer test-api-key-12345'
        assert headers['Content-Type'] == 'application/json'
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_success(self, sample_model_with_key):
        """Тест успешного запроса к OpenAI."""
        # Мокируем HTTP ответ
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "Это тестовый ответ от OpenAI"
                    }
                }
            ],
            "usage": {
                "total_tokens": 100
            },
            "model": "test-model"
        }
        
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        provider = OpenAIProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt",
            timeout=30
        )
        
        assert error is None
        assert response_text == "Это тестовый ответ от OpenAI"
        assert route.called
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_with_max_tokens(self, sample_model_with_key):
        """Тест запроса с max_tokens."""
        mock_response = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {"total_tokens": 50}
        }
        
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        provider = OpenAIProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt",
            timeout=30,
            max_tokens=2048
        )
        
        # Проверяем, что запрос был выполнен
        assert route.called
        assert error is None
        # Проверяем, что max_tokens был передан в payload
        if route.calls:
            request = route.calls.last.request
            import json as json_lib
            payload = json_lib.loads(request.read().decode())
            assert "max_tokens" in payload
            assert payload["max_tokens"] == 2048
    
    @pytest.mark.asyncio
    async def test_send_request_no_api_key(self, sample_model_without_key):
        """Тест запроса без API-ключа."""
        provider = OpenAIProvider()
        response_text, error = await provider.send_request(
            sample_model_without_key,
            "Test prompt"
        )
        
        assert response_text == ""
        assert error == "API-ключ не найден"
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_timeout(self, sample_model_with_key):
        """Тест таймаута запроса."""
        route = respx.post(sample_model_with_key.api_url).mock(
            side_effect=httpx.TimeoutException("Request timeout")
        )
        
        provider = OpenAIProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt",
            timeout=5
        )
        
        assert response_text == ""
        assert "Таймаут" in error
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_http_error_401(self, sample_model_with_key):
        """Тест обработки HTTP ошибки 401 (Unauthorized)."""
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        
        provider = OpenAIProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt"
        )
        
        assert response_text == ""
        assert "401" in error or "Unauthorized" in error or "не авторизован" in error
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_http_error_429(self, sample_model_with_key):
        """Тест обработки HTTP ошибки 429 (Too Many Requests)."""
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(429, text="Too Many Requests")
        )
        
        provider = OpenAIProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt"
        )
        
        assert response_text == ""
        assert "429" in error or "Too Many Requests" in error or "много запросов" in error


@pytest.mark.unit
class TestDeepSeekProvider:
    """Тесты для DeepSeekProvider."""
    
    def test_get_headers(self, sample_model_with_key):
        """Тест формирования заголовков для DeepSeek."""
        provider = DeepSeekProvider()
        headers = provider.get_headers(sample_model_with_key)
        
        assert 'Authorization' in headers
        assert headers['Authorization'] == 'Bearer test-api-key-12345'
        assert headers['Content-Type'] == 'application/json'
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_success(self, sample_model_with_key):
        """Тест успешного запроса к DeepSeek."""
        sample_model_with_key.api_url = 'https://api.deepseek.com/v1/chat/completions'
        
        mock_response = {
            "choices": [{"message": {"content": "DeepSeek response"}}]
        }
        
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        provider = DeepSeekProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt"
        )
        
        assert error is None
        assert response_text == "DeepSeek response"


@pytest.mark.unit
class TestGroqProvider:
    """Тесты для GroqProvider."""
    
    def test_get_headers(self, sample_model_with_key):
        """Тест формирования заголовков для Groq."""
        provider = GroqProvider()
        headers = provider.get_headers(sample_model_with_key)
        
        assert 'Authorization' in headers
        assert headers['Authorization'] == 'Bearer test-api-key-12345'
        assert headers['Content-Type'] == 'application/json'
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_success(self, sample_model_with_key):
        """Тест успешного запроса к Groq."""
        sample_model_with_key.api_url = 'https://api.groq.com/openai/v1/chat/completions'
        
        mock_response = {
            "choices": [{"message": {"content": "Groq response"}}]
        }
        
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        provider = GroqProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt"
        )
        
        assert error is None
        assert response_text == "Groq response"


@pytest.mark.unit
class TestOpenRouterProvider:
    """Тесты для OpenRouterProvider."""
    
    def test_get_headers(self, sample_model_with_key):
        """Тест формирования заголовков для OpenRouter."""
        provider = OpenRouterProvider()
        headers = provider.get_headers(sample_model_with_key)
        
        assert 'Authorization' in headers
        assert headers['Authorization'] == 'Bearer test-api-key-12345'
        assert headers['Content-Type'] == 'application/json'
        assert 'HTTP-Referer' in headers or 'X-Title' in headers
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_success(self, sample_model_with_key):
        """Тест успешного запроса к OpenRouter."""
        sample_model_with_key.api_url = 'https://openrouter.ai/api/v1/chat/completions'
        sample_model_with_key.provider_type = 'openrouter'
        
        mock_response = {
            "choices": [{"message": {"content": "OpenRouter response"}}]
        }
        
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        provider = OpenRouterProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt"
        )
        
        assert error is None
        assert response_text == "OpenRouter response"
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_max_tokens_default(self, sample_model_with_key):
        """Тест использования max_tokens по умолчанию (2048) для OpenRouter."""
        sample_model_with_key.api_url = 'https://openrouter.ai/api/v1/chat/completions'
        sample_model_with_key.provider_type = 'openrouter'
        
        mock_response = {"choices": [{"message": {"content": "Response"}}]}
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        provider = OpenRouterProvider()
        response_text, error = await provider.send_request(sample_model_with_key, "Test", max_tokens=None)
        
        # Проверяем, что запрос был выполнен
        assert route.called
        assert error is None
        # Проверяем, что max_tokens был установлен в 2048 по умолчанию
        if route.calls:
            request = route.calls.last.request
            import json as json_lib
            payload = json_lib.loads(request.read().decode())
            assert "max_tokens" in payload
            assert payload["max_tokens"] == 2048
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_error_402(self, sample_model_with_key):
        """Тест обработки ошибки 402 (Payment Required) для OpenRouter."""
        sample_model_with_key.api_url = 'https://openrouter.ai/api/v1/chat/completions'
        
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(402, json={"error": "Insufficient credits"})
        )
        
        provider = OpenRouterProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt"
        )
        
        assert response_text == ""
        assert "402" in error or "кредитов" in error or "max_tokens" in error
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_error_404(self, sample_model_with_key):
        """Тест обработки ошибки 404 (Not Found) для OpenRouter."""
        sample_model_with_key.api_url = 'https://openrouter.ai/api/v1/chat/completions'
        
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(404, text="Model not found")
        )
        
        provider = OpenRouterProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt"
        )
        
        assert response_text == ""
        assert "404" in error or "не найдена" in error.lower()
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_error_429(self, sample_model_with_key):
        """Тест обработки ошибки 429 (Too Many Requests) для OpenRouter."""
        sample_model_with_key.api_url = 'https://openrouter.ai/api/v1/chat/completions'
        
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(429, headers={"Retry-After": "60"}, text="Too Many Requests")
        )
        
        provider = OpenRouterProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt"
        )
        
        assert response_text == ""
        assert "429" in error or "много запросов" in error.lower() or "лимит" in error.lower()


@pytest.mark.unit
class TestCustomProvider:
    """Тесты для CustomProvider."""
    
    def test_get_headers(self, sample_model_with_key):
        """Тест формирования заголовков для Custom."""
        provider = CustomProvider()
        headers = provider.get_headers(sample_model_with_key)
        
        assert 'Authorization' in headers or 'Content-Type' in headers
        assert headers.get('Content-Type') == 'application/json'
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request_success(self, sample_model_with_key):
        """Тест успешного запроса к Custom API."""
        mock_response = {"response": "Custom API response"}
        
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        provider = CustomProvider()
        response_text, error = await provider.send_request(
            sample_model_with_key,
            "Test prompt"
        )
        
        assert error is None
        assert response_text == "Custom API response"


@pytest.mark.unit
class TestRequestManager:
    """Тесты для RequestManager."""
    
    def test_request_manager_initialization(self, temp_db):
        """Тест инициализации RequestManager."""
        manager = RequestManager(temp_db)
        assert manager.db == temp_db
        assert 'openai' in manager.providers
        assert 'deepseek' in manager.providers
        assert 'groq' in manager.providers
        assert 'openrouter' in manager.providers
        assert 'custom' in manager.providers
    
    def test_get_provider(self, temp_db):
        """Тест получения провайдера по типу."""
        manager = RequestManager(temp_db)
        
        provider = manager.get_provider('openai')
        assert isinstance(provider, OpenAIProvider)
        
        provider = manager.get_provider('deepseek')
        assert isinstance(provider, DeepSeekProvider)
        
        provider = manager.get_provider('groq')
        assert isinstance(provider, GroqProvider)
        
        provider = manager.get_provider('openrouter')
        assert isinstance(provider, OpenRouterProvider)
        
        provider = manager.get_provider('custom')
        assert isinstance(provider, CustomProvider)
        
        # Неизвестный тип должен вернуть CustomProvider
        provider = manager.get_provider('unknown')
        assert isinstance(provider, CustomProvider)
    
    def test_get_timeout_from_db(self, temp_db):
        """Тест получения таймаута из БД."""
        temp_db.set_setting('request_timeout', '60')
        
        manager = RequestManager(temp_db)
        timeout = manager.get_timeout()
        
        assert timeout == 60
    
    def test_get_timeout_default(self, temp_db):
        """Тест получения таймаута по умолчанию."""
        manager = RequestManager(temp_db)
        timeout = manager.get_timeout()
        
        # Должно быть значение по умолчанию (30) или из БД
        assert isinstance(timeout, int)
        assert timeout > 0
    
    def test_get_max_tokens_from_db(self, temp_db):
        """Тест получения max_tokens из БД."""
        temp_db.set_setting('max_tokens', '2048')
        
        manager = RequestManager(temp_db)
        max_tokens = manager.get_max_tokens()
        
        assert max_tokens == 2048
    
    def test_get_max_tokens_default(self, temp_db):
        """Тест получения max_tokens по умолчанию."""
        manager = RequestManager(None)
        max_tokens = manager.get_max_tokens()
        
        assert max_tokens is None
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_request(self, temp_db, sample_model_with_key):
        """Тест отправки запроса через RequestManager."""
        sample_model_with_key.provider_type = 'openai'
        
        mock_response = {
            "choices": [{"message": {"content": "Manager response"}}]
        }
        
        route = respx.post(sample_model_with_key.api_url).mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        manager = RequestManager(temp_db)
        response_text, error = await manager.send_request(
            sample_model_with_key,
            "Test prompt"
        )
        
        assert error is None
        assert response_text == "Manager response"
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_batch_requests(self, temp_db):
        """Тест массовой отправки запросов."""
        # Создаем несколько моделей
        model1 = Model(1, 'model1', 'https://api.test.com/v1', 'KEY1', 'openai')
        model1.get_api_key = lambda: 'key1'
        model2 = Model(2, 'model2', 'https://api.test.com/v2', 'KEY2', 'openai')
        model2.get_api_key = lambda: 'key2'
        
        # Мокируем ответы
        route1 = respx.post('https://api.test.com/v1').mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Response 1"}}]})
        )
        route2 = respx.post('https://api.test.com/v2').mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Response 2"}}]})
        )
        
        manager = RequestManager(temp_db)
        results = await manager.send_batch_requests([model1, model2], "Test prompt")
        
        assert len(results) == 2
        assert 'model1' in results
        assert 'model2' in results
        assert results['model1'][0] == "Response 1"
        assert results['model2'][0] == "Response 2"
    
    @respx.mock
    @pytest.mark.asyncio
    async def test_send_batch_requests_with_error(self, temp_db):
        """Тест массовой отправки с частичными ошибками."""
        model1 = Model(1, 'model1', 'https://api.test.com/v1', 'KEY1', 'openai')
        model1.get_api_key = lambda: 'key1'
        model2 = Model(2, 'model2', 'https://api.test.com/v2', 'KEY2', 'openai')
        model2.get_api_key = lambda: None  # Нет ключа
        
        route1 = respx.post('https://api.test.com/v1').mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Success"}}]})
        )
        
        manager = RequestManager(temp_db)
        results = await manager.send_batch_requests([model1, model2], "Test prompt")
        
        assert len(results) == 2
        assert 'model1' in results
        assert 'model2' in results
        assert results['model1'][1] is None  # Успех
        assert results['model2'][1] is not None  # Ошибка
