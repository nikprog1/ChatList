# Схема базы данных ChatList

База данных использует SQLite и состоит из четырех таблиц.

## Таблица: prompts (Промты)

Хранит все запросы (промты), введенные пользователем.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| id | INTEGER | Первичный ключ, автоинкремент | PRIMARY KEY, NOT NULL, AUTOINCREMENT |
| date | TEXT | Дата и время создания промта | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| prompt | TEXT | Текст промта | NOT NULL |
| tags | TEXT | Теги через запятую или JSON | NULL |

**Индексы:**
- `idx_prompts_date` на поле `date` для ускорения поиска по дате
- `idx_prompts_tags` на поле `tags` для поиска по тегам (опционально, если используется полнотекстовый поиск)

**Пример записи:**
```
id: 1
date: "2024-01-15 14:30:00"
prompt: "Объясни концепцию машинного обучения"
tags: "обучение, ИИ, основы"
```

## Таблица: models (Модели нейросетей)

Хранит информацию о доступных нейросетевых моделях.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| id | INTEGER | Первичный ключ, автоинкремент | PRIMARY KEY, NOT NULL, AUTOINCREMENT |
| name | TEXT | Название модели (например, "GPT-4", "Claude 3") | NOT NULL, UNIQUE |
| api_url | TEXT | URL API для отправки запросов | NOT NULL |
| api_id | TEXT | Идентификатор переменной окружения с API-ключом | NOT NULL |
| provider_type | TEXT | Тип провайдера (openai, deepseek, groq, custom) | NOT NULL, DEFAULT 'custom' |
| is_active | INTEGER | Флаг активности (1 - активна, 0 - неактивна) | NOT NULL, DEFAULT 1, CHECK(is_active IN (0, 1)) |
| created_at | TEXT | Дата создания записи | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TEXT | Дата последнего обновления | DEFAULT CURRENT_TIMESTAMP |

**Индексы:**
- `idx_models_name` на поле `name` для быстрого поиска по имени
- `idx_models_active` на поле `is_active` для фильтрации активных моделей

**Примечание:** API-ключи хранятся в файле `.env`, а не в базе данных. В таблице хранится только имя переменной окружения (api_id), например `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`.

**Пример записи:**
```
id: 1
name: "GPT-4"
api_url: "https://api.openai.com/v1/chat/completions"
api_id: "OPENAI_API_KEY"
provider_type: "openai"
is_active: 1
created_at: "2024-01-15 10:00:00"
updated_at: "2024-01-15 10:00:00"
```

## Таблица: results (Сохраненные результаты)

Хранит результаты запросов, которые пользователь отметил для сохранения.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| id | INTEGER | Первичный ключ, автоинкремент | PRIMARY KEY, NOT NULL, AUTOINCREMENT |
| prompt_id | INTEGER | Ссылка на промт из таблицы prompts | NOT NULL, FOREIGN KEY REFERENCES prompts(id) ON DELETE CASCADE |
| model_name | TEXT | Название модели, которая дала ответ | NOT NULL |
| response_text | TEXT | Текст ответа от модели | NOT NULL |
| saved_at | TEXT | Дата и время сохранения | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| response_metadata | TEXT | Дополнительные метаданные (JSON): токены, время ответа и т.д. | NULL |

**Индексы:**
- `idx_results_prompt_id` на поле `prompt_id` для быстрого поиска результатов по промту
- `idx_results_model_name` на поле `model_name` для фильтрации по модели
- `idx_results_saved_at` на поле `saved_at` для сортировки по дате

**Пример записи:**
```
id: 1
prompt_id: 1
model_name: "GPT-4"
response_text: "Машинное обучение - это..."
saved_at: "2024-01-15 14:35:00"
response_metadata: '{"tokens_used": 150, "response_time": 2.3}'
```

## Таблица: settings (Настройки программы)

Хранит настройки приложения в формате ключ-значение.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| id | INTEGER | Первичный ключ, автоинкремент | PRIMARY KEY, NOT NULL, AUTOINCREMENT |
| key | TEXT | Ключ настройки | NOT NULL, UNIQUE |
| value | TEXT | Значение настройки | NOT NULL |
| description | TEXT | Описание настройки | NULL |
| updated_at | TEXT | Дата последнего обновления | DEFAULT CURRENT_TIMESTAMP |

**Индексы:**
- `idx_settings_key` на поле `key` для быстрого поиска по ключу

**Предопределенные настройки:**
- `request_timeout` - таймаут запросов в секундах (по умолчанию: 30)
- `max_concurrent_requests` - максимальное количество одновременных запросов (по умолчанию: 5)
- `auto_save_prompts` - автоматическое сохранение всех промтов (1 или 0, по умолчанию: 1)
- `default_provider` - провайдер по умолчанию (по умолчанию: "openai")
- `ui_theme` - тема интерфейса (по умолчанию: "default")
- `log_level` - уровень логирования (DEBUG, INFO, WARNING, ERROR, по умолчанию: "INFO")

**Пример записи:**
```
id: 1
key: "request_timeout"
value: "30"
description: "Таймаут запросов к API в секундах"
updated_at: "2024-01-15 10:00:00"
```

## Связи между таблицами

```
prompts (1) ──────────< (N) results
   │                        │
   │                        │
   └── prompt_id ───────────┘
```

- Один промт может иметь множество сохраненных результатов
- При удалении промта каскадно удаляются все связанные результаты (ON DELETE CASCADE)

## SQL-скрипт создания базы данных

```sql
-- Создание таблицы prompts
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    prompt TEXT NOT NULL,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date);

-- Создание таблицы models
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_url TEXT NOT NULL,
    api_id TEXT NOT NULL,
    provider_type TEXT NOT NULL DEFAULT 'custom',
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_models_name ON models(name);
CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active);

-- Создание таблицы results
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    response_text TEXT NOT NULL,
    saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response_metadata TEXT,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_results_prompt_id ON results(prompt_id);
CREATE INDEX IF NOT EXISTS idx_results_model_name ON results(model_name);
CREATE INDEX IF NOT EXISTS idx_results_saved_at ON results(saved_at);

-- Создание таблицы settings
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);

-- Вставка начальных настроек
INSERT OR IGNORE INTO settings (key, value, description) VALUES
    ('request_timeout', '30', 'Таймаут запросов к API в секундах'),
    ('max_concurrent_requests', '5', 'Максимальное количество одновременных запросов'),
    ('auto_save_prompts', '1', 'Автоматическое сохранение всех промтов'),
    ('default_provider', 'openai', 'Провайдер по умолчанию'),
    ('ui_theme', 'default', 'Тема интерфейса'),
    ('log_level', 'INFO', 'Уровень логирования');
```

## Миграции и версионирование

Для отслеживания версии схемы БД рекомендуется добавить таблицу `schema_version`:

```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Рекомендации по использованию

1. **Безопасность API-ключей**: API-ключи никогда не должны попадать в БД. Они хранятся только в `.env` файле, который должен быть в `.gitignore`.

2. **Резервное копирование**: Регулярно создавайте резервные копии файла базы данных (обычно `chatlist.db`).

3. **Оптимизация**: При большом количестве записей в `results` рассмотрите возможность архивации старых записей.

4. **Полнотекстовый поиск**: Для улучшения поиска по текстам промтов и ответов можно использовать FTS (Full-Text Search) в SQLite, создав виртуальные таблицы FTS5.
