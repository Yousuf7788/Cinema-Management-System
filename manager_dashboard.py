from employee_dashboard import EmployeeDashboard
from PyQt6.QtWidgets import QMessageBox, QMenu
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import datetime

class ManagerDashboard(EmployeeDashboard):
    
    def __init__(self, db, user_data):
        super().__init__(db, user_data)

        if not isinstance(user_data, dict):
            print("ERROR: ManagerDashboard expected user_data dict but got:", repr(user_data), type(user_data))
            return

        self.db = db
        self.user_data = user_data
        self.current_user = user_data

        self.current_customer_id = user_data.get('customer_id')

        first = user_data.get('first_name') or ''
        last = user_data.get('last_name') or ''
        title_name = (first + ' ' + last).strip()
        if title_name:
            self.setWindowTitle(f"🎯 Cinema Management System - Manager Portal ({title_name})")
        else:
            self.setWindowTitle("🎯 Cinema Management System - Manager Portal")

        if hasattr(self, 'add_manager_features') and callable(self.add_manager_features):
            self.add_manager_features()
    
    def add_manager_features(self):
        """Add additional manager-only features"""
        self.add_reports_tab()
        
        self.enhance_customer_tab()
        
        self.update_header()
    
    def add_reports_tab(self):
        """Add reports and analytics tab for managers"""
        from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QTableWidget, QTableWidgetItem,
                                   QGroupBox, QFormLayout)
        
        reports_tab = QWidget()
        layout = QVBoxLayout(reports_tab)
        
        title = QLabel("📊 Manager Reports & Analytics")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        stats_layout = QHBoxLayout()
        
        revenue_group = QGroupBox("💰 Revenue Overview")
        revenue_layout = QFormLayout()
        
        self.total_revenue_label = QLabel("Calculating...")
        self.daily_revenue_label = QLabel("Calculating...")
        self.avg_booking_label = QLabel("Calculating...")
        
        revenue_layout.addRow("Total Revenue:", self.total_revenue_label)
        revenue_layout.addRow("Today's Revenue:", self.daily_revenue_label)
        revenue_layout.addRow("Avg Booking Value:", self.avg_booking_label)
        
        revenue_group.setLayout(revenue_layout)
        stats_layout.addWidget(revenue_group)
        
        booking_group = QGroupBox("📈 Booking Statistics")
        booking_layout = QFormLayout()
        
        self.total_bookings_label = QLabel("Calculating...")
        self.confirmed_bookings_label = QLabel("Calculating...")
        self.refund_rate_label = QLabel("Calculating...")
        
        booking_layout.addRow("Total Bookings:", self.total_bookings_label)
        booking_layout.addRow("Confirmed Bookings:", self.confirmed_bookings_label)
        booking_layout.addRow("Refund Rate:", self.refund_rate_label)
        
        booking_group.setLayout(booking_layout)
        stats_layout.addWidget(booking_group)
        
        movie_group = QGroupBox("🎬 Movie Performance")
        movie_layout = QFormLayout()
        
        self.total_movies_label = QLabel("Calculating...")
        self.most_popular_label = QLabel("Calculating...")
        self.avg_rating_label = QLabel("Calculating...")
        
        movie_layout.addRow("Total Movies:", self.total_movies_label)
        movie_layout.addRow("Most Popular:", self.most_popular_label)
        movie_layout.addRow("Avg Rating:", self.avg_rating_label)
        
        movie_group.setLayout(movie_layout)
        stats_layout.addWidget(movie_group)
        
        layout.addLayout(stats_layout)
        
        action_layout = QHBoxLayout()
        
        self.generate_report_btn = QPushButton("📄 Generate Detailed Report")
        self.generate_report_btn.clicked.connect(self.generate_detailed_report)
        
        self.refresh_stats_btn = QPushButton("🔄 Refresh Statistics")
        self.refresh_stats_btn.clicked.connect(self.load_statistics)
        
        action_layout.addWidget(self.generate_report_btn)
        action_layout.addWidget(self.refresh_stats_btn)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        self.tabs.addTab(reports_tab, "📊 Reports")
        
        self.load_statistics()
    
    def load_statistics(self):
        """Load and display management statistics"""
        try:
            total_revenue = self.calculate_total_revenue()
            daily_revenue = self.calculate_daily_revenue()
            avg_booking = self.calculate_average_booking_value()
            
            self.total_revenue_label.setText(f"${total_revenue:,.2f}")
            self.daily_revenue_label.setText(f"${daily_revenue:,.2f}")
            self.avg_booking_label.setText(f"${avg_booking:,.2f}")
            
            booking_stats = self.calculate_booking_statistics()
            self.total_bookings_label.setText(str(booking_stats['total']))
            self.confirmed_bookings_label.setText(str(booking_stats['confirmed']))
            self.refund_rate_label.setText(f"{booking_stats['refund_rate']:.1f}%")
            
            movie_stats = self.calculate_movie_statistics()
            self.total_movies_label.setText(str(movie_stats['total_movies']))
            self.most_popular_label.setText(movie_stats['most_popular'])
            self.avg_rating_label.setText(movie_stats['avg_rating'])
            
        except Exception as e:
            print(f"Error loading statistics: {e}")
    
    def calculate_total_revenue(self):
        """Calculate total revenue from all confirmed bookings"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM Booking 
                WHERE status = 'confirmed'
            """)
            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else 0.0
        except Exception as e:
            print(f"Error calculating total revenue: {e}")
            return 0.0
    
    def calculate_daily_revenue(self):
        """Calculate revenue from today's bookings"""
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM Booking 
                WHERE status = 'confirmed' 
                AND CAST(booking_date AS DATE) = ?
            """, today)
            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else 0.0
        except Exception as e:
            print(f"Error calculating daily revenue: {e}")
            return 0.0
    
    def calculate_average_booking_value(self):
        """Calculate average booking value"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT COALESCE(AVG(total_amount), 0) 
                FROM Booking 
                WHERE status = 'confirmed'
            """)
            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else 0.0
        except Exception as e:
            print(f"Error calculating average booking value: {e}")
            return 0.0
    
    def calculate_booking_statistics(self):
        """Calculate various booking statistics"""
        try:
            cursor = self.db.connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM Booking")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM Booking WHERE status = 'confirmed'")
            confirmed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM Booking WHERE status = 'refunded'")
            refunded = cursor.fetchone()[0]
            refund_rate = (refunded / total * 100) if total > 0 else 0
            
            return {
                'total': total,
                'confirmed': confirmed,
                'refund_rate': refund_rate
            }
        except Exception as e:
            print(f"Error calculating booking statistics: {e}")
            return {'total': 0, 'confirmed': 0, 'refund_rate': 0}
    
    def calculate_movie_statistics(self):
        """Calculate movie-related statistics (robust against non-numeric varchar values)."""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute("SELECT COUNT(*) FROM Movie")
            total_movies = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT TOP 1 m.title, COUNT(b.booking_id) as booking_count
                FROM Movie m
                LEFT JOIN Screening s ON m.movie_id = s.movie_id
                LEFT JOIN Booking b ON s.screening_id = b.screening_id AND b.status = 'confirmed'
                GROUP BY m.movie_id, m.title
                ORDER BY booking_count DESC
            """)
            popular_result = cursor.fetchone()
            most_popular = popular_result[0] if popular_result else "N/A"

            cursor.execute("""
                SELECT AVG(TRY_CONVERT(float, NULLIF(LTRIM(RTRIM(rating)), ''))) AS avg_rating
                FROM Movie
                WHERE rating IS NOT NULL
            """)
            avg_rating_result = cursor.fetchone()
            avg_value = avg_rating_result[0] if avg_rating_result else None

            avg_rating = f"{avg_value:.1f}" if isinstance(avg_value, (float, int)) else "N/A"

            return {
                'total_movies': total_movies,
                'most_popular': most_popular,
                'avg_rating': avg_rating
            }

        except Exception as e:
            print(f"Error calculating movie statistics: {e}")
            return {'total_movies': 0, 'most_popular': 'N/A', 'avg_rating': 'N/A'}

    def enhance_customer_tab(self):
        """Add manager-specific features to customer management"""
        pass
    
    def update_header(self):
        """Update header to show manager status prominently"""
        pass
    
    def generate_detailed_report(self):
        """Generate a detailed management report"""
        try:
            report_data = {
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'revenue': {
                    'total': self.calculate_total_revenue(),
                    'daily': self.calculate_daily_revenue(),
                    'average_booking': self.calculate_average_booking_value()
                },
                'bookings': self.calculate_booking_statistics(),
                'movies': self.calculate_movie_statistics(),
                'refunds': len(self.db.get_pending_refunds())
            }
            
            report_text = f"""
🎬 CINEMA MANAGEMENT SYSTEM - MANAGER REPORT
Generated: {report_data['timestamp']}
============================================

💰 REVENUE ANALYSIS
-------------------
Total Revenue: ${report_data['revenue']['total']:,.2f}
Today's Revenue: ${report_data['revenue']['daily']:,.2f}
Average Booking Value: ${report_data['revenue']['average_booking']:,.2f}

📈 BOOKING STATISTICS
---------------------
Total Bookings: {report_data['bookings']['total']}
Confirmed Bookings: {report_data['bookings']['confirmed']}
Refund Rate: {report_data['bookings']['refund_rate']:.1f}%

🎬 MOVIE PERFORMANCE
--------------------
Total Movies: {report_data['movies']['total_movies']}
Most Popular Movie: {report_data['movies']['most_popular']}
Average Rating: {report_data['movies']['avg_rating']}

⚠️  PENDING ACTIONS
-------------------
Pending Refunds: {report_data['refunds']}

============================================
Report generated by: {self.user_data['first_name']} {self.user_data['last_name']}
            """.strip()
            
            from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QPushButton, QHBoxLayout
            from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
            from PyQt6.QtGui import QTextDocument
            
            dialog = QDialog(self)
            dialog.setWindowTitle("📊 Management Report")
            dialog.setModal(True)
            dialog.setFixedSize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(report_text)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            button_layout = QHBoxLayout()
            
            print_btn = QPushButton("🖨️ Print Report")
            print_btn.clicked.connect(lambda: self.print_report(report_text))
            
            save_btn = QPushButton("💾 Save to File")
            save_btn.clicked.connect(lambda: self.save_report_to_file(report_text))
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            
            button_layout.addWidget(print_btn)
            button_layout.addWidget(save_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Report Error", f"Failed to generate report: {str(e)}")
    
    def print_report(self, report_text):
        """Print the management report"""
        try:
            printer = QPrinter()
            print_dialog = QPrintDialog(printer, self)
            
            if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
                document = QTextDocument()
                document.setPlainText(report_text)
                document.print(printer)
                QMessageBox.information(self, "Print", "Report sent to printer!")
                
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print: {str(e)}")
    
    def save_report_to_file(self, report_text):
        """Save report to text file"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Report", f"cinema_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt", 
                "Text Files (*.txt)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(report_text)
                QMessageBox.information(self, "Save Successful", f"Report saved to:\n{filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save file: {str(e)}")
    
    def show_employee_management(self):
        """Show employee management features (placeholder for future enhancement)"""
        QMessageBox.information(self, "Employee Management", 
                              "Employee management features will be implemented in the next version.")