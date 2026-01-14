# Инструкции по сборке ChatList в EXE файл

## Требования

1. **Python 3.11+** установлен и доступен в PATH
2. **PyInstaller** установлен:
   ```powershell
   pip install pyinstaller
   ```
3. **Все зависимости** установлены:
   ```powershell
   pip install -r requirements.txt
   ```

## Сборка EXE файла

### Способ 1: Использование .spec файла (рекомендуется)

1. Убедитесь, что вы находитесь в директории проекта:
   ```powershell
   cd C:\Work\ChatList
   ```

2. Запустите сборку:
   ```powershell
   pyinstaller MinimalProgram.spec --clean --noconfirm
   ```

3. Готовый EXE файл будет в папке `dist\ChatList.exe`

### Способ 2: Прямая сборка без .spec файла

```powershell
pyinstaller --name=ChatList --onefile --windowed --hidden-import=PyQt5.QtCore --hidden-import=PyQt5.QtGui --hidden-import=PyQt5.QtWidgets --hidden-import=sqlite3 --hidden-import=httpx --hidden-import=dotenv --hidden-import=asyncio --hidden-import=markdown --hidden-import=db --hidden-import=models --hidden-import=network --hidden-import=models_dialog --hidden-import=history_widget main.py
```

## Опции сборки

### Основные параметры:
- `--name=ChatList` - имя выходного файла
- `--onefile` - создание одного EXE файла (все включено)
- `--windowed` или `--noconsole` - запуск без консоли (GUI приложение)
- `--clean` - очистка временных файлов перед сборкой
- `--noconfirm` - не спрашивать подтверждения при перезаписи

### Включение модулей:
- `--hidden-import=module_name` - принудительное включение модуля

### Исключение модулей (для уменьшения размера):
- `--exclude-module=module_name` - исключение ненужного модуля

## Результат сборки

После успешной сборки:
- **EXE файл:** `dist\ChatList.exe`
- **Размер:** ~43 МБ (зависит от включенных библиотек)
- **Временные файлы:** в папке `build\` (можно удалить)

## Проверка сборки

1. **Проверка размера файла:**
   ```powershell
   Get-Item dist\ChatList.exe | Select-Object Name, Length
   ```

2. **Запуск EXE файла:**
   ```powershell
   .\dist\ChatList.exe
   ```

## Важные замечания

### 1. Файлы окружения (.env, .env.local)
EXE файл НЕ включает файлы `.env` или `.env.local`. Пользователь должен создать их самостоятельно рядом с EXE файлом.

**Рекомендация:** Создайте файл `.env.example` и инструкцию для пользователей.

### 2. База данных
База данных `chatlist.db` будет создаваться автоматически рядом с EXE файлом при первом запуске.

### 3. Распространение
Для распространения EXE файла:
- **Минимальный набор:** только `ChatList.exe`
- **Рекомендуется включить:**
  - `ChatList.exe`
  - `.env.example` (как шаблон)
  - `README.md` (с инструкциями по настройке)

### 4. Антивирусы
Некоторые антивирусы могут выдавать ложные срабатывания на PyInstaller-собранные EXE файлы. Это нормально, так как PyInstaller упаковывает Python-приложение в один файл.

**Решение:** Добавить исключение для папки `dist\` или подписать EXE файл цифровой подписью (требует сертификата).

## Оптимизация размера

### Уменьшение размера EXE:

1. **Исключить ненужные модули:**
   ```python
   excludes=[
       'matplotlib',
       'numpy',
       'pandas',
       'PIL',
       'tkinter',
   ]
   ```

2. **Использовать UPX** (если установлен):
   ```python
   upx=True
   ```

3. **Оптимизация Python кода:**
   - Использовать `--optimize=2` (но может сломать некоторые библиотеки)

### Пример минимального .spec файла:

```python
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['db', 'models', 'network', 'models_dialog', 'history_widget'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'PIL', 'tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
```

## Устранение проблем

### Проблема: "ModuleNotFoundError" при запуске EXE

**Решение:** Добавить недостающий модуль в `hiddenimports`:
```python
hiddenimports=[
    # ...
    'недостающий_модуль',
]
```

### Проблема: "DLL load failed"

**Решение:** Убедиться, что все DLL файлы включены. Иногда нужно добавить пути к библиотекам:
```python
binaries=[
    ('path/to/dll', '.'),
]
```

### Проблема: Очень большой размер EXE файла

**Решение:**
1. Проверить, какие модули включены
2. Исключить ненужные модули
3. Использовать `--exclude-module` для больших библиотек

### Проблема: EXE не запускается на другой машине

**Решение:**
1. Убедиться, что используется `--onefile`
2. Проверить, что все зависимости включены
3. Тестировать на чистой системе Windows

## Тестирование EXE файла

### На локальной машине:
```powershell
.\dist\ChatList.exe
```

### На чистой системе:
1. Скопировать `ChatList.exe` на другую машину
2. Создать `.env.local` с API-ключами
3. Запустить EXE файл
4. Проверить создание `chatlist.db`
5. Проверить работу всех функций

## Дополнительные ресурсы

- [Документация PyInstaller](https://pyinstaller.org/)
- [PyInstaller Troubleshooting](https://pyinstaller.org/en/stable/when-things-go-wrong.html)
- [PyInstaller Spec File](https://pyinstaller.org/en/stable/spec-files.html)

## Статус последней сборки

- **Дата:** 10.01.2026 21:58:26
- **Версия PyInstaller:** 6.17.0
- **Python:** 3.14.2
- **Размер EXE:** ~43 МБ
- **Статус:** ✅ Успешно собрано

Файл: `dist\ChatList.exe`
