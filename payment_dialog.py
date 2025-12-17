from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                             QPushButton, QHBoxLayout, QFrame, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

class PaymentDialog(QDialog):
    def __init__(self, amount, title="Payment", parent=None):
        super().__init__(parent)
        self.amount = amount
        self.setWindowTitle("Secure Payment")
        self.setFixedSize(400, 350)
        self.setStyleSheet("""
            QDialog {
                background-color: #ecf0f1;
            }
            QLabel {
                color: #2c3e50;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton {
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton#payBtn {
                background-color: #27ae60;
                color: white;
            }
            QPushButton#payBtn:hover {
                background-color: #2ecc71;
            }
            QPushButton#cancelBtn {
                background-color: #e74c3c;
                color: white;
            }
            QPushButton#cancelBtn:hover {
                background-color: #c0392b;
            }
        """)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QLabel("Complete Your Purchase")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Amount Display
        amount_frame = QFrame()
        amount_frame.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #ddd;")
        amount_layout = QVBoxLayout(amount_frame)
        
        amount_label = QLabel(f"Total Amount")
        amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        amount_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        
        price = QLabel(f"${self.amount:.2f}")
        price.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        price.setStyleSheet("color: #2c3e50;")
        
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(price)
        layout.addWidget(amount_frame)
        
        # Payment Method
        method_label = QLabel("Select Payment Method:")
        method_label.setFont(QFont("Arial", 12))
        layout.addWidget(method_label)
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Cash", "Credit Card", "Debit Card", "PayPal", "Apple Pay", "Google Pay"])
        layout.addWidget(self.method_combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.pay_btn = QPushButton(f"Pay ${self.amount:.2f}")
        self.pay_btn.setObjectName("payBtn")
        self.pay_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.pay_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_payment_method(self):
        return self.method_combo.currentText()
