"""
Главный модуль приложения ChatList.
Основной интерфейс для работы с промтами и нейросетями.
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QComboBox, QPushButton, 
                             QLabel, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QCheckBox, QProgressBar, QTabWidget, QLineEdit,
                             QDialog, QTextBrowser, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from db import Database
from models import ModelManager, Model
from network import RequestManager, send_batch_requests_sync
from models_dialog import ModelsManagementWidget
from history_widget import HistoryWidget
from prompt_improver import PromptImprover
from typing import Dict, Tuple, Optional, List


class PromptInputWidget(QWidget):
    """Виджет для ввода промта."""
    
    def __init__(self, db: Database, model_manager: ModelManager = None, on_send_callback=None):
        """
        Инициализация виджета ввода промта.
        
        Args:
            db: Экземпляр Database
            model_manager: Менеджер моделей для улучшения промтов
            on_send_callback: Функция обратного вызова при отправке промта
        """
        super().__init__()
        self.db = db
        self.model_manager = model_manager
        self.on_send_callback = on_send_callback
        self.improvement_thread = None  # Поток для улучшения промта
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
        
        # Кнопка фильтрации промтов без результатов
        self.filter_without_results_button = QPushButton("Без результатов")
        self.filter_without_results_button.clicked.connect(self.filter_prompts_without_results)
        self.filter_without_results_button.setToolTip("Показать только промты без сохраненных результатов")
        self.filter_without_results_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 5px 15px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        saved_prompt_layout.addWidget(self.filter_without_results_button)
        
        # Кнопка удаления выбранного промта
        self.delete_prompt_button = QPushButton("Удалить")
        self.delete_prompt_button.clicked.connect(self.delete_selected_prompt)
        self.delete_prompt_button.setEnabled(False)  # Изначально отключена (выбран "Новый промт")
        self.delete_prompt_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 5px 15px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        saved_prompt_layout.addWidget(self.delete_prompt_button)
        
        # Кнопка показа всех промтов
        self.show_all_prompts_button = QPushButton("Все")
        self.show_all_prompts_button.clicked.connect(self.load_saved_prompts)
        self.show_all_prompts_button.setToolTip("Показать все сохраненные промты")
        self.show_all_prompts_button.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                padding: 5px 15px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        saved_prompt_layout.addWidget(self.show_all_prompts_button)
        
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
        self.tags_input.setToolTip("Введите теги через запятую для категоризации промта (опционально)")
        tags_layout.addWidget(tags_label)
        tags_layout.addWidget(self.tags_input)
        layout.addLayout(tags_layout)
        
        # Кнопки отправки и улучшения
        buttons_layout = QHBoxLayout()
        
        # Кнопка улучшения промта
        self.improve_button = QPushButton("✨ Улучшить промт")
        self.improve_button.clicked.connect(self.on_improve_clicked)
        self.improve_button.setToolTip("Улучшить промт с помощью AI-ассистента. Выберите модель для улучшения.")
        self.improve_button.setEnabled(bool(self.model_manager))  # Включаем только если есть model_manager
        self.improve_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #6A1B9A;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        buttons_layout.addWidget(self.improve_button)
        
        buttons_layout.addStretch()
        
        # Кнопка отправки
        self.send_button = QPushButton("Отправить")
        self.send_button.clicked.connect(self.on_send_clicked)
        self.send_button.setToolTip("Отправить промт всем активным моделям. Ответы будут отображены в таблице результатов.")
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
        buttons_layout.addWidget(self.send_button)
        
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_saved_prompts(self):
        """Загрузка сохраненных промтов в выпадающий список."""
        self.saved_prompts_combo.clear()
        self.saved_prompts_combo.addItem("-- Новый промт --", None)
        
        prompts = self.db.get_all_prompts()
        for prompt in prompts:
            # Отображение промта с ID, датой и ограничением по длине
            prompt_id = prompt.get('id', 'N/A')
            prompt_text = prompt['prompt'][:50] + "..." if len(prompt['prompt']) > 50 else prompt['prompt']
            date = prompt.get('date', '')
            display_text = f"ID: {prompt_id} | [{date}] {prompt_text}"
            self.saved_prompts_combo.addItem(display_text, prompt)
    
    def on_prompt_selected(self, index):
        """Обработка выбора сохраненного промта."""
        # Активируем/деактивируем кнопку удаления в зависимости от выбора
        self.delete_prompt_button.setEnabled(index > 0)  # Активна только если выбран сохраненный промт
        
        if index > 0:  # Не "Новый промт"
            prompt_data = self.saved_prompts_combo.itemData(index)
            if prompt_data:
                self.prompt_input.setPlainText(prompt_data['prompt'])
                self.tags_input.setPlainText(prompt_data.get('tags', ''))
        else:
            # Если выбран "Новый промт", очищаем поля
            self.prompt_input.clear()
            self.tags_input.clear()
    
    def filter_prompts_without_results(self):
        """Фильтрация промтов без сохраненных результатов."""
        prompts_without_results = self.db.get_prompts_without_results()
        
        self.saved_prompts_combo.clear()
        self.saved_prompts_combo.addItem("-- Новый промт --", None)
        
        if not prompts_without_results:
            QMessageBox.information(
                self,
                "Информация",
                "Нет промтов без сохраненных результатов.\nВсе промты имеют связанные результаты."
            )
            # Загружаем все промты
            self.load_saved_prompts()
            return
        
        # Добавляем только промты без результатов
        for prompt in prompts_without_results:
            prompt_id = prompt.get('id', 'N/A')
            prompt_text = prompt['prompt'][:50] + "..." if len(prompt['prompt']) > 50 else prompt['prompt']
            date = prompt.get('date', '')
            display_text = f"ID: {prompt_id} | [{date}] {prompt_text} ⚠ (без результатов)"
            self.saved_prompts_combo.addItem(display_text, prompt)
        
        QMessageBox.information(
            self,
            "Фильтр применен",
            f"Найдено промтов без сохраненных результатов: {len(prompts_without_results)}\n\n"
            "Эти промты можно безопасно удалить, так как они не связаны с сохраненными результатами."
        )
    
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
    
    def delete_selected_prompt(self):
        """Удаление выбранного сохраненного промта."""
        current_index = self.saved_prompts_combo.currentIndex()
        
        # Проверяем, что выбран сохраненный промт (не "Новый промт")
        if current_index == 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите сохраненный промт для удаления!")
            return
        
        prompt_data = self.saved_prompts_combo.itemData(current_index)
        if not prompt_data:
            QMessageBox.warning(self, "Предупреждение", "Не удалось получить данные промта!")
            return
        
        prompt_id = prompt_data.get('id')
        prompt_text = prompt_data.get('prompt', '')[:50] + "..." if len(prompt_data.get('prompt', '')) > 50 else prompt_data.get('prompt', '')
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить этот промт?\n\n{prompt_text}\n\nВсе связанные результаты также будут удалены!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Удаление промта (связанные результаты удалятся автоматически благодаря ON DELETE CASCADE)
                success = self.db.delete_prompt(prompt_id)
                
                if success:
                    QMessageBox.information(self, "Успех", "Промт удален успешно!")
                    # Обновляем список промтов
                    self.load_saved_prompts()
                    # Сбрасываем выбор на "Новый промт"
                    self.saved_prompts_combo.setCurrentIndex(0)
                    # Очищаем поля
                    self.prompt_input.clear()
                    self.tags_input.clear()
                else:
                    QMessageBox.warning(self, "Предупреждение", "Не удалось удалить промт!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении промта: {str(e)}")
    
    def on_improve_clicked(self):
        """Обработка нажатия кнопки 'Улучшить промт'."""
        if not self.model_manager:
            QMessageBox.warning(self, "Предупреждение", "Менеджер моделей не доступен")
            return
        
        # Получаем текст промта
        prompt_text = self.prompt_input.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Предупреждение", "Введите промт для улучшения")
            return
        
        # Получаем список активных моделей с OpenRouter провайдером
        active_models = self.model_manager.get_active_models()
        openrouter_models = [m for m in active_models if m.has_api_key() and m.provider_type == 'openrouter']
        
        if not openrouter_models:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Нет доступных моделей для улучшения промтов.\n\n"
                "Добавьте активную модель с типом провайдера 'openrouter' и API-ключом."
            )
            return
        
        # Сохраняем текущий текст на случай ошибки
        self._backup_prompt = prompt_text
        
        # Запускаем улучшение в отдельном потоке для всех моделей
        self.improve_button.setEnabled(False)
        self.improve_button.setText("Улучшение...")
        
        self.improvement_thread = ImprovementThread(prompt_text, openrouter_models)
        self.improvement_thread.finished.connect(self.on_improvement_finished)
        self.improvement_thread.result_ready.connect(self.on_improvement_result_ready)
        self.improvement_thread.start()
    
    def on_improvement_result_ready(self, model_name: str, improvements: Dict):
        """Обработка получения результата улучшения от одной модели."""
        # Этот метод вызывается для каждого результата, но мы не обрабатываем их по отдельности
        # Все результаты будут обработаны в on_improvement_finished
        pass
    
    def on_improvement_finished(self, all_improvements: Dict):
        """Обработка завершения улучшения промта от всех моделей."""
        self.improve_button.setEnabled(True)
        self.improve_button.setText("✨ Улучшить промт")
        
        # Восстанавливаем исходный промт из backup
        original_prompt = getattr(self, '_backup_prompt', self.prompt_input.toPlainText().strip())
        
        # Проверяем, есть ли ошибка в результатах
        if 'error' in all_improvements and len(all_improvements) == 1:
            # Если только ошибка, показываем её
            QMessageBox.critical(self, "Ошибка", f"Ошибка при улучшении промта:\n\n{all_improvements.get('error', 'Неизвестная ошибка')}")
            return
        
        # Открываем диалог с улучшениями от всех моделей
        dialog = PromptImprovementDialog(self, original_prompt, all_improvements)
        
        if dialog.exec_() == QDialog.Accepted:
            # Если пользователь выбрал вариант, подставляем его в поле ввода
            selected_prompt = dialog.get_selected_prompt()
            if selected_prompt:
                self.prompt_input.setPlainText(selected_prompt)
                # Переключаемся на "Новый промт" в комбобоксе, так как текст изменился
                self.saved_prompts_combo.setCurrentIndex(0)


class RequestThread(QThread):
    """Поток для выполнения запросов к API без блокировки интерфейса."""
    
    finished = pyqtSignal(dict, int)  # Сигнал завершения: (результаты, prompt_id)
    result_ready = pyqtSignal(str, str, str)  # Сигнал результата: (model_name, response, error_or_empty)
    
    def __init__(self, models: List[Model], prompt: str, prompt_id: int, request_manager: RequestManager):
        """
        Инициализация потока запросов.
        
        Args:
            models: Список моделей для отправки запросов
            prompt: Текст промта
            prompt_id: ID промта в БД
            request_manager: Менеджер запросов
        """
        super().__init__()
        self.models = models
        self.prompt = prompt
        self.prompt_id = prompt_id
        self.request_manager = request_manager
    
    def run(self):
        """Выполнение запросов."""
        import asyncio
        
        # Добавляем фразу "Ответь на русском языке" к промту перед отправкой к моделям
        # Это не отображается в поле ввода и не сохраняется в БД
        enhanced_prompt = f"{self.prompt}\n\nОтветь на русском языке."
        
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Отправляем запросы параллельно для скорости
            async def send_all():
                tasks = []
                model_names = []
                
                for model in self.models:
                    task = self.request_manager.send_request(model, enhanced_prompt)
                    tasks.append(task)
                    model_names.append(model.name)
                
                # Дожидаемся всех результатов параллельно
                results_list = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Формируем словарь результатов и эмитируем сигналы
                results = {}
                for model_name, result in zip(model_names, results_list):
                    if isinstance(result, Exception):
                        error_msg = f"Исключение: {str(result)}"
                        results[model_name] = ("", error_msg)
                        # Эмитируем сигнал для обновления интерфейса
                        self.result_ready.emit(model_name, "", error_msg or "")
                    else:
                        response, error = result
                        results[model_name] = (response, error)
                        # Эмитируем сигнал для обновления интерфейса
                        self.result_ready.emit(model_name, response or "", error or "")
                
                return results
            
            results = loop.run_until_complete(send_all())
            
            # Эмитируем финальные результаты
            self.finished.emit(results, self.prompt_id)
        finally:
            loop.close()


class MarkdownViewDialog(QDialog):
    """Диалог для просмотра ответа нейросети в формате Markdown."""
    
    def __init__(self, parent=None, model_name: str = "", response_text: str = "", prompt_text: str = ""):
        """
        Инициализация диалога просмотра Markdown.
        
        Args:
            parent: Родительское окно
            model_name: Название модели
            response_text: Текст ответа (markdown)
            prompt_text: Текст промта (опционально)
        """
        super().__init__(parent)
        self.model_name = model_name
        self.response_text = response_text
        self.prompt_text = prompt_text
        self.init_ui()
        self.load_content()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle(f"Ответ модели: {self.model_name}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout()
        
        # Информация о модели и промте
        info_layout = QVBoxLayout()
        if self.prompt_text:
            prompt_label = QLabel("<b>Промт:</b>")
            prompt_display = QTextEdit()
            prompt_display.setPlainText(self.prompt_text)
            prompt_display.setReadOnly(True)
            prompt_display.setMaximumHeight(100)
            info_layout.addWidget(prompt_label)
            info_layout.addWidget(prompt_display)
        
        model_label = QLabel(f"<b>Модель:</b> {self.model_name}")
        info_layout.addWidget(model_label)
        
        layout.addLayout(info_layout)
        
        # Разделитель
        separator = QLabel("─" * 80)
        layout.addWidget(separator)
        
        # Отображение ответа в формате Markdown
        response_label = QLabel("<b>Ответ:</b>")
        layout.addWidget(response_label)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(True)  # Разрешаем открывать внешние ссылки
        layout.addWidget(self.text_browser)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Кнопка "Копировать"
        copy_button = QPushButton("Копировать текст")
        copy_button.clicked.connect(self.copy_to_clipboard)
        buttons_layout.addWidget(copy_button)
        
        # Кнопка "Закрыть"
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def load_content(self):
        """Загрузка и форматирование содержимого."""
        try:
            # Пытаемся импортировать markdown
            import markdown
            
            # Конвертируем markdown в HTML с расширениями
            # Расширения: codehilite (подсветка кода), fenced_code (блоки кода), tables (таблицы), nl2br (переносы строк)
            html_content = markdown.markdown(
                self.response_text,
                extensions=['codehilite', 'fenced_code', 'tables', 'nl2br']
            )
            
            # Добавляем стили для лучшего отображения
            styled_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        font-size: 14px;
                        line-height: 1.6;
                        color: #333;
                        padding: 15px;
                        background-color: #ffffff;
                    }}
                    h1, h2, h3, h4, h5, h6 {{
                        margin-top: 20px;
                        margin-bottom: 10px;
                        color: #2c3e50;
                    }}
                    h1 {{ font-size: 24px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }}
                    h2 {{ font-size: 20px; border-bottom: 1px solid #e0e0e0; padding-bottom: 8px; }}
                    h3 {{ font-size: 18px; }}
                    code {{
                        background-color: #f5f5f5;
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-family: 'Courier New', monospace;
                        font-size: 0.9em;
                    }}
                    pre {{
                        background-color: #f5f5f5;
                        padding: 15px;
                        border-radius: 5px;
                        overflow-x: auto;
                        border-left: 4px solid #2196F3;
                    }}
                    pre code {{
                        background-color: transparent;
                        padding: 0;
                    }}
                    blockquote {{
                        border-left: 4px solid #2196F3;
                        padding-left: 15px;
                        margin-left: 0;
                        color: #666;
                        font-style: italic;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 15px 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px 12px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f5f5f5;
                        font-weight: bold;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    a {{
                        color: #2196F3;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                    ul, ol {{
                        margin: 10px 0;
                        padding-left: 30px;
                    }}
                    li {{
                        margin: 5px 0;
                    }}
                    p {{
                        margin: 10px 0;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            self.text_browser.setHtml(styled_html)
        except ImportError:
            # Если библиотека markdown не установлена, показываем простой текст
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Библиотека markdown не установлена.\n"
                "Установите её командой: pip install markdown\n"
                "Показываю текст без форматирования."
            )
            self.text_browser.setPlainText(self.response_text)
        except Exception as e:
            # В случае ошибки показываем простой текст
            QMessageBox.warning(
                self,
                "Ошибка форматирования",
                f"Не удалось отформатировать Markdown: {str(e)}\n"
                "Показываю текст без форматирования."
            )
            self.text_browser.setPlainText(self.response_text)
    
    def copy_to_clipboard(self):
        """Копирование текста в буфер обмена."""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.response_text)
        QMessageBox.information(self, "Успех", "Текст скопирован в буфер обмена!")


class ImprovementThread(QThread):
    """Поток для улучшения промта без блокировки интерфейса."""
    
    finished = pyqtSignal(dict)  # Сигнал завершения: (результаты улучшения от всех моделей)
    result_ready = pyqtSignal(str, dict)  # Сигнал результата: (model_name, improvements)
    
    def __init__(self, prompt: str, models: List[Model]):
        """
        Инициализация потока улучшения промта.
        
        Args:
            prompt: Исходный промт для улучшения
            models: Список моделей для использования при улучшении
        """
        super().__init__()
        self.prompt = prompt
        self.models = models
        self.improver = PromptImprover()
    
    def run(self):
        """Выполнение улучшения промта для всех моделей."""
        import asyncio
        
        # Добавляем фразу "Ответь на русском языке" к запросу на улучшение
        enhanced_prompt = f"{self.prompt}\n\nОтветь на русском языке."
        
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Отправляем запросы параллельно для скорости
            async def improve_all():
                tasks = []
                model_names = []
                
                for model in self.models:
                    # Формируем запрос на улучшение с добавлением "Ответь на русском языке"
                    task = self.improver.improve_prompt(enhanced_prompt, model, timeout=60)
                    tasks.append(task)
                    model_names.append(model.name)
                
                # Дожидаемся всех результатов параллельно
                results_list = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Формируем словарь результатов и эмитируем сигналы
                results = {}
                for model_name, result in zip(model_names, results_list):
                    if isinstance(result, Exception):
                        error_result = {
                            'improved': '',
                            'alternatives': [],
                            'adaptations': {
                                'code': '',
                                'analysis': '',
                                'creative': ''
                            },
                            'error': f"Исключение: {str(result)}"
                        }
                        results[model_name] = error_result
                        self.result_ready.emit(model_name, error_result)
                    else:
                        results[model_name] = result
                        self.result_ready.emit(model_name, result)
                
                return results
            
            results = loop.run_until_complete(improve_all())
            
            # Эмитируем финальные результаты
            self.finished.emit(results)
        except Exception as e:
            error_result = {
                'error': f"Неожиданная ошибка: {str(e)}"
            }
            self.finished.emit(error_result)
        finally:
            loop.close()


class PromptImprovementDialog(QDialog):
    """Диалог для отображения улучшений промта от всех моделей."""
    
    def __init__(self, parent=None, original_prompt: str = "", improvements: Optional[Dict] = None):
        """
        Инициализация диалога улучшения промта.
        
        Args:
            parent: Родительское окно
            original_prompt: Исходный промт
            improvements: Словарь с результатами улучшения от всех моделей
                         Формат: {model_name: {improved: str, alternatives: List, adaptations: Dict, error: str}}
        """
        super().__init__(parent)
        self.original_prompt = original_prompt
        self.improvements = improvements or {}
        self.selected_prompt = None  # Выбранный промт для использования
        
        self.setWindowTitle("Улучшение промта - Ответы от всех моделей")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700)
        
        self.init_ui()
        if improvements:
            self.load_improvements(improvements)
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        
        # Исходный промт
        original_label = QLabel("<b>Исходный промт:</b>")
        layout.addWidget(original_label)
        
        self.original_text = QTextEdit()
        self.original_text.setPlainText(self.original_prompt)
        self.original_text.setReadOnly(True)
        self.original_text.setMaximumHeight(100)
        self.original_text.setStyleSheet("background-color: #f5f5f5;")
        layout.addWidget(self.original_text)
        
        # Разделитель
        separator = QLabel("─" * 80)
        layout.addWidget(separator)
        
        # Таблица с ответами от всех моделей
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(3)
        self.models_table.setHorizontalHeaderLabels(["Модель", "Краткий ответ", "Открыть"])
        
        # Настройка таблицы
        header = self.models_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Модель - по содержимому
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Ответ - растягивается
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Открыть - по содержимому
        
        self.models_table.setAlternatingRowColors(True)
        self.models_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.models_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.models_table)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.reject)
        close_button.setDefault(True)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_improvements(self, improvements: Dict):
        """Загрузка результатов улучшения от всех моделей в таблицу."""
        # Очищаем таблицу
        self.models_table.setRowCount(0)
        
        # Проверяем, есть ли общая ошибка
        if 'error' in improvements and len(improvements) == 1:
            QMessageBox.warning(self, "Ошибка", f"При улучшении промта произошла ошибка:\n\n{improvements.get('error', 'Неизвестная ошибка')}")
            return
        
        # Заполняем таблицу результатами от всех моделей
        row = 0
        for model_name, model_result in improvements.items():
            if model_name == 'error':
                continue  # Пропускаем общую ошибку
            
            self.models_table.insertRow(row)
            
            # Колонка "Модель"
            model_item = QTableWidgetItem(model_name)
            model_item.setFlags(model_item.flags() & ~Qt.ItemIsEditable)
            self.models_table.setItem(row, 0, model_item)
            
            # Получаем полный ответ от модели для отображения
            full_response = self.format_model_response(model_result)
            
            # Колонка "Краткий ответ" - показываем улучшенный промт или ошибку
            if 'error' in model_result and model_result['error']:
                response_text = f"Ошибка: {model_result['error'][:200]}..."
                response_item = QTableWidgetItem(response_text)
                response_item.setForeground(Qt.red)
            else:
                improved = model_result.get('improved', '')
                if improved:
                    response_text = improved[:200] + "..." if len(improved) > 200 else improved
                else:
                    response_text = "(Нет улучшенной версии)"
                response_item = QTableWidgetItem(response_text)
            
            response_item.setFlags(response_item.flags() & ~Qt.ItemIsEditable)
            # Убираем tooltip, чтобы избежать дублирования содержимого
            self.models_table.setItem(row, 1, response_item)
            
            # Колонка "Открыть" - кнопка
            if 'error' not in model_result or not model_result.get('error'):
                open_button = QPushButton("Открыть")
                open_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        padding: 5px 15px;
                        font-weight: bold;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                # Сохраняем полный ответ для передачи в диалог
                open_button.clicked.connect(lambda checked, model=model_name, resp=full_response: 
                                           self.open_markdown_dialog(model, resp))
                self.models_table.setCellWidget(row, 2, open_button)
            else:
                # Для ошибок оставляем пустую ячейку
                empty_label = QLabel("")
                self.models_table.setCellWidget(row, 2, empty_label)
            
            # Высота строки
            self.models_table.setRowHeight(row, 80)
            
            row += 1
    
    def format_model_response(self, model_result: Dict) -> str:
        """Форматирование полного ответа от модели для отображения в Markdown."""
        lines = []
        
        if 'error' in model_result and model_result['error']:
            lines.append(f"## Ошибка\n\n{model_result['error']}")
        else:
            # Улучшенный промт
            improved = model_result.get('improved', '')
            if improved:
                lines.append(f"## Улучшенный промт\n\n{improved}")
            
            # Альтернативные варианты
            alternatives = model_result.get('alternatives', [])
            if alternatives:
                lines.append("\n## Альтернативные варианты\n")
                for i, alt in enumerate(alternatives, 1):
                    if alt and alt.strip():
                        lines.append(f"{i}. {alt}")
            
            # Адаптации
            adaptations = model_result.get('adaptations', {})
            if isinstance(adaptations, dict):
                has_adaptations = any(adaptations.get(key) for key in ['code', 'analysis', 'creative'])
                if has_adaptations:
                    lines.append("\n## Адаптации для разных типов задач\n")
                    
                    code_adaptation = adaptations.get('code', '')
                    if code_adaptation:
                        lines.append(f"### Для задач программирования\n\n{code_adaptation}\n")
                    
                    analysis_adaptation = adaptations.get('analysis', '')
                    if analysis_adaptation:
                        lines.append(f"### Для аналитических задач\n\n{analysis_adaptation}\n")
                    
                    creative_adaptation = adaptations.get('creative', '')
                    if creative_adaptation:
                        lines.append(f"### Для креативных задач\n\n{creative_adaptation}\n")
        
        return "\n".join(lines)
    
    def open_markdown_dialog(self, model_name: str, response_text: str):
        """Открытие диалога для просмотра полного ответа модели в формате Markdown."""
        dialog = MarkdownViewDialog(
            parent=self,
            model_name=model_name,
            response_text=response_text,
            prompt_text=self.original_prompt
        )
        dialog.exec_()
    
    def use_prompt(self, prompt_text: str):
        """Использование выбранного промта."""
        if prompt_text and prompt_text.strip():
            self.selected_prompt = prompt_text.strip()
            self.accept()
    
    def use_selected_alternative(self):
        """Использование выбранного альтернативного варианта."""
        selected_item = self.alternatives_list.currentItem()
        if selected_item:
            self.use_prompt(selected_item.text())
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите вариант из списка")
    
    def copy_selected_to_clipboard(self):
        """Копирование выбранного текста в буфер обмена."""
        clipboard = QApplication.clipboard()
        
        # Приоритет: выбранный альтернативный вариант > улучшенный > исходный
        if self.alternatives_list.currentItem():
            text = self.alternatives_list.currentItem().text()
        elif self.improved_text.toPlainText().strip():
            text = self.improved_text.toPlainText()
        else:
            text = self.original_prompt
        
        clipboard.setText(text)
        QMessageBox.information(self, "Успех", "Текст скопирован в буфер обмена!")
    
    def get_selected_prompt(self) -> Optional[str]:
        """Получение выбранного промта."""
        return self.selected_prompt


class ResultsTableWidget(QWidget):
    """Виджет таблицы результатов."""
    
    def __init__(self, db: Database):
        """
        Инициализация виджета таблицы результатов.
        
        Args:
            db: Экземпляр Database
        """
        super().__init__()
        self.db = db
        self.current_prompt_id: Optional[int] = None
        self.current_prompt_text: str = ""  # Сохраняем текст промта для передачи в диалог
        self.results_data: Dict[str, Tuple[str, Optional[str]]] = {}  # model_name: (response, error)
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel("Результаты запросов")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_label.setToolTip("Таблица с результатами запросов ко всем активным моделям")
        layout.addWidget(title_label)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setToolTip("Прогресс выполнения запросов к моделям")
        layout.addWidget(self.progress_bar)
        
        # Таблица результатов
        self.table = QTableWidget()
        self.table.setColumnCount(4)  # Добавлена колонка "Открыть"
        self.table.setHorizontalHeaderLabels(["Модель", "Ответ", "Выбрать", "Открыть"])
        
        # Настройка таблицы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Модель - по содержимому
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Ответ - растягивается
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Чекбокс - по содержимому
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Кнопка "Открыть" - по содержимому
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)  # Скрываем вертикальный заголовок
        
        # Настройка стиля для переноса текста в ячейках
        self.table.setStyleSheet("""
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget {
                gridline-color: #e0e0e0;
            }
        """)
        # Используем фиксированную высоту строк (будет устанавливаться динамически для каждой строки)
        self.table.verticalHeader().setDefaultSectionSize(120)  # Начальная высота по умолчанию
        # Отключаем автоматическое изменение размера, используем фиксированную высоту
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        
        layout.addWidget(self.table)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Очистить")
        self.clear_button.clicked.connect(self.clear_table)
        self.clear_button.setToolTip("Очистить таблицу результатов")
        buttons_layout.addWidget(self.clear_button)
        
        buttons_layout.addStretch()
        
        self.save_button = QPushButton("Сохранить выбранные")
        self.save_button.clicked.connect(self.save_selected)
        self.save_button.setToolTip("Сохранить отмеченные результаты в базу данных")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def clear_table(self):
        """Очистка таблицы."""
        self.table.setRowCount(0)
        self.results_data.clear()
        self.current_prompt_id = None
        self.save_button.setEnabled(False)
    
    def set_results(self, results: Dict[str, Tuple[str, Optional[str]]], prompt_id: int):
        """
        Установка результатов в таблицу.
        
        Args:
            results: Словарь {model_name: (response_text, error_message)}
            prompt_id: ID промта
        """
        self.clear_table()
        self.current_prompt_id = prompt_id
        self.results_data = results
        
        # Получаем текст промта из базы данных
        try:
            prompt_data = self.db.get_prompt_by_id(prompt_id)
            if prompt_data:
                self.current_prompt_text = prompt_data.get('prompt', '')
            else:
                self.current_prompt_text = ''
        except:
            self.current_prompt_text = ''
        
        row = 0
        for model_name, (response, error) in results.items():
            self.table.insertRow(row)
            
            # Колонка "Модель"
            model_item = QTableWidgetItem(model_name)
            model_item.setFlags(model_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, model_item)
            
            # Колонка "Ответ"
            if error:
                # Улучшенное отображение ошибки 402
                if "402" in error and ("credits" in error.lower() or "max_tokens" in error.lower()):
                    # Извлекаем понятное сообщение из JSON ошибки
                    error_msg = "Ошибка 402: Недостаточно кредитов или слишком много токенов.\n"
                    error_msg += "Решение: Уменьшите max_tokens в настройках (сейчас: по умолчанию 4096)\n"
                    error_msg += "или пополните баланс на https://openrouter.ai/settings/credits"
                    
                    # Пытаемся извлечь детали из JSON
                    try:
                        import json as json_module
                        if "{" in error:
                            json_part = error[error.find("{"):error.rfind("}")+1]
                            error_data = json_module.loads(json_part)
                            if "error" in error_data and "message" in error_data["error"]:
                                detail_msg = error_data["error"]["message"]
                                if "can only afford" in detail_msg:
                                    # Извлекаем информацию о доступных токенах
                                    error_msg = f"Ошибка 402: {detail_msg[:200]}"
                    except:
                        pass
                    
                    response_text = error_msg
                else:
                    # Для других ошибок показываем как есть, но обрезаем длинный текст
                    response_text = error[:500] + "..." if len(error) > 500 else error
                
                response_item = QTableWidgetItem(response_text)
                response_item.setForeground(Qt.red)
            else:
                response_text = response or "(Пустой ответ)"
                response_item = QTableWidgetItem(response_text)
            
            response_item.setFlags(response_item.flags() & ~Qt.ItemIsEditable)
            response_item.setToolTip(response_text)  # Подсказка при наведении
            # Перенос текста для длинных ответов
            response_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.table.setItem(row, 1, response_item)
            
            # Колонка "Выбрать" - чекбокс
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            self.table.setCellWidget(row, 2, checkbox)
            
            # Колонка "Открыть" - кнопка
            if not error:  # Показываем кнопку только если нет ошибки
                open_button = QPushButton("Открыть")
                open_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        padding: 5px 15px;
                        font-weight: bold;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                # Сохраняем данные для передачи в диалог
                open_button.clicked.connect(lambda checked, model=model_name, resp=response: 
                                           self.open_markdown_dialog(model, resp))
                self.table.setCellWidget(row, 3, open_button)
            else:
                # Для ошибок оставляем пустую ячейку или показываем кнопку с отключенным состоянием
                empty_label = QLabel("")
                self.table.setCellWidget(row, 3, empty_label)
            
            # Высота строки для длинных ответов - увеличена для отображения нескольких строк
            # Вычисляем примерную высоту на основе длины текста (примерно 60 символов на строку при ширине колонки)
            text_length = len(response_text)
            # Оцениваем количество строк: примерно 60-80 символов на строку в зависимости от ширины
            estimated_lines = max(4, min(20, (text_length // 70) + 3))  # Минимум 4 строки, максимум 20
            row_height = max(120, estimated_lines * 22)  # Минимум 120px, примерно 22px на строку с учетом padding
            self.table.setRowHeight(row, row_height)
            
            row += 1
        
        if row > 0:
            self.save_button.setEnabled(True)
    
    def add_result(self, model_name: str, response: str, error: Optional[str] = None):
        """
        Добавление одного результата в таблицу (для прогрессивного обновления).
        
        Args:
            model_name: Название модели
            response: Текст ответа
            error: Сообщение об ошибке (если есть)
        """
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Колонка "Модель"
        model_item = QTableWidgetItem(model_name)
        model_item.setFlags(model_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, 0, model_item)
        
        # Колонка "Ответ"
        if error:
            # Улучшенное отображение различных типов ошибок
            if "402" in error and ("credits" in error.lower() or "max_tokens" in error.lower()):
                error_msg = "Ошибка 402: Недостаточно кредитов или слишком много токенов.\n"
                error_msg += "Решение: Уменьшите max_tokens в настройках или пополните баланс на https://openrouter.ai/settings/credits"
                
                # Пытаемся извлечь детали из JSON
                try:
                    import json as json_module
                    if "{" in error:
                        json_part = error[error.find("{"):error.rfind("}")+1]
                        error_data = json_module.loads(json_part)
                        if "error" in error_data and "message" in error_data["error"]:
                            detail_msg = error_data["error"]["message"]
                            if "can only afford" in detail_msg:
                                error_msg = f"Ошибка 402: {detail_msg[:250]}"
                except:
                    pass
                
                response_text = error_msg
            elif "404" in error or "не найдена" in error.lower() or "not found" in error.lower():
                # Ошибка 404 - модель не найдена
                response_text = error  # Уже содержит понятное сообщение из network.py
            elif "400" in error or "неверный" in error.lower() or "invalid" in error.lower():
                # Ошибка 400 - неверный ID модели
                response_text = error  # Уже содержит понятное сообщение из network.py
            elif "429" in error or "слишком много запросов" in error.lower() or "too many requests" in error.lower():
                # Ошибка 429 - слишком много запросов
                response_text = error  # Уже содержит понятное сообщение из network.py
            else:
                # Для других ошибок
                response_text = error[:500] + "..." if len(error) > 500 else error
            
            response_item = QTableWidgetItem(response_text)
            response_item.setForeground(Qt.red)
        else:
            response_text = response or "(Пустой ответ)"
            response_item = QTableWidgetItem(response_text)
        
        response_item.setFlags(response_item.flags() & ~Qt.ItemIsEditable)
        response_item.setToolTip(response_text)  # Подсказка при наведении
        # Перенос текста для длинных ответов
        response_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.table.setItem(row, 1, response_item)
        
        # Колонка "Выбрать" - чекбокс
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        self.table.setCellWidget(row, 2, checkbox)
        
        # Колонка "Открыть" - кнопка
        if not error:  # Показываем кнопку только если нет ошибки
            open_button = QPushButton("Открыть")
            open_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 5px 15px;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            # Сохраняем данные для передачи в диалог
            open_button.clicked.connect(lambda checked, model=model_name, resp=response: 
                                       self.open_markdown_dialog(model, resp))
            self.table.setCellWidget(row, 3, open_button)
        else:
            # Для ошибок оставляем пустую ячейку
            empty_label = QLabel("")
            self.table.setCellWidget(row, 3, empty_label)
        
        # Высота строки для длинных ответов - увеличена для отображения нескольких строк
        # Вычисляем примерную высоту на основе длины текста (примерно 60 символов на строку при ширине колонки)
        text_length = len(response_text)
        # Оцениваем количество строк: примерно 60-80 символов на строку в зависимости от ширины
        estimated_lines = max(4, min(20, (text_length // 70) + 3))  # Минимум 4 строки, максимум 20
        row_height = max(120, estimated_lines * 22)  # Минимум 120px, примерно 22px на строку с учетом padding
        self.table.setRowHeight(row, row_height)
        
        # Сохраняем результат
        self.results_data[model_name] = (response, error)
        
        if not self.save_button.isEnabled():
            self.save_button.setEnabled(True)
    
    def get_selected_results(self) -> Dict[str, Tuple[str, Optional[str]]]:
        """
        Получение выбранных результатов.
        
        Returns:
            Словарь {model_name: (response_text, error_message)} для выбранных строк
        """
        selected = {}
        
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 2)
            if checkbox and checkbox.isChecked():
                model_name = self.table.item(row, 0).text()
                if model_name in self.results_data:
                    selected[model_name] = self.results_data[model_name]
        
        return selected
    
    def open_markdown_dialog(self, model_name: str, response_text: str):
        """
        Открытие диалога для просмотра ответа в формате Markdown.
        
        Args:
            model_name: Название модели
            response_text: Текст ответа
        """
        dialog = MarkdownViewDialog(
            parent=self,
            model_name=model_name,
            response_text=response_text,
            prompt_text=self.current_prompt_text
        )
        dialog.exec_()
    
    def save_selected(self):
        """Сохранение выбранных результатов в БД."""
        if not self.current_prompt_id:
            QMessageBox.warning(self, "Предупреждение", "Нет активного промта для сохранения!")
            return
        
        selected = self.get_selected_results()
        
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Не выбрано ни одного результата для сохранения!")
            return
        
        # Сохранение каждого выбранного результата
        saved_count = 0
        for model_name, (response, error) in selected.items():
            if not error:  # Сохраняем только успешные ответы
                self.db.save_result(self.current_prompt_id, model_name, response)
                saved_count += 1
        
        if saved_count > 0:
            QMessageBox.information(
                self,
                "Успех",
                f"Сохранено {saved_count} результат(ов) в базу данных."
            )
            # Очистка таблицы после сохранения (опционально)
            # self.clear_table()
        else:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Не удалось сохранить результаты. Возможно, выбраны только ошибки."
            )
    
    def update_progress(self, total: int, current: int):
        """Обновление прогресс-бара."""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            self.progress_bar.setVisible(True)
        else:
            self.progress_bar.setVisible(False)


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
        
        # Центральный виджет с вкладками
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Вкладка "Работа с промтами"
        main_tab = QWidget()
        main_layout = QVBoxLayout()
        main_tab.setLayout(main_layout)
        
        # Виджет ввода промта
        self.prompt_input_widget = PromptInputWidget(self.db, self.model_manager, self.on_prompt_sent)
        main_layout.addWidget(self.prompt_input_widget)
        
        # Виджет таблицы результатов
        self.results_widget = ResultsTableWidget(self.db)
        main_layout.addWidget(self.results_widget)
        
        self.tabs.addTab(main_tab, "Запросы")
        
        # Вкладка "Управление моделями"
        self.models_widget = ModelsManagementWidget(self.db)
        self.tabs.addTab(self.models_widget, "Модели")
        
        # Вкладка "История"
        self.history_widget = HistoryWidget(self.db)
        self.tabs.addTab(self.history_widget, "История")
        
        # Вкладка "Настройки"
        settings_tab = QWidget()
        settings_layout = QVBoxLayout()
        settings_tab.setLayout(settings_layout)
        
        settings_title = QLabel("Настройки программы")
        settings_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        settings_layout.addWidget(settings_title)
        
        # Таймаут запросов
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Таймаут запросов (секунды):")
        self.timeout_input = QLineEdit()
        self.timeout_input.setText(str(self.db.get_setting('request_timeout') or '30'))
        timeout_save_btn = QPushButton("Сохранить")
        timeout_save_btn.clicked.connect(lambda: self.save_setting('request_timeout', self.timeout_input.text()))
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_input)
        timeout_layout.addWidget(timeout_save_btn)
        settings_layout.addLayout(timeout_layout)
        
        # Максимальное количество одновременных запросов
        max_req_layout = QHBoxLayout()
        max_req_label = QLabel("Макс. одновременных запросов:")
        self.max_req_input = QLineEdit()
        self.max_req_input.setText(str(self.db.get_setting('max_concurrent_requests') or '5'))
        max_req_save_btn = QPushButton("Сохранить")
        max_req_save_btn.clicked.connect(lambda: self.save_setting('max_concurrent_requests', self.max_req_input.text()))
        max_req_layout.addWidget(max_req_label)
        max_req_layout.addWidget(self.max_req_input)
        max_req_layout.addWidget(max_req_save_btn)
        settings_layout.addLayout(max_req_layout)
        
        # Максимальное количество токенов (для избежания ошибки 402)
        max_tokens_layout = QHBoxLayout()
        max_tokens_label = QLabel("Макс. токенов в ответе:")
        self.max_tokens_input = QLineEdit()
        max_tokens_default = self.db.get_setting('max_tokens') or '2048'
        self.max_tokens_input.setText(str(max_tokens_default))
        self.max_tokens_input.setPlaceholderText("2048 (рекомендуется для бесплатных аккаунтов)")
        max_tokens_save_btn = QPushButton("Сохранить")
        max_tokens_save_btn.clicked.connect(lambda: self.save_setting('max_tokens', self.max_tokens_input.text() if self.max_tokens_input.text() else '2048'))
        max_tokens_help = QLabel("(помогает избежать ошибки 402 на OpenRouter. Для бесплатных аккаунтов рекомендуется 2048)")
        max_tokens_help.setStyleSheet("color: gray; font-size: 10px;")
        max_tokens_layout.addWidget(max_tokens_label)
        max_tokens_layout.addWidget(self.max_tokens_input)
        max_tokens_layout.addWidget(max_tokens_save_btn)
        settings_layout.addLayout(max_tokens_layout)
        settings_layout.addWidget(max_tokens_help)
        
        settings_layout.addStretch()
        self.tabs.addTab(settings_tab, "Настройки")
        
        # Поток для отправки запросов (будет создан при необходимости)
        self.request_thread: Optional[RequestThread] = None
    
    def save_setting(self, key: str, value: str):
        """Сохранение настройки."""
        self.db.set_setting(key, value)
        QMessageBox.information(self, "Успех", f"Настройка '{key}' сохранена!")
    
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
            # Проверяем, какой файл используется
            import os
            import sys
            
            # Определяем директорию EXE файла или скрипта
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Проверяем наличие файлов
            env_local_path = os.path.join(base_dir, '.env.local')
            env_path = os.path.join(base_dir, '.env')
            
            env_local_exists = os.path.exists(env_local_path)
            env_exists = os.path.exists(env_path)
            
            if env_local_exists:
                env_file = env_local_path
            elif env_exists:
                env_file = env_path
            else:
                env_file = f"{base_dir}\\.env.local или {base_dir}\\.env"
            
            QMessageBox.warning(
                self,
                "Предупреждение",
                f"У активных моделей не найдены API-ключи!\n\n"
                f"Создайте файл рядом с приложением:\n{env_file}\n\n"
                f"Добавьте в файл строку:\nOPENROUTER_API_KEY=ваш_ключ\n\n"
                f"После создания файла перезапустите приложение.\n\n"
                f"Примечание: файл .env.local имеет приоритет над .env"
            )
            return
        
        # Очистить предыдущие результаты
        self.results_widget.clear_table()
        
        # Отключить кнопку отправки на время выполнения запросов
        self.prompt_input_widget.send_button.setEnabled(False)
        self.prompt_input_widget.send_button.setText("Отправка...")
        
        # Показать прогресс-бар
        self.results_widget.progress_bar.setMaximum(len(models_with_keys))
        self.results_widget.progress_bar.setValue(0)
        self.results_widget.progress_bar.setVisible(True)
        
        # Создать и запустить поток для отправки запросов
        self.request_thread = RequestThread(models_with_keys, prompt_text, prompt_id, self.request_manager)
        self.request_thread.finished.connect(self.on_requests_finished)
        self.request_thread.result_ready.connect(self.on_result_ready)
        self.request_thread.start()
        
        print(f"Промт отправлен: {prompt_text}")
        print(f"ID промта: {prompt_id}")
        print(f"Отправка к {len(models_with_keys)} моделям...")
    
    def on_result_ready(self, model_name: str, response: str, error: str):
        """Обработка получения результата от одной модели."""
        # Если error пустая строка, значит ошибки нет
        error_or_none = error if error else None
        
        # Улучшенное отображение ошибки 402
        if error_or_none and "402" in error_or_none:
            # Извлекаем понятное сообщение из ошибки
            if "credits" in error_or_none.lower() or "max_tokens" in error_or_none.lower():
                error_or_none = (
                    "Ошибка 402: Недостаточно кредитов или слишком много токенов.\n"
                    "Решение: Уменьшите max_tokens в настройках или пополните баланс на https://openrouter.ai/settings/credits"
                )
        
        self.results_widget.add_result(model_name, response, error_or_none)
        current = self.results_widget.table.rowCount()
        total = self.results_widget.progress_bar.maximum()
        if current <= total:
            self.results_widget.progress_bar.setValue(current)
    
    def on_requests_finished(self, results: Dict[str, Tuple[str, Optional[str]]], prompt_id: int):
        """Обработка завершения всех запросов."""
        # Установить все результаты в таблицу
        self.results_widget.set_results(results, prompt_id)
        
        # Скрыть прогресс-бар
        self.results_widget.progress_bar.setVisible(False)
        
        # Включить кнопку отправки
        self.prompt_input_widget.send_button.setEnabled(True)
        self.prompt_input_widget.send_button.setText("Отправить")
        
        # Показать сообщение о завершении
        successful = sum(1 for r, e in results.values() if not e)
        total = len(results)
        
        if successful == total:
            QMessageBox.information(
                self,
                "Завершено",
                f"Все запросы выполнены успешно! Получено {successful} ответов."
            )
        elif successful > 0:
            QMessageBox.warning(
                self,
                "Частично завершено",
                f"Выполнено {successful} из {total} запросов. Некоторые завершились с ошибками."
            )
        else:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Все запросы завершились с ошибками. Проверьте настройки API и подключение к интернету."
            )
        
        print(f"Запросы завершены. Успешно: {successful}/{total}")
    
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
