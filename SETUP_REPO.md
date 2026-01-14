# ⚙️ Настройка репозитория перед публикацией

Этот файл содержит инструкции по настройке всех файлов для публикации.

## 🚀 Быстрая настройка (рекомендуется)

### Вариант 1: Автоматическая настройка

1. Откройте `setup_repo.py`
2. Обновите значения в начале файла:
   ```python
   REPO_USERNAME = "ваш_username"  # Ваш GitHub username
   REPO_NAME = "название_репозитория"  # Название репозитория
   VERSION = "1.0.0"  # Версия (должна совпадать с version.py)
   ```
3. Запустите скрипт:
   ```powershell
   python setup_repo.py
   ```

Скрипт автоматически обновит все необходимые файлы.

### Вариант 2: Ручная настройка

## 📝 Файлы, которые нужно обновить

### 1. HTML-лендинги

#### `docs/index.html`
Замените `yourusername/chatlist` на ваш репозиторий в **3 местах**:
- Строка ~303: Ссылка на скачивание EXE
- Строка ~306: Ссылка на скачивание установщика
- Строка ~338: Ссылка на CHANGELOG.md
- Строки ~344-346: Ссылки в футере (GitHub, Issues, Releases)

#### `docs/index-simple.html`
Замените `yourusername/chatlist` на ваш репозиторий в **3 местах**:
- Строка ~143: Ссылка на скачивание EXE
- Строка ~146: Ссылка на скачивание установщика
- Строки ~179-181: Ссылки в футере

**Формат замены:**
```
https://github.com/yourusername/chatlist
↓
https://github.com/ВАШ_USERNAME/ВАШ_РЕПОЗИТОРИЙ
```

### 2. Шаблоны релизов

#### `RELEASE_NOTES_SIMPLE.md`
- Строка ~56: Ссылка на Issues
- Строка ~60: Ссылка на скачивание

#### `RELEASE_NOTES_TEMPLATE.md`
- Строка ~59: Ссылка на Issues
- Строка ~67: Ссылка на скачивание

### 3. Inno Setup скрипт

#### `ChatList.iss`
- Строка ~7: `#define MyAppURL` - обновите URL репозитория

### 4. Версия

#### `version.py`
Убедитесь, что версия актуальна:
```python
__version__ = "1.0.0"  # Обновите при необходимости
```

## ✅ Чеклист настройки

- [ ] Обновлен `setup_repo.py` с правильными значениями
- [ ] Запущен `setup_repo.py` (или обновлены файлы вручную)
- [ ] Проверены все ссылки в `docs/index.html`
- [ ] Проверены все ссылки в `docs/index-simple.html`
- [ ] Обновлена версия в `version.py`
- [ ] Обновлены ссылки в `RELEASE_NOTES_SIMPLE.md`
- [ ] Обновлены ссылки в `RELEASE_NOTES_TEMPLATE.md`
- [ ] Обновлен URL в `ChatList.iss`

## 🔍 Проверка

После настройки проверьте:

1. **Поиск плейсхолдеров:**
   ```powershell
   Select-String -Path "docs\*.html","*.md","*.iss" -Pattern "yourusername|chatlist" -CaseSensitive
   ```
   Не должно быть найдено совпадений (кроме этого файла и setup_repo.py).

2. **Проверка версии:**
   ```powershell
   python -c "from version import __version__; print(__version__)"
   ```
   Версия должна совпадать во всех файлах.

## 🚀 После настройки

1. Соберите EXE:
   ```powershell
   pyinstaller MinimalProgram.spec --clean --noconfirm
   ```

2. Создайте Release на GitHub (см. `PUBLISH_GUIDE.md`)

3. Настройте GitHub Pages:
   - Settings → Pages
   - Source: branch `main`, folder `/docs`
   - Save

## 📚 Дополнительная информация

- **PUBLISH_GUIDE.md** - Полная инструкция по публикации
- **PUBLISH_QUICK.md** - Быстрая инструкция
- **PUBLISH_CHECKLIST.md** - Чеклист перед релизом

---

**Готово к публикации! 🎉**
