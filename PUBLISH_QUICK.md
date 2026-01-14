# ⚡ Быстрая публикация ChatList

Минимальная инструкция для быстрой публикации.

## 📋 3 шага

### 1️⃣ Обновите версию и соберите
```powershell
# Обновите version.py
# Затем:
pyinstaller MinimalProgram.spec --clean --noconfirm
```

### 2️⃣ Создайте Release на GitHub
1. GitHub → Releases → Draft a new release
2. Тег: `v1.0.0`
3. Заголовок: `ChatList v1.0.0`
4. Описание: Скопируйте из `RELEASE_NOTES_SIMPLE.md`
5. Загрузите: `dist/ChatList-1.0.0.exe`
6. Publish

### 3️⃣ Настройте Pages
1. Settings → Pages
2. Source: branch `main`, folder `/docs`
3. Save

**Готово!** 🎉

---

## 📝 Обновление ссылок

Перед публикацией обновите в `docs/index.html`:
- `yourusername/chatlist` → ваш репозиторий (3 места)

---

**Детальная инструкция**: `PUBLISH_GUIDE.md`
