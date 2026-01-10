"""
Диалог для управления моделями нейросетей.
"""

from PyQt5.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QCheckBox, QLineEdit,
                             QTextEdit, QComboBox)
from PyQt5.QtCore import Qt
from db import Database
from models import ModelManager, Model
from typing import Optional, List


class ModelEditDialog(QDialog):
    """Диалог для добавления/редактирования модели."""
    
    def __init__(self, parent=None, model: Optional[Model] = None, db: Optional[Database] = None):
        """
        Инициализация диалога.
        
        Args:
            parent: Родительское окно
            model: Модель для редактирования (None для создания новой)
            db: Экземпляр Database
        """
        super().__init__(parent)
        self.model = model
        self.db = db
        self.is_edit_mode = model is not None
        self.init_ui()
        
        if self.is_edit_mode:
            self.load_model_data()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle("Редактировать модель" if self.is_edit_mode else "Добавить модель")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Название модели
        name_layout = QHBoxLayout()
        name_label = QLabel("Название модели:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # URL API
        url_layout = QHBoxLayout()
        url_label = QLabel("API URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://api.openrouter.ai/api/v1/chat/completions")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Идентификатор переменной окружения (API ID)
        api_id_layout = QHBoxLayout()
        api_id_label = QLabel("Переменная окружения (API ID):")
        self.api_id_input = QLineEdit()
        self.api_id_input.setPlaceholderText("OPENROUTER_API_KEY")
        api_id_layout.addWidget(api_id_label)
        api_id_layout.addWidget(self.api_id_input)
        layout.addLayout(api_id_layout)
        
        # Тип провайдера
        provider_layout = QHBoxLayout()
        provider_label = QLabel("Тип провайдера:")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(['openai', 'deepseek', 'groq', 'openrouter', 'custom'])
        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_combo)
        layout.addLayout(provider_layout)
        
        # Активна ли модель
        self.active_checkbox = QCheckBox("Модель активна")
        self.active_checkbox.setChecked(True)
        layout.addWidget(self.active_checkbox)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.accept_and_save)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def load_model_data(self):
        """Загрузка данных модели для редактирования."""
        if not self.model:
            return
        
        self.name_input.setText(self.model.name)
        self.url_input.setText(self.model.api_url)
        self.api_id_input.setText(self.model.api_id)
        index = self.provider_combo.findText(self.model.provider_type)
        if index >= 0:
            self.provider_combo.setCurrentIndex(index)
        self.active_checkbox.setChecked(self.model.is_active == 1)
    
    def accept_and_save(self):
        """Проверка и сохранение модели."""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        api_id = self.api_id_input.text().strip()
        
        # Валидация
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название модели не может быть пустым!")
            return
        
        if not url:
            QMessageBox.warning(self, "Ошибка", "API URL не может быть пустым!")
            return
        
        if not api_id:
            QMessageBox.warning(self, "Ошибка", "Идентификатор переменной окружения не может быть пустым!")
            return
        
        # Проверка формата URL
        if not (url.startswith("http://") or url.startswith("https://")):
            QMessageBox.warning(self, "Ошибка", "API URL должен начинаться с http:// или https://")
            return
        
        # Сохранение
        provider_type = self.provider_combo.currentText()
        is_active = 1 if self.active_checkbox.isChecked() else 0
        
        if self.is_edit_mode and self.model:
            # Обновление существующей модели
            success = self.db.update_model(
                self.model.id,
                name=name,
                api_url=url,
                api_id=api_id,
                provider_type=provider_type,
                is_active=is_active
            )
            if not success:
                QMessageBox.critical(self, "Ошибка", "Не удалось обновить модель!")
                return
        else:
            # Создание новой модели
            try:
                self.db.add_model(name, url, api_id, provider_type, is_active)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать модель: {str(e)}")
                return
        
        QMessageBox.information(self, "Успех", "Модель сохранена успешно!")
        self.accept()


class ModelsManagementWidget(QWidget):
    """Виджет для управления моделями."""
    
    def __init__(self, db: Database):
        """
        Инициализация виджета управления моделями.
        
        Args:
            db: Экземпляр Database
        """
        super().__init__()
        self.db = db
        self.model_manager = ModelManager(db)
        self.init_ui()
        self.load_models()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel("Управление моделями")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Добавить модель")
        self.add_button.clicked.connect(self.add_model)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Редактировать")
        self.edit_button.clicked.connect(self.edit_model)
        buttons_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_model)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        buttons_layout.addWidget(self.delete_button)
        
        buttons_layout.addStretch()
        
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.load_models)
        buttons_layout.addWidget(self.refresh_button)
        
        layout.addLayout(buttons_layout)
        
        # Таблица моделей
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "API URL", "API ID", "Тип", "Активна"])
        
        # Настройка таблицы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Название
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # URL
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # API ID
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Тип
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Активна
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_models(self):
        """Загрузка списка моделей в таблицу."""
        models = self.model_manager.get_all_models()
        self.table.setRowCount(len(models))
        
        for row, model in enumerate(models):
            # ID
            id_item = QTableWidgetItem(str(model.id))
            id_item.setData(Qt.UserRole, model.id)
            self.table.setItem(row, 0, id_item)
            
            # Название
            name_item = QTableWidgetItem(model.name)
            self.table.setItem(row, 1, name_item)
            
            # API URL
            url_item = QTableWidgetItem(model.api_url)
            self.table.setItem(row, 2, url_item)
            
            # API ID
            api_id_item = QTableWidgetItem(model.api_id)
            self.table.setItem(row, 3, api_id_item)
            
            # Тип провайдера
            provider_item = QTableWidgetItem(model.provider_type)
            self.table.setItem(row, 4, provider_item)
            
            # Активна
            active_item = QTableWidgetItem("Да" if model.is_active == 1 else "Нет")
            self.table.setItem(row, 5, active_item)
    
    def get_selected_model_id(self) -> Optional[int]:
        """Получение ID выбранной модели."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        
        id_item = self.table.item(current_row, 0)
        if id_item:
            return id_item.data(Qt.UserRole)
        return None
    
    def get_selected_model(self) -> Optional[Model]:
        """Получение выбранной модели."""
        model_id = self.get_selected_model_id()
        if model_id:
            return self.model_manager.get_model_by_id(model_id)
        return None
    
    def add_model(self):
        """Добавление новой модели."""
        dialog = ModelEditDialog(self, model=None, db=self.db)
        if dialog.exec_() == QDialog.Accepted:
            self.load_models()
    
    def edit_model(self):
        """Редактирование выбранной модели."""
        model = self.get_selected_model()
        if not model:
            QMessageBox.warning(self, "Предупреждение", "Выберите модель для редактирования!")
            return
        
        dialog = ModelEditDialog(self, model=model, db=self.db)
        if dialog.exec_() == QDialog.Accepted:
            self.load_models()
    
    def delete_model(self):
        """Удаление выбранной модели."""
        model = self.get_selected_model()
        if not model:
            QMessageBox.warning(self, "Предупреждение", "Выберите модель для удаления!")
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить модель '{model.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Удаление модели из БД
            success = self.db.delete_model(model.id)
            
            if success:
                QMessageBox.information(self, "Успех", "Модель удалена успешно!")
                self.load_models()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить модель!")
