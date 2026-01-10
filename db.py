"""
Модуль для работы с базой данных SQLite.
Инкапсулирует всю логику работы с БД.
"""

import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class Database:
    """Класс для работы с базой данных SQLite."""
    
    def __init__(self, db_path: str = "chatlist.db"):
        """
        Инициализация подключения к базе данных.
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.init_db()
    
    def connect(self):
        """Установка соединения с базой данных."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Возвращать результаты как словари
    
    def init_db(self):
        """Создание всех таблиц при первом запуске."""
        cursor = self.conn.cursor()
        
        # Создание таблицы prompts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                prompt TEXT NOT NULL,
                tags TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date)")
        
        # Создание таблицы models
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                api_url TEXT NOT NULL,
                api_id TEXT NOT NULL,
                provider_type TEXT NOT NULL DEFAULT 'custom',
                is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_name ON models(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active)")
        
        # Создание таблицы results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                response_text TEXT NOT NULL,
                saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                response_metadata TEXT,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_prompt_id ON results(prompt_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_model_name ON results(model_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_saved_at ON results(saved_at)")
        
        # Создание таблицы settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)")
        
        # Вставка начальных настроек
        default_settings = [
            ('request_timeout', '30', 'Таймаут запросов к API в секундах'),
            ('max_concurrent_requests', '5', 'Максимальное количество одновременных запросов'),
            ('max_tokens', '2048', 'Максимальное количество токенов в ответе (для избежания ошибки 402, по умолчанию 2048 для бесплатных аккаунтов)'),
            ('auto_save_prompts', '1', 'Автоматическое сохранение всех промтов'),
            ('default_provider', 'openai', 'Провайдер по умолчанию'),
            ('ui_theme', 'default', 'Тема интерфейса'),
            ('log_level', 'INFO', 'Уровень логирования')
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)
        """, default_settings)
        
        # Инициализация предустановленных моделей OpenRouter
        self.init_default_models(cursor)
        
        self.conn.commit()
    
    def init_default_models(self, cursor):
        """
        Инициализация предустановленных моделей OpenRouter.
        Модели добавляются только если их еще нет в БД.
        
        Args:
            cursor: Курсор базы данных
        """
        # Список предустановленных моделей OpenRouter
        default_models = [
            ('allenai/molmo-2-8b:free', 'openrouter'),  # Исправлено: было allenai/molmo-2-8b
            ('deepseek/deepseek-r1-0528', 'openrouter'),
            ('google/gemma-3-27b-it', 'openrouter'),  # Исправлено: было google/gemma-3-27b
            ('google/gemini-2.0-flash-exp', 'openrouter'),
            ('kwaipilot/kat-coder-pro', 'openrouter'),
            ('meta-llama/llama-3.3-70b-instruct', 'openrouter'),
            ('mistralai/devstral-2512', 'openrouter'),
            ('nvidia/nemotron-3-nano-30b-a3b', 'openrouter'),
            ('nvidia/nemotron-nano-12b-v2-vl', 'openrouter'),
            ('openai/gpt-oss-120b', 'openrouter'),
            ('qwen/qwen3-coder', 'openrouter'),
            ('tngtech/deepseek-r1t-chimera', 'openrouter'),
            ('tngtech/deepseek-r1t2-chimera', 'openrouter'),
            ('tngtech/tng-r1t-chimera', 'openrouter'),
            ('cognitivecomputations/dolphin-mistral-24b-venice-edition:free', 'openrouter'),  # Исправлено: было cognitivecomputations/dolphin-mistral-24b-venice-edition
            ('xiaomi/mimo-v2-flash', 'openrouter'),
            ('z-ai/glm-4.5-air', 'openrouter'),
        ]
        
        # URL OpenRouter API
        openrouter_url = 'https://openrouter.ai/api/v1/chat/completions'
        openrouter_api_id = 'OPENROUTER_API_KEY'
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Карта исправлений названий моделей (старое название -> новое название)
        model_name_fixes = {
            'google/gemma-3-27b': 'google/gemma-3-27b-it',  # Исправление неправильного названия
            'allenai/molmo-2-8b': 'allenai/molmo-2-8b:free',  # Добавлен суффикс :free
            'cognitivecomputations/dolphin-mistral-24b-venice-edition': 'cognitivecomputations/dolphin-mistral-24b-venice-edition:free',  # Добавлен суффикс :free
        }
        
        # Обновляем существующие модели с неправильными названиями
        for old_name, new_name in model_name_fixes.items():
            cursor.execute("SELECT id, name FROM models WHERE name = ?", (old_name,))
            old_model = cursor.fetchone()
            if old_model:
                # Проверяем, нет ли уже модели с новым названием
                cursor.execute("SELECT COUNT(*) FROM models WHERE name = ?", (new_name,))
                new_exists = cursor.fetchone()[0] > 0
                if not new_exists:
                    # Обновляем название существующей модели
                    cursor.execute("""
                        UPDATE models SET name = ?, updated_at = ? 
                        WHERE id = ?
                    """, (new_name, now, old_model[0]))
                    print(f"[INFO] Обновлено название модели: '{old_name}' -> '{new_name}'")
                else:
                    # Если новая модель уже существует, удаляем старую
                    cursor.execute("DELETE FROM models WHERE id = ?", (old_model[0],))
                    print(f"[INFO] Удалена дублирующая модель: '{old_name}' (уже существует '{new_name}')")
        
        # Добавляем модели, если их еще нет
        for model_name, provider_type in default_models:
            # Проверяем, существует ли уже модель с таким именем
            cursor.execute("SELECT COUNT(*) FROM models WHERE name = ?", (model_name,))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                # Добавляем новую модель (по умолчанию неактивна, чтобы пользователь мог выбрать нужные)
                cursor.execute("""
                    INSERT INTO models (name, api_url, api_id, provider_type, is_active, 
                                      created_at, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (model_name, openrouter_url, openrouter_api_id, provider_type, 0, now, now))
    
    # Методы для работы с таблицей prompts
    
    def add_prompt(self, prompt: str, tags: Optional[str] = None, date: Optional[str] = None) -> int:
        """
        Добавление нового промта.
        
        Args:
            prompt: Текст промта
            tags: Теги через запятую
            date: Дата в формате YYYY-MM-DD HH:MM:SS (если None, используется текущая)
        
        Returns:
            ID добавленного промта
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO prompts (date, prompt, tags) VALUES (?, ?, ?)
        """, (date, prompt, tags))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_prompts(self) -> List[Dict]:
        """
        Получение всех промтов.
        
        Returns:
            Список словарей с данными промтов
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM prompts ORDER BY date DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_prompt_by_id(self, prompt_id: int) -> Optional[Dict]:
        """
        Получение промта по ID.
        
        Args:
            prompt_id: ID промта
        
        Returns:
            Словарь с данными промта или None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def search_prompts(self, query: str) -> List[Dict]:
        """
        Поиск промтов по тексту.
        
        Args:
            query: Поисковый запрос
        
        Returns:
            Список словарей с найденными промтами
        """
        cursor = self.conn.cursor()
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM prompts 
            WHERE prompt LIKE ? OR tags LIKE ?
            ORDER BY date DESC
        """, (search_pattern, search_pattern))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_prompts_without_results(self) -> List[Dict]:
        """
        Получение промтов, которые не имеют сохраненных результатов.
        Полезно для поиска и удаления неиспользуемых промтов.
        
        Returns:
            Список словарей с данными промтов без сохраненных результатов
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.* 
            FROM prompts p
            LEFT JOIN results r ON p.id = r.prompt_id
            WHERE r.id IS NULL
            ORDER BY p.date DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_prompts_with_results_count(self) -> List[Dict]:
        """
        Получение всех промтов с количеством связанных результатов.
        
        Returns:
            Список словарей с данными промтов и количеством результатов
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.*, COUNT(r.id) as results_count
            FROM prompts p
            LEFT JOIN results r ON p.id = r.prompt_id
            GROUP BY p.id
            ORDER BY p.date DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """
        Удаление промта по ID.
        Все связанные результаты будут удалены автоматически (ON DELETE CASCADE).
        
        Args:
            prompt_id: ID промта для удаления
        
        Returns:
            True если промт удален успешно, False если промт не найден
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_prompts(self, prompt_ids: List[int]) -> int:
        """
        Удаление нескольких промтов по списку ID.
        Все связанные результаты будут удалены автоматически (ON DELETE CASCADE).
        
        Args:
            prompt_ids: Список ID промтов для удаления
        
        Returns:
            Количество удаленных промтов
        """
        if not prompt_ids:
            return 0
        
        cursor = self.conn.cursor()
        placeholders = ','.join(['?'] * len(prompt_ids))
        cursor.execute(f"DELETE FROM prompts WHERE id IN ({placeholders})", prompt_ids)
        self.conn.commit()
        return cursor.rowcount
    
    # Методы для работы с таблицей models
    
    def add_model(self, name: str, api_url: str, api_id: str, 
                  provider_type: str = 'custom', is_active: int = 1) -> int:
        """
        Добавление новой модели.
        
        Args:
            name: Название модели
            api_url: URL API
            api_id: Идентификатор переменной окружения с API-ключом
            provider_type: Тип провайдера (openai, deepseek, groq, custom)
            is_active: Активна ли модель (1 - да, 0 - нет)
        
        Returns:
            ID добавленной модели
        """
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO models (name, api_url, api_id, provider_type, is_active, 
                              created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, api_url, api_id, provider_type, is_active, now, now))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_active_models(self) -> List[Dict]:
        """
        Получение всех активных моделей.
        
        Returns:
            Список словарей с данными активных моделей
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM models WHERE is_active = 1 ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_models(self) -> List[Dict]:
        """
        Получение всех моделей.
        
        Returns:
            Список словарей с данными всех моделей
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM models ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_model_status(self, model_id: int, is_active: int) -> bool:
        """
        Обновление статуса активности модели.
        
        Args:
            model_id: ID модели
            is_active: Новый статус (1 - активна, 0 - неактивна)
        
        Returns:
            True если обновление успешно, False если модель не найдена
        """
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE models SET is_active = ?, updated_at = ? WHERE id = ?
        """, (is_active, now, model_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_model(self, model_id: int) -> bool:
        """
        Удаление модели.
        
        Args:
            model_id: ID модели
        
        Returns:
            True если удаление успешно, False если модель не найдена
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def update_model(self, model_id: int, **kwargs) -> bool:
        """
        Обновление данных модели.
        
        Args:
            model_id: ID модели
            **kwargs: Поля для обновления (name, api_url, api_id, provider_type, is_active)
        
        Returns:
            True если обновление успешно, False если модель не найдена
        """
        allowed_fields = ['name', 'api_url', 'api_id', 'provider_type', 'is_active']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        updates['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [model_id]
        
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE models SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return cursor.rowcount > 0
    
    # Методы для работы с таблицей results
    
    def save_result(self, prompt_id: int, model_name: str, response_text: str, 
                   response_metadata: Optional[str] = None) -> int:
        """
        Сохранение результата запроса.
        
        Args:
            prompt_id: ID промта
            model_name: Название модели
            response_text: Текст ответа
            response_metadata: Метаданные ответа в формате JSON (опционально)
        
        Returns:
            ID сохраненного результата
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO results (prompt_id, model_name, response_text, response_metadata) 
            VALUES (?, ?, ?, ?)
        """, (prompt_id, model_name, response_text, response_metadata))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_results(self) -> List[Dict]:
        """
        Получение всех сохраненных результатов.
        
        Returns:
            Список словарей с данными результатов
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.*, p.prompt, p.date as prompt_date 
            FROM results r
            LEFT JOIN prompts p ON r.prompt_id = p.id
            ORDER BY r.saved_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_results_by_prompt_id(self, prompt_id: int) -> List[Dict]:
        """
        Получение результатов по ID промта.
        
        Args:
            prompt_id: ID промта
        
        Returns:
            Список словарей с результатами
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM results WHERE prompt_id = ? ORDER BY saved_at DESC
        """, (prompt_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def search_results(self, query: str) -> List[Dict]:
        """
        Поиск результатов по тексту.
        
        Args:
            query: Поисковый запрос
        
        Returns:
            Список словарей с найденными результатами
        """
        cursor = self.conn.cursor()
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT r.*, p.prompt, p.date as prompt_date 
            FROM results r
            LEFT JOIN prompts p ON r.prompt_id = p.id
            WHERE r.response_text LIKE ? OR r.model_name LIKE ? OR p.prompt LIKE ?
            ORDER BY r.saved_at DESC
        """, (search_pattern, search_pattern, search_pattern))
        return [dict(row) for row in cursor.fetchall()]
    
    # Методы для работы с таблицей settings
    
    def get_setting(self, key: str) -> Optional[str]:
        """
        Получение значения настройки.
        
        Args:
            key: Ключ настройки
        
        Returns:
            Значение настройки или None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else None
    
    def set_setting(self, key: str, value: str, description: Optional[str] = None) -> bool:
        """
        Установка значения настройки.
        
        Args:
            key: Ключ настройки
            value: Значение настройки
            description: Описание настройки (опционально)
        
        Returns:
            True если настройка успешно установлена
        """
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO settings (key, value, description, updated_at) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET 
                value = excluded.value,
                updated_at = excluded.updated_at,
                description = COALESCE(excluded.description, settings.description)
        """, (key, value, description, now))
        self.conn.commit()
        return True
    
    def close(self):
        """Закрытие соединения с базой данных."""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Деструктор для закрытия соединения."""
        self.close()
