"""
Модуль для работы с моделями нейросетей.
Логика управления моделями и получения API-ключей.
"""

import os
from typing import List, Optional, Dict
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
# Сначала пробуем загрузить .env.local (для локальной разработки), затем .env
env_local_path = '.env.local'
env_path = '.env'

# Проверяем, что файл не пустой перед загрузкой
if os.path.exists(env_local_path):
    file_size = os.path.getsize(env_local_path)
    if file_size > 0:
        load_dotenv(env_local_path, override=True)  # .env.local имеет приоритет
        print(f"[INFO] Загружен {env_local_path} ({file_size} байт)")
    else:
        print(f"[WARNING] Файл {env_local_path} существует, но пустой (0 байт)")
        # Пробуем загрузить .env или системные переменные
        if os.path.exists(env_path) and os.path.getsize(env_path) > 0:
            load_dotenv(env_path, override=True)
            print(f"[INFO] Загружен {env_path} вместо пустого {env_local_path}")
        else:
            load_dotenv()  # Попытка загрузить из системных переменных
elif os.path.exists(env_path):
    file_size = os.path.getsize(env_path)
    if file_size > 0:
        load_dotenv(env_path, override=True)  # Загружаем .env, если .env.local нет
        print(f"[INFO] Загружен {env_path} ({file_size} байт)")
    else:
        print(f"[WARNING] Файл {env_path} существует, но пустой (0 байт)")
        load_dotenv()  # Попытка загрузить из системных переменных
else:
    load_dotenv()  # Попытка загрузить .env или системные переменные
    print(f"[INFO] Попытка загрузки из системных переменных окружения")


class Model:
    """Класс для представления одной модели нейросети."""
    
    def __init__(self, id: int, name: str, api_url: str, api_id: str, 
                 provider_type: str = 'custom', is_active: int = 1,
                 created_at: Optional[str] = None, updated_at: Optional[str] = None):
        """
        Инициализация модели.
        
        Args:
            id: ID модели в БД
            name: Название модели
            api_url: URL API для отправки запросов
            api_id: Идентификатор переменной окружения с API-ключом
            provider_type: Тип провайдера (openai, deepseek, groq, custom)
            is_active: Активна ли модель (1 - да, 0 - нет)
            created_at: Дата создания
            updated_at: Дата последнего обновления
        """
        self.id = id
        self.name = name
        self.api_url = api_url
        self.api_id = api_id
        self.provider_type = provider_type
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
    
    def get_api_key(self) -> Optional[str]:
        """
        Получение API-ключа из переменных окружения.
        
        Returns:
            API-ключ или None, если ключ не найден
        """
        return os.getenv(self.api_id)
    
    def has_api_key(self) -> bool:
        """
        Проверка наличия API-ключа.
        
        Returns:
            True если API-ключ найден, False иначе
        """
        return self.get_api_key() is not None
    
    def to_dict(self) -> Dict:
        """
        Преобразование модели в словарь.
        
        Returns:
            Словарь с данными модели
        """
        return {
            'id': self.id,
            'name': self.name,
            'api_url': self.api_url,
            'api_id': self.api_id,
            'provider_type': self.provider_type,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Model':
        """
        Создание модели из словаря.
        
        Args:
            data: Словарь с данными модели
        
        Returns:
            Экземпляр класса Model
        """
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            api_url=data.get('api_url'),
            api_id=data.get('api_id'),
            provider_type=data.get('provider_type', 'custom'),
            is_active=data.get('is_active', 1),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


class ModelManager:
    """Класс для управления моделями нейросетей."""
    
    def __init__(self, db):
        """
        Инициализация менеджера моделей.
        
        Args:
            db: Экземпляр класса Database
        """
        self.db = db
        self._models_cache: Optional[List[Model]] = None
        self._cache_valid = False
    
    def get_active_models(self) -> List[Model]:
        """
        Получение списка активных моделей.
        
        Returns:
            Список активных моделей
        """
        models_data = self.db.get_active_models()
        return [Model.from_dict(data) for data in models_data]
    
    def get_all_models(self) -> List[Model]:
        """
        Получение списка всех моделей.
        
        Returns:
            Список всех моделей
        """
        models_data = self.db.get_all_models()
        return [Model.from_dict(data) for data in models_data]
    
    def get_model_by_id(self, model_id: int) -> Optional[Model]:
        """
        Получение модели по ID.
        
        Args:
            model_id: ID модели
        
        Returns:
            Модель или None если не найдена
        """
        all_models = self.get_all_models()
        for model in all_models:
            if model.id == model_id:
                return model
        return None
    
    def get_model_by_name(self, name: str) -> Optional[Model]:
        """
        Получение модели по имени.
        
        Args:
            name: Название модели
        
        Returns:
            Модель или None если не найдена
        """
        all_models = self.get_all_models()
        for model in all_models:
            if model.name == name:
                return model
        return None
    
    def add_model(self, name: str, api_url: str, api_id: str, 
                  provider_type: str = 'custom', is_active: int = 1) -> Model:
        """
        Добавление новой модели.
        
        Args:
            name: Название модели
            api_url: URL API
            api_id: Идентификатор переменной окружения с API-ключом
            provider_type: Тип провайдера
            is_active: Активна ли модель
        
        Returns:
            Созданная модель
        """
        model_id = self.db.add_model(name, api_url, api_id, provider_type, is_active)
        self._cache_valid = False  # Инвалидируем кэш
        return self.get_model_by_id(model_id)
    
    def update_model(self, model_id: int, **kwargs) -> bool:
        """
        Обновление модели.
        
        Args:
            model_id: ID модели
            **kwargs: Поля для обновления
        
        Returns:
            True если обновление успешно
        """
        result = self.db.update_model(model_id, **kwargs)
        self._cache_valid = False  # Инвалидируем кэш
        return result
    
    def update_model_status(self, model_id: int, is_active: int) -> bool:
        """
        Обновление статуса активности модели.
        
        Args:
            model_id: ID модели
            is_active: Новый статус (1 - активна, 0 - неактивна)
        
        Returns:
            True если обновление успешно
        """
        result = self.db.update_model_status(model_id, is_active)
        self._cache_valid = False  # Инвалидируем кэш
        return result
    
    def get_models_with_valid_keys(self) -> List[Model]:
        """
        Получение активных моделей с валидными API-ключами.
        
        Returns:
            Список моделей, у которых есть API-ключи
        """
        active_models = self.get_active_models()
        return [model for model in active_models if model.has_api_key()]
