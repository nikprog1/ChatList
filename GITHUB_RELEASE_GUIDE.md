# Инструкция по публикации ChatList на GitHub Release

## Подготовка к релизу

### Шаг 1: Обновление версии

1. Откройте файл `version.py`
2. Обновите версию (например, с `1.0.0` на `1.0.1`)
3. Сохраните изменения

### Шаг 2: Обновление CHANGELOG.md

1. Откройте файл `CHANGELOG.md`
2. Добавьте новую секцию с версией и датой
3. Перечислите все изменения (новые функции, исправления, улучшения)
4. Сохраните изменения

### Шаг 3: Сборка EXE файла

```powershell
# Убедитесь, что все зависимости установлены
pip install -r requirements.txt

# Соберите EXE файл
pyinstaller MinimalProgram.spec --clean --noconfirm
```

Проверьте, что файл `dist/ChatList-X.X.X.exe` создан успешно.

### Шаг 4: Создание установщика (опционально)

Если используете Inno Setup:

```powershell
# Обновите версию в ChatList.iss
# Затем скомпилируйте установщик через Inno Setup Compiler
# Или используйте командную строку:
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" ChatList.iss
```

## Создание GitHub Release

### Шаг 5: Подготовка файлов для релиза

Создайте папку `release` и скопируйте туда:

```powershell
# Создайте папку для релиза
New-Item -ItemType Directory -Path "release" -Force

# Скопируйте EXE файл
Copy-Item "dist\ChatList-1.0.0.exe" -Destination "release\"

# Скопируйте установщик (если есть)
Copy-Item "installer\ChatList-Setup-1.0.0.exe" -Destination "release\"

# Скопируйте README.md
Copy-Item "README.md" -Destination "release\"

# Скопируйте CHANGELOG.md
Copy-Item "CHANGELOG.md" -Destination "release\"
```

### Шаг 6: Создание тега версии

```powershell
# Убедитесь, что все изменения закоммичены
git add .
git commit -m "Release v1.0.0"

# Создайте тег
git tag -a v1.0.0 -m "Release version 1.0.0"

# Отправьте тег на GitHub
git push origin v1.0.0
```

### Шаг 7: Создание Release на GitHub

1. Перейдите на GitHub в ваш репозиторий
2. Нажмите на "Releases" в правой панели
3. Нажмите "Draft a new release"
4. Выберите тег `v1.0.0` (или создайте новый)
5. Заполните заголовок: `ChatList v1.0.0`
6. Вставьте описание из шаблона `RELEASE_NOTES_TEMPLATE.md` или `CHANGELOG.md`
7. Загрузите файлы:
   - `ChatList-1.0.0.exe` (основной исполняемый файл)
   - `ChatList-Setup-1.0.0.exe` (установщик, если есть)
8. Отметьте "This is a pre-release" если это бета-версия
9. Нажмите "Publish release"

### Шаг 8: Обновление GitHub Pages (опционально)

Если настроен GitHub Pages:

1. Обновите файл `docs/index.html` (лендинг)
2. Закоммитьте и запушьте изменения:
   ```powershell
   git add docs/index.html
   git commit -m "Update landing page for v1.0.0"
   git push origin main
   ```
3. GitHub Pages автоматически обновится

## Автоматизация через GitHub Actions (опционально)

Создайте файл `.github/workflows/release.yml` для автоматической сборки и публикации релизов.

## Чеклист перед релизом

- [ ] Версия обновлена в `version.py`
- [ ] `CHANGELOG.md` обновлен
- [ ] EXE файл собран и протестирован
- [ ] Установщик создан (если используется)
- [ ] Все изменения закоммичены
- [ ] Тег версии создан и отправлен на GitHub
- [ ] Release создан на GitHub с правильным описанием
- [ ] Файлы загружены в Release
- [ ] GitHub Pages обновлен (если используется)

## Полезные ссылки

- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
