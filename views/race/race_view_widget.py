# views/race/race_view_widget.py
import math
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout
from PySide6.QtCore import Qt, Slot, QSize, QPointF
from PySide6.QtGui import QFont, QPainter, QColor, QPolygonF, QBrush, QPen

# A smaller, simpler arrow widget for the race view
class SmallArrowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        # --- MODIFIED: Increased fixed size by 25% ---
        self.setFixedSize(QSize(50, 50))
        self.arrow_color = QColor("white")
        # --- MODIFIED: Increased polygon size by 25% ---
        self.arrow_polygon = QPolygonF([QPointF(0, -15), QPointF(10, 5), QPointF(-10, 5)])

    def setAngle(self, angle):
        if self.angle != angle:
            self.angle = angle
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        painter.setBrush(QBrush(self.arrow_color))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(self.arrow_polygon)

# A custom widget for the new boat speed display
class BoatSpeedWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.max_speed = 0.0
        self.min_speed = 999.0

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        
        title = QLabel("BOAT SPEED (kts)")
        title.setStyleSheet("font-family: Oxanium; font-size: 24px; color: #888; font-weight: bold;")
        
        self.speed_label = QLabel("---")
        self.speed_label.setStyleSheet("font-family: Oxanium; font-size: 110px; color: white; font-weight: bold;")

        max_min_layout = QGridLayout()
        max_min_layout.setContentsMargins(10, 0, 0, 0)
        max_label = QLabel("Max"); max_label.setStyleSheet("font-family: Oxanium; font-size: 20px; color: #888;")
        self.max_speed_label = QLabel("---"); self.max_speed_label.setStyleSheet("font-family: Oxanium; font-size: 36px; color: white;")
        min_label = QLabel("Min"); min_label.setStyleSheet("font-family: Oxanium; font-size: 20px; color: #888;")
        self.min_speed_label = QLabel("---"); self.min_speed_label.setStyleSheet("font-family: Oxanium; font-size: 36px; color: white;")

        max_min_layout.addWidget(max_label, 0, 0); max_min_layout.addWidget(self.max_speed_label, 1, 0)
        max_min_layout.addWidget(min_label, 0, 1); max_min_layout.addWidget(self.min_speed_label, 1, 1)
        
        layout.addWidget(title); layout.addWidget(self.speed_label); layout.addLayout(max_min_layout)
        layout.addStretch()

    @Slot(float)
    def update_speed(self, speed_knots):
        self.speed_label.setText(f"{speed_knots:.1f}")
        if speed_knots > self.max_speed:
            self.max_speed = speed_knots
            self.max_speed_label.setText(f"{self.max_speed:.1f}")
        if 0 < speed_knots < self.min_speed:
            self.min_speed = speed_knots
            self.min_speed_label.setText(f"{self.min_speed:.1f}")


# A custom widget for the race wind display
class RaceWindWidget(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)

        title = QLabel("WIND SPEED")
        title.setStyleSheet("font-family: Oxanium; font-size: 24px; color: #888; font-weight: bold;")

        data_layout = QHBoxLayout()
        data_layout.setSpacing(5)
        
        # Speed Value and Trend
        self.speed_label = QLabel("---")
        self.speed_label.setStyleSheet("font-family: Oxanium; font-size: 64px; color: white; font-weight: bold;")
        self.trend_label = QLabel("▲0")
        self.trend_label.setStyleSheet("font-family: Oxanium; font-size: 24px; color: #888; font-weight: bold;")
        
        # --- MODIFIED: Create a vertical layout for the direction arrow and text ---
        direction_stack = QVBoxLayout()
        direction_stack.setSpacing(0)
        self.arrow_widget = SmallArrowWidget()
        self.direction_label = QLabel("NW")
        self.direction_label.setStyleSheet("font-family: Oxanium; font-size: 24px; color: #888; font-weight: bold;")
        # Add arrow and text to the new vertical layout
        direction_stack.addWidget(self.arrow_widget, alignment=Qt.AlignCenter)
        direction_stack.addWidget(self.direction_label, alignment=Qt.AlignCenter)
        
        # Add widgets to the main horizontal layout
        data_layout.addWidget(self.speed_label)
        data_layout.addWidget(self.trend_label, alignment=Qt.AlignHCenter)
        data_layout.addStretch()
        # Add the entire vertical direction layout to the horizontal layout
        data_layout.addLayout(direction_stack)

        main_layout.addWidget(title)
        main_layout.addLayout(data_layout)

    @Slot(float, float)
    def update_wind(self, speed_mps, angle_rad):
        speed_knots = speed_mps * 1.94384
        angle_deg = math.degrees(angle_rad)
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        idx = round(angle_deg / 45) % 8

        self.speed_label.setText(f"{speed_knots:.0f}")
        self.direction_label.setText(dirs[idx])
        self.arrow_widget.setAngle(angle_deg)


# The main widget for the entire race view
class RaceViewWidget(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self); main_layout.setContentsMargins(20, 20, 20, 20); main_layout.setSpacing(20)

        map_placeholder = QWidget(); map_placeholder.setStyleSheet("background-color: #1a1a1a; border-radius: 10px;")
        map_layout = QVBoxLayout(map_placeholder)
        map_label = QLabel("Map Placeholder"); map_label.setAlignment(Qt.AlignCenter); map_label.setStyleSheet("font-family: Oxanium; font-size: 30px; color: #555;")
        map_layout.addWidget(map_label)
        
        data_layout = QVBoxLayout()
        self.boat_speed_widget = BoatSpeedWidget()
        self.wind_widget = RaceWindWidget()
        
        data_layout.addStretch()
        data_layout.addWidget(self.boat_speed_widget)
        data_layout.addStretch()
        data_layout.addWidget(self.wind_widget)
        data_layout.addStretch()

        main_layout.addWidget(map_placeholder, 2)
        main_layout.addLayout(data_layout, 1)

    @Slot(float)
    def update_speed_display(self, speed_knots):
        self.boat_speed_widget.update_speed(speed_knots)
    
    @Slot(float, float, str)
    def update_wind_display(self, speed_mps, angle_rad, reference):
        self.wind_widget.update_wind(speed_mps, angle_rad)