# customer_dashboard.py - MODIFIED VERSION
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QLabel, 
                             QPushButton, QDialog, QListWidget, QDialogButtonBox,
                             QInputDialog, QHeaderView, QScrollArea, QFrame, QGridLayout, QLineEdit, QFormLayout)
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime
from PyQt6.QtGui import QFont, QPixmap
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ClickableFrame(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class CustomerDashboard(QWidget):
    logout_signal = pyqtSignal()
    
    def __init__(self, db, user_data=None, *, allow_none=False, parent=None):
            """
            db: your DB wrapper/connection
            user_data: either dict containing 'customer_id', or int, or None
            allow_none: if True, constructor will create a dashboard usable by staff (no customer)
            """
            super().__init__(parent)

            # Basic required attribute so partial init won't break callers
            self.db = db
            self.user_data = None
            self.current_customer_id = None

            # Accept either dict, int, or None (if allow_none True)
            if isinstance(user_data, dict):
                self.user_data = user_data
                self.current_customer_id = self.user_data.get('customer_id')
            elif isinstance(user_data, int):
                self.user_data = None
                self.current_customer_id = user_data
            elif user_data is None:
                # allow None for staff views; caller must set allow_none when that's expected
                if not allow_none:
                    # Prefer to raise so calling code notices programmer error.
                    raise ValueError("CustomerDashboard expected user_data (dict) or customer_id (int); got None. "
                                    "If you want a staff view, call with allow_none=True.")
                # else: leave current_customer_id as None (staff/manager view)
                logger.debug("Creating staff/manager CustomerDashboard (no customer_id).")
            else:
                # invalid payload — raise (don't show QMessageBox here)
                raise TypeError(f"CustomerDashboard expected user_data (dict) or customer_id (int) or None, "
                                f"got {type(user_data)!r}: {user_data!r}")

            # Now safe to proceed to UI construction
            # Any heavy UI setup should be in init_ui() which must guard against None customer_id
            self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header with welcome message and logout
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #2c3e50; padding: 10px;")
        header_layout = QHBoxLayout(header_widget)
        
# safe welcome label — works for customers and staff (no customer_data)
        if self.user_data:
            first = self.user_data.get('first_name', '').strip()
            last = self.user_data.get('last_name', '').strip()
            if first or last:
                welcome_text = f"🎬 Welcome, {first} {last}!"
            else:
                welcome_text = "🎬 Welcome!"
        else:
            # staff/manager view when no customer provided
            welcome_text = "🎬 Welcome, staff member!"

        welcome_label = QLabel(welcome_text)

        welcome_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: white;")
        
        self.logout_btn = QPushButton("🚪 Logout")
        self.logout_btn.setFixedSize(100, 35)
        self.logout_btn.clicked.connect(self.logout_signal.emit)
        
        header_layout.addWidget(welcome_label)
        header_layout.addStretch()
        header_layout.addWidget(self.logout_btn)
        
        layout.addWidget(header_widget)
        
        # Create tab widget for different customer features
        self.tabs = QTabWidget()
        
        # Movie Booking Tab
        self.movies_tab = MoviesTab(self.db, self.current_customer_id)
        self.tabs.addTab(self.movies_tab, "🎥 Book Movies")
        
        # My Bookings Tab  
        self.bookings_tab = MyBookingsTab(self.db, self.current_customer_id)
        self.tabs.addTab(self.bookings_tab, "📋 My Bookings")
        
        # Profile Tab
        self.profile_tab = ProfileTab(self.db, self.current_customer_id, self.user_data)
        self.tabs.addTab(self.profile_tab, "👤 My Profile")
        
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
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #2980b9;
                color: white;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)

class MoviesTab(QWidget):
    def __init__(self, db, customer_id):
        super().__init__()
        self.db = db
        self.customer_id = customer_id
        self.selected_screening = None
        self.init_ui()
        self.load_movies()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🎬 Now Showing - Book Your Tickets")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Movies grid scroll area
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.movies_layout = QGridLayout(scroll_widget)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        layout.addWidget(scroll_area)
        self.setLayout(layout)
    
    def load_movies(self):
        movies = self.db.get_movies()
        
        # Clear existing movies
        for i in reversed(range(self.movies_layout.count())): 
            self.movies_layout.itemAt(i).widget().setParent(None)
        
        if not movies:
            no_movies_label = QLabel("No movies available at the moment.")
            no_movies_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.movies_layout.addWidget(no_movies_label, 0, 0)
            return
        
        row, col = 0, 0
        max_cols = 3
        
        for movie in movies:
            movie_card = self.create_movie_card(movie)
            self.movies_layout.addWidget(movie_card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def create_movie_card(self, movie):
        card = ClickableFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                padding: 15px;
                margin: 10px;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        card.setFixedSize(300, 400)
        card.clicked.connect(lambda: self.show_movie_details(movie))
        
        layout = QVBoxLayout(card)
        
        # Movie title
        title = QLabel(movie['title'])
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        title.setWordWrap(True)
        layout.addWidget(title)
        
        # Movie details
        details = QLabel(f"🎭 {movie['genre']} | ⏱ {movie['duration_minutes']} min | ⭐ {movie['rating']}")
        details.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(details)
        
        # Synopsis (truncated)
        synopsis = QLabel(movie['synopsis'][:150] + "..." if len(movie['synopsis']) > 150 else movie['synopsis'])
        synopsis.setWordWrap(True)
        synopsis.setStyleSheet("color: #555; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(synopsis)
        
        # Director and cast
        director = QLabel(f"🎬 Director: {movie['director']}")
        director.setStyleSheet("color: #555; font-size: 11px; margin-bottom: 5px;")
        layout.addWidget(director)
        
        # Click hint
        hint = QLabel("👆 Click to view available showtimes & details")
        hint.setStyleSheet("color: #3498db; font-size: 10px; font-style: italic; margin-top: 10px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        
        layout.addStretch()
        return card
    
    def show_movie_details(self, movie):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{movie['title']} - Details & Showtimes")
        dialog.setModal(True)
        dialog.setFixedSize(600, 700)
        
        layout = QVBoxLayout(dialog)
        
        # --- Movie Information Section ---
        info_scroll = QScrollArea()
        info_scroll.setWidgetResizable(True)
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        # Title
        title = QLabel(f"🎬 {movie['title']}")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        title.setWordWrap(True)
        info_layout.addWidget(title)
        
        # Quick Stats
        stats = QLabel(f"<b>Genre:</b> {movie['genre']} &nbsp;|&nbsp; <b>Duration:</b> {movie['duration_minutes']} min &nbsp;|&nbsp; <b>Rating:</b> {movie['rating']}")
        stats.setStyleSheet("color: #000000; font-size: 13px; margin-bottom: 15px;")
        info_layout.addWidget(stats)
        
        # Full Synopsis
        synopsis_label = QLabel("<b>📝 Synopsis:</b>")
        synopsis_label.setStyleSheet("color: #2c3e50; font-size: 14px; margin-top: 10px;")
        info_layout.addWidget(synopsis_label)
        
        synopsis_text = QLabel(movie['synopsis'])
        synopsis_text.setWordWrap(True)
        synopsis_text.setStyleSheet("color: #000000; font-size: 13px; line-height: 1.4; margin-bottom: 15px;")
        info_layout.addWidget(synopsis_text)
        
        # Director
        director_label = QLabel(f"<b>🎬 Director:</b> {movie['director']}")
        director_label.setStyleSheet("color: #000000; font-size: 13px; margin-bottom: 5px;")
        info_layout.addWidget(director_label)
        
        info_layout.addStretch()
        info_scroll.setWidget(info_widget)
        # Give info section about 40% of height
        layout.addWidget(info_scroll, stretch=4)
        
        
        # --- Showtimes Section ---
        screenings = self.db.get_screenings(movie['movie_id'])
        
        showtimes_label = QLabel("📅 Available Showtimes")
        showtimes_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        showtimes_label.setStyleSheet("color: #2c3e50; margin-top: 15px;")
        layout.addWidget(showtimes_label)
        
        showtimes_list = QListWidget()
        showtimes_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        if screenings:
            for screening in screenings:
                available_seats = screening['available_seats']
                item_text = f"🏛 {screening['hall_name']}  |  🕒 {screening['start_time']}  |  💺 {available_seats} seats left  |  💰 ${screening['ticket_price']}"
                showtimes_list.addItem(item_text)
        else:
            showtimes_list.addItem("No showtimes available currently.")
            showtimes_list.setEnabled(False)
            
        layout.addWidget(showtimes_list, stretch=3)
        
        # Buttons
        button_layout = QHBoxLayout()
        book_btn = QPushButton("🎟 Book Selected Showtime")
        book_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; 
                color: white; 
                padding: 10px; 
                font-weight: bold; 
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #219150; }
        """)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d; 
                color: white; 
                padding: 10px; 
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #95a5a6; }
        """)
        
        if screenings:
            book_btn.clicked.connect(lambda: self.book_screening(screenings[showtimes_list.currentRow()], dialog))
        else:
            book_btn.setEnabled(False)
            book_btn.setStyleSheet("background-color: #bdc3c7; color: white; padding: 10px; border-radius: 5px;")
            
        close_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(book_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def book_screening(self, screening, dialog):
        dialog.accept()
        
        # Get available seats
        available_seats = self.db.get_available_seats(screening['screening_id'])
        if not available_seats:
            QMessageBox.warning(self, "Sold Out", "No available seats for this screening!")
            return
        
        # Show shared seat selection dialog
        from seat_selection_dialog import SeatSelectionDialog
        dialog = SeatSelectionDialog(available_seats, parent=self)
        
        selected_seat_ids = []
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_seat_ids = dialog.get_selected_seats()
            
        if selected_seat_ids:
            # Calculate total amount
            seat_ids = list(selected_seat_ids)
            total_amount = float(screening['ticket_price']) * len(seat_ids)
            # Show Payment Screen
            from payment_dialog import PaymentDialog
            payment_dialog = PaymentDialog(total_amount, parent=self)
            if payment_dialog.exec() != QDialog.DialogCode.Accepted:
                return # User cancelled payment

            method = payment_dialog.get_payment_method()

            # Create booking with pending status
            booking_id = self.db.create_booking(
                self.customer_id, 
                screening['screening_id'], 
                seat_ids, 
                total_amount,
                status='pending',
                payment_method=method,
                payment_status='pending'
            )
            
            if booking_id:
                QMessageBox.information(self, "Payment Recorded", 
                                      f"🎉 Payment recorded!\n"
                                      f"Booking ID: {booking_id}\n"
                                      f"Status: Pending Approval\n"
                                      f"Please wait for an employee to confirm your booking.")
                self.load_movies()  # Refresh available movies
            else:
                QMessageBox.critical(self, "Booking Failed", "Failed to create booking. Please try again.")

class MyBookingsTab(QWidget):
    def __init__(self, db, customer_id):
        super().__init__()
        self.db = db
        self.customer_id = customer_id
        self.init_ui()
        self.load_bookings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📋 My Bookings & Refunds")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Bookings table
        self.bookings_table = QTableWidget()
        self.bookings_table.setAlternatingRowColors(True)
        layout.addWidget(self.bookings_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_bookings)
        
        self.refund_btn = QPushButton("💸 Request Refund")
        self.refund_btn.clicked.connect(self.request_refund)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.refund_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_bookings(self):
        bookings = self.db.get_user_bookings(self.customer_id)
        
        if bookings:
            self.bookings_table.setRowCount(len(bookings))
            self.bookings_table.setColumnCount(7)
            self.bookings_table.setHorizontalHeaderLabels([
                "Booking ID", "Movie", "Date & Time", "Hall", "Seats", "Amount", "Status"
            ])
            
            for row_idx, booking in enumerate(bookings):
                self.bookings_table.setItem(row_idx, 0, QTableWidgetItem(str(booking['booking_id'])))
                self.bookings_table.setItem(row_idx, 1, QTableWidgetItem(booking['title']))
                self.bookings_table.setItem(row_idx, 2, QTableWidgetItem(str(booking['start_time'])))
                self.bookings_table.setItem(row_idx, 3, QTableWidgetItem(booking['hall_name']))
                self.bookings_table.setItem(row_idx, 4, QTableWidgetItem(booking['seats']))
                self.bookings_table.setItem(row_idx, 5, QTableWidgetItem(f"${booking['total_amount']:.2f}"))
                
                status_item = QTableWidgetItem(booking['status'])
                if booking['status'] == 'confirmed':
                    status_item.setForeground(Qt.GlobalColor.green)
                elif booking['status'] == 'refunded':
                    status_item.setForeground(Qt.GlobalColor.blue)
                elif booking['status'] == 'pending_refund':
                    status_item.setForeground(Qt.GlobalColor.darkYellow)  # Orange/Dark Yellow for pending
                    status_item.setText("Pending Refund")
                elif booking['status'] == 'cancelled':
                    status_item.setForeground(Qt.GlobalColor.red)
                self.bookings_table.setItem(row_idx, 6, status_item)
            
            # Resize columns to content
            header = self.bookings_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        else:
            self.bookings_table.setRowCount(0)
            self.bookings_table.setColumnCount(1)
            self.bookings_table.setHorizontalHeaderLabels(["No bookings found"])
    
    def request_refund(self):
        selected_items = self.bookings_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select a booking to request refund!")
            return
        
        booking_id = self.bookings_table.item(selected_items[0].row(), 0).text()
        booking_status = self.bookings_table.item(selected_items[0].row(), 6).text()
        
        if booking_status != 'confirmed':
            QMessageBox.warning(self, "Invalid Selection", "Only confirmed bookings can be refunded!")
            return
        
        reason, ok = QInputDialog.getText(self, "Refund Request", 
                                        "Please explain why you need a refund:")
        
        if ok and reason:
            if self.db.request_refund(int(booking_id), reason):
                QMessageBox.information(self, "Refund Request Submitted", 
                                      "Your refund request has been submitted and will be reviewed by our staff.")
                self.load_bookings()
            else:
                QMessageBox.critical(self, "Request Failed", "Failed to submit refund request. Please try again.")

class ProfileTab(QWidget):
    def __init__(self, db, customer_id, user_data):
        super().__init__()
        self.db = db
        self.customer_id = customer_id
        self.user_data = user_data
        self.init_ui()
        self.load_profile()
    
    def init_ui(self):
        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form_layout = QVBoxLayout(container)
        
        # Title
        title = QLabel("👤 My Profile")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(title)
        
        # --- Profile Info (Edit Details) ---
        info_group = QFrame()
        info_group.setFrameStyle(QFrame.Shape.StyledPanel)
        info_group.setStyleSheet("background-color: white; border-radius: 5px; border: 1px solid #ddd; padding: 10px;")
        info_layout = QFormLayout(info_group)
        
        self.username_label = QLabel()
        self.username_label.setStyleSheet("font-weight: bold; color: #555;")
        
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        
        info_layout.addRow("Username:", self.username_label)
        info_layout.addRow("First Name:", self.first_name_input)
        info_layout.addRow("Last Name:", self.last_name_input)
        info_layout.addRow("Email:", self.email_input)
        info_layout.addRow("Phone:", self.phone_input)
        
        self.update_btn = QPushButton("Confirm")
        self.update_btn.setStyleSheet("color: black;")
        self.update_btn.clicked.connect(self.update_profile)
        info_layout.addRow(self.update_btn)
        
        form_layout.addWidget(info_group)
        
        # --- Change Password Section ---
        pass_group = QFrame()
        pass_group.setFrameStyle(QFrame.Shape.StyledPanel)
        pass_group.setStyleSheet("background-color: white; border-radius: 5px; border: 1px solid #ddd; padding: 10px; margin-top: 20px;")
        pass_layout = QFormLayout(pass_group)
        
        pass_title = QLabel("🔒 Change Password")
        pass_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        pass_layout.addRow(pass_title)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("New Password")
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Confirm New Password")
        
        pass_layout.addRow("New Password:", self.new_password_input)
        pass_layout.addRow("Confirm:", self.confirm_password_input)
        
        self.change_pass_btn = QPushButton("Confirm Password")
        self.change_pass_btn.setStyleSheet("color: black;")
        self.change_pass_btn.clicked.connect(self.change_password)
        pass_layout.addRow(self.change_pass_btn)
        
        form_layout.addWidget(pass_group)
        form_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        self.setLayout(layout)
    
    def load_profile(self):
        profile = self.db.get_customer_profile(self.customer_id)
        
        if not profile:
            # Fallback to user_data if db fetch fails (though it shouldn't)
            print(f"load_profile: full profile fetch failed for id: {self.customer_id}")
            if self.user_data:
                self.username_label.setText(self.user_data.get('username', ''))
                self.first_name_input.setText(self.user_data.get('first_name', ''))
                self.last_name_input.setText(self.user_data.get('last_name', ''))
                self.email_input.setText(self.user_data.get('email', ''))
                self.phone_input.setText(self.user_data.get('phone', ''))
            return

        self.username_label.setText(str(profile.get('username', '')))
        self.first_name_input.setText(str(profile.get('first_name', '')))
        self.last_name_input.setText(str(profile.get('last_name', '')))
        self.email_input.setText(str(profile.get('email', '')))
        self.phone_input.setText(str(profile.get('phone_number', '') or ''))
    
    def update_profile(self):
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        
        if not first_name or not last_name or not email:
            QMessageBox.warning(self, "Validation Error", "First name, last name, and email are required!")
            return
        
        if self.db.update_customer(self.customer_id, first_name, last_name, email, phone):
            QMessageBox.information(self, "Success", "Profile updated successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to update profile!")

    def change_password(self):
        new_pass = self.new_password_input.text()
        confirm_pass = self.confirm_password_input.text()
        
        if not new_pass:
            QMessageBox.warning(self, "Error", "Please enter a new password")
            return
            
        if len(new_pass) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters")
            return
            
        if new_pass != confirm_pass:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
            
        if self.db.update_password(self.customer_id, new_pass):
            QMessageBox.information(self, "Success", "Password changed successfully!")
            self.new_password_input.clear()
            self.confirm_password_input.clear()
        else:
            QMessageBox.critical(self, "Error", "Failed to change password!")