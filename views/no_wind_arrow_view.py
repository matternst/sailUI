# views/no_wind_arrow_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
# --- ADD THIS IMPORT ---
from PySide6.QtCore import Qt

class NoWindArrowView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("Standard View (No Wind Arrow)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 30px; font-family: Oxanium;")
        layout.addWidget(label)