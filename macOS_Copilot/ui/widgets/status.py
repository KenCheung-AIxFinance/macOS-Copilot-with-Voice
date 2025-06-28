from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

class StatusLabel(QLabel):
    """状态显示标签"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #2c3e50;
                padding: 12px 20px;
                background-color: #ecf0f1;
                border-radius: 8px;
                border: 2px solid #bdc3c7;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(50) 