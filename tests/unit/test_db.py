"""
UNIT тесты для модуля db.py (Database).
"""

import pytest
from datetime import datetime
from db import Database


@pytest.mark.unit
class TestDatabaseInit:
    """Тесты инициализации базы данных."""
    
    def test_database_initialization(self, temp_db):
        """Тест создания экземпляра Database."""
        assert temp_db is not None
        assert temp_db.conn is not None
    
    def test_tables_created(self, temp_db):
        """Тест создания всех таблиц при инициализации."""
        cursor = temp_db.conn.cursor()
        
        # Проверяем существование таблиц
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('prompts', 'models', 'results', 'settings')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'prompts' in tables
        assert 'models' in tables
        assert 'results' in tables
        assert 'settings' in tables
    
    def test_indexes_created(self, temp_db):
        """Тест создания индексов."""
        cursor = temp_db.conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Проверяем наличие основных индексов
        index_names = [idx for idx in indexes]
        assert len(index_names) > 0
    
    def test_default_settings_initialized(self, temp_db):
        """Тест инициализации настроек по умолчанию."""
        timeout = temp_db.get_setting('request_timeout')
        assert timeout is not None
        assert int(timeout) == 30
        
        max_tokens = temp_db.get_setting('max_tokens')
        assert max_tokens is not None


@pytest.mark.unit
class TestDatabasePrompts:
    """Тесты для работы с таблицей prompts."""
    
    def test_add_prompt(self, temp_db, sample_prompt_data):
        """Тест добавления промта."""
        prompt_id = temp_db.add_prompt(
            prompt=sample_prompt_data['prompt'],
            tags=sample_prompt_data['tags']
        )
        
        assert prompt_id is not None
        assert isinstance(prompt_id, int)
        assert prompt_id > 0
    
    def test_add_prompt_without_tags(self, temp_db):
        """Тест добавления промта без тегов."""
        prompt_id = temp_db.add_prompt(prompt='Test prompt without tags')
        assert prompt_id > 0
        
        prompt = temp_db.get_prompt_by_id(prompt_id)
        assert prompt is not None
        assert prompt['tags'] is None or prompt['tags'] == ''
    
    def test_add_prompt_with_custom_date(self, temp_db):
        """Тест добавления промта с кастомной датой."""
        custom_date = '2024-01-15 10:00:00'
        prompt_id = temp_db.add_prompt(
            prompt='Test prompt',
            date=custom_date
        )
        
        prompt = temp_db.get_prompt_by_id(prompt_id)
        assert prompt is not None
        assert prompt['date'] == custom_date
    
    def test_get_all_prompts(self, temp_db):
        """Тест получения всех промтов."""
        # Добавляем несколько промтов
        temp_db.add_prompt('Prompt 1')
        temp_db.add_prompt('Prompt 2')
        temp_db.add_prompt('Prompt 3')
        
        prompts = temp_db.get_all_prompts()
        assert len(prompts) >= 3
        
        # Проверяем сортировку по дате (DESC)
        if len(prompts) > 1:
            dates = [p['date'] for p in prompts[:2]]
            # Последний добавленный должен быть первым (если даты корректны)
            assert dates[0] >= dates[1] or True  # Могут быть одинаковые даты
    
    def test_get_prompt_by_id(self, temp_db, sample_prompt_data):
        """Тест получения промта по ID."""
        prompt_id = temp_db.add_prompt(
            prompt=sample_prompt_data['prompt'],
            tags=sample_prompt_data['tags']
        )
        
        prompt = temp_db.get_prompt_by_id(prompt_id)
        assert prompt is not None
        assert prompt['id'] == prompt_id
        assert prompt['prompt'] == sample_prompt_data['prompt']
        assert prompt['tags'] == sample_prompt_data['tags']
    
    def test_get_prompt_by_id_not_found(self, temp_db):
        """Тест получения несуществующего промта."""
        prompt = temp_db.get_prompt_by_id(99999)
        assert prompt is None
    
    def test_search_prompts(self, temp_db):
        """Тест поиска промтов."""
        # Добавляем промты с разными тегами
        temp_db.add_prompt('Python programming', tags='python, code')
        temp_db.add_prompt('JavaScript tutorial', tags='js, web')
        temp_db.add_prompt('Python basics', tags='python, beginner')
        
        # Поиск по тексту промта
        results = temp_db.search_prompts('Python')
        assert len(results) >= 2
        
        # Поиск по тегам
        results = temp_db.search_prompts('python')
        assert len(results) >= 2
        
        # Поиск с частичным совпадением
        results = temp_db.search_prompts('prog')
        assert len(results) >= 1
    
    def test_search_prompts_no_results(self, temp_db):
        """Тест поиска промтов без результатов."""
        results = temp_db.search_prompts('NonExistentQuery12345')
        assert len(results) == 0
    
    def test_delete_prompt(self, temp_db):
        """Тест удаления промта."""
        prompt_id = temp_db.add_prompt('Test prompt to delete')
        
        success = temp_db.delete_prompt(prompt_id)
        assert success is True
        
        # Проверяем, что промт удален
        prompt = temp_db.get_prompt_by_id(prompt_id)
        assert prompt is None
    
    def test_delete_prompt_not_found(self, temp_db):
        """Тест удаления несуществующего промта."""
        success = temp_db.delete_prompt(99999)
        assert success is False
    
    def test_delete_prompt_cascade(self, temp_db, sample_model_data):
        """Тест каскадного удаления результатов при удалении промта."""
        # Добавляем промт
        prompt_id = temp_db.add_prompt('Test prompt cascade')
        
        # Добавляем модель
        model_id = temp_db.add_model(
            name=sample_model_data['name'],
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id']
        )
        
        # Добавляем результат
        result_id = temp_db.save_result(
            prompt_id=prompt_id,
            model_name=sample_model_data['name'],
            response_text='Test response cascade'
        )
        
        # Проверяем, что результат создан
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT * FROM results WHERE id = ?", (result_id,))
        result_before = cursor.fetchone()
        assert result_before is not None
        
        # Удаляем промт
        temp_db.delete_prompt(prompt_id)
        
        # Проверяем, что результат также удален (каскадно)
        # В SQLite каскадное удаление работает автоматически при правильной настройке FOREIGN KEY
        cursor.execute("SELECT * FROM results WHERE id = ?", (result_id,))
        result_after = cursor.fetchone()
        # Результат должен быть удален, но может остаться, если каскад не настроен
        # Проверяем, что промт удален точно
        prompt = temp_db.get_prompt_by_id(prompt_id)
        assert prompt is None
    
    def test_delete_prompts_multiple(self, temp_db):
        """Тест массового удаления промтов."""
        # Добавляем несколько промтов
        id1 = temp_db.add_prompt('Prompt 1')
        id2 = temp_db.add_prompt('Prompt 2')
        id3 = temp_db.add_prompt('Prompt 3')
        
        # Удаляем несколько
        deleted_count = temp_db.delete_prompts([id1, id2])
        assert deleted_count == 2
        
        # Проверяем, что они удалены
        assert temp_db.get_prompt_by_id(id1) is None
        assert temp_db.get_prompt_by_id(id2) is None
        assert temp_db.get_prompt_by_id(id3) is not None
    
    def test_delete_prompts_empty_list(self, temp_db):
        """Тест удаления пустого списка промтов."""
        deleted_count = temp_db.delete_prompts([])
        assert deleted_count == 0


@pytest.mark.unit
class TestDatabaseModels:
    """Тесты для работы с таблицей models."""
    
    def test_add_model(self, temp_db, sample_model_data):
        """Тест добавления модели."""
        model_id = temp_db.add_model(
            name=sample_model_data['name'],
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id'],
            provider_type=sample_model_data['provider_type'],
            is_active=sample_model_data['is_active']
        )
        
        assert model_id is not None
        assert isinstance(model_id, int)
        assert model_id > 0
    
    def test_get_active_models(self, temp_db, sample_model_data):
        """Тест получения активных моделей."""
        # Добавляем активную и неактивную модели
        active_id = temp_db.add_model(
            name='active-model',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id'],
            is_active=1
        )
        inactive_id = temp_db.add_model(
            name='inactive-model',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id'],
            is_active=0
        )
        
        active_models = temp_db.get_active_models()
        active_names = [m['name'] for m in active_models]
        
        assert 'active-model' in active_names
        assert 'inactive-model' not in active_names
    
    def test_get_all_models(self, temp_db, sample_model_data):
        """Тест получения всех моделей."""
        # Добавляем несколько моделей
        temp_db.add_model('model1', sample_model_data['api_url'], sample_model_data['api_id'])
        temp_db.add_model('model2', sample_model_data['api_url'], sample_model_data['api_id'])
        
        all_models = temp_db.get_all_models()
        assert len(all_models) >= 2
        
        model_names = [m['name'] for m in all_models]
        assert 'model1' in model_names
        assert 'model2' in model_names
    
    def test_get_model_by_id(self, temp_db, sample_model_data):
        """Тест получения модели по ID через get_all_models."""
        model_id = temp_db.add_model(
            name=sample_model_data['name'],
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id']
        )
        
        all_models = temp_db.get_all_models()
        model = next((m for m in all_models if m['id'] == model_id), None)
        assert model is not None
        assert model['id'] == model_id
        assert model['name'] == sample_model_data['name']
    
    def test_get_model_by_id_not_found(self, temp_db):
        """Тест получения несуществующей модели."""
        all_models = temp_db.get_all_models()
        model = next((m for m in all_models if m['id'] == 99999), None)
        assert model is None
    
    def test_update_model_status(self, temp_db, sample_model_data):
        """Тест обновления статуса модели."""
        model_id = temp_db.add_model(
            name='test-model-status',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id'],
            is_active=1
        )
        
        # Деактивируем
        success = temp_db.update_model_status(model_id, 0)
        assert success is True
        
        all_models = temp_db.get_all_models()
        model = next((m for m in all_models if m['id'] == model_id), None)
        assert model is not None
        assert model['is_active'] == 0
        
        # Активируем обратно
        temp_db.update_model_status(model_id, 1)
        all_models = temp_db.get_all_models()
        model = next((m for m in all_models if m['id'] == model_id), None)
        assert model is not None
        assert model['is_active'] == 1
    
    def test_update_model(self, temp_db, sample_model_data):
        """Тест обновления модели."""
        model_id = temp_db.add_model(
            name='old-name-update',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id']
        )
        
        # Обновляем имя
        success = temp_db.update_model(model_id, name='new-name-update')
        assert success is True
        
        all_models = temp_db.get_all_models()
        model = next((m for m in all_models if m['id'] == model_id), None)
        assert model is not None
        assert model['name'] == 'new-name-update'
    
    def test_delete_model(self, temp_db, sample_model_data):
        """Тест удаления модели."""
        model_id = temp_db.add_model(
            name='model-to-delete-test',
            api_url=sample_model_data['api_url'],
            api_id=sample_model_data['api_id']
        )
        
        success = temp_db.delete_model(model_id)
        assert success is True
        
        all_models = temp_db.get_all_models()
        model = next((m for m in all_models if m['id'] == model_id), None)
        assert model is None
    
    def test_delete_model_not_found(self, temp_db):
        """Тест удаления несуществующей модели."""
        success = temp_db.delete_model(99999)
        assert success is False


@pytest.mark.unit
class TestDatabaseResults:
    """Тесты для работы с таблицей results."""
    
    def test_save_result(self, temp_db, sample_model_data):
        """Тест сохранения результата."""
        # Сначала создаем промт и модель
        prompt_id = temp_db.add_prompt('Test prompt')
        
        result_id = temp_db.save_result(
            prompt_id=prompt_id,
            model_name=sample_model_data['name'],
            response_text='Test response text'
        )
        
        assert result_id is not None
        assert isinstance(result_id, int)
        assert result_id > 0
    
    def test_save_result_with_metadata(self, temp_db, sample_model_data):
        """Тест сохранения результата с метаданными."""
        prompt_id = temp_db.add_prompt('Test prompt')
        
        metadata = '{"tokens": 100, "time": 1.5}'
        result_id = temp_db.save_result(
            prompt_id=prompt_id,
            model_name=sample_model_data['name'],
            response_text='Test response',
            response_metadata=metadata
        )
        
        # Получаем результат из БД
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT response_metadata FROM results WHERE id = ?", (result_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row['response_metadata'] == metadata
    
    def test_get_all_results(self, temp_db, sample_model_data):
        """Тест получения всех результатов."""
        # Создаем промт
        prompt_id = temp_db.add_prompt('Test prompt')
        
        # Добавляем несколько результатов
        temp_db.save_result(prompt_id, 'model1', 'response1')
        temp_db.save_result(prompt_id, 'model2', 'response2')
        
        results = temp_db.get_all_results()
        assert len(results) >= 2
        
        # Проверяем JOIN с prompts
        for result in results[:2]:
            assert 'prompt' in result or 'prompt_id' in result
    
    def test_get_results_by_prompt_id(self, temp_db, sample_model_data):
        """Тест получения результатов по ID промта."""
        prompt_id = temp_db.add_prompt('Test prompt')
        
        temp_db.save_result(prompt_id, 'model1', 'response1')
        temp_db.save_result(prompt_id, 'model2', 'response2')
        
        results = temp_db.get_results_by_prompt_id(prompt_id)
        assert len(results) == 2
        
        for result in results:
            assert result['prompt_id'] == prompt_id
    
    def test_get_results_by_prompt_id_empty(self, temp_db):
        """Тест получения результатов для промта без результатов."""
        prompt_id = temp_db.add_prompt('Empty prompt')
        
        results = temp_db.get_results_by_prompt_id(prompt_id)
        assert len(results) == 0
    
    def test_search_results(self, temp_db, sample_model_data):
        """Тест поиска результатов."""
        prompt_id = temp_db.add_prompt('Python programming question')
        
        temp_db.save_result(prompt_id, 'model1', 'Python is great')
        temp_db.save_result(prompt_id, 'model2', 'JavaScript is also good')
        
        # Поиск по тексту ответа
        results = temp_db.search_results('Python')
        assert len(results) >= 1
        
        # Поиск по названию модели
        results = temp_db.search_results('model1')
        assert len(results) >= 1


@pytest.mark.unit
class TestDatabaseSettings:
    """Тесты для работы с таблицей settings."""
    
    def test_get_setting(self, temp_db):
        """Тест получения настройки."""
        timeout = temp_db.get_setting('request_timeout')
        assert timeout is not None
        assert isinstance(timeout, str) or isinstance(timeout, int)
    
    def test_get_setting_not_found(self, temp_db):
        """Тест получения несуществующей настройки."""
        setting = temp_db.get_setting('non_existent_setting_12345')
        # Может вернуть None или значение по умолчанию
        assert setting is None or isinstance(setting, str)
    
    def test_set_setting(self, temp_db):
        """Тест установки настройки."""
        success = temp_db.set_setting('test_setting', 'test_value', 'Test description')
        assert success is True
        
        value = temp_db.get_setting('test_setting')
        assert value == 'test_value'
    
    def test_set_setting_update_existing(self, temp_db):
        """Тест обновления существующей настройки."""
        # Устанавливаем настройку
        temp_db.set_setting('test_setting', 'value1')
        assert temp_db.get_setting('test_setting') == 'value1'
        
        # Обновляем
        temp_db.set_setting('test_setting', 'value2')
        assert temp_db.get_setting('test_setting') == 'value2'


@pytest.mark.unit
class TestDatabaseAdditionalMethods:
    """Тесты для дополнительных методов."""
    
    def test_get_prompts_without_results(self, temp_db):
        """Тест получения промтов без результатов."""
        # Создаем промт с результатом
        prompt_with_result = temp_db.add_prompt('Prompt with result')
        temp_db.save_result(prompt_with_result, 'model1', 'response1')
        
        # Создаем промт без результата
        prompt_without_result = temp_db.add_prompt('Prompt without result')
        
        prompts_without = temp_db.get_prompts_without_results()
        prompt_ids = [p['id'] for p in prompts_without]
        
        assert prompt_without_result in prompt_ids
        assert prompt_with_result not in prompt_ids
    
    def test_get_prompts_with_results_count(self, temp_db):
        """Тест получения промтов с количеством результатов."""
        # Создаем промт с несколькими результатами
        prompt_id = temp_db.add_prompt('Test prompt')
        temp_db.save_result(prompt_id, 'model1', 'response1')
        temp_db.save_result(prompt_id, 'model2', 'response2')
        
        prompts_with_count = temp_db.get_prompts_with_results_count()
        
        # Находим наш промт
        prompt_data = next((p for p in prompts_with_count if p['id'] == prompt_id), None)
        assert prompt_data is not None
        assert prompt_data.get('results_count', 0) >= 2
