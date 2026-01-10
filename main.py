"""
Главный модуль приложения ChatList.
Основной интерфейс для работы с промтами и нейросетями.
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QComboBox, QPushButton, 
                             QLabel, QMessageBox)
from PyQt5.QtCore import Qt
from db import Database
from models import ModelManager
from network import RequestManager, send_batch_requests_sync


class PromptInputWidget(QWidget):
    """Виджет для ввода промта."""
    
    def __init__(self, db: Database, on_send_callback=None):
        """
        Инициализация виджета ввода промта.
        
        Args:
            db: Экземпляр Database
            on_send_callback: Функция обратного вызова при отправке промта
        """
        super().__init__()
        self.db = db
        self.on_send_callback = on_send_callback
        self.init_ui()
        self.load_saved_prompts()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel("Ввод промта")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Выбор сохраненного промта
        saved_prompt_layout = QHBoxLayout()
        saved_prompt_label = QLabel("Выбрать сохраненный промт:")
        self.saved_prompts_combo = QComboBox()
        self.saved_prompts_combo.setEditable(False)
        self.saved_prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        saved_prompt_layout.addWidget(saved_prompt_label)
        saved_prompt_layout.addWidget(self.saved_prompts_combo)
        layout.addLayout(saved_prompt_layout)
        
        # Или ввод нового промта
        new_prompt_label = QLabel("Или введите новый промт:")
        layout.addWidget(new_prompt_label)
        
        # Текстовое поле для ввода промта
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Введите ваш промт здесь...")
        self.prompt_input.setMinimumHeight(150)
        layout.addWidget(self.prompt_input)
        
        # Поле для тегов (опционально)
        tags_layout = QHBoxLayout()
        tags_label = QLabel("Теги (через запятую):")
        self.tags_input = QTextEdit()
        self.tags_input.setPlaceholderText("обучение, ИИ, основы")
        self.tags_input.setMaximumHeight(50)
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.tags_input)
        layout.addLayout(tags_layout)
        
        # Кнопка отправки
        self.send_button = QPushButton("Отправить")
        self.send_button.clicked.connect(self.on_send_clicked)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        layout.addWidget(self.send_button)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_saved_prompts(self):
        """Загрузка сохраненных промтов в выпадающий список."""
        self.saved_prompts_combo.clear()
        self.saved_prompts_combo.addItem("-- Новый промт --", None)
        
        prompts = self.db.get_all_prompts()
        for prompt in prompts:
            # Отображение промта с ограничением по длине
            display_text = prompt['prompt'][:50] + "..." if len(prompt['prompt']) > 50 else prompt['prompt']
            display_text = f"[{prompt['date']}] {display_text}"
            self.saved_prompts_combo.addItem(display_text, prompt)
    
    def on_prompt_selected(self, index):
        """Обработка выбора сохраненного промта."""
        if index > 0:  # Не "Новый промт"
            prompt_data = self.saved_prompts_combo.itemData(index)
            if prompt_data:
                self.prompt_input.setPlainText(prompt_data['prompt'])
                self.tags_input.setPlainText(prompt_data.get('tags', ''))
    
    def on_send_clicked(self):
        """Обработка нажатия кнопки отправки."""
        prompt_text = self.prompt_input.toPlainText().strip()
        
        if not prompt_text:
            QMessageBox.warning(self, "Предупреждение", "Пожалуйста, введите промт!")
            return
        
        # Автосохранение нового промта в БД (если это не выбранный промт)
        if self.saved_prompts_combo.currentIndex() == 0:  # "Новый промт"
            tags = self.tags_input.toPlainText().strip() or None
            prompt_id = self.db.add_prompt(prompt_text, tags)
            self.load_saved_prompts()  # Обновить список
        else:
            # Если выбран сохраненный промт, получить его ID
            prompt_data = self.saved_prompts_combo.itemData(self.saved_prompts_combo.currentIndex())
            prompt_id = prompt_data['id'] if prompt_data else None
        
        # Вызов функции обратного вызова
        if self.on_send_callback:
            self.on_send_callback(prompt_text, prompt_id)
    
    def clear_input(self):
        """Очистка полей ввода."""
        self.prompt_input.clear()
        self.tags_input.clear()
        self.saved_prompts_combo.setCurrentIndex(0)
    
    def get_current_prompt(self) -> str:
        """Получение текущего текста промта."""
        return self.prompt_input.toPlainText().strip()


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        """Инициализация главного окна."""
        super().__init__()
        try:
            print("Инициализация базы данных...")
            self.db = Database()
            print("База данных инициализирована")
            print("Инициализация менеджера моделей...")
            self.model_manager = ModelManager(self.db)
            print("Менеджер моделей инициализирован")
            print("Инициализация менеджера запросов...")
            self.request_manager = RequestManager(self.db)
            print("Менеджер запросов инициализирован")
            
            print("Инициализация интерфейса...")
            self.init_ui()
            print("Интерфейс инициализирован")
        except Exception as e:
            print(f"Ошибка при инициализации: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def init_ui(self):
        """Инициализация интерфейса главного окна."""
        self.setWindowTitle("ChatList - Сравнение ответов нейросетей")
        
        # Центрирование окна на экране
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        window_width = 800
        window_height = 600
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Виджет ввода промта
        self.prompt_input_widget = PromptInputWidget(self.db, self.on_prompt_sent)
        main_layout.addWidget(self.prompt_input_widget)
        
        # Заглушка для будущей таблицы результатов (будет добавлена на этапе 6)
        results_label = QLabel("Таблица результатов появится здесь после отправки промта")
        results_label.setAlignment(Qt.AlignCenter)
        results_label.setStyleSheet("color: gray; padding: 20px;")
        main_layout.addWidget(results_label)
        
        self.results_widget = results_label  # Временно храним ссылку для будущей замены
    
    def on_prompt_sent(self, prompt_text: str, prompt_id: int):
        """
        Обработка отправки промта.
        
        Args:
            prompt_text: Текст промта
            prompt_id: ID промта в БД
        """
        # Получить активные модели
        active_models = self.model_manager.get_active_models()
        
        if not active_models:
            QMessageBox.warning(
                self, 
                "Предупреждение", 
                "Нет активных моделей! Пожалуйста, добавьте модели в настройках."
            )
            return
        
        # Проверить наличие API-ключей
        models_with_keys = [m for m in active_models if m.has_api_key()]
        if not models_with_keys:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "У активных моделей не найдены API-ключи! Проверьте файл .env"
            )
            return
        
        # Показать сообщение о начале отправки
        QMessageBox.information(
            self,
            "Информация",
            f"Отправка запроса к {len(models_with_keys)} моделям...\n"
            f"Это временное сообщение. На этапе 6 здесь будет таблица результатов."
        )
        
        # TODO: На этапе 6 здесь будет отправка запросов и отображение результатов
        # Временная заглушка
        print(f"Промт отправлен: {prompt_text}")
        print(f"ID промта: {prompt_id}")
        print(f"Активных моделей: {len(models_with_keys)}")
    
    def closeEvent(self, event):
        """Обработка закрытия приложения."""
        self.db.close()
        event.accept()


def main():
    """Главная функция запуска приложения."""
    try:
        app = QApplication(sys.argv)
        
        # Настройка стиля приложения
        app.setStyle('Fusion')
        
        window = MainWindow()
        window.show()
        window.raise_()  # Поднять окно на передний план
        window.activateWindow()  # Активировать окно
        
        print("Приложение запущено. Окно должно быть видно на экране.")
        print("Если окно не видно, проверьте, что оно не свернуто в трей.")
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
