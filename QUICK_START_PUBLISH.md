# Быстрый старт: Публикация ChatList на GitHub

## 📋 Что было подготовлено

1. **GITHUB_RELEASE_GUIDE.md** - Подробная пошаговая инструкция
2. **CHANGELOG.md** - История изменений
3. **RELEASE_NOTES_TEMPLATE.md** - Шаблон описания релиза
4. **PUBLISH_CHECKLIST.md** - Чеклист перед публикацией
5. **docs/index.html** - HTML-лендинг для GitHub Pages
6. **.github/workflows/release.yml** - Автоматическая сборка и публикация
7. **.github/workflows/pages.yml** - Автоматическое развертывание GitHub Pages

## 🚀 Быстрая публикация (5 шагов)

### Шаг 1: Обновите ссылки в HTML

Откройте `docs/index.html` и замените `yourusername/chatlist` на ваш репозиторий:

```html
<!-- Найдите и замените все вхождения: -->
https://github.com/yourusername/chatlist
<!-- На: -->
https://github.com/ВАШ_USERNAME/ВАШ_РЕПОЗИТОРИЙ
```

### Шаг 2: Обновите версию

```powershell
# Откройте version.py и проверьте версию
# Если нужно изменить - измените и пересоберите EXE
```

### Шаг 3: Соберите EXE

```powershell
pyinstaller MinimalProgram.spec --clean --noconfirm
```

### Шаг 4: Создайте тег и Release

```powershell
# Создайте тег
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Или создайте Release через веб-интерфейс GitHub:
# 1. Перейдите в Releases → Draft a new release
# 2. Выберите тег v1.0.0
# 3. Скопируйте текст из RELEASE_NOTES_TEMPLATE.md
# 4. Загрузите ChatList-1.0.0.exe
# 5. Нажмите "Publish release"
```

### Шаг 5: Настройте GitHub Pages

1. Перейдите в Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` / folder: `/docs`
4. Save

Через несколько минут ваш сайт будет доступен по адресу:
`https://ВАШ_USERNAME.github.io/ВАШ_РЕПОЗИТОРИЙ/`

## 📝 Детальная инструкция

См. **GITHUB_RELEASE_GUIDE.md** для подробной инструкции.

## ✅ Чеклист

Используйте **PUBLISH_CHECKLIST.md** перед каждым релизом.

## 🎨 Кастомизация лендинга

Отредактируйте `docs/index.html`:
- Измените цвета (найдите `#667eea` и `#764ba2`)
- Добавьте скриншоты
- Измените текст описаний
- Обновите ссылки на скачивание

## 🔄 Автоматизация

Если настроены GitHub Actions (`.github/workflows/`):
- При создании тега `v*` автоматически соберется EXE и создастся Release
- При изменении файлов в `docs/` автоматически обновится GitHub Pages

## ❓ Проблемы?

1. **GitHub Pages не обновляется**: Подождите 5-10 минут, очистите кэш браузера
2. **Release не создается**: Проверьте права доступа к репозиторию
3. **EXE не скачивается**: Проверьте, что файл загружен в Assets релиза
