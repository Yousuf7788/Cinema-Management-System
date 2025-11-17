# auth_system.py - MODIFIED VERSION
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QComboBox, QFormLayout, QGroupBox, QMessageBox,
                             QStackedWidget)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QPixmap

class WelcomeScreen(QWidget):
    show_login = pyqtSignal()
    show_signup = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🎬 Cinema Management System")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #000000; margin: 20px;")
        layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Your Ultimate Movie Experience")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #000000; margin-bottom: 30px;")
        layout.addWidget(subtitle)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        self.login_btn = QPushButton("🔐 Login to Existing Account")
        self.login_btn.setFixedHeight(50)
        self.login_btn.clicked.connect(self.show_login.emit)
        
        self.signup_btn = QPushButton("👤 Create New Customer Account")
        self.signup_btn.setFixedHeight(50)
        self.signup_btn.clicked.connect(self.show_signup.emit)
        
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.signup_btn)
        
        layout.addLayout(button_layout)
        
        # Info section
        info_group = QGroupBox("About the System")
        info_layout = QVBoxLayout()
        
        customer_info = QLabel("• Customers: Book movies, manage bookings, request refunds")
        employee_info = QLabel("• Employees: Process bookings, manage refunds, update screenings")
        manager_info = QLabel("• Managers: Add/remove movies, manage employees, full system access")
        
        for label in [customer_info, employee_info, manager_info]:
            label.setStyleSheet("color: #000000; margin: 5px;")
            info_layout.addWidget(label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        self.setLayout(layout)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)

class LoginWindow(QWidget):
    login_successful = pyqtSignal(dict)
    show_welcome = pyqtSignal()
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🔐 Login to Cinema System")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #2c3e50; margin: 15px;")
        layout.addWidget(header)
        
        # Login form
        form_group = QGroupBox("Enter Your Credentials")
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFixedHeight(35)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(35)
        
        form_layout.addRow("👤 Username:", self.username_input)
        form_layout.addRow("🔒 Password:", self.password_input)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setFixedHeight(40)
        self.login_btn.clicked.connect(self.handle_login)
        
        self.back_btn = QPushButton("Back to Welcome")
        self.back_btn.setFixedHeight(40)
        self.back_btn.clicked.connect(self.show_welcome.emit)
        
        button_layout.addWidget(self.back_btn)
        button_layout.addWidget(self.login_btn)
        
        layout.addLayout(button_layout)
        
        # User type info
        info_label = QLabel("💡 Employees: Use provided work credentials\n💡 Customers: Use your created account")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: 10px;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            self.show_error("Error", "Please enter both username and password")
            return
        
        # Show loading state
        self.login_btn.setText("Logging in...")
        self.login_btn.setEnabled(False)
        
        # Authenticate user
        user_data = self.db.authenticate_user(username, password)
        if user_data:
            self.login_successful.emit(user_data)
        else:
            self.show_error("Login Failed", "Invalid username or password")
            self.login_btn.setText("Login")
            self.login_btn.setEnabled(True)
    
    def clear_fields(self):
        self.username_input.clear()
        self.password_input.clear()
        self.login_btn.setText("Login")
        self.login_btn.setEnabled(True)
    
    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)

class SignupWindow(QWidget):
    signup_successful = pyqtSignal()
    show_welcome = pyqtSignal()
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("👤 Create Customer Account")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #2c3e50; margin: 15px;")
        layout.addWidget(header)
        
        # Signup form
        form_group = QGroupBox("Customer Information")
        form_layout = QFormLayout()
        
        # Create input fields
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.confirm_password_input = QLineEdit()
        
        # Set properties
        inputs = [
            self.first_name_input, self.last_name_input, self.email_input,
            self.phone_input, self.username_input, self.password_input,
            self.confirm_password_input
        ]
        
        for input_field in inputs:
            input_field.setFixedHeight(35)
        
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Set placeholders
        self.first_name_input.setPlaceholderText("Enter first name")
        self.last_name_input.setPlaceholderText("Enter last name")
        self.email_input.setPlaceholderText("Enter email address")
        self.phone_input.setPlaceholderText("Enter phone number (optional)")
        self.username_input.setPlaceholderText("Choose a username")
        self.password_input.setPlaceholderText("Enter password (min 6 characters)")
        self.confirm_password_input.setPlaceholderText("Confirm your password")
        
        # Add to form
        form_layout.addRow("👤 First Name:", self.first_name_input)
        form_layout.addRow("👤 Last Name:", self.last_name_input)
        form_layout.addRow("📧 Email:", self.email_input)
        form_layout.addRow("📞 Phone:", self.phone_input)
        form_layout.addRow("👤 Username:", self.username_input)
        form_layout.addRow("🔒 Password:", self.password_input)
        form_layout.addRow("🔒 Confirm Password:", self.confirm_password_input)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("Back to Welcome")
        self.back_btn.setFixedHeight(40)
        self.back_btn.clicked.connect(self.show_welcome.emit)
        
        self.signup_btn = QPushButton("Create Account")
        self.signup_btn.setFixedHeight(40)
        self.signup_btn.clicked.connect(self.handle_signup)
        
        button_layout.addWidget(self.back_btn)
        button_layout.addWidget(self.signup_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def handle_signup(self):
        # Get form data
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        
        # Validation
        if not all([first_name, last_name, email, username, password]):
            self.show_error("Error", "Please fill in all required fields")
            return
        
        if password != confirm_password:
            self.show_error("Error", "Passwords do not match")
            return
        
        if len(password) < 6:
            self.show_error("Error", "Password must be at least 6 characters")
            return
        
        if '@' not in email or '.' not in email:
            self.show_error("Error", "Please enter a valid email address")
            return
        
        # Show loading state
        self.signup_btn.setText("Creating Account...")
        self.signup_btn.setEnabled(False)
        
        # Create user account
        success = self.db.create_user(username, password, email, 'customer', first_name, last_name, phone)
        if success:
            self.show_success("Account Created", "Your account has been created successfully! You can now login.")
            self.signup_successful.emit()
        else:
            self.show_error("Error", "Username or email already exists")
            self.signup_btn.setText("Create Account")
            self.signup_btn.setEnabled(True)
    
    def clear_fields(self):
        self.first_name_input.clear()
        self.last_name_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.signup_btn.setText("Create Account")
        self.signup_btn.setEnabled(True)
    
    def show_success(self, title, message):
        QMessageBox.information(self, title, message)
    
    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #27ae60;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)