# customer_dashboard.py - MODIFIED VERSION
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QLabel, 
                             QPushButton, QDialog, QListWidget, QDialogButtonBox,
                             QInputDialog, QHeaderView, QScrollArea, QFrame, QGridLayout, QLineEdit)
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime
from PyQt6.QtGui import QFont, QPixmap
import os

class CustomerDashboard(QWidget):
    logout_signal = pyqtSignal()
    
    def __init__(self, db, user_data):
        super().__init__()
        self.db = db
        self.user_data = user_data
        self.current_customer_id = user_data['customer_id']
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header with welcome message and logout
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #2c3e50; padding: 10px;")
        header_layout = QHBoxLayout(header_widget)
        
        welcome_label = QLabel(f"🎬 Welcome, {self.user_data['first_name']} {self.user_data['last_name']}!")
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
        card = QFrame()
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
        
        # Showtimes button
        showtimes_btn = QPushButton("📅 Check Showtimes & Book")
        showtimes_btn.clicked.connect(lambda checked, m=movie: self.show_showtimes(m))
        layout.addWidget(showtimes_btn)
        
        layout.addStretch()
        return card
    
    def show_showtimes(self, movie):
        screenings = self.db.get_screenings(movie['movie_id'])
        
        if not screenings:
            QMessageBox.information(self, "No Showtimes", f"No showtimes available for {movie['title']}")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Showtimes for {movie['title']}")
        dialog.setModal(True)
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel(f"🎬 {movie['title']} - Available Showtimes")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Showtimes list
        showtimes_list = QListWidget()
        for screening in screenings:
            available_seats = screening['available_seats']
            item_text = f"🏛 {screening['hall_name']} | 🕒 {screening['start_time']} | 💺 {available_seats} seats | 💰 ${screening['ticket_price']}"
            showtimes_list.addItem(item_text)
        
        layout.addWidget(showtimes_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        book_btn = QPushButton("🎟 Book Selected Showtime")
        cancel_btn = QPushButton("Cancel")
        
        book_btn.clicked.connect(lambda: self.book_screening(screenings[showtimes_list.currentRow()], dialog))
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(book_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def book_screening(self, screening, dialog):
        dialog.accept()
        
        # Get available seats
        available_seats = self.db.get_available_seats(screening['screening_id'])
        if not available_seats:
            QMessageBox.warning(self, "Sold Out", "No available seats for this screening!")
            return
        
        # Simple seat selection (in real app, show a visual seat map)
        seat_list = [f"Row {seat['row_letter']} - Seat {seat['seat_number']} ({seat['seat_type']})" 
                    for seat in available_seats[:5]]  # Show first 5 seats for simplicity
        
        seat, ok = QInputDialog.getItem(self, "Select Seat", "Choose a seat:", seat_list, 0, False)
        
        if ok and seat:
            # Find the seat ID
            seat_info = seat.split(" - ")
            row = seat_info[0].replace("Row ", "")
            import re
            m = re.search(r'\d+', seat_info[1] or "")
            if not m:
                self.show_error_message("Error", f"Could not parse seat number from '{seat_info[1]}'")
                return
            number = int(m.group())

            
            seat_id = None
            for available_seat in available_seats:
                if available_seat['row_letter'] == row and available_seat['seat_number'] == number:
                    seat_id = available_seat['seat_id']
                    break
            
            if seat_id:
                # Create booking
                booking_id = self.db.create_booking(self.customer_id, screening['screening_id'], [seat_id], screening['ticket_price'])
                
                if booking_id:
                    QMessageBox.information(self, "Booking Successful!", 
                                          f"🎉 Booking confirmed!\n"
                                          f"Booking ID: {booking_id}\n"
                                          f"Movie: {screening['title']}\n"
                                          f"Seat: {seat}\n"
                                          f"Total: ${screening['ticket_price']}")
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
        
        # Title
        title = QLabel("👤 My Profile")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Profile form
        form_layout = QVBoxLayout()
        
        # Username (read-only)
        self.username_label = QLabel()
        form_layout.addWidget(QLabel("Username:"))
        form_layout.addWidget(self.username_label)
        
        # First Name
        self.first_name_input = QLineEdit()
        form_layout.addWidget(QLabel("First Name *:"))
        form_layout.addWidget(self.first_name_input)
        
        # Last Name
        self.last_name_input = QLineEdit()
        form_layout.addWidget(QLabel("Last Name *:"))
        form_layout.addWidget(self.last_name_input)
        
        # Email
        self.email_input = QLineEdit()
        form_layout.addWidget(QLabel("Email *:"))
        form_layout.addWidget(self.email_input)
        
        # Phone
        self.phone_input = QLineEdit()
        form_layout.addWidget(QLabel("Phone:"))
        form_layout.addWidget(self.phone_input)
        
        # Update button
        self.update_btn = QPushButton("💾 Update Profile")
        self.update_btn.clicked.connect(self.update_profile)
        form_layout.addWidget(self.update_btn)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        self.setLayout(layout)
    
    def load_profile(self):
        import json

        # Try to get customer data (the DB method name suggests a single record may be returned)
        try:
            result = self.db.get_customer_name(self.customer_id)
        except Exception as e:
            print("load_profile: error calling get_customer_name:", e)
            result = None

        # Normalise possible return shapes into a single dict 'customer' or None
        customer = None

        # 1) If DB returned None -> not found
        if result is None:
            customer = None

        # 2) If result already a dict (best case)
        elif isinstance(result, dict):
            customer = result

        # 3) If result is a list/tuple of rows
        elif isinstance(result, (list, tuple)):
            # If it's a list of rows and first element is dict, pick the first matching one
            if len(result) == 0:
                customer = None
            else:
                first = result[0]
                if isinstance(first, dict):
                    # If it's a list of dicts, try to find the one with matching id
                    try:
                        target_id = int(self.customer_id)
                    except Exception:
                        target_id = self.customer_id
                    # try by common keys
                    customer = next(
                        (c for c in result if (
                            ('customer_id' in c and str(c['customer_id']) == str(target_id))
                            or ('id' in c and str(c['id']) == str(target_id))
                        )), 
                        None
                    )
                    # fallback to first element if not found
                    if not customer:
                        customer = first
                else:
                    # It's a list/tuple of tuples (e.g. cursor.fetchall()). Assume a common column order:
                    # (customer_id, first_name, last_name, email, phone_number)
                    # If your DB returns different order, change the indices below.
                    row = first
                    # If the fetch returned multiple rows, try to find matching id
                    try:
                        target_id = str(int(self.customer_id))
                    except Exception:
                        target_id = str(self.customer_id)

                    found = None
                    for r in result:
                        if not isinstance(r, (list, tuple)):
                            continue
                        if len(r) > 0 and str(r[0]) == target_id:
                            found = r
                            break
                    if not found:
                        found = row  # fallback to first row

                    # Map tuple -> dict (adjust indices if your SELECT order differs)
                    customer = {
                        'customer_id': found[0] if len(found) > 0 else None,
                        'first_name': found[1] if len(found) > 1 else '',
                        'last_name': found[2] if len(found) > 2 else '',
                        'email': found[3] if len(found) > 3 else '',
                        'phone_number': found[4] if len(found) > 4 else ''
                    }

        # 4) If result is a JSON string
        elif isinstance(result, str):
            try:
                parsed = json.loads(result)
                # parsed could be dict or list; reuse logic by recursion-like assignment
                if isinstance(parsed, dict):
                    customer = parsed
                elif isinstance(parsed, (list, tuple)) and parsed:
                    first = parsed[0]
                    if isinstance(first, dict):
                        customer = first
                    elif isinstance(first, (list, tuple)):
                        found = parsed[0]
                        customer = {
                            'customer_id': found[0] if len(found) > 0 else None,
                            'first_name': found[1] if len(found) > 1 else '',
                            'last_name': found[2] if len(found) > 2 else '',
                            'email': found[3] if len(found) > 3 else '',
                            'phone_number': found[4] if len(found) > 4 else ''
                        }
            except Exception:
                # Not JSON — maybe it's a single username string; treat as missing structured data
                customer = None

        else:
            # Unknown type: convert to string and try to match (unlikely)
            try:
                s = str(result)
                customer = None
            except Exception:
                customer = None

        # --- Use the normalized 'customer' dict or handle not-found ---
        if not customer:
            # No customer found — clear fields or set defaults
            print(f"load_profile: no customer found for id: {self.customer_id}")
            self.username_label.setText(self.user_data.get('username', '') if isinstance(self.user_data, dict) else "")
            self.first_name_input.setText("")
            self.last_name_input.setText("")
            self.email_input.setText("")
            self.phone_input.setText("")
            return

        # Fill UI fields safely using .get to avoid KeyError
        self.username_label.setText(self.user_data.get('username', '') if isinstance(self.user_data, dict) else "")
        self.first_name_input.setText(str(customer.get('first_name', '')))
        self.last_name_input.setText(str(customer.get('last_name', '')))
        self.email_input.setText(str(customer.get('email', '')))
        self.phone_input.setText(str(customer.get('phone_number', '') or ""))

    
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