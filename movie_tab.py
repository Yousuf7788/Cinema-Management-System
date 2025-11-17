# movie_tab.py - INTEGRATED VERSION
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox, QDialog, QVBoxLayout, QFormLayout, QTextEdit, QDialogButtonBox, QPushButton
from ui_movie_tab import Ui_MovieTab
from base_tab import BaseTab

class MovieTab(BaseTab, Ui_MovieTab):
    def __init__(self, db, is_manager=False):
        """
        Initialize Movie Tab
        
        Args:
            db: Database connection
            is_manager: Whether user has manager permissions
        """
        super().__init__(db, "Movie")
        self.setupUi(self)
        self.is_manager = is_manager
        self.connect_signals()
        self.setup_form()
        self.apply_permissions()
        self.load_data()
    
    def connect_signals(self):
        """Connect UI signals to methods"""
        self.addMovieBtn.clicked.connect(self.add_record)
        self.updateMovieBtn.clicked.connect(self.update_record)
        self.deleteMovieBtn.clicked.connect(self.delete_record)
        self.refreshMovieBtn.clicked.connect(self.refresh_data)
        self.movieTable.itemSelectionChanged.connect(self.on_row_selected)
        
        # View details button
        self.viewDetailsBtn = getattr(self, 'viewDetailsBtn', None)
        if not self.viewDetailsBtn:
            # Add view details button if not in UI
            from PyQt6.QtWidgets import QPushButton, QHBoxLayout
            button_layout = QHBoxLayout()
            self.viewDetailsBtn = QPushButton("👁 View Details")
            self.viewDetailsBtn.clicked.connect(self.view_movie_details)
            button_layout.addWidget(self.viewDetailsBtn)
            button_layout.addStretch()
            
            # Find the layout to add the button
            for i in range(self.layout().count()):
                widget = self.layout().itemAt(i).widget()
                if widget and hasattr(widget, 'layout'):
                    widget.layout().addLayout(button_layout)
                    break
    
    def setup_form(self):
        """Initialize form values"""
        self.durationInput.setRange(60, 240)
        self.durationInput.setSuffix(" minutes")
        self.durationInput.setValue(120)
        
        # Populate rating combo if not already done in UI
        if self.ratingCombo.count() == 0:
            self.ratingCombo.addItems(["G", "PG", "PG-13", "R", "NC-17"])
    
    def apply_permissions(self):
        """Apply role-based permissions"""
        if not self.is_manager:
            # Regular employees can only view and update, not add/delete
            self.addMovieBtn.hide()
            self.deleteMovieBtn.hide()
            self.addMovieBtn.setEnabled(False)
            self.deleteMovieBtn.setEnabled(False)
            
            # Update button text for clarity
            self.updateMovieBtn.setText("Update Movie Details")
    
    def refresh_data(self):
        """Refresh movie data"""
        self.load_data()
        self.show_success_message("Refresh", "Movie data refreshed successfully!")
    
    def load_data(self):
        """Load movie data into table using new database methods"""
        movies = self.db.get_movies()
        
        if movies:
            self.movieTable.setRowCount(len(movies))
            self.movieTable.setColumnCount(6)
            self.movieTable.setHorizontalHeaderLabels([
                "ID", "Title", "Genre", "Duration", "Rating", "Director"
            ])
            
            for row_idx, movie in enumerate(movies):
                self.movieTable.setItem(row_idx, 0, QTableWidgetItem(str(movie['movie_id'])))
                self.movieTable.setItem(row_idx, 1, QTableWidgetItem(movie['title']))
                self.movieTable.setItem(row_idx, 2, QTableWidgetItem(movie['genre']))
                self.movieTable.setItem(row_idx, 3, QTableWidgetItem(f"{movie['duration_minutes']} min"))
                self.movieTable.setItem(row_idx, 4, QTableWidgetItem(movie['rating']))
                self.movieTable.setItem(row_idx, 5, QTableWidgetItem(movie['director']))
        else:
            self.movieTable.setRowCount(0)
            self.movieTable.setColumnCount(1)
            self.movieTable.setHorizontalHeaderLabels(["No movies found"])
    
    def add_record(self):
        """Add new movie with full details"""
        if not self.is_manager:
            self.show_error_message("Access Denied", "Only managers can add new movies!")
            return
        
        # Get basic movie info from form
        title = self.titleInput.text().strip()
        genre = self.genreInput.text().strip()
        duration = self.durationInput.value()
        rating = self.ratingCombo.currentText()
        
        if not title:
            self.show_error_message("Error", "Movie title is required!")
            return
        
        # Show detailed movie info dialog
        movie_details = self.get_movie_details_dialog()
        if not movie_details:
            return  # User cancelled
        
        # Add movie using new database method
        success = self.db.add_movie(
            title=title,
            genre=genre,
            duration=duration,
            rating=rating,
            director=movie_details['director'],
            cast=movie_details['cast'],
            synopsis=movie_details['synopsis'],
            release_date=movie_details['release_date']
        )
        
        if success:
            self.show_success_message("Success", f"Movie '{title}' added successfully!")
            self.clear_form()
            self.load_data()
        else:
            self.show_error_message("Error", "Failed to add movie. It may already exist.")
    
    def get_movie_details_dialog(self):
        """Show dialog to get detailed movie information"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Movie Details")
        dialog.setModal(True)
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        # Director input
        director_input = QTextEdit()
        director_input.setMaximumHeight(60)
        director_input.setPlaceholderText("Enter director name(s)")
        
        # Cast input
        cast_input = QTextEdit()
        cast_input.setMaximumHeight(80)
        cast_input.setPlaceholderText("Enter main cast members")
        
        # Synopsis input
        synopsis_input = QTextEdit()
        synopsis_input.setMaximumHeight(120)
        synopsis_input.setPlaceholderText("Enter movie synopsis or plot summary")
        
        # Release date (simplified - in real app use QDateEdit)
        from PyQt6.QtWidgets import QLineEdit
        release_input = QLineEdit()
        release_input.setPlaceholderText("YYYY-MM-DD")
        release_input.setText("2024-01-01")
        
        form_layout.addRow("Director:", director_input)
        form_layout.addRow("Cast:", cast_input)
        form_layout.addRow("Synopsis:", synopsis_input)
        form_layout.addRow("Release Date:", release_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return {
                'director': director_input.toPlainText().strip(),
                'cast': cast_input.toPlainText().strip(),
                'synopsis': synopsis_input.toPlainText().strip(),
                'release_date': release_input.text().strip()
            }
        
        return None
    
    def update_record(self):
        """Update existing movie"""
        selected_items = self.movieTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select a movie to update!")
            return
        
        movie_id = int(self.movieTable.item(selected_items[0].row(), 0).text())
        title = self.titleInput.text().strip()
        genre = self.genreInput.text().strip()
        duration = self.durationInput.value()
        rating = self.ratingCombo.currentText()
        
        if not title:
            self.show_error_message("Error", "Movie title is required!")
            return
        
        # Update basic movie info
        query = """
        UPDATE Movie 
        SET title = ?, genre = ?, duration_minutes = ?, rating = ?
        WHERE movie_id = ?
        """
        
        success, result, error = self.execute_query(query, (title, genre, duration, rating, movie_id))
        if success:
            self.show_success_message("Success", "Movie updated successfully!")
            self.load_data()
        else:
            self.show_error_message("Error", f"Failed to update movie: {error}")
    
    def delete_record(self):
        """Delete movie (manager only)"""
        if not self.is_manager:
            self.show_error_message("Access Denied", "Only managers can delete movies!")
            return
        
        selected_items = self.movieTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select a movie to delete!")
            return
        
        movie_id = int(self.movieTable.item(selected_items[0].row(), 0).text())
        movie_title = self.movieTable.item(selected_items[0].row(), 1).text()
        
        # Check if movie has screenings
        screenings = self.db.get_screenings(movie_id)
        if screenings:
            self.show_error_message(
                "Cannot Delete", 
                f"Cannot delete '{movie_title}' because it has {len(screenings)} scheduled screening(s)."
            )
            return
        
        if self.confirm_action("Confirm Delete", f"Are you sure you want to delete '{movie_title}'?"):
            # Delete from Movie_Details first (due to foreign key)
            details_success, _, _ = self.execute_query(
                "DELETE FROM Movie_Details WHERE movie_id = ?", 
                (movie_id,)
            )
            
            if details_success:
                # Then delete from Movie
                movie_success, _, error = self.execute_query(
                    "DELETE FROM Movie WHERE movie_id = ?", 
                    (movie_id,)
                )
                
                if movie_success:
                    self.show_success_message("Success", f"Movie '{movie_title}' deleted successfully!")
                    self.clear_form()
                    self.load_data()
                else:
                    self.show_error_message("Error", f"Failed to delete movie: {error}")
            else:
                self.show_error_message("Error", "Failed to delete movie details.")
    
    def view_movie_details(self):
        """View detailed movie information"""
        selected_items = self.movieTable.selectedItems()
        if not selected_items:
            self.show_error_message("Error", "Please select a movie to view details!")
            return
        
        movie_id = int(self.movieTable.item(selected_items[0].row(), 0).text())
        movie_title = self.movieTable.item(selected_items[0].row(), 1).text()
        
        # Get movie details from database
        movies = self.db.get_movies()
        movie = next((m for m in movies if m['movie_id'] == movie_id), None)
        
        if not movie:
            self.show_error_message("Error", "Could not load movie details!")
            return
        
        # Show details dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Movie Details - {movie_title}")
        dialog.setModal(True)
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        details_text = f"""
        <h2>{movie['title']}</h2>
        <hr>
        <p><b>Genre:</b> {movie['genre']}</p>
        <p><b>Duration:</b> {movie['duration_minutes']} minutes</p>
        <p><b>Rating:</b> {movie['rating']}</p>
        <p><b>Director:</b> {movie['director']}</p>
        <p><b>Cast:</b> {movie['cast']}</p>
        <p><b>Release Date:</b> {movie['release_date']}</p>
        <hr>
        <h3>Synopsis:</h3>
        <p>{movie['synopsis']}</p>
        """
        
        from PyQt6.QtWidgets import QTextBrowser
        details_browser = QTextBrowser()
        details_browser.setHtml(details_text)
        details_browser.setOpenExternalLinks(False)
        
        layout.addWidget(details_browser)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def clear_form(self):
        """Clear form fields"""
        self.titleInput.clear()
        self.genreInput.clear()
        self.durationInput.setValue(120)
        self.ratingCombo.setCurrentIndex(0)
    
    def on_row_selected(self):
        """Populate form when row is selected"""
        selected_items = self.movieTable.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            self.titleInput.setText(self.movieTable.item(row, 1).text())
            self.genreInput.setText(self.movieTable.item(row, 2).text())
            
            # Extract duration number from "X min" format
            duration_text = self.movieTable.item(row, 3).text()
            duration = int(duration_text.replace(' min', '')) if 'min' in duration_text else 120
            self.durationInput.setValue(duration)
            
            # Set rating
            rating = self.movieTable.item(row, 4).text()
            index = self.ratingCombo.findText(rating)
            if index >= 0:
                self.ratingCombo.setCurrentIndex(index)