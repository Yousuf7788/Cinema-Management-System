# screening_tab.py - INTEGRATED VERSION
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox, QHeaderView, QDoubleSpinBox, QFormLayout
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor
from ui_screening_tab import Ui_ScreeningTab
from base_tab import BaseTab

class ScreeningTab(BaseTab, Ui_ScreeningTab):
    def __init__(self, db, is_manager=False):
        """
        Initialize Screening Tab
        
        Args:
            db: Database connection
            is_manager: Whether user has manager permissions
        """
        super().__init__(db, "Screening")
        self.setupUi(self)
        self.is_manager = is_manager
        self.connect_signals()
        self.setup_form()
        self.add_price_input()
        self.apply_permissions()
        self.load_dynamic_data()
        self.load_data()
    
    def connect_signals(self):
        """Connect UI signals to methods"""
        self.addScreeningBtn.clicked.connect(self.add_record)
        self.updateScreeningBtn.clicked.connect(self.update_record)
        self.deleteScreeningBtn.clicked.connect(self.delete_record)
        self.refreshScreeningBtn.clicked.connect(self.refresh_data)
        self.screeningTable.itemSelectionChanged.connect(self.on_row_selected)
        
        # Auto-calculate end time when movie or start time changes
        self.movieCombo.currentIndexChanged.connect(self.calculate_end_time)
        self.movieCombo.currentIndexChanged.connect(self.calculate_end_time)
        self.startTimeInput.dateTimeChanged.connect(self.calculate_end_time)
        self.hallCombo.currentIndexChanged.connect(self.set_auto_price)
    
    def setup_form(self):
        """Initialize form values"""
        self.startTimeInput.setDateTime(QDateTime.currentDateTime())
        self.endTimeInput.setDateTime(QDateTime.currentDateTime().addSecs(7200))  # +2 hours
    
    def add_price_input(self):
        """Add ticket price input to the form if it doesn't exist"""
        # Check if price input already exists in UI
        if not hasattr(self, 'priceInput'):
            # Find a layout to add the price input
            for i in range(self.layout().count()):
                widget = self.layout().itemAt(i).widget()
                if widget and hasattr(widget, 'layout'):
                    layout = widget.layout()
                    if isinstance(layout, QFormLayout):
                        self.priceInput = QDoubleSpinBox()
                        self.priceInput.setRange(0, 100)
                        self.priceInput.setPrefix("$ ")
                        self.priceInput.setValue(12.50)
                        self.priceInput.setDecimals(2)
                        layout.insertRow(3, "Ticket Price:", self.priceInput)
                        break
    
    def apply_permissions(self):
        """Apply role-based permissions"""
        if not self.is_manager:
            # Regular employees cannot manage screenings
            self.addScreeningBtn.hide()
            self.updateScreeningBtn.hide()
            self.deleteScreeningBtn.hide()
            self.addScreeningBtn.setEnabled(False)
            self.updateScreeningBtn.setEnabled(False)
            self.deleteScreeningBtn.setEnabled(False)
            
            # Disable form inputs for non-managers
            self.movieCombo.setEnabled(False)
            self.hallCombo.setEnabled(False)
            self.startTimeInput.setEnabled(False)
            self.endTimeInput.setEnabled(False)
            if hasattr(self, 'priceInput'):
                self.priceInput.setEnabled(False)
    
    def load_dynamic_data(self):
        """Load combo box data using new database methods"""
        # Load movies
        movies = self.db.get_movies()
        self.movieCombo.clear()
        if movies:
            for movie in movies:
                self.movieCombo.addItem(movie['title'], movie['movie_id'])
        
        # Load halls
        halls = self.db.get_halls()
        self.hallCombo.clear()
        if halls:
            for hall in halls:
                display_text = f"{hall['hall_name']} ({hall['capacity']} seats)"
                self.hallCombo.addItem(display_text, hall['hall_id'])
    
    def calculate_end_time(self):
        """Calculate end time based on movie duration and start time"""
        movie_id = self.movieCombo.currentData()
        start_time = self.startTimeInput.dateTime()
        
        if movie_id:
            # Get movie duration from database
            movies = self.db.get_movies()
            for movie in movies:
                if movie['movie_id'] == movie_id:
                    duration_minutes = movie['duration_minutes']
                    # Add movie duration + 30 minutes for cleaning/prep
                    end_time = start_time.addSecs((duration_minutes + 30) * 60)
                    self.endTimeInput.setDateTime(end_time)
                    
                    # Auto-set price based on hall type
                    self.set_auto_price()
                    break
    
    def set_auto_price(self):
        """Set automatic price based on hall type/name"""
        hall_id = self.hallCombo.currentData()
        if hall_id:
            halls = self.db.get_halls()
            for hall in halls:
                if hall['hall_id'] == hall_id:
                    name = hall.get('hall_name', '').upper()
                    price = 12.00  # Default standard price
                    
                    if 'IMAX' in name:
                        price = 20.00
                    elif 'VIP' in name:
                        price = 25.00
                    elif 'PREMIUM' in name:
                        price = 18.00
                    elif '3D' in name:
                        price = 15.00
                    elif 'STANDARD' in name:
                        price = 12.00
                    
                    if hasattr(self, 'priceInput'):
                        self.priceInput.setValue(price)
                    break
    
    def refresh_data(self):
        """Refresh all data"""
        self.load_dynamic_data()
        self.load_data()
        self.show_success_message("Refresh", "Screening data refreshed successfully!")
    
    def load_data(self):
        """Load screening data into table using new database methods"""
        screenings = self.db.get_screenings()
        
        if screenings:
            self.screeningTable.setRowCount(len(screenings))
            self.screeningTable.setColumnCount(7)
            self.screeningTable.setHorizontalHeaderLabels([
                "Screening ID", "Movie", "Hall", "Start Time", "End Time", "Price", "Available Seats"
            ])
            
            for row_idx, screening in enumerate(screenings):
                self.screeningTable.setItem(row_idx, 0, QTableWidgetItem(str(screening['screening_id'])))
                self.screeningTable.setItem(row_idx, 1, QTableWidgetItem(screening['title']))
                self.screeningTable.setItem(row_idx, 2, QTableWidgetItem(screening['hall_name']))
                self.screeningTable.setItem(row_idx, 3, QTableWidgetItem(str(screening['start_time'])))
                self.screeningTable.setItem(row_idx, 4, QTableWidgetItem(str(screening['end_time'])))
                
                # Format price
                price_item = QTableWidgetItem(f"${screening['ticket_price']:.2f}")
                self.screeningTable.setItem(row_idx, 5, price_item)
                
                # Show available seats with color coding
                available_seats = screening.get('available_seats', 0)
                seats_item = QTableWidgetItem(str(available_seats))
                
                if available_seats == 0:
                    seats_item.setForeground(QColor('red'))
                elif available_seats < 10:
                    seats_item.setForeground(QColor('orange'))
                else:
                    seats_item.setForeground(QColor('green'))
                    
                self.screeningTable.setItem(row_idx, 6, seats_item)
            
            # Resize columns to content
            header = self.screeningTable.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        else:
            self.screeningTable.setRowCount(0)
            self.screeningTable.setColumnCount(1)
            self.screeningTable.setHorizontalHeaderLabels(["No screenings found"])
    
    def add_record(self):
        """Add new screening with conflict detection"""
        if not self.is_manager:
            self.show_error_message("Access Denied", "Only managers can add screenings!")
            return
        
        movie_id = self.movieCombo.currentData()
        hall_id = self.hallCombo.currentData()
        start_time = self.startTimeInput.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_time = self.endTimeInput.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        ticket_price = self.priceInput.value() if hasattr(self, 'priceInput') else 12.50
        
        if not movie_id or not hall_id:
            self.show_error_message("Error", "Movie and Hall selection are required!")
            return
        
        # Validate time range
        start_dt = self.startTimeInput.dateTime()
        end_dt = self.endTimeInput.dateTime()
        if end_dt <= start_dt:
            self.show_error_message("Error", "End time must be after start time!")
            return
        
        # Check for scheduling conflicts
        if self.has_scheduling_conflict(hall_id, start_time, end_time):
            self.show_error_message(
                "Scheduling Conflict", 
                "This hall is already booked during the selected time period!"
            )
            return
        
        # Add screening using new database method
        success = self.db.add_screening(movie_id, hall_id, start_time, end_time, ticket_price)
        
        if success:
            self.show_success_message("Success", "Screening added successfully!")
            self.clear_form()
            self.load_data()
        else:
            self.show_error_message("Error", "Failed to add screening. Please check for conflicts.")
    
    def has_scheduling_conflict(self, hall_id, new_start, new_end):
        """Check if there's a scheduling conflict for the hall"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT screening_id FROM Screening 
                WHERE hall_id = ? AND (
                    (start_time < ? AND end_time > ?) OR  -- Overlaps start
                    (start_time < ? AND end_time > ?) OR  -- Overlaps end
                    (start_time >= ? AND end_time <= ?)   -- Completely within
                )
            """, hall_id, new_end, new_start, new_start, new_end, new_start, new_end)
            
            conflict = cursor.fetchone()
            return conflict is not None
            
        except Exception as e:
            self.logger.error(f"Error checking scheduling conflict: {e}")
            return False  # Allow creation if we can't check conflicts
    
    def update_record(self):
        """Update existing screening"""
        if not self.is_manager:
            self.show_error_message("Access Denied", "Only managers can update screenings!")
            return
        
        selected_items = self.screeningTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select a screening to update!")
            return
        
        screening_id = int(self.screeningTable.item(selected_items[0].row(), 0).text())
        movie_id = self.movieCombo.currentData()
        hall_id = self.hallCombo.currentData()
        start_time = self.startTimeInput.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_time = self.endTimeInput.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        ticket_price = self.priceInput.value() if hasattr(self, 'priceInput') else 12.50
        
        # Validate time range
        start_dt = self.startTimeInput.dateTime()
        end_dt = self.endTimeInput.dateTime()
        if end_dt <= start_dt:
            self.show_error_message("Error", "End time must be after start time!")
            return
        
        # Check for scheduling conflicts (excluding current screening)
        if self.has_scheduling_conflict_excluding_current(hall_id, start_time, end_time, screening_id):
            self.show_error_message(
                "Scheduling Conflict", 
                "This hall is already booked during the selected time period!"
            )
            return
        
        query = """
        UPDATE Screening 
        SET movie_id = ?, hall_id = ?, start_time = ?, end_time = ?, ticket_price = ?
        WHERE screening_id = ?
        """
        
        success, result, error = self.execute_query(query, 
            (movie_id, hall_id, start_time, end_time, ticket_price, screening_id))
        
        if success:
            self.show_success_message("Success", "Screening updated successfully!")
            self.load_data()
        else:
            self.show_error_message("Error", f"Failed to update screening: {error}")
    
    def has_scheduling_conflict_excluding_current(self, hall_id, new_start, new_end, exclude_screening_id):
        """Check scheduling conflict excluding the current screening being updated"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT screening_id FROM Screening 
                WHERE hall_id = ? AND screening_id != ? AND (
                    (start_time < ? AND end_time > ?) OR
                    (start_time < ? AND end_time > ?) OR
                    (start_time >= ? AND end_time <= ?)
                )
            """, hall_id, exclude_screening_id, new_end, new_start, new_start, new_end, new_start, new_end)
            
            conflict = cursor.fetchone()
            return conflict is not None
            
        except Exception as e:
            self.logger.error(f"Error checking scheduling conflict: {e}")
            return False
    
    def delete_record(self):
        """Delete screening (with safety checks)"""
        if not self.is_manager:
            self.show_error_message("Access Denied", "Only managers can delete screenings!")
            return
        
        selected_items = self.screeningTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select a screening to delete!")
            return
        
        screening_id = int(self.screeningTable.item(selected_items[0].row(), 0).text())
        movie_title = self.screeningTable.item(selected_items[0].row(), 1).text()
        hall_name = self.screeningTable.item(selected_items[0].row(), 2).text()
        
        # Check if there are existing bookings for this screening
        if self.has_existing_bookings(screening_id):
            self.show_error_message(
                "Cannot Delete", 
                f"Cannot delete screening with existing bookings! Cancel the bookings first."
            )
            return
        
        if self.confirm_action(
            "Confirm Delete", 
            f"Are you sure you want to delete this screening?\n\nMovie: {movie_title}\nHall: {hall_name}"
        ):
            query = "DELETE FROM Screening WHERE screening_id = ?"
            success, result, error = self.execute_query(query, (screening_id,))
            
            if success:
                self.show_success_message("Success", "Screening deleted successfully!")
                self.clear_form()
                self.load_data()
            else:
                self.show_error_message("Error", f"Failed to delete screening: {error}")
    
    def has_existing_bookings(self, screening_id):
        """Check if there are existing bookings for this screening"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM Booking 
                WHERE screening_id = ? AND status = 'confirmed'
            """, screening_id)
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            self.logger.error(f"Error checking existing bookings: {e}")
            return True  # Err on the side of caution
    
    def clear_form(self):
        """Clear form fields"""
        self.startTimeInput.setDateTime(QDateTime.currentDateTime())
        self.endTimeInput.setDateTime(QDateTime.currentDateTime().addSecs(7200))
        if hasattr(self, 'priceInput'):
            self.priceInput.setValue(12.50)
        self.movieCombo.setCurrentIndex(0)
        self.hallCombo.setCurrentIndex(0)
    
    def on_row_selected(self):
        """Populate form when row is selected"""
        selected_items = self.screeningTable.selectedItems()
        if selected_items and self.is_manager:  # Only populate if user can edit
            row = selected_items[0].row()
            
            # Set movie
            movie_title = self.screeningTable.item(row, 1).text()
            index = self.movieCombo.findText(movie_title)
            if index >= 0:
                self.movieCombo.setCurrentIndex(index)
            
            # Set hall
            hall_name = self.screeningTable.item(row, 2).text().split(' (')[0]  # Remove seat count
            index = self.hallCombo.findText(hall_name, Qt.MatchFlag.MatchContains)
            if index >= 0:
                self.hallCombo.setCurrentIndex(index)
            
            # Set price if available
            if hasattr(self, 'priceInput') and self.screeningTable.columnCount() > 5:
                price_text = self.screeningTable.item(row, 5).text()
                if price_text.startswith('$'):
                    price = float(price_text[1:])
                    self.priceInput.setValue(price)