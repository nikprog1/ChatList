"""
Модуль для отправки запросов к API нейросетей.
Поддерживает работу с разными провайдерами и асинхронные запросы.
"""

import json
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Tuple
import httpx
from models import Model

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIProvider(ABC):
    """Базовый класс для унификации работы с разными API провайдерами."""
    
    @abstractmethod
    async def send_request(self, model: Model, prompt: str, timeout: int = 30, max_tokens: Optional[int] = None) -> Tuple[str, Optional[str]]:
        """
        Отправка запроса к API.
        
        Args:
            model: Модель для отправки запроса
            prompt: Текст промта
            timeout: Таймаут запроса в секундах
            max_tokens: Максимальное количество токенов в ответе (None = не ограничивать)
        
        Returns:
            Кортеж (response_text, error_message)
            response_text - текст ответа, error_message - сообщение об ошибке (если есть)
        """
        pass
    
    @abstractmethod
    def get_headers(self, model: Model) -> Dict[str, str]:
        """
        Получение заголовков HTTP-запроса.
        
        Args:
            model: Модель для запроса
        
        Returns:
            Словарь с заголовками
        """
        pass
    
    def log_request(self, model: Model, prompt: str, response: Optional[str] = None, error: Optional[str] = None):
        """
        Логирование запроса.
        
        Args:
            model: Модель
            prompt: Промт
            response: Ответ (если есть)
            error: Ошибка (если есть)
        """
        if error:
            logger.error(f"[{model.name}] Ошибка: {error}")
            logger.debug(f"[{model.name}] Промт: {prompt[:100]}...")
        else:
            logger.info(f"[{model.name}] Запрос успешен")
            logger.debug(f"[{model.name}] Промт: {prompt[:100]}...")
            logger.debug(f"[{model.name}] Ответ: {response[:200] if response else 'Нет ответа'}...")


class OpenAIProvider(APIProvider):
    """Провайдер для OpenAI API."""
    
    async def send_request(self, model: Model, prompt: str, timeout: int = 30, max_tokens: Optional[int] = None) -> Tuple[str, Optional[str]]:
        """Отправка запроса к OpenAI API."""
        api_key = model.get_api_key()
        if not api_key:
            return "", "API-ключ не найден"
        
        headers = self.get_headers(model)
        payload = {
            "model": model.name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    model.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Извлечение текста ответа из структуры OpenAI
                response_text = ""
                if "choices" in data and len(data["choices"]) > 0:
                    response_text = data["choices"][0]["message"]["content"]
                
                metadata = json.dumps({
                    "tokens_used": data.get("usage", {}).get("total_tokens"),
                    "model": data.get("model")
                })
                
                self.log_request(model, prompt, response_text)
                return response_text, None
                
        except httpx.TimeoutException:
            error = f"Таймаут запроса ({timeout} сек)"
            self.log_request(model, prompt, error=error)
            return "", error
        except httpx.HTTPStatusError as e:
            # Улучшенная обработка ошибок
            error_text = e.response.text
            try:
                error_data = e.response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_text = error_data["error"]["message"]
            except:
                pass
            error = f"HTTP ошибка {e.response.status_code}: {error_text[:300]}"
            self.log_request(model, prompt, error=error)
            return "", error
        except Exception as e:
            error = f"Неожиданная ошибка: {str(e)}"
            self.log_request(model, prompt, error=error)
            return "", error
    
    def get_headers(self, model: Model) -> Dict[str, str]:
        """Получение заголовков для OpenAI API."""
        api_key = model.get_api_key()
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }


class DeepSeekProvider(APIProvider):
    """Провайдер для DeepSeek API."""
    
    async def send_request(self, model: Model, prompt: str, timeout: int = 30, max_tokens: Optional[int] = None) -> Tuple[str, Optional[str]]:
        """Отправка запроса к DeepSeek API."""
        api_key = model.get_api_key()
        if not api_key:
            return "", "API-ключ не найден"
        
        headers = self.get_headers(model)
        payload = {
            "model": model.name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    model.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Извлечение текста ответа из структуры DeepSeek (аналогично OpenAI)
                response_text = ""
                if "choices" in data and len(data["choices"]) > 0:
                    response_text = data["choices"][0]["message"]["content"]
                
                metadata = json.dumps({
                    "tokens_used": data.get("usage", {}).get("total_tokens"),
                    "model": data.get("model")
                })
                
                self.log_request(model, prompt, response_text)
                return response_text, None
                
        except httpx.TimeoutException:
            error = f"Таймаут запроса ({timeout} сек)"
            self.log_request(model, prompt, error=error)
            return "", error
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            try:
                error_data = e.response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_text = error_data["error"]["message"]
            except:
                pass
            error = f"HTTP ошибка {e.response.status_code}: {error_text[:300]}"
            self.log_request(model, prompt, error=error)
            return "", error
        except Exception as e:
            error = f"Неожиданная ошибка: {str(e)}"
            self.log_request(model, prompt, error=error)
            return "", error
    
    def get_headers(self, model: Model) -> Dict[str, str]:
        """Получение заголовков для DeepSeek API."""
        api_key = model.get_api_key()
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }


class GroqProvider(APIProvider):
    """Провайдер для Groq API."""
    
    async def send_request(self, model: Model, prompt: str, timeout: int = 30, max_tokens: Optional[int] = None) -> Tuple[str, Optional[str]]:
        """Отправка запроса к Groq API."""
        api_key = model.get_api_key()
        if not api_key:
            return "", "API-ключ не найден"
        
        headers = self.get_headers(model)
        payload = {
            "model": model.name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    model.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Извлечение текста ответа из структуры Groq (аналогично OpenAI)
                response_text = ""
                if "choices" in data and len(data["choices"]) > 0:
                    response_text = data["choices"][0]["message"]["content"]
                
                metadata = json.dumps({
                    "tokens_used": data.get("usage", {}).get("total_tokens"),
                    "model": data.get("model")
                })
                
                self.log_request(model, prompt, response_text)
                return response_text, None
                
        except httpx.TimeoutException:
            error = f"Таймаут запроса ({timeout} сек)"
            self.log_request(model, prompt, error=error)
            return "", error
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            try:
                error_data = e.response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_text = error_data["error"]["message"]
            except:
                pass
            error = f"HTTP ошибка {e.response.status_code}: {error_text[:300]}"
            self.log_request(model, prompt, error=error)
            return "", error
        except Exception as e:
            error = f"Неожиданная ошибка: {str(e)}"
            self.log_request(model, prompt, error=error)
            return "", error
    
    def get_headers(self, model: Model) -> Dict[str, str]:
        """Получение заголовков для Groq API."""
        api_key = model.get_api_key()
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }


class OpenRouterProvider(APIProvider):
    """Провайдер для OpenRouter API."""
    
    async def send_request(self, model: Model, prompt: str, timeout: int = 30, max_tokens: Optional[int] = None) -> Tuple[str, Optional[str]]:
        """Отправка запроса к OpenRouter API."""
        api_key = model.get_api_key()
        if not api_key:
            return "", "API-ключ не найден"
        
        headers = self.get_headers(model)
        payload = {
            "model": model.name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        # Добавляем max_tokens, если указан (важно для избежания ошибки 402)
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        else:
            # Для OpenRouter по умолчанию устанавливаем меньшее ограничение для бесплатных аккаунтов
            # Бесплатные аккаунты обычно имеют лимит ~5000 токенов
            payload["max_tokens"] = 2048  # Более безопасное значение по умолчанию для бесплатных аккаунтов
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    model.api_url,
                    headers=headers,
                    json=payload
                )
                
                # Обработка ошибок перед raise_for_status для более понятных сообщений
                if response.status_code == 402:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", "")
                        if "credits" in error_msg.lower() or "max_tokens" in error_msg.lower():
                            # Извлекаем понятное сообщение
                            error = f"Недостаточно кредитов или слишком много токенов. Попробуйте уменьшить max_tokens в настройках.\n\nДетали: {error_msg[:200]}"
                        else:
                            error = f"Ошибка 402: {error_msg[:200]}"
                    except:
                        error = f"HTTP ошибка 402: Недостаточно кредитов. Проверьте баланс на https://openrouter.ai/settings/credits"
                    self.log_request(model, prompt, error=error)
                    return "", error
                
                # Обработка ошибки 404 (модель не найдена)
                if response.status_code == 404:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", "")
                        if "endpoints" in error_msg.lower() or "not found" in error_msg.lower():
                            error = f"Модель '{model.name}' не найдена в OpenRouter.\nВозможно, модель устарела или имеет другое название.\nПроверьте доступные модели на https://openrouter.ai/models\n\nДетали: {error_msg[:150]}"
                        else:
                            error = f"Модель '{model.name}' не найдена: {error_msg[:200]}"
                    except:
                        error = f"HTTP ошибка 404: Модель '{model.name}' не найдена. Проверьте название модели на https://openrouter.ai/models"
                    self.log_request(model, prompt, error=error)
                    return "", error
                
                # Обработка ошибки 400 (неверный ID модели)
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", "")
                        if "not a valid model" in error_msg.lower() or "invalid model" in error_msg.lower():
                            error = f"Неверный ID модели: '{model.name}'\nМодель не существует или имеет другое название.\nПроверьте доступные модели на https://openrouter.ai/models\n\nДетали: {error_msg[:150]}"
                        else:
                            error = f"HTTP ошибка 400: Неверный запрос для модели '{model.name}'\n\nДетали: {error_msg[:200]}"
                    except:
                        error = f"HTTP ошибка 400: Неверный ID модели '{model.name}'. Проверьте название на https://openrouter.ai/models"
                    self.log_request(model, prompt, error=error)
                    return "", error
                
                # Обработка ошибки 429 (Too Many Requests - слишком много запросов)
                if response.status_code == 429:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", "")
                        
                        # Проверяем, есть ли информация о времени ожидания
                        retry_after = response.headers.get("Retry-After", "")
                        if retry_after:
                            error = f"Слишком много запросов (429): Превышен лимит запросов к модели '{model.name}'.\nПодождите {retry_after} секунд перед следующим запросом.\n\nРешение: Уменьшите количество одновременных запросов или сделайте паузу между запросами.\n\nДетали: {error_msg[:150]}"
                        else:
                            error = f"Слишком много запросов (429): Превышен лимит запросов к модели '{model.name}'.\n\nРешение: Подождите несколько секунд перед повторным запросом или уменьшите количество одновременных запросов.\nПроверьте лимиты на https://openrouter.ai/settings\n\nДетали: {error_msg[:150]}" if error_msg else "Слишком много запросов (429): Превышен лимит запросов. Подождите перед повторным запросом."
                    except:
                        error = f"HTTP ошибка 429: Слишком много запросов к модели '{model.name}'.\nПодождите несколько секунд или уменьшите количество одновременных запросов.\nПроверьте лимиты на https://openrouter.ai/settings"
                    self.log_request(model, prompt, error=error)
                    return "", error
                
                response.raise_for_status()
                data = response.json()
                
                # Извлечение текста ответа из структуры OpenRouter (аналогично OpenAI)
                response_text = ""
                if "choices" in data and len(data["choices"]) > 0:
                    response_text = data["choices"][0]["message"]["content"]
                
                metadata = json.dumps({
                    "tokens_used": data.get("usage", {}).get("total_tokens"),
                    "model": data.get("model")
                })
                
                self.log_request(model, prompt, response_text)
                return response_text, None
                
        except httpx.TimeoutException:
            error = f"Таймаут запроса ({timeout} сек)"
            self.log_request(model, prompt, error=error)
            return "", error
        except httpx.HTTPStatusError as e:
            # Улучшенная обработка ошибок для всех статусов
            error_text = e.response.text
            try:
                error_data = e.response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_text = error_data["error"]["message"]
            except:
                pass
            
            error = f"HTTP ошибка {e.response.status_code}: {error_text[:300]}"
            self.log_request(model, prompt, error=error)
            return "", error
        except Exception as e:
            error = f"Неожиданная ошибка: {str(e)}"
            self.log_request(model, prompt, error=error)
            return "", error
    
    def get_headers(self, model: Model) -> Dict[str, str]:
        """Получение заголовков для OpenRouter API."""
        api_key = model.get_api_key()
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/nikprog1/ChatList",  # Опционально, для отслеживания
            "X-Title": "ChatList"  # Опционально, название приложения
        }


class CustomProvider(APIProvider):
    """Провайдер для кастомных API."""
    
    async def send_request(self, model: Model, prompt: str, timeout: int = 30, max_tokens: Optional[int] = None) -> Tuple[str, Optional[str]]:
        """Отправка запроса к кастомному API."""
        api_key = model.get_api_key()
        if not api_key:
            return "", "API-ключ не найден"
        
        headers = self.get_headers(model)
        payload = {
            "prompt": prompt,
            "model": model.name
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    model.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Простая попытка извлечь ответ (может потребоваться адаптация под конкретный API)
                response_text = data.get("response") or data.get("text") or data.get("content") or str(data)
                
                self.log_request(model, prompt, response_text)
                return response_text, None
                
        except httpx.TimeoutException:
            error = f"Таймаут запроса ({timeout} сек)"
            self.log_request(model, prompt, error=error)
            return "", error
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            try:
                error_data = e.response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_text = error_data["error"]["message"]
            except:
                pass
            error = f"HTTP ошибка {e.response.status_code}: {error_text[:300]}"
            self.log_request(model, prompt, error=error)
            return "", error
        except Exception as e:
            error = f"Неожиданная ошибка: {str(e)}"
            self.log_request(model, prompt, error=error)
            return "", error
    
    def get_headers(self, model: Model) -> Dict[str, str]:
        """Получение заголовков для кастомного API."""
        api_key = model.get_api_key()
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }


class RequestManager:
    """Класс для управления запросами к API."""
    
    def __init__(self, db=None):
        """
        Инициализация менеджера запросов.
        
        Args:
            db: Экземпляр Database (опционально, для получения настроек)
        """
        self.db = db
        self.providers = {
            'openai': OpenAIProvider(),
            'deepseek': DeepSeekProvider(),
            'groq': GroqProvider(),
            'openrouter': OpenRouterProvider(),
            'custom': CustomProvider()
        }
    
    def get_provider(self, provider_type: str) -> APIProvider:
        """
        Получение провайдера по типу.
        
        Args:
            provider_type: Тип провайдера (openai, deepseek, groq, custom)
        
        Returns:
            Экземпляр провайдера
        """
        return self.providers.get(provider_type.lower(), self.providers['custom'])
    
    def get_timeout(self) -> int:
        """Получение таймаута из настроек."""
        if self.db:
            timeout_str = self.db.get_setting('request_timeout')
            if timeout_str:
                try:
                    return int(timeout_str)
                except ValueError:
                    pass
        return 30  # Значение по умолчанию
    
    def get_max_tokens(self) -> Optional[int]:
        """Получение max_tokens из настроек."""
        if self.db:
            max_tokens_str = self.db.get_setting('max_tokens')
            if max_tokens_str:
                try:
                    return int(max_tokens_str)
                except ValueError:
                    pass
        return None  # По умолчанию не ограничиваем (API сам решает)
    
    async def send_request(self, model: Model, prompt: str) -> Tuple[str, Optional[str]]:
        """
        Отправка запроса к конкретной модели.
        
        Args:
            model: Модель для отправки запроса
            prompt: Текст промта
        
        Returns:
            Кортеж (response_text, error_message)
        """
        provider = self.get_provider(model.provider_type)
        timeout = self.get_timeout()
        max_tokens = self.get_max_tokens()
        return await provider.send_request(model, prompt, timeout, max_tokens)
    
    async def send_batch_requests(self, models: List[Model], prompt: str) -> Dict[str, Tuple[str, Optional[str]]]:
        """
        Параллельная отправка запросов к нескольким моделям.
        
        Args:
            models: Список моделей для отправки запросов
            prompt: Текст промта
        
        Returns:
            Словарь {model_name: (response_text, error_message)}
        """
        tasks = []
        model_names = []
        
        for model in models:
            tasks.append(self.send_request(model, prompt))
            model_names.append(model.name)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        batch_results = {}
        for model_name, result in zip(model_names, results):
            if isinstance(result, Exception):
                batch_results[model_name] = ("", f"Исключение: {str(result)}")
            else:
                batch_results[model_name] = result
        
        return batch_results


# Синхронные обёртки для использования в синхронном коде
def send_request_sync(model: Model, prompt: str, request_manager: RequestManager = None) -> Tuple[str, Optional[str]]:
    """
    Синхронная отправка запроса к модели.
    
    Args:
        model: Модель для отправки запроса
        prompt: Текст промта
        request_manager: Менеджер запросов (если None, создаётся новый)
    
    Returns:
        Кортеж (response_text, error_message)
    """
    if request_manager is None:
        request_manager = RequestManager()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(request_manager.send_request(model, prompt))
    finally:
        loop.close()


def send_batch_requests_sync(models: List[Model], prompt: str, request_manager: RequestManager = None) -> Dict[str, Tuple[str, Optional[str]]]:
    """
    Синхронная параллельная отправка запросов к нескольким моделям.
    
    Args:
        models: Список моделей для отправки запросов
        prompt: Текст промта
        request_manager: Менеджер запросов (если None, создаётся новый)
    
    Returns:
        Словарь {model_name: (response_text, error_message)}
    """
    if request_manager is None:
        request_manager = RequestManager()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(request_manager.send_batch_requests(models, prompt))
    finally:
        loop.close()
