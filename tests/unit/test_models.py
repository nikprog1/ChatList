"""
UNIT тесты для модуля models.py (Model, ModelManager).
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from models import Model, ModelManager


@pytest.mark.unit
class TestModel:
    """Тесты для класса Model."""
    
    def test_model_initialization(self):
        """Тест инициализации модели с валидными параметрами."""
        model = Model(
            id=1,
            name='test-model',
            api_url='https://api.test.com/v1/chat/completions',
            api_id='TEST_API_KEY',
            provider_type='custom',
            is_active=1
        )
        
        assert model.id == 1
        assert model.name == 'test-model'
        assert model.api_url == 'https://api.test.com/v1/chat/completions'
        assert model.api_id == 'TEST_API_KEY'
        assert model.provider_type == 'custom'
        assert model.is_active == 1
    
    def test_model_defaults(self):
        """Тест значений по умолчанию при инициализации."""
        model = Model(
            id=1,
            name='test-model',
            api_url='https://api.test.com',
            api_id='TEST_KEY'
        )
        
        assert model.provider_type == 'custom'
        assert model.is_active == 1
    
    @patch.dict(os.environ, {'TEST_API_KEY': 'test-api-key-value'})
    def test_get_api_key_exists(self):
        """Тест получения API-ключа из переменных окружения (ключ существует)."""
        model = Model(
            id=1,
            name='test-model',
            api_url='https://api.test.com',
            api_id='TEST_API_KEY'
        )
        
        api_key = model.get_api_key()
        assert api_key == 'test-api-key-value'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_key_not_exists(self):
        """Тест получения API-ключа из переменных окружения (ключ отсутствует)."""
        model = Model(
            id=1,
            name='test-model',
            api_url='https://api.test.com',
            api_id='NON_EXISTENT_KEY'
        )
        
        api_key = model.get_api_key()
        assert api_key is None
    
    @patch.dict(os.environ, {'TEST_API_KEY': 'test-api-key-value'})
    def test_has_api_key_true(self):
        """Тест проверки наличия API-ключа (ключ есть)."""
        model = Model(
            id=1,
            name='test-model',
            api_url='https://api.test.com',
            api_id='TEST_API_KEY'
        )
        
        assert model.has_api_key() is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_has_api_key_false(self):
        """Тест проверки наличия API-ключа (ключа нет)."""
        model = Model(
            id=1,
            name='test-model',
            api_url='https://api.test.com',
            api_id='NON_EXISTENT_KEY'
        )
        
        assert model.has_api_key() is False
    
    def test_to_dict(self):
        """Тест преобразования модели в словарь."""
        model = Model(
            id=1,
            name='test-model',
            api_url='https://api.test.com',
            api_id='TEST_KEY',
            provider_type='openai',
            is_active=1,
            created_at='2024-01-15 10:00:00',
            updated_at='2024-01-15 11:00:00'
        )
        
        model_dict = model.to_dict()
        
        assert isinstance(model_dict, dict)
        assert model_dict['id'] == 1
        assert model_dict['name'] == 'test-model'
        assert model_dict['api_url'] == 'https://api.test.com'
        assert model_dict['api_id'] == 'TEST_KEY'
        assert model_dict['provider_type'] == 'openai'
        assert model_dict['is_active'] == 1
        assert model_dict['created_at'] == '2024-01-15 10:00:00'
        assert model_dict['updated_at'] == '2024-01-15 11:00:00'
    
    def test_from_dict(self):
        """Тест создания модели из словаря."""
        data = {
            'id': 2,
            'name': 'model-from-dict',
            'api_url': 'https://api.test.com',
            'api_id': 'TEST_KEY',
            'provider_type': 'custom',
            'is_active': 0,
            'created_at': '2024-01-15 10:00:00',
            'updated_at': '2024-01-15 11:00:00'
        }
        
        model = Model.from_dict(data)
        
        assert isinstance(model, Model)
        assert model.id == 2
        assert model.name == 'model-from-dict'
        assert model.api_url == 'https://api.test.com'
        assert model.api_id == 'TEST_KEY'
        assert model.provider_type == 'custom'
        assert model.is_active == 0
    
    def test_from_dict_with_defaults(self):
        """Тест создания модели из словаря с значениями по умолчанию."""
        data = {
            'id': 3,
            'name': 'model-defaults',
            'api_url': 'https://api.test.com',
            'api_id': 'TEST_KEY'
        }
        
        model = Model.from_dict(data)
        
        assert model.provider_type == 'custom'
        assert model.is_active == 1
        assert model.created_at is None
        assert model.updated_at is None


@pytest.mark.unit
class TestModelManager:
    """Тесты для класса ModelManager."""
    
    def test_model_manager_initialization(self, temp_db):
        """Тест инициализации ModelManager."""
        manager = ModelManager(temp_db)
        assert manager.db == temp_db
        assert manager._models_cache is None
        assert manager._cache_valid is False
    
    def test_get_active_models(self, temp_db, sample_model_data):
        """Тест получения активных моделей."""
        # Добавляем активную и неактивную модели
        temp_db.add_model(
            name='active-model',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id'],
            is_active=1
        )
        temp_db.add_model(
            name='inactive-model',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id'],
            is_active=0
        )
        
        manager = ModelManager(temp_db)
        active_models = manager.get_active_models()
        
        assert isinstance(active_models, list)
        model_names = [m.name for m in active_models]
        assert 'active-model' in model_names
        assert 'inactive-model' not in model_names
        
        # Проверяем, что все элементы - экземпляры Model
        for model in active_models:
            assert isinstance(model, Model)
    
    def test_get_all_models(self, temp_db, sample_model_data):
        """Тест получения всех моделей."""
        # Добавляем несколько моделей
        temp_db.add_model('model1', sample_model_data['api_url'], sample_model_data['api_id'])
        temp_db.add_model('model2', sample_model_data['api_url'], sample_model_data['api_id'])
        
        manager = ModelManager(temp_db)
        all_models = manager.get_all_models()
        
        assert isinstance(all_models, list)
        assert len(all_models) >= 2
        
        model_names = [m.name for m in all_models]
        assert 'model1' in model_names
        assert 'model2' in model_names
        
        # Проверяем, что все элементы - экземпляры Model
        for model in all_models:
            assert isinstance(model, Model)
    
    def test_get_model_by_id(self, temp_db, sample_model_data):
        """Тест получения модели по ID."""
        model_id = temp_db.add_model(
            name='model-by-id',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id']
        )
        
        manager = ModelManager(temp_db)
        model = manager.get_model_by_id(model_id)
        
        assert model is not None
        assert isinstance(model, Model)
        assert model.id == model_id
        assert model.name == 'model-by-id'
    
    def test_get_model_by_id_not_found(self, temp_db):
        """Тест получения несуществующей модели по ID."""
        manager = ModelManager(temp_db)
        model = manager.get_model_by_id(99999)
        assert model is None
    
    def test_get_model_by_name(self, temp_db, sample_model_data):
        """Тест получения модели по имени."""
        temp_db.add_model(
            name='unique-model-name',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id']
        )
        
        manager = ModelManager(temp_db)
        model = manager.get_model_by_name('unique-model-name')
        
        assert model is not None
        assert isinstance(model, Model)
        assert model.name == 'unique-model-name'
    
    def test_get_model_by_name_not_found(self, temp_db):
        """Тест получения несуществующей модели по имени."""
        manager = ModelManager(temp_db)
        model = manager.get_model_by_name('non-existent-model-name')
        assert model is None
    
    def test_add_model(self, temp_db, sample_model_data):
        """Тест добавления новой модели."""
        manager = ModelManager(temp_db)
        
        model = manager.add_model(
            name='new-model',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id'],
            provider_type='custom',
            is_active=1
        )
        
        assert isinstance(model, Model)
        assert model.name == 'new-model'
        assert model.id is not None
        
        # Проверяем, что модель действительно добавлена в БД
        all_models = manager.get_all_models()
        model_names = [m.name for m in all_models]
        assert 'new-model' in model_names
    
    def test_update_model(self, temp_db, sample_model_data):
        """Тест обновления модели."""
        model_id = temp_db.add_model(
            name='old-name',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id']
        )
        
        manager = ModelManager(temp_db)
        success = manager.update_model(model_id, name='new-name')
        
        assert success is True
        
        # Проверяем обновление
        updated_model = manager.get_model_by_id(model_id)
        assert updated_model is not None
        assert updated_model.name == 'new-name'
    
    def test_update_model_not_found(self, temp_db):
        """Тест обновления несуществующей модели."""
        manager = ModelManager(temp_db)
        success = manager.update_model(99999, name='new-name')
        assert success is False
    
    def test_update_model_status(self, temp_db, sample_model_data):
        """Тест обновления статуса активности модели."""
        model_id = temp_db.add_model(
            name='test-status-model',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id'],
            is_active=1
        )
        
        manager = ModelManager(temp_db)
        
        # Деактивируем
        success = manager.update_model_status(model_id, 0)
        assert success is True
        
        model = manager.get_model_by_id(model_id)
        assert model.is_active == 0
        
        # Активируем обратно
        manager.update_model_status(model_id, 1)
        model = manager.get_model_by_id(model_id)
        assert model.is_active == 1
    
    @patch.dict(os.environ, {'TEST_API_KEY': 'test-key-value', 'OTHER_KEY': 'other-value'})
    def test_get_models_with_valid_keys(self, temp_db):
        """Тест получения моделей с валидными API-ключами."""
        # Добавляем модели с разными API-ключами
        model_with_key_id = temp_db.add_model(
            name='model-with-key',
            api_url='https://api.test.com',
            api_id='TEST_API_KEY',
            is_active=1
        )
        model_without_key_id = temp_db.add_model(
            name='model-without-key',
            api_url='https://api.test.com',
            api_id='NON_EXISTENT_KEY',
            is_active=1
        )
        
        manager = ModelManager(temp_db)
        models_with_keys = manager.get_models_with_valid_keys()
        
        # Проверяем, что только модель с ключом включена
        model_ids = [m.id for m in models_with_keys]
        assert model_with_key_id in model_ids
        assert model_without_key_id not in model_ids
        
        # Проверяем, что все модели активны
        for model in models_with_keys:
            assert model.is_active == 1
            assert model.has_api_key() is True
    
    def test_get_models_with_valid_keys_only_active(self, temp_db):
        """Тест, что get_models_with_valid_keys возвращает только активные модели."""
        # Добавляем неактивную модель с ключом
        with patch.dict(os.environ, {'TEST_API_KEY': 'test-key'}):
            inactive_model_id = temp_db.add_model(
                name='inactive-with-key',
                api_url='https://api.test.com',
                api_id='TEST_API_KEY',
                is_active=0
            )
            
            manager = ModelManager(temp_db)
            models_with_keys = manager.get_models_with_valid_keys()
            
            # Неактивная модель не должна быть включена
            model_ids = [m.id for m in models_with_keys]
            assert inactive_model_id not in model_ids
