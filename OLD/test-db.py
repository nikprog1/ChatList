"""
Тестовая программа для просмотра и редактирования SQLite баз данных.
"""

import sys
import sqlite3
import os
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QLabel, QLineEdit, QDialog, QFormLayout, QListWidget, QDialogButtonBox,
    QComboBox, QSpinBox, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class TableViewDialog(QDialog):
    """Диалог для просмотра и редактирования таблицы с пагинацией."""
    
    def __init__(self, parent, db_path: str, table_name: str):
        super().__init__(parent)
        self.db_path = db_path
        self.table_name = table_name
        self.current_page = 1
        self.rows_per_page = 50
        self.total_rows = 0
        
        self.setWindowTitle(f"Таблица: {table_name}")
        self.setMinimumSize(900, 600)
        
        self.init_ui()
        self.load_table_data()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        
        # Заголовок и информация
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"Таблица: <b>{self.table_name}</b>"))
        info_layout.addStretch()
        self.rows_label = QLabel("")
        info_layout.addWidget(self.rows_label)
        layout.addLayout(info_layout)
        
        # Пагинация (вверху)
        pagination_top = QHBoxLayout()
        pagination_top.addStretch()
        self.page_label = QLabel("Страница: 1")
        pagination_top.addWidget(self.page_label)
        
        self.prev_button = QPushButton("← Назад")
        self.prev_button.clicked.connect(self.prev_page)
        pagination_top.addWidget(self.prev_button)
        
        self.rows_spin = QSpinBox()
        self.rows_spin.setMinimum(10)
        self.rows_spin.setMaximum(500)
        self.rows_spin.setValue(self.rows_per_page)
        self.rows_spin.valueChanged.connect(self.on_rows_per_page_changed)
        pagination_top.addWidget(QLabel("Строк на странице:"))
        pagination_top.addWidget(self.rows_spin)
        
        self.next_button = QPushButton("Вперед →")
        self.next_button.clicked.connect(self.next_page)
        pagination_top.addWidget(self.next_button)
        layout.addLayout(pagination_top)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("➕ Добавить")
        self.add_button.clicked.connect(self.add_row)
        buttons_layout.addWidget(self.add_button)
        
        self.update_button = QPushButton("✏️ Изменить")
        self.update_button.clicked.connect(self.update_row)
        buttons_layout.addWidget(self.update_button)
        
        self.delete_button = QPushButton("🗑️ Удалить")
        self.delete_button.clicked.connect(self.delete_row)
        buttons_layout.addWidget(self.delete_button)
        
        buttons_layout.addStretch()
        
        self.refresh_button = QPushButton("🔄 Обновить")
        self.refresh_button.clicked.connect(self.load_table_data)
        buttons_layout.addWidget(self.refresh_button)
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def get_connection(self):
        """Получение соединения с БД."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_table_structure(self) -> List[Dict[str, Any]]:
        """Получение структуры таблицы."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({self.table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[1],
                'type': row[2],
                'notnull': row[3],
                'default': row[4],
                'pk': row[5]
            })
        conn.close()
        return columns
    
    def load_table_data(self):
        """Загрузка данных таблицы с пагинацией."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Получаем общее количество строк
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            self.total_rows = cursor.fetchone()[0]
            
            # Получаем структуру таблицы
            columns = self.get_table_structure()
            column_names = [col['name'] for col in columns]
            
            # Вычисляем offset и limit
            offset = (self.current_page - 1) * self.rows_per_page
            limit = self.rows_per_page
            
            # Загружаем данные с пагинацией
            cursor.execute(f"SELECT * FROM {self.table_name} LIMIT ? OFFSET ?", (limit, offset))
            rows = cursor.fetchall()
            
            conn.close()
            
            # Настраиваем таблицу
            self.table.setColumnCount(len(column_names))
            self.table.setHorizontalHeaderLabels(column_names)
            self.table.setRowCount(len(rows))
            
            # Заполняем таблицу
            for row_idx, row_data in enumerate(rows):
                for col_idx, col_name in enumerate(column_names):
                    value = row_data[col_name] if col_name in row_data.keys() else None
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setData(Qt.UserRole, col_name)  # Сохраняем имя колонки
                    self.table.setItem(row_idx, col_idx, item)
            
            # Обновляем информацию
            total_pages = (self.total_rows + self.rows_per_page - 1) // self.rows_per_page if self.total_rows > 0 else 1
            self.page_label.setText(f"Страница: {self.current_page} / {total_pages}")
            self.rows_label.setText(f"Всего строк: {self.total_rows}")
            
            # Обновляем состояние кнопок
            self.prev_button.setEnabled(self.current_page > 1)
            self.next_button.setEnabled(self.current_page < total_pages)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{str(e)}")
    
    def prev_page(self):
        """Переход на предыдущую страницу."""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_table_data()
    
    def next_page(self):
        """Переход на следующую страницу."""
        total_pages = (self.total_rows + self.rows_per_page - 1) // self.rows_per_page if self.total_rows > 0 else 1
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_table_data()
    
    def on_rows_per_page_changed(self, value):
        """Изменение количества строк на странице."""
        self.rows_per_page = value
        self.current_page = 1
        self.load_table_data()
    
    def add_row(self):
        """Добавление новой строки."""
        columns = self.get_table_structure()
        
        dialog = AddEditRowDialog(self, columns, {})
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Формируем INSERT запрос
                col_names = [col['name'] for col in columns if col['name'] in data]
                placeholders = ', '.join(['?' for _ in col_names])
                col_names_str = ', '.join(col_names)
                values = [data[col] for col in col_names]
                
                cursor.execute(
                    f"INSERT INTO {self.table_name} ({col_names_str}) VALUES ({placeholders})",
                    values
                )
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Успех", "Строка добавлена успешно")
                self.load_table_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить строку:\n{str(e)}")
    
    def update_row(self):
        """Изменение выбранной строки."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для изменения")
            return
        
        row_idx = selected_rows[0].row()
        
        # Получаем данные из таблицы
        columns = self.get_table_structure()
        current_data = {}
        for col_idx, col in enumerate(columns):
            item = self.table.item(row_idx, col_idx)
            if item:
                current_data[col['name']] = item.text()
        
        # Получаем реальные данные из БД по первичному ключу
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Находим первичные ключи
            pk_columns = [col['name'] for col in columns if col['pk']]
            if not pk_columns:
                QMessageBox.warning(self, "Предупреждение", "Таблица не имеет первичного ключа")
                conn.close()
                return
            
            # Получаем значения PK из таблицы
            pk_values = {}
            for col_idx, col in enumerate(columns):
                if col['pk']:
                    item = self.table.item(row_idx, col_idx)
                    if item:
                        pk_values[col['name']] = item.text()
            
            # Загружаем полную строку из БД
            where_clause = ' AND '.join([f"{col} = ?" for col in pk_columns])
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE {where_clause}", list(pk_values.values()))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                QMessageBox.warning(self, "Предупреждение", "Строка не найдена в базе данных")
                return
            
            # Заполняем данные
            row_data = {}
            for col in columns:
                row_data[col['name']] = row[col['name']] if row[col['name']] is not None else ""
            
            dialog = AddEditRowDialog(self, columns, row_data, is_edit=True, pk_columns=pk_columns)
            if dialog.exec_() == QDialog.Accepted:
                new_data = dialog.get_data()
                try:
                    conn = self.get_connection()
                    cursor = conn.cursor()
                    
                    # Формируем UPDATE запрос
                    set_clause = ', '.join([f"{col} = ?" for col in new_data.keys() if col not in pk_columns])
                    where_clause = ' AND '.join([f"{col} = ?" for col in pk_columns])
                    
                    set_values = [new_data[col] for col in new_data.keys() if col not in pk_columns]
                    where_values = [new_data[col] for col in pk_columns]
                    
                    cursor.execute(
                        f"UPDATE {self.table_name} SET {set_clause} WHERE {where_clause}",
                        set_values + where_values
                    )
                    conn.commit()
                    conn.close()
                    
                    QMessageBox.information(self, "Успех", "Строка изменена успешно")
                    self.load_table_data()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось изменить строку:\n{str(e)}")
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при получении данных:\n{str(e)}")
    
    def delete_row(self):
        """Удаление выбранной строки."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для удаления")
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить выбранную строку?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        row_idx = selected_rows[0].row()
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            columns = self.get_table_structure()
            pk_columns = [col['name'] for col in columns if col['pk']]
            
            if not pk_columns:
                QMessageBox.warning(self, "Предупреждение", "Таблица не имеет первичного ключа")
                conn.close()
                return
            
            # Получаем значения PK из таблицы
            pk_values = {}
            for col_idx, col in enumerate(columns):
                if col['pk']:
                    item = self.table.item(row_idx, col_idx)
                    if item:
                        pk_values[col['name']] = item.text()
            
            # Формируем DELETE запрос
            where_clause = ' AND '.join([f"{col} = ?" for col in pk_columns])
            cursor.execute(f"DELETE FROM {self.table_name} WHERE {where_clause}", list(pk_values.values()))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Успех", "Строка удалена успешно")
            self.load_table_data()
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить строку:\n{str(e)}")


class AddEditRowDialog(QDialog):
    """Диалог для добавления/изменения строки."""
    
    def __init__(self, parent, columns: List[Dict], data: Dict, is_edit: bool = False, pk_columns: List[str] = None):
        super().__init__(parent)
        self.columns = columns
        self.data = data.copy()
        self.is_edit = is_edit
        self.pk_columns = pk_columns or []
        self.fields = {}
        
        title = "Изменение строки" if is_edit else "Добавление строки"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QFormLayout()
        
        for col in self.columns:
            col_name = col['name']
            label_text = col_name
            if col['pk']:
                label_text += " (PK)"
            if col['notnull']:
                label_text += " *"
            
            value = self.data.get(col_name, col.get('default', ''))
            
            # Для первичного ключа при редактировании делаем поле только для чтения
            if self.is_edit and col_name in self.pk_columns:
                field = QLineEdit(str(value) if value else "")
                field.setReadOnly(True)
                field.setStyleSheet("background-color: #f0f0f0;")
            else:
                field = QLineEdit(str(value) if value else "")
            
            layout.addRow(label_text, field)
            self.fields[col_name] = field
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_data(self) -> Dict[str, str]:
        """Получение данных из формы."""
        data = {}
        for col_name, field in self.fields.items():
            data[col_name] = field.text()
        return data


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        self.db_path: Optional[str] = None
        self.setWindowTitle("SQLite Database Viewer")
        self.setMinimumSize(500, 400)
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Заголовок
        title_label = QLabel("Просмотр SQLite базы данных")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Кнопка выбора файла
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл не выбран")
        file_layout.addWidget(self.file_label)
        
        select_button = QPushButton("📁 Выбрать файл")
        select_button.clicked.connect(self.select_file)
        file_layout.addWidget(select_button)
        layout.addLayout(file_layout)
        
        # Список таблиц
        layout.addWidget(QLabel("Таблицы в базе данных:"))
        self.tables_list = QListWidget()
        self.tables_list.itemDoubleClicked.connect(self.open_table)
        layout.addWidget(self.tables_list)
        
        # Кнопка открытия
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.open_button = QPushButton("Открыть")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_selected_table)
        button_layout.addWidget(self.open_button)
        
        layout.addLayout(button_layout)
        
        # Подключение сигнала выбора
        self.tables_list.itemSelectionChanged.connect(self.on_table_selection_changed)
    
    def select_file(self):
        """Выбор SQLite файла."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл SQLite",
            "",
            "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*.*)"
        )
        
        if file_path:
            self.db_path = file_path
            self.file_label.setText(f"Файл: {os.path.basename(file_path)}")
            self.load_tables()
    
    def load_tables(self):
        """Загрузка списка таблиц."""
        if not self.db_path:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем список таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            self.tables_list.clear()
            self.tables_list.addItems(tables)
            
            if not tables:
                QMessageBox.information(self, "Информация", "База данных не содержит таблиц")
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить таблицы:\n{str(e)}")
            self.tables_list.clear()
    
    def on_table_selection_changed(self):
        """Обработка изменения выбора таблицы."""
        self.open_button.setEnabled(len(self.tables_list.selectedItems()) > 0)
    
    def open_selected_table(self):
        """Открытие выбранной таблицы."""
        selected_items = self.tables_list.selectedItems()
        if not selected_items:
            return
        
        table_name = selected_items[0].text()
        self.open_table_by_name(table_name)
    
    def open_table(self, item):
        """Открытие таблицы по двойному клику."""
        table_name = item.text()
        self.open_table_by_name(table_name)
    
    def open_table_by_name(self, table_name: str):
        """Открытие диалога просмотра таблицы."""
        if not self.db_path:
            return
        
        dialog = TableViewDialog(self, self.db_path, table_name)
        dialog.exec_()


def main():
    """Главная функция."""
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
