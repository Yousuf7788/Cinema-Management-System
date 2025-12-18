from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox, QHeaderView, QPushButton
from PyQt6.QtCore import QDateTime
from PyQt6.QtGui import QColor
from ui_payment_tab import Ui_PaymentTab
from base_tab import BaseTab

class PaymentTab(BaseTab, Ui_PaymentTab):
    def __init__(self, db, user_data=None):
        """
        Initialize Payment Tab
        
        Args:
            db: Database connection
            user_data: User information for role-based access
        """
        super().__init__(db, "Payment")
        self.setupUi(self)
        self.user_data = user_data
        self.user_type = user_data.get('user_type') if user_data else None
        self.connect_signals()
        self.setup_form()
        self.load_dynamic_data()
        self.load_dynamic_data()
        self.load_data()
        
        if hasattr(self, 'horizontalLayout'):
            self.approve_btn = QPushButton("✅ Approve Payment")
            self.approve_btn.clicked.connect(self.approve_payment)
            self.horizontalLayout.insertWidget(3, self.approve_btn)
        else:
             self.approve_btn = QPushButton("✅ Approve Payment")
             self.approve_btn.clicked.connect(self.approve_payment)
             self.layout().addWidget(self.approve_btn)
    
    def approve_payment(self):
        """Approve a pending payment"""
        selected_items = self.paymentTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select a payment to approve!")
            return
            
        row = selected_items[0].row()
        payment_id = int(self.paymentTable.item(row, 0).text())
        current_status = self.paymentTable.item(row, 5).text().lower()
        
        if current_status == 'completed':
            self.show_error_message("Info", "Payment is already completed.")
            return

        if self.confirm_action("Approve Payment", "Approve this payment and confirm the booking?"):
             print(f"[DEBUG] Approving payment {payment_id}...")
             b_query = "SELECT booking_id FROM Payment WHERE payment_id = ?"
             s, r, e = self.execute_query(b_query, (payment_id,), fetch=True)
             if s and r:
                 booking_id = r[0][0]
                 print(f"[DEBUG] Found booking_id: {booking_id}")
                 
                 p_query = "UPDATE Payment SET payment_status = 'completed' WHERE payment_id = ?"
                 self.execute_query(p_query, (payment_id,))
                 
                 b_update = "UPDATE Booking SET status = 'confirmed' WHERE booking_id = ?"
                 self.execute_query(b_update, (booking_id,))
                 print(f"[DEBUG] Updated booking {booking_id} status to 'confirmed'")
                 
                 self.show_success_message("Success", "Payment approved and booking confirmed!")
                 self.load_data()
             else:
                 print(f"[ERROR] Could not find booking for payment {payment_id}")
                 self.show_error_message("Error", "Could not find associated booking.")
    
    def connect_signals(self):
        """Connect UI signals to methods"""
        self.addPaymentBtn.clicked.connect(self.add_record)
        self.updatePaymentBtn.clicked.connect(self.update_record)
        self.deletePaymentBtn.clicked.connect(self.delete_record)
        self.refreshPaymentBtn.clicked.connect(self.refresh_data)
        self.paymentTable.itemSelectionChanged.connect(self.on_row_selected)
        
        self.bookingCombo.currentIndexChanged.connect(self.auto_fill_amount)
    
    def setup_form(self):
        """Initialize form values"""
        self.amountInput.setRange(0, 1000)
        self.amountInput.setPrefix("$ ")
        
        if self.paymentMethodCombo.count() == 0:
            self.paymentMethodCombo.addItems(["Credit Card", "Debit Card", "Cash", "Mobile Payment", "Online"])
        
        if self.paymentStatusCombo.count() == 0:
            self.paymentStatusCombo.addItems(["pending", "completed", "failed", "refunded"])
        
        self.paymentMethodCombo.setCurrentText("Credit Card")
        self.paymentStatusCombo.setCurrentText("completed")
    
    def load_dynamic_data(self):
        """Load combo box data"""
        query = """
        SELECT b.booking_id, 
               c.first_name + ' ' + c.last_name + ' - ' + m.title + ' ($' + CAST(b.total_amount AS VARCHAR) + ')'
        FROM Booking b
        JOIN Customer c ON b.customer_id = c.customer_id
        JOIN Screening s ON b.screening_id = s.screening_id
        JOIN Movie m ON s.movie_id = m.movie_id
        WHERE b.booking_id NOT IN (SELECT booking_id FROM Payment WHERE payment_status != 'refunded')
        OR b.status = 'confirmed'
        """
        
        success, results, error = self.execute_query(query, fetch=True)
        
        self.bookingCombo.clear()
        if success and results:
            for booking_id, booking_info in results:
                self.bookingCombo.addItem(booking_info, booking_id)
        else:
            self.show_error_message("Database Error", f"Failed to load bookings: {error}")
    
    def auto_fill_amount(self):
        """Auto-fill amount based on selected booking"""
        booking_id = self.bookingCombo.currentData()
        if booking_id:
            query = "SELECT total_amount FROM Booking WHERE booking_id = ?"
            success, results, error = self.execute_query(query, (booking_id,), fetch=True)
            
            if success and results:
                amount = float(results[0][0])
                self.amountInput.setValue(amount)
    
    def refresh_data(self):
        """Refresh all data"""
        self.load_dynamic_data()
        self.load_data()
        self.show_success_message("Refresh", "Payment data refreshed successfully!")
    
    def load_data(self):
        """Load payment data into table"""
        if self.user_type == 'customer':
            query = """
            SELECT p.payment_id, c.first_name + ' ' + c.last_name, m.title,
                   p.amount, p.payment_method, p.payment_status, p.payment_date
            FROM Payment p
            JOIN Booking b ON p.booking_id = b.booking_id
            JOIN Customer c ON b.customer_id = c.customer_id
            JOIN Screening s ON b.screening_id = s.screening_id
            JOIN Movie m ON s.movie_id = m.movie_id
            WHERE c.customer_id = ?
            ORDER BY p.payment_date DESC
            """
            success, results, error = self.execute_query(query, (self.user_data['customer_id'],), fetch=True)
        else:
            query = """
            SELECT p.payment_id, c.first_name + ' ' + c.last_name, m.title,
                   p.amount, p.payment_method, p.payment_status, p.payment_date
            FROM Payment p
            JOIN Booking b ON p.booking_id = b.booking_id
            JOIN Customer c ON b.customer_id = c.customer_id
            JOIN Screening s ON b.screening_id = s.screening_id
            JOIN Movie m ON s.movie_id = m.movie_id
            ORDER BY p.payment_date DESC
            """
            success, results, error = self.execute_query(query, fetch=True)
        
        if success and results:
            self.paymentTable.setRowCount(len(results))
            self.paymentTable.setColumnCount(7)
            self.paymentTable.setHorizontalHeaderLabels([
                "Payment ID", "Customer", "Movie", "Amount", 
                "Payment Method", "Status", "Payment Date"
            ])
            
            for row_idx, row_data in enumerate(results):
                for col_idx, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    
                    if col_idx == 5:
                        self.color_status_item(item, str(col_data).lower())
                    
                    if col_idx == 3 and col_data:
                        try:
                            item.setText(self.format_currency(float(col_data)))
                        except (ValueError, TypeError):
                            pass
                    
                    self.paymentTable.setItem(row_idx, col_idx, item)
            
            header = self.paymentTable.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        else:
            self.paymentTable.setRowCount(0)
            self.paymentTable.setColumnCount(1)
            self.paymentTable.setHorizontalHeaderLabels(["No payments found"])
            
            if error:
                self.show_error_message("Database Error", f"Failed to load payments: {error}")
    
    def add_record(self):
        """Add new payment record"""
        booking_id = self.bookingCombo.currentData()
        amount = self.amountInput.value()
        payment_method = self.paymentMethodCombo.currentText()
        payment_status = self.paymentStatusCombo.currentText()
        
        if not booking_id:
            self.show_error_message("Error", "Booking selection is required!")
            return
        
        if amount <= 0:
            self.show_error_message("Error", "Payment amount must be greater than 0!")
            return
        
        check_query = "SELECT payment_id FROM Payment WHERE booking_id = ? AND payment_status != 'refunded'"
        success, existing_payment, error = self.execute_query(check_query, (booking_id,), fetch=True)
        
        if success and existing_payment:
            self.show_error_message("Error", "This booking already has an active payment!")
            return
        
        query = """
        INSERT INTO Payment (booking_id, amount, payment_method, payment_status, payment_date)
        VALUES (?, ?, ?, ?, GETDATE())
        """
        
        success, result, error = self.execute_query(query, (booking_id, amount, payment_method, payment_status))
        if success:
            self.show_success_message("Success", "Payment recorded successfully!")
            
            if payment_status == 'completed':
                update_booking_query = "UPDATE Booking SET status = 'pending' WHERE booking_id = ?"
                self.execute_query(update_booking_query, (booking_id,))
            
            self.clear_form()
            self.load_data()
        else:
            self.show_error_message("Error", f"Failed to record payment: {error}")
    
    def update_record(self):
        """Update existing payment record"""
        selected_items = self.paymentTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select a payment to update!")
            return
        
        payment_id = int(self.paymentTable.item(selected_items[0].row(), 0).text())
        booking_id = self.bookingCombo.currentData()
        amount = self.amountInput.value()
        payment_method = self.paymentMethodCombo.currentText()
        payment_status = self.paymentStatusCombo.currentText()
        
        if not booking_id:
            self.show_error_message("Error", "Booking selection is required!")
            return
        
        old_status_query = "SELECT payment_status FROM Payment WHERE payment_id = ?"
        success, old_status_result, error = self.execute_query(old_status_query, (payment_id,), fetch=True)
        old_status = old_status_result[0][0] if success and old_status_result else None
        
        query = """
        UPDATE Payment 
        SET booking_id = ?, amount = ?, payment_method = ?, payment_status = ?
        WHERE payment_id = ?
        """
        
        success, result, error = self.execute_query(query, (booking_id, amount, payment_method, payment_status, payment_id))
        if success:
            if old_status != payment_status:
                if payment_status == 'completed':
                    update_query = "UPDATE Booking SET status = 'confirmed' WHERE booking_id = ?"
                    self.execute_query(update_query, (booking_id,))
                elif old_status == 'completed' and payment_status != 'completed':
                    update_query = "UPDATE Booking SET status = 'cancelled' WHERE booking_id = ?"
                    self.execute_query(update_query, (booking_id,))
            
            self.show_success_message("Success", "Payment updated successfully!")
            self.load_data()
        else:
            self.show_error_message("Error", f"Failed to update payment: {error}")
    
    def delete_record(self):
        """Delete payment record (with restrictions)"""
        selected_items = self.paymentTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select a payment to delete!")
            return
        
        payment_id = int(self.paymentTable.item(selected_items[0].row(), 0).text())
        payment_status = self.paymentTable.item(selected_items[0].row(), 5).text()
        
        if payment_status.lower() == 'completed':
            self.show_error_message(
                "Cannot Delete", 
                "Completed payments cannot be deleted. Please process a refund instead."
            )
            return
        
        if self.confirm_action("Confirm Delete", "Are you sure you want to delete this payment record?"):
            query = "DELETE FROM Payment WHERE payment_id = ?"
            success, result, error = self.execute_query(query, (payment_id,))
            
            if success:
                self.show_success_message("Success", "Payment record deleted successfully!")
                self.clear_form()
                self.load_data()
            else:
                self.show_error_message("Error", f"Failed to delete payment: {error}")
    
    def process_refund(self):
        """Process refund for a payment (simplified version)"""
        selected_items = self.paymentTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select a payment to refund!")
            return
        
        payment_id = int(self.paymentTable.item(selected_items[0].row(), 0).text())
        payment_amount = float(self.paymentTable.item(selected_items[0].row(), 3).text().replace('$', ''))
        
        if self.paymentTable.item(selected_items[0].row(), 5).text().lower() != 'completed':
            self.show_error_message("Error", "Only completed payments can be refunded!")
            return
        
        refund_query = """
        INSERT INTO Refund (payment_id, refund_amount, refund_reason, status, refund_date)
        VALUES (?, ?, ?, 'pending', GETDATE())
        """
        
        from PyQt6.QtWidgets import QInputDialog
        reason, ok = QInputDialog.getText(self, "Refund Reason", "Enter reason for refund:")
        
        if ok and reason:
            success, result, error = self.execute_query(refund_query, (payment_id, payment_amount, reason))
            if success:
                update_query = "UPDATE Payment SET payment_status = 'refunded' WHERE payment_id = ?"
                self.execute_query(update_query, (payment_id,))
                
                booking_update_query = """
                UPDATE Booking SET status = 'refunded' 
                WHERE booking_id = (SELECT booking_id FROM Payment WHERE payment_id = ?)
                """
                self.execute_query(booking_update_query, (payment_id,))
                
                self.show_success_message("Refund Processed", "Refund request submitted successfully!")
                self.load_data()
            else:
                self.show_error_message("Error", f"Failed to process refund: {error}")
    
    def clear_form(self):
        """Clear form fields"""
        self.amountInput.setValue(0)
        self.paymentMethodCombo.setCurrentIndex(0)
        self.paymentStatusCombo.setCurrentIndex(0)
        self.bookingCombo.setCurrentIndex(0)
    
    def on_row_selected(self):
        """Populate form when row is selected"""
        selected_items = self.paymentTable.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            
            amount_text = self.paymentTable.item(row, 3).text()
            if amount_text.startswith('$'):
                amount = float(amount_text[1:])
                self.amountInput.setValue(amount)
            
            payment_method = self.paymentTable.item(row, 4).text()
            index = self.paymentMethodCombo.findText(payment_method)
            if index >= 0:
                self.paymentMethodCombo.setCurrentIndex(index)
            
            payment_status = self.paymentTable.item(row, 5).text()
            index = self.paymentStatusCombo.findText(payment_status)
            if index >= 0:
                self.paymentStatusCombo.setCurrentIndex(index)
            
            customer_info = self.paymentTable.item(row, 1).text()
            movie_info = self.paymentTable.item(row, 2).text()
            search_text = f"{customer_info} - {movie_info}"
            
            index = self.bookingCombo.findText(search_text)
            if index >= 0:
                self.bookingCombo.setCurrentIndex(index)