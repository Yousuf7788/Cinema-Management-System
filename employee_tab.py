from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox, QHeaderView, QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
from ui_employee_tab import Ui_EmployeeTab
from base_tab import BaseTab

class EmployeeTab(BaseTab, Ui_EmployeeTab):
    def __init__(self, db, is_manager=False):
        """
        Initialize Employee Tab
        
        Args:
            db: Database connection
            is_manager: Whether user has manager permissions
        """
        super().__init__(db, "Employee")
        self.setupUi(self)
        self.is_manager = is_manager
        self.connect_signals()
        self.setup_form()
        self.apply_permissions()
        self.load_data()
    
    def connect_signals(self):
        """Connect UI signals to methods"""
        self.addEmployeeBtn.clicked.connect(self.add_record)
        self.updateEmployeeBtn.clicked.connect(self.update_record)
        self.deleteEmployeeBtn.clicked.connect(self.delete_record)
        self.refreshEmployeeBtn.clicked.connect(self.refresh_data)
        self.employeeTable.itemSelectionChanged.connect(self.on_row_selected)
    
    def setup_form(self):
        """Initialize form values"""
        self.hireDateInput.setDate(QDate.currentDate())
        self.hireDateInput.setCalendarPopup(True)
        
        if not hasattr(self, 'salaryInput'):
            self.add_salary_field()
    
    def add_salary_field(self):
        """Add salary field to the form"""
        from PyQt6.QtWidgets import QDoubleSpinBox
        
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget and hasattr(widget, 'layout'):
                layout = widget.layout()
                if isinstance(layout, QFormLayout):
                    self.salaryInput = QDoubleSpinBox()
                    self.salaryInput.setRange(0, 100000)
                    self.salaryInput.setPrefix("$ ")
                    self.salaryInput.setValue(30000)
                    self.salaryInput.setDecimals(2)
                    layout.insertRow(4, "Salary:", self.salaryInput)
                    break
    
    def apply_permissions(self):
        """Apply role-based permissions"""
        if not self.is_manager:
            self.addEmployeeBtn.hide()
            self.updateEmployeeBtn.hide()
            self.deleteEmployeeBtn.hide()
            self.addEmployeeBtn.setEnabled(False)
            self.updateEmployeeBtn.setEnabled(False)
            self.deleteEmployeeBtn.setEnabled(False)
            
            self.firstNameInput.setEnabled(False)
            self.lastNameInput.setEnabled(False)
            self.positionInput.setEnabled(False)
            self.hireDateInput.setEnabled(False)
            if hasattr(self, 'salaryInput'):
                self.salaryInput.setEnabled(False)
            
            self.refreshEmployeeBtn.setText("View Employees")
    
    def refresh_data(self):
        """Refresh employee data"""
        self.load_data()
        self.show_success_message("Refresh", "Employee data refreshed successfully!")
    
    def load_data(self):
        """Load employee data into table"""
        query = """
        SELECT e.employee_id, e.first_name, e.last_name, e.position, e.hire_date,
               u.username, u.email
        FROM Employee e
        LEFT JOIN Users u ON e.employee_id = u.employee_id
        ORDER BY e.employee_id
        """
        
        success, results, error = self.execute_query(query, fetch=True)
        
        if success and results:
            self.employeeTable.setRowCount(len(results))
            self.employeeTable.setColumnCount(7)
            self.employeeTable.setHorizontalHeaderLabels([
                "ID", "First Name", "Last Name", "Position", "Hire Date", "Username", "Email"
            ])
            
            for row_idx, row_data in enumerate(results):
                for col_idx, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data) if col_data else "")
                    self.employeeTable.setItem(row_idx, col_idx, item)
            
            header = self.employeeTable.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        else:
            self.employeeTable.setRowCount(0)
            self.employeeTable.setColumnCount(1)
            self.employeeTable.setHorizontalHeaderLabels(["No employees found"])
            
            if error:
                self.show_error_message("Database Error", f"Failed to load employees: {error}")
    
    def add_record(self):
        """Add new employee with user account creation"""
        if not self.is_manager:
            self.show_error_message("Access Denied", "Only managers can add employees!")
            return
        
        first_name = self.firstNameInput.text().strip()
        last_name = self.lastNameInput.text().strip()
        position = self.positionInput.text().strip()
        hire_date = self.hireDateInput.date().toString("yyyy-MM-dd")
        salary = self.salaryInput.value() if hasattr(self, 'salaryInput') else 0
        
        if not first_name or not last_name or not position:
            self.show_error_message("Error", "First name, last name, and position are required!")
            return
        
        user_credentials = self.get_user_credentials_dialog()
        if not user_credentials:
            return
        
        try:
            cursor = self.db.connection.cursor()
            
            employee_query = """
            INSERT INTO Employee (first_name, last_name, position, hire_date)
            OUTPUT INSERTED.employee_id
            VALUES (?, ?, ?, ?)
            """
            cursor.execute(employee_query, (first_name, last_name, position, hire_date))
            employee_id = cursor.fetchone()[0]
            
            user_query = """
            INSERT INTO Users (username, password_hash, email, user_type, employee_id)
            VALUES (?, ?, ?, ?, ?)
            """
            
            import hashlib
            password_hash = hashlib.md5(user_credentials['password'].encode()).hexdigest()
            
            user_type = 'manager' if position.lower() in ['manager', 'admin'] else 'employee'
            
            cursor.execute(user_query, (
                user_credentials['username'],
                password_hash,
                user_credentials['email'],
                user_type,
                employee_id
            ))
            
            self.db.connection.commit()
            cursor.close()
            
            self.show_success_message("Success", 
                f"Employee '{first_name} {last_name}' added successfully!\n\n"
                f"Username: {user_credentials['username']}\n"
                f"Password: {user_credentials['password']}\n\n"
                f"Please provide these credentials to the employee."
            )
            self.clear_form()
            self.load_data()
            
        except Exception as e:
            self.db.connection.rollback()
            self.show_error_message("Error", f"Failed to add employee: {str(e)}")
    
    def get_user_credentials_dialog(self):
        """Show dialog to get user account credentials"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Employee User Account")
        dialog.setModal(True)
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        username_input = QLineEdit()
        username_input.setPlaceholderText("Enter username for login")
        
        email_input = QLineEdit()
        email_input.setPlaceholderText("Enter email address")
        
        password_input = QLineEdit()
        password_input.setPlaceholderText("Enter temporary password")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        confirm_password_input = QLineEdit()
        confirm_password_input.setPlaceholderText("Confirm temporary password")
        confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        form_layout.addRow("Username:", username_input)
        form_layout.addRow("Email:", email_input)
        form_layout.addRow("Password:", password_input)
        form_layout.addRow("Confirm Password:", confirm_password_input)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        
        def validate_and_accept():
            username = username_input.text().strip()
            email = email_input.text().strip()
            password = password_input.text().strip()
            confirm_password = confirm_password_input.text().strip()
            
            if not username or not email or not password:
                QMessageBox.warning(dialog, "Error", "All fields are required!")
                return
            
            if password != confirm_password:
                QMessageBox.warning(dialog, "Error", "Passwords do not match!")
                return
            
            if len(password) < 6:
                QMessageBox.warning(dialog, "Error", "Password must be at least 6 characters!")
                return
            
            check_query = "SELECT user_id FROM Users WHERE username = ?"
            success, existing_user, error = self.execute_query(check_query, (username,), fetch=True)
            
            if success and existing_user:
                QMessageBox.warning(dialog, "Error", "Username already exists!")
                return
            
            dialog.accept()
        
        button_box.accepted.connect(validate_and_accept)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return {
                'username': username_input.text().strip(),
                'email': email_input.text().strip(),
                'password': password_input.text().strip()
            }
        
        return None
    
    def update_record(self):
        """Update existing employee"""
        if not self.is_manager:
            self.show_error_message("Access Denied", "Only managers can update employees!")
            return
        
        selected_items = self.employeeTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select an employee to update!")
            return
        
        employee_id = int(self.employeeTable.item(selected_items[0].row(), 0).text())
        first_name = self.firstNameInput.text().strip()
        last_name = self.lastNameInput.text().strip()
        position = self.positionInput.text().strip()
        hire_date = self.hireDateInput.date().toString("yyyy-MM-dd")
        
        if not first_name or not last_name or not position:
            self.show_error_message("Error", "First name, last name, and position are required!")
            return
        
        query = """
        UPDATE Employee 
        SET first_name = ?, last_name = ?, position = ?, hire_date = ?
        WHERE employee_id = ?
        """
        
        success, result, error = self.execute_query(query, (first_name, last_name, position, hire_date, employee_id))
        if success:
            self.show_success_message("Success", "Employee updated successfully!")
            self.load_data()
        else:
            self.show_error_message("Error", f"Failed to update employee: {error}")
    
    def delete_record(self):
        """Delete employee (with safety checks)"""
        if not self.is_manager:
            self.show_error_message("Access Denied", "Only managers can delete employees!")
            return
        
        selected_items = self.employeeTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select an employee to delete!")
            return
        
        employee_id = int(self.employeeTable.item(selected_items[0].row(), 0).text())
        first_name = self.employeeTable.item(selected_items[0].row(), 1).text()
        last_name = self.employeeTable.item(selected_items[0].row(), 2).text()
        
        check_query = "SELECT user_id FROM Users WHERE employee_id = ?"
        success, user_account, error = self.execute_query(check_query, (employee_id,), fetch=True)
        
        if success and user_account:
            self.show_warning_message(
                "Cannot Delete", 
                f"Cannot delete {first_name} {last_name} because they have an active user account.\n"
                f"Please deactivate the user account first."
            )
            return
        
        if self.confirm_action(
            "Confirm Delete", 
            f"Are you sure you want to delete employee {first_name} {last_name}?"
        ):
            query = "DELETE FROM Employee WHERE employee_id = ?"
            success, result, error = self.execute_query(query, (employee_id,))
            
            if success:
                self.show_success_message("Success", f"Employee {first_name} {last_name} deleted successfully!")
                self.clear_form()
                self.load_data()
            else:
                self.show_error_message("Error", f"Failed to delete employee: {error}")
    
    def clear_form(self):
        """Clear form fields"""
        self.firstNameInput.clear()
        self.lastNameInput.clear()
        self.positionInput.clear()
        self.hireDateInput.setDate(QDate.currentDate())
        if hasattr(self, 'salaryInput'):
            self.salaryInput.setValue(30000)
    
    def on_row_selected(self):
        """Populate form when row is selected"""
        selected_items = self.employeeTable.selectedItems()
        if selected_items and self.is_manager:
            row = selected_items[0].row()
            self.firstNameInput.setText(self.employeeTable.item(row, 1).text())
            self.lastNameInput.setText(self.employeeTable.item(row, 2).text())
            self.positionInput.setText(self.employeeTable.item(row, 3).text())
            
            hire_date_str = self.employeeTable.item(row, 4).text()
            hire_date = QDate.fromString(hire_date_str, "yyyy-MM-dd")
            if hire_date.isValid():
                self.hireDateInput.setDate(hire_date)