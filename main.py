# main.py - APPLICATION ENTRY POINT
import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from auth_system import WelcomeScreen, LoginWindow, SignupWindow
from customer_dashboard import CustomerDashboard
from employee_dashboard import EmployeeDashboard
from manager_dashboard import ManagerDashboard
from database import Database

class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.current_user = None
        self.init_database()
        self.init_ui()
    
    def init_database(self) -> bool:
        """
        Initialize database connection for macOS/Docker (use SQL auth).
        Assumes SQL Server is reachable at localhost:1433 (change if different).
        """
        host = "localhost"         # change if Azure Data Studio shows a different host
        port = 1433                # change if you published a different port
        server = f"{host},{port}"  # pass host,port to pyodbc (comma-separated)
        database = "CinemaDB"
        username = "sa"            # change to the SQL login you use
        password = "reallyStrongPwd123"  # change to your real SA/password

        # Always try SQL auth on macOS — Trusted_Connection won't work here.
        try:
            ok = self.db.connect(server, database, username, password)
            if not ok:
                # connection failed — log and show UI error
                print("DB.connect returned False using SQL auth")
                self.show_db_error()
                return False

            print("init_database: connected to database successfully")
            return True

        except Exception as e:
            # Defensive: if Database.connect raises an exception instead of returning False
            print("Exception while connecting to DB: %s", e)
            self.show_db_error()
            return False


    
    def show_db_error(self):
        """Show database connection error and exit"""
        error_msg = """
        Cannot connect to database!
        
        Please ensure:
        1. SQL Server is running
        2. Database 'CinemaDB' exists
        3. Connection details are correct
        
        The application will now exit.
        """
        QMessageBox.critical(self, "Database Error", error_msg)
        sys.exit(1)
    
    def init_ui(self):
        """Initialize the main UI with stacked widgets"""
        self.setWindowTitle("Cinema Management System")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget with stacked layout
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create all screens
        self.create_welcome_screen()
        self.create_login_screen()
        self.create_signup_screen()
        self.create_dashboards()
        
        # Show welcome screen first
        self.stacked_widget.setCurrentWidget(self.welcome_screen)
        
        self.apply_styles()
    
    def create_welcome_screen(self):
        """Create the welcome/landing screen"""
        self.welcome_screen = WelcomeScreen()
        self.welcome_screen.show_login.connect(self.show_login)
        self.welcome_screen.show_signup.connect(self.show_signup)
        self.stacked_widget.addWidget(self.welcome_screen)
    
    def create_login_screen(self):
        """Create the login screen"""
        self.login_screen = LoginWindow(self.db)
        self.login_screen.login_successful.connect(self.handle_login_success)
        self.login_screen.show_welcome.connect(self.show_welcome)
        self.stacked_widget.addWidget(self.login_screen)
    
    def create_signup_screen(self):
        """Create the signup screen"""
        self.signup_screen = SignupWindow(self.db)
        self.signup_screen.signup_successful.connect(self.handle_signup_success)
        self.signup_screen.show_welcome.connect(self.show_welcome)
        self.stacked_widget.addWidget(self.signup_screen)
    
    def create_dashboards(self):
        """Create role-specific dashboards"""
        self.customer_dashboard = None
        self.employee_dashboard = None
        self.manager_dashboard = None
    
    def show_welcome(self):
        """Show welcome screen"""
        self.stacked_widget.setCurrentWidget(self.welcome_screen)
        self.clear_auth_fields()
    
    def show_login(self):
        """Show login screen"""
        self.stacked_widget.setCurrentWidget(self.login_screen)
    
    def show_signup(self):
        """Show signup screen"""
        self.stacked_widget.setCurrentWidget(self.signup_screen)
    
    def handle_login_success(self, user_data):
        """Handle successful login and redirect to appropriate dashboard"""
        self.current_user = user_data
        user_type = user_data['user_type']
        
        if user_type == 'customer':
            self.show_customer_dashboard()
        elif user_type == 'employee':
            self.show_employee_dashboard()
        elif user_type == 'manager':
            self.show_manager_dashboard()
        else:
            QMessageBox.critical(self, "Error", f"Unknown user type: {user_type}")
    
    def handle_signup_success(self):
        """Handle successful signup - return to welcome screen"""
        self.signup_screen.clear_fields()
        self.show_welcome()
        QMessageBox.information(self, "Success", 
                              "Account created successfully! You can now login.")
    
    def show_customer_dashboard(self):
        """Show customer dashboard"""
        if not self.customer_dashboard:
            self.customer_dashboard = CustomerDashboard(self.db, self.current_user)
            self.customer_dashboard.logout_signal.connect(self.handle_logout)
            self.stacked_widget.addWidget(self.customer_dashboard)
        
        self.stacked_widget.setCurrentWidget(self.customer_dashboard)
        self.login_screen.clear_fields()
    
    def show_employee_dashboard(self):
        """Show employee dashboard"""
        if not self.employee_dashboard:
            self.employee_dashboard = EmployeeDashboard(self.db, self.current_user)
            self.employee_dashboard.logout_signal.connect(self.handle_logout)
            self.stacked_widget.addWidget(self.employee_dashboard)
        
        self.stacked_widget.setCurrentWidget(self.employee_dashboard)
        self.login_screen.clear_fields()
    
    def show_manager_dashboard(self):
        """Show manager dashboard"""
        if not self.manager_dashboard:
            self.manager_dashboard = ManagerDashboard(self.db, self.current_user)
            self.manager_dashboard.logout_signal.connect(self.handle_logout)
            self.stacked_widget.addWidget(self.manager_dashboard)
        
        self.stacked_widget.setCurrentWidget(self.manager_dashboard)
        self.login_screen.clear_fields()
    
    def handle_logout(self):
        """Handle logout from any dashboard"""
        self.current_user = None
        
        # Clean up dashboards
        self.customer_dashboard = None
        self.employee_dashboard = None
        self.manager_dashboard = None
        
        # Recreate welcome and auth screens
        self.stacked_widget.removeWidget(self.welcome_screen)
        self.stacked_widget.removeWidget(self.login_screen)
        self.stacked_widget.removeWidget(self.signup_screen)
        
        self.create_welcome_screen()
        self.create_login_screen()
        self.create_signup_screen()
        
        self.stacked_widget.setCurrentWidget(self.welcome_screen)
        
        QMessageBox.information(self, "Logged Out", "You have been successfully logged out.")
    
    def clear_auth_fields(self):
        """Clear authentication fields"""
        if hasattr(self, 'login_screen'):
            self.login_screen.clear_fields()
        if hasattr(self, 'signup_screen'):
            self.signup_screen.clear_fields()
    
    def apply_styles(self):
        """Apply global application styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QMessageBox {
                background-color: white;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # Set application font
        app_font = QFont("Segoe UI", 10)
        QApplication.setFont(app_font)
    
    def closeEvent(self, event):
        """Handle application closure"""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit the Cinema Management System?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clean up resources
            if hasattr(self.db, 'connection') and self.db.connection:
                self.db.connection.close()
            event.accept()
        else:
            event.ignore()

def main():
    """Main application entry point"""
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Cinema Management System")
        app.setApplicationVersion("1.0")
        
        # Create and show main window
        main_window = MainApplication()
        main_window.show()
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Application error: {e}")
        QMessageBox.critical(None, "Fatal Error", 
                           f"The application encountered a fatal error:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()