"""
Общие фикстуры и конфигурация для pytest.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import Database


@pytest.fixture
def temp_db():
    """Создание временной БД для тестов."""
    fd, path = tempfile.mkstemp(suffix='.db')
    db = Database(db_path=path)
    yield db
    db.conn.close()
    os.close(fd)
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def sample_model_data():
    """Тестовые данные модели."""
    return {
        'name': 'test-model',
        'api_url': 'https://api.test.com/v1/chat/completions',
        'api_id': 'TEST_API_KEY',
        'provider_type': 'custom',
        'is_active': 1
    }


@pytest.fixture
def sample_prompt_data():
    """Тестовые данные промта."""
    return {
        'prompt': 'Test prompt для тестирования',
        'tags': 'test, unit-test'
    }


@pytest.fixture
def sample_result_data():
    """Тестовые данные результата."""
    return {
        'model_name': 'test-model',
        'response_text': 'Это тестовый ответ от модели',
        'response_metadata': '{"tokens": 100, "time": 1.5}'
    }


@pytest.fixture
def populated_db(temp_db, sample_model_data, sample_prompt_data):
    """База данных с предварительно заполненными данными."""
    # Добавляем модель
    model_id = temp_db.add_model(
        name=sample_model_data['name'],
        api_url=sample_model_data['api_url'],
        api_id=sample_model_data['api_id'],
        provider_type=sample_model_data['provider_type'],
        is_active=sample_model_data['is_active']
    )
    
    # Добавляем промт
    prompt_id = temp_db.add_prompt(
        prompt=sample_prompt_data['prompt'],
        tags=sample_prompt_data['tags']
    )
    
    # Добавляем результат
    result_id = temp_db.save_result(
        prompt_id=prompt_id,
        model_name=sample_model_data['name'],
        response_text=sample_result_data()['response_text']
    )
    
    return {
        'db': temp_db,
        'model_id': model_id,
        'prompt_id': prompt_id,
        'result_id': result_id
    }
