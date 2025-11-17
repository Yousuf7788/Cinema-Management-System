# employee_dashboard.py - MODIFIED VERSION
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QLabel, 
                             QPushButton, QHeaderView, QInputDialog, QDoubleSpinBox,
                             QDialog, QFormLayout, QTextEdit, QDateEdit, QSpinBox)
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime
from PyQt6.QtGui import QFont, QColor
from customer_dashboard import CustomerDashboard
from booking_tab import BookingTab
from screening_tab import ScreeningTab
from movie_tab import MovieTab
import datetime

class EmployeeDashboard(QWidget):
    logout_signal = pyqtSignal()
    
    def __init__(self, db, user_data):
            super().__init__()

            # Defensive: ensure user_data is a dict
            if not isinstance(user_data, dict):
                print("ERROR: EmployeeDashboard expected user_data dict but got:", repr(user_data), type(user_data))
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Internal Error", "Invalid user data passed to Employee Dashboard.")
                return

            # store user data under both names for compatibility with other modules
            self.db = db
            self.user_data = user_data
            self.current_user = user_data

            # safely extract fields (use .get to avoid KeyError)
            self.employee_id = user_data.get('employee_id')
            # normalize user_type to a string if present
            user_type = user_data.get('user_type')
            self.is_manager = (str(user_type).lower() == 'manager') if user_type is not None else False

            # continue initialization
            self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header with user info and logout
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #2c3e50; padding: 10px;")
        header_layout = QHBoxLayout(header_widget)
        
        role = "🎯 Manager" if self.is_manager else "👨‍💼 Employee"
        welcome_label = QLabel(f"{role} Portal - {self.user_data['first_name']} {self.user_data['last_name']} ({self.user_data['position']})")
        welcome_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: white;")
        
        self.logout_btn = QPushButton("🚪 Logout")
        self.logout_btn.setFixedSize(100, 35)
        self.logout_btn.clicked.connect(self.logout_signal.emit)
        
        header_layout.addWidget(welcome_label)
        header_layout.addStretch()
        header_layout.addWidget(self.logout_btn)
        
        layout.addWidget(header_widget)
        
        # Create tab widget for different employee features
        self.tabs = QTabWidget()
        
        # Refund Management Tab
        self.refund_tab = RefundManagementTab(self.db, self.employee_id, self.is_manager)
        self.tabs.addTab(self.refund_tab, "💸 Refunds")
        
        # Movie Management Tab
        self.movie_tab = MovieManagementTab(self.db, self.is_manager)
        self.tabs.addTab(self.movie_tab, "🎬 Movies")
        
        # Customer Management Tab
        self.customer_tab = CustomerDashboard(self.db, self.current_user.get('customer_id'))


        self.tabs.addTab(self.customer_tab, "👥 Customers")
        
        # Booking Management Tab
        self.booking_tab = BookingTab(self.db)
        self.tabs.addTab(self.booking_tab, "📋 Bookings")
        
        # Screening Management Tab (MANAGER ONLY)
        if self.is_manager:
            self.screening_tab = ScreeningTab(self.db)
            self.tabs.addTab(self.screening_tab, "📅 Screenings")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        self.apply_styles()
    
    def apply_styles(self):
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #e74c3c;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #c0392b;
                color: white;
            }
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)

class RefundManagementTab(QWidget):
    def __init__(self, db, employee_id, is_manager):
        super().__init__()
        self.db = db
        self.employee_id = employee_id
        self.is_manager = is_manager
        self.init_ui()
        self.load_refunds()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("💸 Refund Request Management")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Status filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by status:"))
        
        self.status_combo = QPushButton("🔄 All Statuses")  # Using button as dropdown
        self.status_combo.setStyleSheet("text-align: left;")
        self.status_combo.clicked.connect(self.show_status_menu)
        filter_layout.addWidget(self.status_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Refunds table
        self.refund_table = QTableWidget()
        self.refund_table.setAlternatingRowColors(True)
        layout.addWidget(self.refund_table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.view_btn = QPushButton("👁 View Details")
        self.view_btn.clicked.connect(self.view_refund_details)
        
        self.approve_btn = QPushButton("✅ Approve Refund")
        self.approve_btn.clicked.connect(self.approve_refund)
        
        self.reject_btn = QPushButton("❌ Reject Refund")
        self.reject_btn.clicked.connect(self.reject_refund)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_refunds)
        
        button_layout.addWidget(self.view_btn)
        button_layout.addWidget(self.approve_btn)
        button_layout.addWidget(self.reject_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def show_status_menu(self):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        
        statuses = [
            ("🔄 All", "all"),
            ("⏳ Pending", "pending"),
            ("✅ Approved", "approved"),
            ("❌ Rejected", "rejected")
        ]
        
        for text, status in statuses:
            action = menu.addAction(text)
            action.triggered.connect(lambda checked, s=status, t=text: self.filter_by_status(s, t))
        
        menu.exec(self.status_combo.mapToGlobal(self.status_combo.rect().bottomLeft()))
    
    def filter_by_status(self, status, text):
        self.status_combo.setText(text)
        self.load_refunds(status)
    
    def load_refunds(self, status_filter="all"):
        refunds = self.db.get_pending_refunds()  # This gets pending by default
        
        # Apply additional filtering if needed
        if status_filter != "all":
            refunds = [r for r in refunds if r['status'] == status_filter]
        
        if refunds:
            self.refund_table.setRowCount(len(refunds))
            self.refund_table.setColumnCount(8)
            self.refund_table.setHorizontalHeaderLabels([
                "Refund ID", "Customer", "Movie", "Booking ID", "Amount", "Reason", "Status", "Request Date"
            ])
            
            for row_idx, refund in enumerate(refunds):
                self.refund_table.setItem(row_idx, 0, QTableWidgetItem(str(refund['refund_id'])))
                self.refund_table.setItem(row_idx, 1, QTableWidgetItem(f"{refund['first_name']} {refund['last_name']}"))
                self.refund_table.setItem(row_idx, 2, QTableWidgetItem(refund['title']))
                self.refund_table.setItem(row_idx, 3, QTableWidgetItem(str(refund['booking_id'])))
                self.refund_table.setItem(row_idx, 4, QTableWidgetItem(f"${refund['total_amount']:.2f}"))
                
                # Truncate long reasons
                reason = refund['refund_reason']
                if len(reason) > 50:
                    reason = reason[:50] + "..."
                self.refund_table.setItem(row_idx, 5, QTableWidgetItem(reason))
                
                status_item = QTableWidgetItem(refund['status'].title())
                if refund['status'] == 'pending':
                    status_item.setForeground(QColor('orange'))
                elif refund['status'] == 'approved':
                    status_item.setForeground(QColor('green'))
                elif refund['status'] == 'rejected':
                    status_item.setForeground(QColor('red'))
                self.refund_table.setItem(row_idx, 6, status_item)
                
                self.refund_table.setItem(row_idx, 7, QTableWidgetItem(str(refund['refund_date'])))
            
            # Resize columns to content
            header = self.refund_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        else:
            self.refund_table.setRowCount(0)
            self.refund_table.setColumnCount(1)
            self.refund_table.setHorizontalHeaderLabels(["No refund requests found"])
    
    def view_refund_details(self):
        selected_items = self.refund_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select a refund request to view details!")
            return
        
        refund_id = int(self.refund_table.item(selected_items[0].row(), 0).text())
        
        # Get detailed refund information
        refunds = self.db.get_pending_refunds()
        refund = next((r for r in refunds if r['refund_id'] == refund_id), None)
        
        if refund:
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Refund Details - ID: {refund_id}")
            dialog.setModal(True)
            dialog.setFixedSize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Refund details
            details = QLabel(
                f"<h3>Refund Request Details</h3>"
                f"<b>Customer:</b> {refund['first_name']} {refund['last_name']}<br>"
                f"<b>Movie:</b> {refund['title']}<br>"
                f"<b>Booking ID:</b> {refund['booking_id']}<br>"
                f"<b>Original Amount:</b> ${refund['total_amount']:.2f}<br>"
                f"<b>Status:</b> {refund['status'].title()}<br>"
                f"<b>Request Date:</b> {refund['refund_date']}<br><br>"
                f"<b>Reason for Refund:</b><br>{refund['refund_reason']}"
            )
            details.setWordWrap(True)
            layout.addWidget(details)
            
            dialog.exec()
    
    def approve_refund(self):
        selected_items = self.refund_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select a refund request to approve!")
            return
        
        refund_id = int(self.refund_table.item(selected_items[0].row(), 0).text())
        original_amount = float(self.refund_table.item(selected_items[0].row(), 4).text().replace('$', ''))
        
        # Get refund amount (could be partial or full)
        amount, ok = QInputDialog.getDouble(
            self, "Refund Amount", 
            f"Enter refund amount (max: ${original_amount:.2f}):", 
            value=original_amount, min=0.0, max=original_amount, decimals=2
        )
        
        if ok:
            if self.db.process_refund(refund_id, self.employee_id, 'approved', amount):
                QMessageBox.information(self, "Success", f"Refund approved for ${amount:.2f}!")
                self.load_refunds()
            else:
                QMessageBox.critical(self, "Error", "Failed to process refund!")
    
    def reject_refund(self):
        selected_items = self.refund_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select a refund request to reject!")
            return
        
        refund_id = int(self.refund_table.item(selected_items[0].row(), 0).text())
        
        reason, ok = QInputDialog.getText(self, "Rejection Reason", "Please enter reason for rejection:")
        
        if ok:
            if self.db.process_refund(refund_id, self.employee_id, 'rejected'):
                QMessageBox.information(self, "Rejected", "Refund request has been rejected!")
                self.load_refunds()
            else:
                QMessageBox.critical(self, "Error", "Failed to reject refund!")

class MovieManagementTab(QWidget):
    def __init__(self, db, is_manager):
        super().__init__()
        self.db = db
        self.is_manager = is_manager
        self.init_ui()
        self.load_movies()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🎬 Movie Management")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Movies table
        self.movie_table = QTableWidget()
        self.movie_table.setAlternatingRowColors(True)
        layout.addWidget(self.movie_table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        if self.is_manager:
            self.add_btn = QPushButton("➕ Add Movie")
            self.add_btn.clicked.connect(self.add_movie)
            button_layout.addWidget(self.add_btn)
            
            self.edit_btn = QPushButton("✏️ Edit Movie")
            self.edit_btn.clicked.connect(self.edit_movie)
            button_layout.addWidget(self.edit_btn)
            
            self.delete_btn = QPushButton("🗑️ Delete Movie")
            self.delete_btn.clicked.connect(self.delete_movie)
            button_layout.addWidget(self.delete_btn)
        else:
            info_label = QLabel("📋 View-only mode - Managers can edit movies")
            info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
            button_layout.addWidget(info_label)
        
        button_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_movies)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_movies(self):
        movies = self.db.get_movies()
        
        if movies:
            self.movie_table.setRowCount(len(movies))
            self.movie_table.setColumnCount(6)
            self.movie_table.setHorizontalHeaderLabels([
                "ID", "Title", "Genre", "Duration", "Rating", "Director"
            ])
            
            for row_idx, movie in enumerate(movies):
                self.movie_table.setItem(row_idx, 0, QTableWidgetItem(str(movie['movie_id'])))
                self.movie_table.setItem(row_idx, 1, QTableWidgetItem(movie['title']))
                self.movie_table.setItem(row_idx, 2, QTableWidgetItem(movie['genre']))
                self.movie_table.setItem(row_idx, 3, QTableWidgetItem(f"{movie['duration_minutes']} min"))
                self.movie_table.setItem(row_idx, 4, QTableWidgetItem(movie['rating']))
                self.movie_table.setItem(row_idx, 5, QTableWidgetItem(movie['director']))
            
            # Resize columns to content
            header = self.movie_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        else:
            self.movie_table.setRowCount(0)
            self.movie_table.setColumnCount(1)
            self.movie_table.setHorizontalHeaderLabels(["No movies found"])
    
    def add_movie(self):
        if not self.is_manager:
            QMessageBox.warning(self, "Access Denied", "Only managers can add movies!")
            return
        
        dialog = MovieTab.get_movie_details_dialog(self, self.db)
        if dialog.exec():
            self.load_movies()
    
    def edit_movie(self):
        selected_items = self.movie_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select a movie to edit!")
            return
        
        if not self.is_manager:
            QMessageBox.warning(self, "Access Denied", "Only managers can edit movies!")
            return
        
        movie_id = int(self.movie_table.item(selected_items[0].row(), 0).text())
        dialog = MovieTab.get_movie_details_dialog(self, self.db, movie_id)
        if dialog.exec():
            self.load_movies()
    
    def delete_movie(self):
        selected_items = self.movie_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select a movie to delete!")
            return
        
        if not self.is_manager:
            QMessageBox.warning(self, "Access Denied", "Only managers can delete movies!")
            return
        
        movie_id = int(self.movie_table.item(selected_items[0].row(), 0).text())
        movie_title = self.movie_table.item(selected_items[0].row(), 1).text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete '{movie_title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Check if movie has screenings
            screenings = self.db.get_screenings(movie_id)
            if screenings:
                QMessageBox.warning(
                    self, "Cannot Delete", 
                    f"Cannot delete '{movie_title}' because it has {len(screenings)} scheduled screening(s)."
                )
                return
            
            # Delete movie
            if self.db.execute_query("DELETE FROM Movie WHERE movie_id = ?", (movie_id,))[0]:
                QMessageBox.information(self, "Success", "Movie deleted successfully!")
                self.load_movies()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete movie!")

