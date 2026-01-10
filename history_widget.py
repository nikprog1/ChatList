"""
Виджет для просмотра истории сохраненных результатов.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QLineEdit, QDialog,
                             QTextEdit)
from PyQt5.QtCore import Qt
from db import Database
from typing import Optional, List, Dict


class ResultDetailDialog(QDialog):
    """Диалог для просмотра детальной информации о результате."""
    
    def __init__(self, parent=None, result: Dict = None):
        """
        Инициализация диалога.
        
        Args:
            parent: Родительское окно
            result: Словарь с данными результата
        """
        super().__init__(parent)
        self.result = result
        self.init_ui()
        self.load_result_data()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        self.setWindowTitle("Детали результата")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Промт
        prompt_label = QLabel("Промт:")
        self.prompt_text = QTextEdit()
        self.prompt_text.setReadOnly(True)
        layout.addWidget(prompt_label)
        layout.addWidget(self.prompt_text)
        
        # Модель и дата
        info_layout = QHBoxLayout()
        model_label = QLabel("Модель:")
        self.model_text = QLabel()
        date_label = QLabel("Дата сохранения:")
        self.date_text = QLabel()
        info_layout.addWidget(model_label)
        info_layout.addWidget(self.model_text)
        info_layout.addWidget(date_label)
        info_layout.addWidget(self.date_text)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Ответ
        response_label = QLabel("Ответ:")
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        layout.addWidget(response_label)
        layout.addWidget(self.response_text)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def load_result_data(self):
        """Загрузка данных результата."""
        if not self.result:
            return
        
        self.prompt_text.setPlainText(self.result.get('prompt', ''))
        self.model_text.setText(self.result.get('model_name', ''))
        self.date_text.setText(self.result.get('saved_at', ''))
        self.response_text.setPlainText(self.result.get('response_text', ''))


class HistoryWidget(QWidget):
    """Виджет для просмотра истории сохраненных результатов."""
    
    def __init__(self, db: Database):
        """
        Инициализация виджета истории.
        
        Args:
            db: Экземпляр Database
        """
        super().__init__()
        self.db = db
        self.init_ui()
        self.load_history()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        
        # Заголовок и поиск
        header_layout = QHBoxLayout()
        title_label = QLabel("История сохраненных результатов")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        search_label = QLabel("Поиск:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по промту, ответу или модели...")
        self.search_input.textChanged.connect(self.on_search_changed)
        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input)
        
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.load_history)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Таблица результатов
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Промт", "Модель", "Дата сохранения", "Ответ (первые 100 символов)"])
        
        # Настройка таблицы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Промт
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Модель
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Дата
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Ответ
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        
        # Двойной клик для просмотра деталей
        self.table.itemDoubleClicked.connect(self.view_result_details)
        
        layout.addWidget(self.table)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.view_button = QPushButton("Просмотр")
        self.view_button.clicked.connect(self.view_result_details)
        buttons_layout.addWidget(self.view_button)
        
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_result)
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
        
        self.export_button = QPushButton("Экспорт выбранных")
        self.export_button.clicked.connect(self.export_selected)
        buttons_layout.addWidget(self.export_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_history(self):
        """Загрузка истории результатов."""
        results = self.db.get_all_results()
        self.table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # ID
            id_item = QTableWidgetItem(str(result.get('id', '')))
            id_item.setData(Qt.UserRole, result)
            self.table.setItem(row, 0, id_item)
            
            # Промт (обрезанный)
            prompt = result.get('prompt', '')
            prompt_short = prompt[:50] + "..." if len(prompt) > 50 else prompt
            prompt_item = QTableWidgetItem(prompt_short)
            prompt_item.setToolTip(prompt)
            self.table.setItem(row, 1, prompt_item)
            
            # Модель
            model_item = QTableWidgetItem(result.get('model_name', ''))
            self.table.setItem(row, 2, model_item)
            
            # Дата
            date_item = QTableWidgetItem(result.get('saved_at', ''))
            self.table.setItem(row, 3, date_item)
            
            # Ответ (обрезанный)
            response = result.get('response_text', '')
            response_short = response[:100] + "..." if len(response) > 100 else response
            response_item = QTableWidgetItem(response_short)
            response_item.setToolTip(response)
            self.table.setItem(row, 4, response_item)
    
    def on_search_changed(self, text: str):
        """Обработка изменения поискового запроса."""
        if not text.strip():
            self.load_history()
            return
        
        # Поиск результатов
        results = self.db.search_results(text)
        self.table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            id_item = QTableWidgetItem(str(result.get('id', '')))
            id_item.setData(Qt.UserRole, result)
            self.table.setItem(row, 0, id_item)
            
            prompt = result.get('prompt', '')
            prompt_short = prompt[:50] + "..." if len(prompt) > 50 else prompt
            prompt_item = QTableWidgetItem(prompt_short)
            prompt_item.setToolTip(prompt)
            self.table.setItem(row, 1, prompt_item)
            
            model_item = QTableWidgetItem(result.get('model_name', ''))
            self.table.setItem(row, 2, model_item)
            
            date_item = QTableWidgetItem(result.get('saved_at', ''))
            self.table.setItem(row, 3, date_item)
            
            response = result.get('response_text', '')
            response_short = response[:100] + "..." if len(response) > 100 else response
            response_item = QTableWidgetItem(response_short)
            response_item.setToolTip(response)
            self.table.setItem(row, 4, response_item)
    
    def get_selected_result(self) -> Optional[Dict]:
        """Получение выбранного результата."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        
        id_item = self.table.item(current_row, 0)
        if id_item:
            return id_item.data(Qt.UserRole)
        return None
    
    def view_result_details(self):
        """Просмотр детальной информации о результате."""
        result = self.get_selected_result()
        if not result:
            QMessageBox.warning(self, "Предупреждение", "Выберите результат для просмотра!")
            return
        
        dialog = ResultDetailDialog(self, result)
        dialog.exec_()
    
    def delete_result(self):
        """Удаление выбранного результата."""
        result = self.get_selected_result()
        if not result:
            QMessageBox.warning(self, "Предупреждение", "Выберите результат для удаления!")
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить этот результат?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM results WHERE id = ?", (result.get('id'),))
            self.db.conn.commit()
            
            QMessageBox.information(self, "Успех", "Результат удален успешно!")
            self.load_history()
    
    def export_selected(self):
        """Экспорт выбранных результатов."""
        result = self.get_selected_result()
        if not result:
            QMessageBox.warning(self, "Предупреждение", "Выберите результат для экспорта!")
            return
        
        # Простой экспорт в текстовый файл (можно расширить)
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результат",
            "",
            "Markdown Files (*.md);;JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    import json
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                else:
                    # Markdown или текстовый формат
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"# Результат запроса\n\n")
                        f.write(f"**Промт:**\n{result.get('prompt', '')}\n\n")
                        f.write(f"**Модель:** {result.get('model_name', '')}\n\n")
                        f.write(f"**Дата:** {result.get('saved_at', '')}\n\n")
                        f.write(f"**Ответ:**\n{result.get('response_text', '')}\n")
                
                QMessageBox.information(self, "Успех", f"Результат экспортирован в {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать результат: {str(e)}")
