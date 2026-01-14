# 📦 Руководство по публикации ChatList на GitHub

Простое пошаговое руководство для публикации приложения на GitHub Release и GitHub Pages.

## 🎯 Быстрый старт (5 шагов)

### Шаг 1: Обновите версию
Откройте `version.py` и измените версию (например, `1.0.0` → `1.0.1`)

### Шаг 2: Обновите CHANGELOG.md
Добавьте новую секцию с изменениями в файл `CHANGELOG.md`

### Шаг 3: Соберите EXE
```powershell
pyinstaller MinimalProgram.spec --clean --noconfirm
```

### Шаг 4: Создайте Release на GitHub
1. Перейдите в ваш репозиторий на GitHub
2. Нажмите "Releases" → "Draft a new release"
3. Выберите тег `v1.0.0` (или создайте новый)
4. Заполните описание (используйте `RELEASE_NOTES_TEMPLATE.md`)
5. Загрузите файл `dist/ChatList-1.0.0.exe`
6. Нажмите "Publish release"

### Шаг 5: Настройте GitHub Pages
1. Settings → Pages
2. Source: "Deploy from a branch"
3. Branch: `main`, folder: `/docs`
4. Save

Готово! 🎉

---

## 📝 Подробная инструкция

### Подготовка к релизу

#### 1. Обновление версии
```python
# version.py
__version__ = "1.0.1"  # Обновите версию
```

#### 2. Обновление CHANGELOG.md
Добавьте новую секцию:
```markdown
## [1.0.1] - 2025-01-XX

### Добавлено
- Новая функция

### Исправлено
- Исправлен баг
```

#### 3. Сборка приложения
```powershell
# Установите зависимости (если нужно)
pip install -r requirements.txt

# Соберите EXE
pyinstaller MinimalProgram.spec --clean --noconfirm

# Проверьте, что файл создан
Test-Path dist\ChatList-1.0.1.exe
```

### Создание GitHub Release

#### Вариант A: Через веб-интерфейс (рекомендуется)

1. **Создайте тег** (опционально, можно создать при создании Release):
   ```powershell
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin v1.0.1
   ```

2. **Создайте Release**:
   - Перейдите: `https://github.com/ВАШ_USERNAME/ВАШ_РЕПОЗИТОРИЙ/releases`
   - Нажмите "Draft a new release"
   - Выберите тег или создайте новый
   - Заголовок: `ChatList v1.0.1`
   - Описание: Скопируйте из `RELEASE_NOTES_TEMPLATE.md` и обновите версию
   - Загрузите файлы:
     - `ChatList-1.0.1.exe` (основной файл)
     - `ChatList-Setup-1.0.1.exe` (если есть установщик)
   - Нажмите "Publish release"

#### Вариант B: Через GitHub CLI
```powershell
# Установите GitHub CLI (если нет)
# winget install GitHub.cli

# Создайте Release
gh release create v1.0.1 `
  --title "ChatList v1.0.1" `
  --notes-file RELEASE_NOTES_TEMPLATE.md `
  dist/ChatList-1.0.1.exe
```

### Настройка GitHub Pages

1. **Обновите ссылки в `docs/index.html`**:
   - Замените `yourusername/chatlist` на ваш репозиторий (3 места)
   - Обновите версию в заголовке

2. **Настройте Pages**:
   - Перейдите: Settings → Pages
   - Source: "Deploy from a branch"
   - Branch: `main` (или `master`)
   - Folder: `/docs`
   - Нажмите "Save"

3. **Проверьте**:
   - Через 2-5 минут сайт будет доступен по адресу:
   - `https://ВАШ_USERNAME.github.io/ВАШ_РЕПОЗИТОРИЙ/`

### Автоматизация (опционально)

Если настроены GitHub Actions (`.github/workflows/`):
- **Автоматическая сборка**: При создании тега `v*` автоматически соберется EXE и создастся Release
- **Автоматический Pages**: При изменении файлов в `docs/` автоматически обновится сайт

## ✅ Чеклист перед релизом

Используйте `PUBLISH_CHECKLIST.md` для проверки всех пунктов.

## 📚 Дополнительные файлы

- **GITHUB_RELEASE_GUIDE.md** - Детальная инструкция
- **QUICK_START_PUBLISH.md** - Быстрый старт
- **RELEASE_NOTES_TEMPLATE.md** - Шаблон описания релиза
- **PUBLISH_CHECKLIST.md** - Чеклист
- **docs/index.html** - HTML-лендинг

## ❓ Частые вопросы

**Q: Как обновить ссылки в лендинге?**  
A: Откройте `docs/index.html` и замените `yourusername/chatlist` на ваш репозиторий.

**Q: GitHub Pages не обновляется**  
A: Подождите 5-10 минут, очистите кэш браузера (Ctrl+F5).

**Q: Как создать тег?**  
A: `git tag -a v1.0.1 -m "Release version 1.0.1"` затем `git push origin v1.0.1`

**Q: EXE файл не скачивается**  
A: Проверьте, что файл загружен в раздел "Assets" релиза.

---

**Удачной публикации! 🚀**
