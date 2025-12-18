from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, 
                             QGridLayout, QPushButton, QHBoxLayout, QDialogButtonBox, QFrame)
from PyQt6.QtCore import Qt

class SeatSelectionDialog(QDialog):
    def __init__(self, all_seats, parent=None):
        super().__init__(parent)
        self.all_seats = all_seats
        self.selected_seats = set()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Select Seats")
        self.resize(800, 600)
        
        main_layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Please select your seats")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)
        
        # Legend
        self.create_legend(main_layout)
        
        # Scroll Area for Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f0f0f0; }")
        
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setSpacing(20)
        
        # Screen visuals
        screen_label = QLabel("SCREEN")
        screen_label.setStyleSheet("""
            background-color: #95a5a6; 
            color: white; 
            font-weight: bold; 
            padding: 5px;
            border-radius: 5px;
        """)
        screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        screen_label.setFixedHeight(30)
        container_layout.addWidget(screen_label)
        
        # Grid for seats
        seat_grid = QGridLayout()
        seat_grid.setSpacing(10)
        seat_grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addLayout(seat_grid)
        
        # Organize seats by row
        rows = {}
        for seat in self.all_seats:
            r = seat['row_letter']
            if r not in rows:
                rows[r] = []
            rows[r].append(seat)
            
        sorted_keys = sorted(rows.keys())
        
        for row_idx, row_curr in enumerate(sorted_keys):
            # Sort seats by number
            row_seats = sorted(rows[row_curr], key=lambda x: int(x['seat_number']) if str(x['seat_number']).isdigit() else 999)
            
            # Row Label (Left)
            lbl_left = QLabel(row_curr)
            lbl_left.setStyleSheet("font-weight: bold; color: #7f8c8d; font-size: 14px;")
            seat_grid.addWidget(lbl_left, row_idx, 0, Qt.AlignmentFlag.AlignRight)
            
            for i, seat in enumerate(row_seats):
                # Try to use seat number for column, fallback to index + 1
                try:
                    seat_num = int(seat['seat_number'])
                    col_idx = seat_num
                except:
                    col_idx = i + 1
                
                btn = QPushButton(str(seat['seat_number']))
                btn.setFixedSize(40, 40)
                
                is_booked = seat.get('status') == 'booked'
                
                # Store data
                btn.setProperty('seat_id', seat['seat_id'])
                
                if is_booked:
                    btn.setEnabled(False)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #bdc3c7;
                            color: #7f8c8d;
                            border: 1px solid #95a5a6;
                            border-radius: 6px;
                            font-weight: bold;
                        }
                    """)
                else:
                    btn.setCheckable(True)
                    btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    # Green for available
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2ecc71; 
                            color: white; 
                            border: 1px solid #27ae60;
                            border-radius: 6px;
                            font-weight: bold;
                        }
                        QPushButton:checked {
                            background-color: #3498db;
                            border: 1px solid #2980b9;
                        }
                        QPushButton:hover:!checked {
                            background-color: #27ae60;
                        }
                    """)
                    
                    def on_click(checked, s_id=seat['seat_id']):
                        if checked:
                            self.selected_seats.add(s_id)
                        else:
                            if s_id in self.selected_seats:
                                self.selected_seats.remove(s_id)
                            
                    btn.clicked.connect(on_click)
                
                seat_grid.addWidget(btn, row_idx, col_idx)
                
            # Row Label (Right)
            lbl_right = QLabel(row_curr)
            lbl_right.setStyleSheet("font-weight: bold; color: #7f8c8d; font-size: 14px;")
            seat_grid.addWidget(lbl_right, row_idx, 20, Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(container_widget)
        main_layout.addWidget(scroll)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
    def create_legend(self, layout):
        legend_frame = QFrame()
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        def add_item(color, text):
            item = QHBoxLayout()
            box = QLabel()
            box.setFixedSize(15, 15)
            box.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
            label = QLabel(text)
            item.addWidget(box)
            item.addWidget(label)
            item.addSpacing(15)
            legend_layout.addLayout(item)
            
        add_item("#2ecc71", "Available")
        add_item("#3498db", "Selected")
        add_item("#bdc3c7", "Booked")
        
        layout.addWidget(legend_frame)
        
    def get_selected_seats(self):
        return list(self.selected_seats)
