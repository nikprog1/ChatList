# GitHub Pages для ChatList

Эта папка содержит файлы для GitHub Pages.

## Структура

- `index.html` - главная страница лендинга

## Настройка GitHub Pages

1. Перейдите в Settings → Pages вашего репозитория
2. В разделе "Source" выберите "Deploy from a branch"
3. Выберите ветку `main` и папку `/docs`
4. Нажмите "Save"

GitHub автоматически опубликует содержимое папки `docs` на `https://yourusername.github.io/chatlist/`

## Обновление лендинга

1. Отредактируйте `docs/index.html`
2. Обновите версию в заголовке
3. Обновите ссылки на скачивание (если нужно)
4. Закоммитьте и запушьте изменения:
   ```powershell
   git add docs/index.html
   git commit -m "Update landing page"
   git push origin main
   ```

## Кастомизация

Отредактируйте `docs/index.html` для изменения:
- Цветовой схемы
- Текста и описаний
- Ссылок на скачивание
- Скриншотов (если добавите)
