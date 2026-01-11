"""
Модуль для улучшения промтов с помощью AI-ассистента.
"""

import json
import re
from typing import Dict, List, Optional, Any
from models import Model
from network import OpenRouterProvider


class PromptImprover:
    """Класс для улучшения промтов с помощью AI-ассистента."""
    
    def __init__(self):
        """Инициализация улучшателя промтов."""
        self.provider = OpenRouterProvider()
    
    def format_improvement_request(self, prompt: str) -> str:
        """
        Формирование структурированного запроса для AI-модели.
        
        Args:
            prompt: Исходный промт для улучшения
            
        Returns:
            Текст запроса для AI-модели
        """
        request = f"""Ты эксперт по написанию эффективных промтов для AI-моделей. Проанализируй следующий промт и улучши его. Отвечай на русском языке.

ИСХОДНЫЙ ПРОМТ:
{prompt}

ТВОЯ ЗАДАЧА:
1. Создай улучшенную версию промта, которая будет более четкой, конкретной и эффективной.
2. Предложи 2-3 альтернативных варианта переформулировки промта.
3. Если применимо, создай адаптации промта для разных типов задач:
   - Код: для задач программирования и работы с кодом
   - Анализ: для аналитических и исследовательских задач
   - Креатив: для креативных и художественных задач

ФОРМАТ ОТВЕТА (в JSON):
{{
    "improved": "Улучшенная версия промта",
    "alternatives": [
        "Альтернативный вариант 1",
        "Альтернативный вариант 2",
        "Альтернативный вариант 3"
    ],
    "adaptations": {{
        "code": "Адаптация для задач программирования (если применимо)",
        "analysis": "Адаптация для аналитических задач (если применимо)",
        "creative": "Адаптация для креативных задач (если применимо)"
    }}
}}

Если адаптации не применимы, оставь соответствующие поля пустыми строками.
Отвечай ТОЛЬКО в формате JSON, без дополнительных пояснений."""
        
        return request
    
    async def improve_prompt(self, prompt: str, model: Model, timeout: int = 60) -> Dict[str, Any]:
        """
        Улучшение промта с помощью AI-модели.
        
        Args:
            prompt: Исходный промт для улучшения
            model: Модель для использования при улучшении
            timeout: Таймаут запроса в секундах (по умолчанию 60)
            
        Returns:
            Словарь с результатами улучшения:
            {
                'improved': str,           # Улучшенная версия
                'alternatives': List[str],  # 2-3 варианта переформулировки
                'adaptations': {
                    'code': str,           # Адаптация для задач программирования
                    'analysis': str,       # Адаптация для аналитических задач
                    'creative': str        # Адаптация для креативных задач
                }
            }
        """
        if not prompt or not prompt.strip():
            return {
                'improved': '',
                'alternatives': [],
                'adaptations': {
                    'code': '',
                    'analysis': '',
                    'creative': ''
                },
                'error': 'Промт не может быть пустым'
            }
        
        # Формируем запрос для улучшения
        improvement_request = self.format_improvement_request(prompt)
        
        # Отправляем запрос к модели
        response_text, error = await self.provider.send_request(
            model=model,
            prompt=improvement_request,
            timeout=timeout,
            max_tokens=3000  # Больше токенов для детального ответа
        )
        
        if error:
            return {
                'improved': '',
                'alternatives': [],
                'adaptations': {
                    'code': '',
                    'analysis': '',
                    'creative': ''
                },
                'error': error
            }
        
        # Парсим ответ
        improvements = self.parse_improvement_response(response_text)
        improvements['original'] = prompt  # Сохраняем исходный промт
        
        return improvements
    
    def parse_improvement_response(self, response: str) -> Dict[str, Any]:
        """
        Парсинг ответа от AI-модели.
        
        Args:
            response: Ответ от AI-модели
            
        Returns:
            Словарь с распарсенными данными
        """
        result = {
            'improved': '',
            'alternatives': [],
            'adaptations': {
                'code': '',
                'analysis': '',
                'creative': ''
            }
        }
        
        if not response or not response.strip():
            return result
        
        # Очистка ответа от markdown разметки
        cleaned_response = response.strip()
        # Убираем ```json ... ```
        cleaned_response = re.sub(r'```json\s*\n?', '', cleaned_response)
        cleaned_response = re.sub(r'```\s*\n?', '', cleaned_response)
        cleaned_response = cleaned_response.strip()
        
        # Попытка 1: Поиск JSON объекта с правильным подсчетом скобок
        # Ищем первый { который может быть началом JSON
        first_brace = cleaned_response.find('{')
        if first_brace != -1:
            try:
                # Находим соответствующий закрывающий }
                brace_count = 0
                json_start = first_brace
                json_end = -1
                
                for i in range(json_start, len(cleaned_response)):
                    if cleaned_response[i] == '{':
                        brace_count += 1
                    elif cleaned_response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if json_end != -1:
                    json_str = cleaned_response[json_start:json_end]
                    data = json.loads(json_str)
                    
                    # Извлекаем данные
                    result['improved'] = str(data.get('improved', '')).strip()
                    alternatives = data.get('alternatives', [])
                    if isinstance(alternatives, list):
                        result['alternatives'] = [str(a).strip() for a in alternatives if a]
                    elif isinstance(alternatives, str):
                        result['alternatives'] = [a.strip() for a in alternatives.split('\n') if a.strip()]
                    
                    adaptations = data.get('adaptations', {})
                    if isinstance(adaptations, dict):
                        result['adaptations']['code'] = str(adaptations.get('code', '')).strip()
                        result['adaptations']['analysis'] = str(adaptations.get('analysis', '')).strip()
                        result['adaptations']['creative'] = str(adaptations.get('creative', '')).strip()
                    
                    return result
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        # Попытка 2: Поиск JSON с помощью регулярного выражения (более гибкий подход)
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*"improved"[^{}]*(?:\{[^{}]*\}[^{}]*)*"alternatives"[^{}]*(?:\{[^{}]*\}[^{}]*)*"adaptations"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
            r'\{.*?"improved".*?"alternatives".*?"adaptations".*?\}',
        ]
        
        for pattern in json_patterns:
            json_match = re.search(pattern, cleaned_response, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    # Попытка исправить некорректный JSON (убираем лишние запятые в конце)
                    json_str = re.sub(r',\s*}', '}', json_str)
                    json_str = re.sub(r',\s*]', ']', json_str)
                    data = json.loads(json_str)
                    
                    result['improved'] = str(data.get('improved', '')).strip()
                    alternatives = data.get('alternatives', [])
                    if isinstance(alternatives, list):
                        result['alternatives'] = [str(a).strip() for a in alternatives if a]
                    elif isinstance(alternatives, str):
                        result['alternatives'] = [a.strip() for a in alternatives.split('\n') if a.strip()]
                    
                    adaptations = data.get('adaptations', {})
                    if isinstance(adaptations, dict):
                        result['adaptations']['code'] = str(adaptations.get('code', '')).strip()
                        result['adaptations']['analysis'] = str(adaptations.get('analysis', '')).strip()
                        result['adaptations']['creative'] = str(adaptations.get('creative', '')).strip()
                    
                    return result
                except (json.JSONDecodeError, ValueError, TypeError):
                    continue
        
        # Попытка 3: Парсинг структурированного текста без JSON
        # Ищем улучшенную версию
        improved_match = re.search(r'(?:улучшенная|improved)[:\-]?\s*\n?(.*?)(?:\n\n|\n(?=##|альтернативы|alternatives|адаптации|adaptations|$))', cleaned_response, re.IGNORECASE | re.DOTALL)
        if improved_match:
            improved_text = improved_match.group(1).strip()
            # Убираем кавычки если есть
            improved_text = re.sub(r'^["\']|["\']$', '', improved_text)
            result['improved'] = improved_text
        
        # Ищем альтернативы
        alternatives_match = re.search(r'(?:альтернативы|alternatives)[:\-]?\s*\n?(.*?)(?:\n\n|\n(?=##|адаптации|adaptations|$))', cleaned_response, re.IGNORECASE | re.DOTALL)
        if alternatives_match:
            alt_text = alternatives_match.group(1).strip()
            # Извлекаем пункты списка (цифры, маркеры, строки в кавычках)
            alt_items = re.findall(r'(?:^|\n)[\s]*[-•\d+\.\s]*["\']?([^"\'\n]+)["\']?', alt_text, re.MULTILINE)
            if not alt_items:
                # Попробуем другой паттерн
                alt_items = re.findall(r'["\']([^"\']+)["\']', alt_text)
            result['alternatives'] = [item.strip() for item in alt_items[:3] if item.strip()]
        
        # Если ничего не нашли, используем весь ответ как улучшенную версию
        if not result['improved']:
            # Убираем возможные JSON структуры из текста
            text_only = re.sub(r'["\']improved["\']\s*:\s*', '', cleaned_response)
            text_only = re.sub(r'["\']alternatives["\']\s*:\s*\[.*?\],?\s*', '', text_only, flags=re.DOTALL)
            text_only = re.sub(r'["\']adaptations["\']\s*:\s*\{.*?\},?\s*', '', text_only, flags=re.DOTALL)
            text_only = re.sub(r'[{}\[\]]', '', text_only)
            text_only = re.sub(r'["\']', '', text_only)
            text_only = re.sub(r',\s*', ' ', text_only)
            result['improved'] = text_only[:500].strip()  # Ограничиваем длину
        
        return result
