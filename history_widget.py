"""
Виджет для просмотра истории сохраненных результатов.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QLineEdit, QDialog,
                             QTextEdit, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
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
        
        # Обрабатываем случай None для всех полей
        prompt = self.result.get('prompt') or '(Промт был удален)'
        self.prompt_text.setPlainText(prompt)
        self.model_text.setText(self.result.get('model_name') or '(Не указана)')
        self.date_text.setText(self.result.get('saved_at') or '(Не указана)')
        self.response_text.setPlainText(self.result.get('response_text') or '(Пустой ответ)')


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
        self.table.setColumnCount(7)  # Добавлены колонки "Выбрать" и "ID запроса"
        self.table.setHorizontalHeaderLabels(["Выбрать", "ID результата", "ID запроса", "Промт", "Модель", "Дата сохранения", "Ответ (первые 100 символов)"])
        
        # Настройка таблицы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Чекбокс
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # ID результата
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # ID запроса
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Промт
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Модель
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Дата
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # Ответ
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)  # Множественный выбор строк
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
        
        self.delete_button = QPushButton("Удалить выбранные")
        self.delete_button.clicked.connect(self.delete_selected_results)
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
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        buttons_layout.addWidget(self.delete_button)
        
        buttons_layout.addStretch()
        
        self.export_button = QPushButton("Экспорт выбранных")
        self.export_button.clicked.connect(self.export_selected)
        buttons_layout.addWidget(self.export_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Изначально кнопка удаления отключена
        self.delete_button.setEnabled(False)
    
    def load_history(self):
        """Загрузка истории результатов."""
        results = self.db.get_all_results()
        self.table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # Колонка "Выбрать" - чекбокс
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self.update_delete_button_state)  # Обновляем состояние кнопки при изменении
            self.table.setCellWidget(row, 0, checkbox)
            
            # ID результата
            result_id = result.get('id', '')
            id_item = QTableWidgetItem(str(result_id))
            id_item.setData(Qt.UserRole, result)
            self.table.setItem(row, 1, id_item)
            
            # ID запроса (prompt_id)
            prompt_id = result.get('prompt_id', '')
            prompt_id_item = QTableWidgetItem(str(prompt_id) if prompt_id else '(Удален)')
            if prompt_id:
                prompt_id_item.setToolTip(f"ID промта: {prompt_id}")
            else:
                prompt_id_item.setToolTip("Промт был удален")
                prompt_id_item.setForeground(QColor(128, 128, 128))  # Серый цвет для удаленных промтов
            self.table.setItem(row, 2, prompt_id_item)
            
            # Промт (обрезанный) - обрабатываем случай None
            prompt = result.get('prompt') or ''  # Если None, используем пустую строку
            prompt_short = prompt[:50] + "..." if prompt and len(prompt) > 50 else (prompt or '(Промт удален)')
            prompt_item = QTableWidgetItem(prompt_short)
            prompt_item.setToolTip(prompt or '(Промт был удален)')
            self.table.setItem(row, 3, prompt_item)
            
            # Модель
            model_name = result.get('model_name') or ''
            model_item = QTableWidgetItem(model_name)
            self.table.setItem(row, 4, model_item)
            
            # Дата
            saved_at = result.get('saved_at') or ''
            date_item = QTableWidgetItem(saved_at)
            self.table.setItem(row, 5, date_item)
            
            # Ответ (обрезанный) - обрабатываем случай None
            response = result.get('response_text') or ''  # Если None, используем пустую строку
            response_short = response[:100] + "..." if response and len(response) > 100 else (response or '(Пустой ответ)')
            response_item = QTableWidgetItem(response_short)
            response_item.setToolTip(response or '(Пустой ответ)')
            self.table.setItem(row, 6, response_item)
        
        # Обновляем состояние кнопки удаления
        self.update_delete_button_state()
    
    def on_search_changed(self, text: str):
        """Обработка изменения поискового запроса."""
        if not text.strip():
            self.load_history()
            return
        
        # Поиск результатов
        results = self.db.search_results(text)
        self.table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # Колонка "Выбрать" - чекбокс
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self.update_delete_button_state)  # Обновляем состояние кнопки при изменении
            self.table.setCellWidget(row, 0, checkbox)
            
            # ID результата
            result_id = result.get('id', '')
            id_item = QTableWidgetItem(str(result_id))
            id_item.setData(Qt.UserRole, result)
            self.table.setItem(row, 1, id_item)
            
            # ID запроса (prompt_id)
            prompt_id = result.get('prompt_id', '')
            prompt_id_item = QTableWidgetItem(str(prompt_id) if prompt_id else '(Удален)')
            if prompt_id:
                prompt_id_item.setToolTip(f"ID промта: {prompt_id}")
            else:
                prompt_id_item.setToolTip("Промт был удален")
                prompt_id_item.setForeground(QColor(128, 128, 128))  # Серый цвет для удаленных промтов
            self.table.setItem(row, 2, prompt_id_item)
            
            # Промт (обрезанный) - обрабатываем случай None
            prompt = result.get('prompt') or ''  # Если None, используем пустую строку
            prompt_short = prompt[:50] + "..." if prompt and len(prompt) > 50 else (prompt or '(Промт удален)')
            prompt_item = QTableWidgetItem(prompt_short)
            prompt_item.setToolTip(prompt or '(Промт был удален)')
            self.table.setItem(row, 3, prompt_item)
            
            model_name = result.get('model_name') or ''
            model_item = QTableWidgetItem(model_name)
            self.table.setItem(row, 4, model_item)
            
            saved_at = result.get('saved_at') or ''
            date_item = QTableWidgetItem(saved_at)
            self.table.setItem(row, 5, date_item)
            
            # Ответ (обрезанный) - обрабатываем случай None
            response = result.get('response_text') or ''  # Если None, используем пустую строку
            response_short = response[:100] + "..." if response and len(response) > 100 else (response or '(Пустой ответ)')
            response_item = QTableWidgetItem(response_short)
            response_item.setToolTip(response or '(Пустой ответ)')
            self.table.setItem(row, 6, response_item)
        
        # Обновляем состояние кнопки удаления
        self.update_delete_button_state()
    
    def get_selected_result(self) -> Optional[Dict]:
        """Получение выбранного результата (для совместимости со старым кодом)."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        
        id_item = self.table.item(current_row, 1)  # ID теперь в колонке 1
        if id_item:
            return id_item.data(Qt.UserRole)
        return None
    
    def get_selected_results(self) -> List[Dict]:
        """Получение всех выбранных результатов."""
        selected = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                id_item = self.table.item(row, 1)  # ID теперь в колонке 1
                if id_item:
                    result = id_item.data(Qt.UserRole)
                    if result:
                        selected.append(result)
        return selected
    
    def update_delete_button_state(self):
        """Обновление состояния кнопки удаления в зависимости от выбранных элементов."""
        selected = self.get_selected_results()
        self.delete_button.setEnabled(len(selected) > 0)
    
    def view_result_details(self):
        """Просмотр детальной информации о результате."""
        result = self.get_selected_result()
        if not result:
            QMessageBox.warning(self, "Предупреждение", "Выберите результат для просмотра!")
            return
        
        dialog = ResultDetailDialog(self, result)
        dialog.exec_()
    
    def delete_selected_results(self):
        """Удаление выбранных результатов."""
        selected = self.get_selected_results()
        
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите результаты для удаления!")
            return
        
        count = len(selected)
        if count == 1:
            message = "Вы уверены, что хотите удалить этот результат?"
        else:
            message = f"Вы уверены, что хотите удалить {count} выбранных результатов?"
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                cursor = self.db.conn.cursor()
                deleted_count = 0
                
                for result in selected:
                    result_id = result.get('id')
                    if result_id:
                        cursor.execute("DELETE FROM results WHERE id = ?", (result_id,))
                        deleted_count += 1
                
                self.db.conn.commit()
                
                if deleted_count > 0:
                    if deleted_count == 1:
                        QMessageBox.information(self, "Успех", "Результат удален успешно!")
                    else:
                        QMessageBox.information(self, "Успех", f"Удалено результатов: {deleted_count}")
                    self.load_history()
                else:
                    QMessageBox.warning(self, "Предупреждение", "Не удалось удалить результаты!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении результатов: {str(e)}")
    
    def export_selected(self):
        """Экспорт выбранных результатов."""
        selected = self.get_selected_results()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите результаты для экспорта!")
            return
        
        # Простой экспорт в текстовый файл (можно расширить)
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результаты",
            "",
            "Markdown Files (*.md);;JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    import json
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(selected, f, ensure_ascii=False, indent=2)
                else:
                    # Markdown или текстовый формат
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"# Экспорт результатов ({len(selected)} шт.)\n\n")
                        for idx, result in enumerate(selected, 1):
                            f.write(f"## Результат {idx}\n\n")
                            prompt = result.get('prompt') or '(Промт был удален)'
                            f.write(f"**Промт:**\n{prompt}\n\n")
                            f.write(f"**Модель:** {result.get('model_name') or '(Не указана)'}\n\n")
                            f.write(f"**Дата:** {result.get('saved_at') or '(Не указана)'}\n\n")
                            response = result.get('response_text') or '(Пустой ответ)'
                            f.write(f"**Ответ:**\n{response}\n\n")
                            f.write("---\n\n")  # Разделитель между результатами
                
                count = len(selected)
                if count == 1:
                    QMessageBox.information(self, "Успех", f"Результат экспортирован в {filename}")
                else:
                    QMessageBox.information(self, "Успех", f"Экспортировано результатов: {count}\nФайл: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать результаты: {str(e)}")
