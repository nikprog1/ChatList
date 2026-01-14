"""
Скрипт для настройки репозитория перед публикацией.
Заменяет плейсхолдеры на реальные значения.
"""
import os
import re
import sys
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Конфигурация - автоматически определено из git remote
REPO_USERNAME = "nikprog1"  # GitHub username
REPO_NAME = "ChatList"  # Название репозитория
VERSION = "1.0.0"  # Версия из version.py

def replace_in_file(file_path: Path, replacements: dict):
    """Заменяет текст в файле."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Обновлен: {file_path}")
            return True
        else:
            print(f"[SKIP] Пропущен (нет изменений): {file_path}")
            return False
    except Exception as e:
        print(f"[ERROR] Ошибка при обработке {file_path}: {e}")
        return False

def main():
    """Основная функция."""
    print("=" * 60)
    print("Настройка репозитория для публикации")
    print("=" * 60)
    print(f"\nТекущие значения:")
    print(f"  Username: {REPO_USERNAME}")
    print(f"  Repository: {REPO_NAME}")
    print(f"  Version: {VERSION}")
    print(f"\nВНИМАНИЕ: Значения определены из git remote")
    print("=" * 60)
    
    # Подготовка замен
    repo_placeholder = "yourusername/chatlist"
    repo_actual = f"{REPO_USERNAME}/{REPO_NAME}"
    
    replacements = {
        "yourusername/chatlist": repo_actual,
        "yourusername": REPO_USERNAME,
        "chatlist": REPO_NAME,
    }
    
    # Файлы для обработки
    files_to_update = [
        "docs/index.html",
        "docs/index-simple.html",
        "RELEASE_NOTES_SIMPLE.md",
        "RELEASE_NOTES_TEMPLATE.md",
        "ChatList.iss",
    ]
    
    print("\nОбработка файлов...\n")
    updated_count = 0
    
    for file_path_str in files_to_update:
        file_path = Path(file_path_str)
        if file_path.exists():
            if replace_in_file(file_path, replacements):
                updated_count += 1
        else:
            print(f"[WARN] Файл не найден: {file_path}")
    
    print(f"\n{'=' * 60}")
    print(f"Готово! Обновлено файлов: {updated_count}")
    print(f"{'=' * 60}")
    print(f"\nСледующие шаги:")
    print(f"1. Проверьте обновленные файлы")
    print(f"2. Обновите version.py если нужно (текущая версия: {VERSION})")
    print(f"3. Соберите EXE: pyinstaller MinimalProgram.spec --clean --noconfirm")
    print(f"4. Создайте Release на GitHub")
    print(f"5. Настройте GitHub Pages (Settings → Pages)")

if __name__ == "__main__":
    main()
