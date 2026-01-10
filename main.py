"""
Главный модуль приложения ChatList.
Основной интерфейс для работы с промтами и нейросетями.
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QComboBox, QPushButton, 
                             QLabel, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QCheckBox, QProgressBar, QTabWidget, QLineEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from db import Database
from models import ModelManager, Model
from network import RequestManager, send_batch_requests_sync
from models_dialog import ModelsManagementWidget
from history_widget import HistoryWidget
from typing import Dict, Tuple, Optional, List


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
        
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Отправляем запросы параллельно для скорости
            async def send_all():
                tasks = []
                model_names = []
                
                for model in self.models:
                    task = self.request_manager.send_request(model, self.prompt)
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
        self.results_data: Dict[str, Tuple[str, Optional[str]]] = {}  # model_name: (response, error)
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel("Результаты запросов")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Таблица результатов
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Модель", "Ответ", "Выбрать"])
        
        # Настройка таблицы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Модель - по содержимому
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Ответ - растягивается
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Чекбокс - по содержимому
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Очистить")
        self.clear_button.clicked.connect(self.clear_table)
        buttons_layout.addWidget(self.clear_button)
        
        buttons_layout.addStretch()
        
        self.save_button = QPushButton("Сохранить выбранные")
        self.save_button.clicked.connect(self.save_selected)
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
            self.table.setItem(row, 1, response_item)
            
            # Колонка "Выбрать" - чекбокс
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            self.table.setCellWidget(row, 2, checkbox)
            
            # Высота строки для длинных ответов
            self.table.setRowHeight(row, 100)
            
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
        self.table.setItem(row, 1, response_item)
        
        # Колонка "Выбрать" - чекбокс
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        self.table.setCellWidget(row, 2, checkbox)
        
        self.table.setRowHeight(row, 100)
        
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
        self.prompt_input_widget = PromptInputWidget(self.db, self.on_prompt_sent)
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
            env_local = os.path.exists('.env.local')
            env_file = '.env.local' if env_local else '.env'
            
            QMessageBox.warning(
                self,
                "Предупреждение",
                f"У активных моделей не найдены API-ключи!\n\n"
                f"Проверьте файл {env_file}\n"
                f"Убедитесь, что переменная OPENROUTER_API_KEY указана правильно:\n"
                f"OPENROUTER_API_KEY=ваш_ключ\n\n"
                f"После изменения файла перезапустите приложение."
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
