# booking_tab.py - INTEGRATED VERSION
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox, QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QLabel
from PyQt6.QtCore import QDateTime
from PyQt6.QtCore import Qt
from ui_booking_tab import Ui_BookingTab
from base_tab import BaseTab

class BookingTab(BaseTab, Ui_BookingTab):
    def __init__(self, db, user_data=None):
        """
        Initialize Booking Tab
        
        Args:
            db: Database connection
            user_data: User information (for customer-specific views)
        """
        super().__init__(db, "Booking")
        self.setupUi(self)
        self.user_data = user_data
        self.current_customer_id = user_data.get('customer_id') if user_data else None
        self.connect_signals()
        self.setup_form()
        self.load_dynamic_data()
        self.load_data()
    
    def connect_signals(self):
        """Connect UI signals to methods"""
        self.addBookingBtn.clicked.connect(self.add_record)
        self.updateBookingBtn.clicked.connect(self.update_record)
        self.deleteBookingBtn.clicked.connect(self.delete_record)
        self.refreshBookingBtn.clicked.connect(self.refresh_data)
        self.bookingTable.itemSelectionChanged.connect(self.on_row_selected)
        
        # Auto-calculate price when screening changes
        self.screeningCombo.currentIndexChanged.connect(self.calculate_price)
    
    def setup_form(self):
        """Initialize form values"""
        self.bookingDateInput.setDateTime(QDateTime.currentDateTime())
        self.totalAmountInput.setRange(0, 1000)
        self.totalAmountInput.setPrefix("$ ")
        
        # Hide customer selection if viewing as customer
        if self.current_customer_id:
            self.customerCombo.hide()
            customer_label = self.findChild(QLabel, "customerLabel")  # You might need to add this label
            if customer_label:
                customer_label.setText(f"Customer: {self.user_data['first_name']} {self.user_data['last_name']}")
    
    def load_dynamic_data(self):
        """Load combo box data"""
        # Load screenings using new database method
        screenings = self.db.get_screenings()
        self.screeningCombo.clear()
        if screenings:
            for screening in screenings:
                # defensive: provider keys may be missing
                title = screening.get('title', '')
                hall = screening.get('hall_name', '')
                start = screening.get('start_time', '')
                price = screening.get('ticket_price', '')
                display_text = f"{title} - {hall} - {start} - ${price}"
                self.screeningCombo.addItem(display_text, screening.get('screening_id'))

        # Clear customer combo first
        self.customerCombo.clear()

        # If current_customer_id is None => we are an employee/manager: load all customers
        if self.current_customer_id is None:
            try:
                cursor = self.db.connection.cursor()
                cursor.execute("SELECT customer_id, first_name, last_name, email FROM Customer")
                rows = cursor.fetchall()
                if rows:
                    for r in rows:
                        # r may be a pyodbc.Row or tuple
                        try:
                            cust_id = getattr(r, 'customer_id', None) or r[0]
                            first = getattr(r, 'first_name', None) or (r[1] if len(r) > 1 else '')
                            last = getattr(r, 'last_name', None) or (r[2] if len(r) > 2 else '')
                            email = getattr(r, 'email', None) or (r[3] if len(r) > 3 else '')
                        except Exception:
                            # fallback mapping
                            cust_id = r[0] if len(r) > 0 else None
                            first = r[1] if len(r) > 1 else ''
                            last = r[2] if len(r) > 2 else ''
                            email = r[3] if len(r) > 3 else ''

                        display_text = f"{(first or '').strip()} {(last or '').strip()} ({(email or '').strip()})".strip()
                        self.customerCombo.addItem(display_text, cust_id)
            except Exception as e:
                print("DEBUG: load_dynamic_data - failed to load customers:", e)
        else:
            # For customers (a logged-in customer), pre-select their ID and show name
            # Use user_data safely (may be None for some flows)
            if isinstance(self.user_data, dict):
                first = self.user_data.get('first_name', '') or ''
                last = self.user_data.get('last_name', '') or ''
                label = f"{first} {last}".strip() or f"Customer {self.current_customer_id}"
            else:
                label = f"Customer {self.current_customer_id}"
            self.customerCombo.addItem(label, self.current_customer_id)
            self.customerCombo.setCurrentIndex(0)

    
    def calculate_price(self):
        """Calculate price based on selected screening"""
        screening_id = self.screeningCombo.currentData()
        if screening_id:
            screenings = self.db.get_screenings()
            for screening in screenings:
                if screening['screening_id'] == screening_id:
                    self.totalAmountInput.setValue(float(screening['ticket_price']))
                    break
    
    def refresh_data(self):
        """Refresh all data"""
        self.load_dynamic_data()
        self.load_data()
        self.show_success_message("Refresh", "Data refreshed successfully!")
    
    def load_data(self):
        """Load booking data into table (safe, tolerant to varying DB column names)."""
        # Choose source depending on whether a specific customer is active
        if self.current_customer_id:
            bookings = self.db.get_user_bookings(self.current_customer_id)
        else:
            bookings = self.db.get_all_bookings()

        # Clear table if no bookings
        if not bookings:
            self.bookingTable.setRowCount(0)
            self.bookingTable.setColumnCount(1)
            self.bookingTable.setHorizontalHeaderLabels(["No bookings found"])
            return

        # Prepare table
        self.bookingTable.setRowCount(len(bookings))
        self.bookingTable.setColumnCount(7)
        self.bookingTable.setHorizontalHeaderLabels([
            "Booking ID", "Customer", "Movie", "Screening Time",
            "Booking Date", "Total Amount", "Status"
        ])

        for row_idx, booking in enumerate(bookings):
            # safe helpers that accept multiple possible key names
            def pick(*keys, default=""):
                for k in keys:
                    if k in booking and booking[k] is not None:
                        return booking[k]
                return default

            booking_id = pick('booking_id', 'id', default='')
            # Customer name:
            if self.current_customer_id:
                # Prefer user_data if available, else try booking fields
                if isinstance(getattr(self, 'user_data', None), dict):
                    first = self.user_data.get('first_name') or ''
                    last = self.user_data.get('last_name') or ''
                else:
                    first = pick('first_name', 'customer_first_name', 'fname', default='')
                    last  = pick('last_name',  'customer_last_name',  'lname', default='')
                customer_name = f"{first} {last}".strip() or f"Customer {self.current_customer_id}"
            else:
                first = pick('first_name', 'customer_first_name', default='')
                last  = pick('last_name',  'customer_last_name', default='')
                customer_name = f"{first} {last}".strip() or "Unknown Customer"

            # Movie title (support 'movie_title' or 'title')
            movie_title = pick('movie_title', 'title', default='Unknown Movie')

            # Times / dates: convert to string safely
            start_time = pick('start_time', 'screening_time', default='')
            booking_date = pick('booking_date', 'date', default='')

            # Amount and status (with defaults)
            total_amount = pick('total_amount', 'total', 'amount', default=0.0)
            try:
                total_str = f"${float(total_amount):.2f}"
            except Exception:
                total_str = f"${0.00:.2f}"

            status = pick('status', default='confirmed')

            # Insert into table (use safe str() conversions)
            self.bookingTable.setItem(row_idx, 0, QTableWidgetItem(str(booking_id)))
            self.bookingTable.setItem(row_idx, 1, QTableWidgetItem(str(customer_name)))
            self.bookingTable.setItem(row_idx, 2, QTableWidgetItem(str(movie_title)))
            self.bookingTable.setItem(row_idx, 3, QTableWidgetItem(str(start_time)))
            self.bookingTable.setItem(row_idx, 4, QTableWidgetItem(str(booking_date)))
            self.bookingTable.setItem(row_idx, 5, QTableWidgetItem(total_str))

            # Status with coloring helper
            status_item = QTableWidgetItem(str(status))
            try:
                self.color_status_item(status_item, status)
            except Exception as e:
                # If color helper fails, still set the item
                print("DEBUG: color_status_item failed:", e)
            self.bookingTable.setItem(row_idx, 6, status_item)

        # Optional: auto-resize columns for readability
        try:
            self.bookingTable.resizeColumnsToContents()
        except Exception:
            pass

    
    def add_record(self):
        """Add new booking with seat selection"""
        customer_id = self.current_customer_id or self.customerCombo.currentData()
        screening_id = self.screeningCombo.currentData()
        booking_date = self.bookingDateInput.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        total_amount = self.totalAmountInput.value()
        
        if not customer_id or not screening_id:
            self.show_error_message("Error", "Customer and Screening are required!")
            return
        
        # Get available seats for the screening
        available_seats = self.db.get_available_seats(screening_id)
        if not available_seats:
            self.show_error_message("Sold Out", "No available seats for this screening!")
            return
        
        # Show seat selection dialog
        seat_ids = self.select_seats_dialog(available_seats)
        if not seat_ids:
            return  # User cancelled
        
        # Create booking
        booking_id = self.db.create_booking(customer_id, screening_id, seat_ids, total_amount)
        
        if booking_id:
            self.show_success_message("Success", f"Booking created successfully! Booking ID: {booking_id}")
            self.clear_form()
            self.load_data()
        else:
            self.show_error_message("Error", "Failed to create booking!")
    
    def select_seats_dialog(self, available_seats):
        """Show seat selection dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Seats")
        dialog.setModal(True)
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Instructions
        instructions = QLabel("Select one or more seats (Ctrl+Click for multiple):")
        layout.addWidget(instructions)
        
        # Seat list
        seat_list = QListWidget()
        seat_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        for seat in available_seats:
            seat_list.addItem(f"Row {seat['row_letter']} - Seat {seat['seat_number']} ({seat['seat_type']})")
        
        layout.addWidget(seat_list)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_items = seat_list.selectedItems()
            selected_seat_ids = []
            
            for item in selected_items:
                seat_text = item.text()
                # Extract seat info and find corresponding seat ID
                for seat in available_seats:
                    if f"Row {seat['row_letter']} - Seat {seat['seat_number']}" in seat_text:
                        selected_seat_ids.append(seat['seat_id'])
                        break
            
            return selected_seat_ids
        
        return None
    
    def update_record(self):
        """Update existing booking"""
        selected_items = self.bookingTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select a booking to update!")
            return
        
        booking_id = self.bookingTable.item(selected_items[0].row(), 0).text()
        customer_id = self.current_customer_id or self.customerCombo.currentData()
        screening_id = self.screeningCombo.currentData()
        booking_date = self.bookingDateInput.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        total_amount = self.totalAmountInput.value()
        
        if not customer_id or not screening_id:
            self.show_error_message("Error", "Customer and Screening are required!")
            return
        
        query = """
        UPDATE Booking 
        SET customer_id = ?, screening_id = ?, booking_date = ?, total_amount = ?
        WHERE booking_id = ?
        """
        
        success, result, error = self.execute_query(query, (customer_id, screening_id, booking_date, total_amount, booking_id))
        if success:
            self.show_success_message("Success", "Booking updated successfully!")
            self.load_data()
        else:
            self.show_error_message("Error", f"Failed to update booking: {error}")
    
    def delete_record(self):
        """Delete booking or request refund"""
        selected_items = self.bookingTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select a booking!")
            return
        
        booking_id = self.bookingTable.item(selected_items[0].row(), 0).text()
        booking_status = self.bookingTable.item(selected_items[0].row(), 6).text() if self.bookingTable.columnCount() > 6 else "confirmed"
        
        if self.current_customer_id:
            # Customers request refunds instead of deleting
            if booking_status == 'confirmed':
                self.request_refund(int(booking_id))
            else:
                self.show_warning_message("Cannot Refund", "Only confirmed bookings can be refunded!")
        else:
            # Employees/managers can delete bookings
            if self.confirm_action("Confirm Delete", "Are you sure you want to delete this booking?"):
                query = "DELETE FROM Booking WHERE booking_id = ?"
                success, result, error = self.execute_query(query, (booking_id,))
                if success:
                    self.show_success_message("Success", "Booking deleted successfully!")
                    self.clear_form()
                    self.load_data()
                else:
                    self.show_error_message("Error", f"Failed to delete booking: {error}")
    
    def request_refund(self, booking_id):
        """Request refund for a booking"""
        from PyQt6.QtWidgets import QInputDialog
        
        reason, ok = QInputDialog.getText(self, "Refund Request", "Please enter reason for refund:")
        
        if ok and reason:
            if self.db.request_refund(booking_id, reason):
                self.show_success_message("Refund Request", "Refund request submitted successfully!")
                self.load_data()
            else:
                self.show_error_message("Error", "Failed to submit refund request!")
    
    def clear_form(self):
        """Clear form fields"""
        self.bookingDateInput.setDateTime(QDateTime.currentDateTime())
        self.totalAmountInput.setValue(0)
        self.screeningCombo.setCurrentIndex(0)
        
        if not self.current_customer_id:
            self.customerCombo.setCurrentIndex(0)
    
    def on_row_selected(self):
        """Populate form when row is selected"""
        selected_items = self.bookingTable.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            
            # Set screening
            movie_title = self.bookingTable.item(row, 2).text()
            screening_time = self.bookingTable.item(row, 3).text()
            screening_text = f"{movie_title} - {screening_time}"
            
            index = self.screeningCombo.findText(screening_text, Qt.MatchFlag.MatchContains)
            if index >= 0:
                self.screeningCombo.setCurrentIndex(index)
            
            # Set customer (if not customer view)
            if not self.current_customer_id and self.bookingTable.columnCount() > 1:
                customer_name = self.bookingTable.item(row, 1).text()
                index = self.customerCombo.findText(customer_name, Qt.MatchFlag.MatchContains)
                if index >= 0:
                    self.customerCombo.setCurrentIndex(index)
            
            # Set amount
            if self.bookingTable.columnCount() > 5:
                amount_text = self.bookingTable.item(row, 5).text()
                if amount_text.startswith('$'):
                    amount = float(amount_text[1:])
                    self.totalAmountInput.setValue(amount)