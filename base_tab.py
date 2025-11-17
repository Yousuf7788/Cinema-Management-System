# base_tab.py - ENHANCED VERSION
"""
Base tab class for all tabs in the Cinema Management System.
Provides common functionality for all dashboard components.
"""

from PyQt6.QtWidgets import QWidget, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
import logging

class BaseTab(QWidget):
    """
    Base class for all tabs in the application.
    Provides common functionality and database connection.
    """
    
    # Signal for data refresh notifications
    data_updated = pyqtSignal()
    
    def __init__(self, db, table_name=None):
        """
        Initialize the base tab.
        
        Args:
            db: Database connection object
            table_name (str, optional): Name of the database table for this tab
        """
        super().__init__()
        self.db = db
        self.table_name = table_name
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Note: We don't call init_ui() here anymore
        # Each tab class will handle its own UI setup via setupUi(self)
    
    def load_data(self):
        """Load data from database. To be implemented by subclasses."""
        self.logger.warning(f"load_data() not implemented in {self.__class__.__name__}")
    
    def add_record(self):
        """Add new record to database. To be implemented by subclasses."""
        self.logger.warning(f"add_record() not implemented in {self.__class__.__name__}")
    
    def update_record(self):
        """Update existing record. To be implemented by subclasses."""
        self.logger.warning(f"update_record() not implemented in {self.__class__.__name__}")
    
    def delete_record(self):
        """Delete record from database. To be implemented by subclasses."""
        self.logger.warning(f"delete_record() not implemented in {self.__class__.__name__}")
    
    def refresh_data(self):
        """Refresh tab data - calls load_data() and emits signal."""
        self.load_data()
        self.data_updated.emit()
        self.logger.debug(f"Data refreshed in {self.__class__.__name__}")

    def execute_query(self, query, params=None, fetch=False):
        """
        Execute query and return (success, result, error) tuple.
        Uses the database connection's execute_query method if available.
        """
        try:
            # Use the database's execute_query method if it exists
            if hasattr(self.db, 'execute_query'):
                return self.db.execute_query(query, params, fetch)
            else:
                # Fallback to direct database connection
                cursor = self.db.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch:
                    result = cursor.fetchall()
                else:
                    result = None
                    self.db.commit()
                
                cursor.close()
                return True, result, None
                
        except Exception as e:
            error_msg = f"Database error: {str(e)}"
            self.logger.error(f"Query failed: {query} - Error: {error_msg}")
            return False, None, error_msg
    
    def show_success_message(self, title, message):
        """Show success message dialog."""
        QMessageBox.information(self, title, message)
        self.logger.info(f"{title}: {message}")
    
    def show_error_message(self, title, message):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
        self.logger.error(f"{title}: {message}")
    
    def show_warning_message(self, title, message):
        """Show warning message dialog."""
        QMessageBox.warning(self, title, message)
        self.logger.warning(f"{title}: {message}")
    
    def confirm_action(self, title, message):
        """
        Show confirmation dialog.
        
        Returns:
            bool: True if user confirmed, False otherwise
        """
        reply = QMessageBox.question(
            self, 
            title, 
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    def validate_required_fields(self, fields_dict):
        """
        Validate that required fields are not empty.
        
        Args:
            fields_dict (dict): Dictionary of field names and values
            
        Returns:
            tuple: (is_valid, error_message)
        """
        for field_name, field_value in fields_dict.items():
            if field_value is None or str(field_value).strip() == "":
                return False, f"Field '{field_name}' is required"
        return True, ""
    
    def populate_table(self, table_widget, data, headers, status_column=None):
        """
        Populate table widget with data.
        
        Args:
            table_widget: QTableWidget to populate
            data (list): List of dictionaries or tuples with row data
            headers (list): List of column headers
            status_column (int, optional): Column index for status coloring
        """
        if not data:
            table_widget.setRowCount(0)
            table_widget.setColumnCount(1)
            table_widget.setHorizontalHeaderLabels(["No data available"])
            return
        
        table_widget.setRowCount(len(data))
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        
        for row_idx, row_data in enumerate(data):
            for col_idx in range(len(headers)):
                if isinstance(row_data, dict):
                    # Data is dictionary
                    cell_value = row_data.get(headers[col_idx].lower().replace(' ', '_'), '')
                else:
                    # Data is tuple/list
                    cell_value = row_data[col_idx] if col_idx < len(row_data) else ''
                
                item = QTableWidgetItem(str(cell_value))
                
                # Apply status coloring if specified
                if status_column == col_idx:
                    self.color_status_item(item, str(cell_value))
                
                table_widget.setItem(row_idx, col_idx, item)
    
    def color_status_item(self, item, status):
        """Apply color coding based on status."""
        status = status.lower()
        if status in ['confirmed', 'approved', 'active', 'completed']:
            item.setForeground(QColor('green'))
        elif status in ['pending', 'processing']:
            item.setForeground(QColor('orange'))
        elif status in ['cancelled', 'rejected', 'refunded', 'inactive']:
            item.setForeground(QColor('red'))
        elif status in ['waiting', 'on hold']:
            item.setForeground(QColor('blue'))
    
    def get_selected_row_data(self, table_widget):
        """
        Get data from the selected row in a table.
        
        Returns:
            tuple: (row_index, row_data) or (None, None) if no selection
        """
        selected_items = table_widget.selectedItems()
        if not selected_items:
            return None, None
        
        row_index = selected_items[0].row()
        row_data = []
        for col in range(table_widget.columnCount()):
            item = table_widget.item(row_index, col)
            row_data.append(item.text() if item else "")
        
        return row_index, row_data
    
    def clear_form_fields(self, *widgets):
        """
        Clear multiple form fields.
        
        Args:
            *widgets: Variable number of form widgets to clear
        """
        for widget in widgets:
            if hasattr(widget, 'clear'):
                widget.clear()
            elif hasattr(widget, 'setText'):
                widget.setText("")
            elif hasattr(widget, 'setValue'):
                if hasattr(widget, 'minimum'):  # It's a spinbox
                    widget.setValue(widget.minimum())
                else:
                    widget.setValue(0)
            elif hasattr(widget, 'setCurrentIndex'):
                widget.setCurrentIndex(0)
            elif hasattr(widget, 'setChecked'):
                widget.setChecked(False)
    
    def enable_widgets(self, enable, *widgets):
        """
        Enable or disable multiple widgets.
        
        Args:
            enable (bool): True to enable, False to disable
            *widgets: Variable number of widgets to modify
        """
        for widget in widgets:
            if hasattr(widget, 'setEnabled'):
                widget.setEnabled(enable)
    
    def format_currency(self, amount):
        """Format amount as currency string."""
        try:
            return f"${float(amount):.2f}"
        except (ValueError, TypeError):
            return "$0.00"
    
    def format_date(self, date_string):
        """Format date string for display."""
        try:
            from datetime import datetime
            if isinstance(date_string, str):
                # Try to parse the date string
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        dt = datetime.strptime(date_string, fmt)
                        return dt.strftime('%b %d, %Y %I:%M %p')
                    except ValueError:
                        continue
            return str(date_string)
        except:
            return str(date_string)
    
    def log_operation(self, operation, details=""):
        """Log user operations for auditing."""
        self.logger.info(f"Operation: {operation} - {details}")