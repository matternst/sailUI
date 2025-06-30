# dashboard_ui.py

import math
import time
from collections import deque
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel,
                               QCheckBox, QPushButton, QGridLayout, QHBoxLayout, QListWidget,
                               QListWidgetItem)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QSize, QPointF
from PySide6.QtGui import QKeyEvent, QPainter, QColor, QPolygonF, QBrush, QPen

# --- Haversine Distance Function ---
def haversine_distance(lat1_rad, lon1_rad, lat2_rad, lon2_rad):
    R = 6371000 # Earth radius in meters
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# --- Arrow Drawing Widget ---
class ArrowWidget(QWidget):
    """A widget that draws a rotatable arrow with a fixed North indicator."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.setMinimumSize(QSize(75, 75))
        self.arrow_color = QColor("white")
        self.arrow_polygon = QPolygonF([
            QPointF(0, -28), QPointF(19, 10), QPointF(-19, 10)
        ])

    def setAngle(self, angle):
        if self.angle != angle:
            self.angle = angle
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        north_marker_pen = QPen(QColor("#888")); north_marker_pen.setWidth(4); north_marker_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(north_marker_pen)
        painter.drawLine(self.width() / 2, 5, self.width() / 2, 15)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        painter.setBrush(QBrush(self.arrow_color)); painter.setPen(Qt.NoPen)
        painter.drawPolygon(self.arrow_polygon)

# --- Data Display Widgets ---
class DataWidget(QWidget):
    def __init__(self, title, unit="", title_size=18, value_size=64, unit_size=18):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(-25)
        self.title_label = QLabel(title); self.title_label.setStyleSheet(f"font-family: Oxanium; font-weight: bold; font-size: {title_size}px; color: #888;")
        self.value_label = QLabel("N/A"); self.value_label.setStyleSheet(f"font-family: Oxanium; font-weight: bold; font-size: {value_size}px; color: white;")
        self.unit_label = QLabel(unit); self.unit_label.setStyleSheet(f"font-family: Oxanium; font-size: {unit_size}px; color: #888;")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.unit_label)

class DirectionalDataWidget(QWidget):
    def __init__(self, title, unit="°"):
        super().__init__()
        main_layout = QVBoxLayout(self); main_layout.setSpacing(5)
        self.title_label = QLabel(title); self.title_label.setStyleSheet("font-family: Oxanium; font-weight: bold; font-size: 30px; color: #888;")
        value_layout = QHBoxLayout(); value_layout.setSpacing(20)
        self.value_label = QLabel("N/A"); self.value_label.setStyleSheet("font-family: Oxanium; font-weight: bold; font-size: 106px; color: white;")
        self.value_label.setFixedWidth(160)
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.arrow_widget = ArrowWidget()
        value_layout.addWidget(self.value_label); value_layout.addWidget(self.arrow_widget)
        self.unit_label = QLabel(unit); self.unit_label.setStyleSheet("font-family: Oxanium; font-size: 30px; color: #888;")
        main_layout.addWidget(self.title_label); main_layout.addLayout(value_layout); main_layout.addWidget(self.unit_label)
    def setValueText(self, text): self.value_label.setText(text)
    def setArrowAngle(self, angle): self.arrow_widget.setAngle(angle)

class TrendDataWidget(QWidget):
    def __init__(self, title, unit=""):
        super().__init__()
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(5)
        self.title_label = QLabel(title); self.title_label.setStyleSheet("font-family: Oxanium; font-weight: bold; font-size: 18px; color: #888;")
        value_layout = QHBoxLayout(); value_layout.setSpacing(15)
        self.value_label = QLabel("N/A"); self.value_label.setStyleSheet("font-family: Oxanium; font-weight: bold; font-size: 64px; color: white;")
        self.trend_label = QLabel(""); self.trend_label.setStyleSheet("font-family: Oxanium; font-weight: bold; font-size: 21px; color: #888;")
        value_layout.addWidget(self.value_label); value_layout.addWidget(self.trend_label, alignment=Qt.AlignBottom); value_layout.addStretch()
        self.unit_label = QLabel(unit); self.unit_label.setStyleSheet("font-family: Oxanium; font-size: 18px; color: #888;")
        main_layout.addWidget(self.title_label); main_layout.addLayout(value_layout); main_layout.addWidget(self.unit_label)

# --- Main Dashboard UI ---
class DashboardUI(QWidget):
    view_changed = Signal(int)
    discoverable_clicked = Signal()
    theme_changed = Signal(bool)
    exit_app_clicked = Signal()
    escape_pressed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sailing Dashboard")
        self.setGeometry(0, 0, 1024, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.wind_history = deque(maxlen=300)
        self.pressure_history = deque(maxlen=300)
        self.anchor_pos_rad = None
        self.current_pos_rad = None
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(); self.tabs.setTabPosition(QTabWidget.South)
        self.tabs.setStyleSheet("""
            QTabBar::tab { background: #282828; color: white; padding: 15px; font-size: 20px; border-top: 2px solid #282828; }
            QTabBar::tab:selected { background: #3c3c3c; border-top: 2px solid #007acc; }
        """)
        self.dashboard_tab = QWidget()
        self.settings_tab = QWidget()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.settings_tab, "Settings")
        layout.addWidget(self.tabs)
        self._setup_dashboard_grid()
        self._setup_settings_panel()
        self.trend_timer = QTimer(self)
        self.trend_timer.timeout.connect(self.update_trends)
        self.trend_timer.start(5000)

    def _setup_dashboard_grid(self):
        grid_layout = QGridLayout(self.dashboard_tab)
        grid_layout.setContentsMargins(60, 50, 60, 50)
        grid_layout.setVerticalSpacing(50)
        grid_layout.setHorizontalSpacing(80)
        self.depth_widget = DataWidget("DEPTH", "feet"); self.trip_dist_widget = DataWidget("TRIP DISTANCE", "miles"); self.trip_time_widget = DataWidget("TRIP TIME", "")
        grid_layout.addWidget(self.depth_widget, 0, 0, alignment=Qt.AlignTop); grid_layout.addWidget(self.trip_dist_widget, 1, 0, alignment=Qt.AlignTop); grid_layout.addWidget(self.trip_time_widget, 2, 0, alignment=Qt.AlignTop)
        self.wind_dir_widget = DirectionalDataWidget("WIND DIR.", ""); self.heading_widget = DirectionalDataWidget("HEADING", "°")
        self.wind_speed_widget = TrendDataWidget("AP. WIND SPEED", "knots"); self.pressure_widget = TrendDataWidget("PRESSURE", "Pascal")
        grid_layout.addWidget(self.wind_dir_widget, 0, 1, alignment=Qt.AlignTop); grid_layout.addWidget(self.wind_speed_widget, 1, 1, alignment=Qt.AlignTop); grid_layout.addWidget(self.pressure_widget, 2, 1, alignment=Qt.AlignTop)
        self.position_widget = DataWidget("POSITION", "", value_size=30); self.drag_widget = DataWidget("DRAG / DRIFT", "ft")
        drag_layout = QHBoxLayout()
        self.anchor_button = QPushButton("⚓"); self.anchor_button.setCheckable(True); self.anchor_button.setFixedSize(80, 80)
        self.anchor_button.setStyleSheet("QPushButton { font-size: 40px; border-radius: 40px; background-color: #444; } QPushButton:checked { background-color: #007acc; }")
        drag_layout.addWidget(self.drag_widget); drag_layout.addWidget(self.anchor_button)
        drag_container = QWidget(); drag_container.setLayout(drag_layout)
        grid_layout.addWidget(self.heading_widget, 0, 2, alignment=Qt.AlignTop); grid_layout.addWidget(self.position_widget, 1, 2, alignment=Qt.AlignTop); grid_layout.addWidget(drag_container, 2, 2, alignment=Qt.AlignTop)
        self.anchor_button.toggled.connect(self.on_anchor_toggled)

    def _setup_settings_panel(self):
        # --- MODIFIED: Reordered to define widgets before applying stylesheets ---
        main_settings_layout = QGridLayout(self.settings_tab)
        main_settings_layout.setContentsMargins(30, 30, 30, 30)
        main_settings_layout.setHorizontalSpacing(40)

        # --- Column 1: UI Configuration ---
        ui_config_layout = QVBoxLayout()
        ui_config_label = QLabel("Sail UI Dashboard")
        ui_config_label.setStyleSheet("font-size: 24px; font-family: Oxanium; padding-bottom: 10px; font-weight:bold; ")
        self.ui_config_list = QListWidget() # Define the widget first
        
        # --- Column 2: Race Courses ---
        race_courses_layout = QVBoxLayout()
        self.race_courses_label = QLabel("Race Courses")
        self.race_courses_label.setStyleSheet("font-size: 24px; font-family: Oxanium; padding-bottom: 10px; font-weight:bold; ")
        self.race_courses_list = QListWidget() # Define the widget first

        # --- Define the stylesheet ---
        list_stylesheet = """
            QListWidget {
                font-size: 18px;
                font-family: Oxanium;
                border: none;
            }
            QListWidget::item {
                padding: 15px;
                margin-bottom: 5px;
            }
            QListWidget::item:selected {
                background-color: #ffffff;
                color: #252525;
                border-radius: 8px;
            }
        """
        # --- Now apply the stylesheet ---
        self.ui_config_list.setStyleSheet(list_stylesheet)
        self.race_courses_list.setStyleSheet(list_stylesheet)

        # Add items to the lists
        QListWidgetItem("Standard View", self.ui_config_list)
        QListWidgetItem("Standard (No Wind Arrow)", self.ui_config_list)
        QListWidgetItem("Race Mode", self.ui_config_list)
        self.ui_config_list.setCurrentRow(0)
        
        QListWidgetItem("Windward/Leeward", self.race_courses_list)
        QListWidgetItem("Triangle Course", self.race_courses_list)
        QListWidgetItem("Custom Course...", self.race_courses_list)

        # Add widgets to the layout for column 1
        ui_config_layout.addWidget(ui_config_label)
        ui_config_layout.addWidget(self.ui_config_list)
        
        # Add widgets to the layout for column 2
        race_courses_layout.addWidget(self.race_courses_label)
        race_courses_layout.addWidget(self.race_courses_list)

        # --- Column 3: General Settings ---
        general_settings_layout = QVBoxLayout()
        general_settings_label = QLabel("Settings")
        general_settings_label.setStyleSheet("font-size: 24px; font-family: Oxanium; padding-bottom: 10px; font-weight:bold; ")
        light_dark_label = QLabel("Light/Dark Mode")
        light_dark_label.setStyleSheet("font-size: 18px; font-family: Oxanium; color: #bbb; font-weight:bold; padding-top: 10px;")
        self.theme_checkbox = QCheckBox("Enable Light Mode"); self.theme_checkbox.setStyleSheet("font-size: 18px; font-family: Oxanium; margin-right:8px;")

        bt_connection_label = QLabel("Bluetooth Connection")
        bt_connection_label.setStyleSheet("font-size: 18px; font-family: Oxanium; color: #bbb; font-weight:bold; padding-top: 45px;")
        self.bt_status_label = QLabel("Status: Checking..."); self.bt_status_label.setStyleSheet("font-size: 18px; font-family: Oxanium; color: #aaa; padding-top: 15px;")
        self.bt_status_label.setFixedWidth(250)
        self.bt_status_label.setWordWrap(True)
        discoverable_button = QPushButton("Make Discoverable"); discoverable_button.setStyleSheet("""
            QPushButton { font-size: 18px; font-family: Oxanium; padding: 15px; background-color: #007acc; color: white; border-radius: 5px; margin-top: 10px; }
            QPushButton:hover { background-color: #0099ff; }
        """)
        exit_button = QPushButton("Exit Sailing App"); exit_button.setStyleSheet("""
            QPushButton { font-size: 18px; font-family: Oxanium; padding: 15px; background-color: #a94442; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #c95452; }
        """)
        general_settings_layout.addWidget(general_settings_label)
        general_settings_layout.addWidget(light_dark_label) # Add the new label here
        general_settings_layout.addWidget(self.theme_checkbox)
        general_settings_layout.addWidget(bt_connection_label) # Add the new label here
        general_settings_layout.addWidget(self.bt_status_label)
        general_settings_layout.addWidget(discoverable_button)
        general_settings_layout.addStretch()
        general_settings_layout.addWidget(exit_button)

        # Add the column layouts to the grid
        main_settings_layout.addLayout(ui_config_layout, 0, 0)
        main_settings_layout.addLayout(race_courses_layout, 0, 1)
        main_settings_layout.addLayout(general_settings_layout, 0, 2)

        # Set the stretch factor for each column to 1
        main_settings_layout.setColumnStretch(0, 1)
        main_settings_layout.setColumnStretch(1, 1)
        main_settings_layout.setColumnStretch(2, 1)

        # Connect signals
        self.ui_config_list.currentItemChanged.connect(self.on_ui_config_changed)
        self.theme_checkbox.stateChanged.connect(self.on_theme_toggled)
        discoverable_button.clicked.connect(self.discoverable_clicked.emit)
        exit_button.clicked.connect(self.exit_app_clicked.emit)
        self.on_ui_config_changed(self.ui_config_list.currentItem())


    @Slot(QListWidgetItem)
    def on_ui_config_changed(self, current_item):
        # --- MODIFIED: Apply different stylesheets based on selection ---
        is_race_mode = current_item.text() == "Race Mode"
        self.race_courses_label.setEnabled(is_race_mode)
        self.race_courses_list.setEnabled(is_race_mode)

        # Stylesheet for when the list is enabled
        enabled_stylesheet = """
            QListWidget {
                font-size: 18px; font-family: Oxanium; border: none;
            }
            QListWidget::item {
                padding: 15px; margin-bottom: 5px;
            }
            QListWidget::item:selected {
                border-radius: 8px; background-color: #ffffff; color: #252525;
            }
        """
        
        # Stylesheet for when the list is disabled (reduced opacity)
        disabled_stylesheet = """
            QListWidget {
                font-size: 18px; font-family: Oxanium; border: none;
            }
            QListWidget::item {
                padding: 15px; margin-bottom: 5px; color: #888;
            }
            QListWidget::item:selected {
                border-radius: 8px; background-color: none; color: #888;
            }
        """

        if is_race_mode:
            self.race_courses_list.setStyleSheet(enabled_stylesheet)
            self.race_courses_label.setStyleSheet("font-size: 24px; font-family: Oxanium; font-weight:bold; padding-bottom: 10px; color: white;")
        else:
            self.race_courses_list.setStyleSheet(disabled_stylesheet)
            self.race_courses_label.setStyleSheet("font-size: 24px; font-family: Oxanium; font-weight:bold; padding-bottom: 10px; color: #888;")

            

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape: self.escape_pressed.emit()
        else: super().keyPressEvent(event)

    @Slot(str)
    def update_bluetooth_status(self, status):
        self.bt_status_label.setText(f"Status: {status}")

    @Slot(int)
    def on_theme_toggled(self, state): self.theme_changed.emit(bool(state))
    @Slot(float)
    def update_depth_display(self, depth_m): self.depth_widget.value_label.setText(f"{depth_m * 3.28084:.1f}")
    @Slot(float, float)
    def update_trip_display(self, dist_m, time_s):
        self.trip_dist_widget.value_label.setText(f"{dist_m / 1609.34:.1f}")
        h, rem = divmod(time_s, 3600); m, _ = divmod(rem, 60)
        self.trip_time_widget.value_label.setText(f"{int(h):02}:{int(m):02}")
    @Slot(float, float, str)
    def update_wind_display(self, speed_mps, angle_rad, ref):
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]; angle_deg = math.degrees(angle_rad); idx = round(angle_deg / 45) % 8
        self.wind_dir_widget.setValueText(dirs[idx]); self.wind_dir_widget.setArrowAngle(angle_deg)
        speed_knots = speed_mps * 1.94384; self.wind_speed_widget.value_label.setText(f"{speed_knots:.0f}"); self.wind_history.append((time.time(), speed_knots))
    @Slot(float)
    def update_pressure_display(self, pressure_pa):
        self.pressure_widget.value_label.setText(f"{pressure_pa:.0f}"); self.pressure_history.append((time.time(), pressure_pa))
    @Slot(float)
    def update_heading_display(self, heading_deg):
        self.heading_widget.setValueText(f"{heading_deg:.0f}"); self.heading_widget.setArrowAngle(heading_deg)
    @Slot(float, float)
    def update_position_display(self, lat_rad, lon_rad):
        self.current_pos_rad = (lat_rad, lon_rad); self.position_widget.value_label.setText(f"{math.degrees(lat_rad):.4f}°    {math.degrees(lon_rad):.4f}°"); self.position_widget.unit_label.setText("Latitude / Longitude")
        if self.anchor_pos_rad:
            dist_m = haversine_distance(self.anchor_pos_rad[0], self.anchor_pos_rad[1], lat_rad, lon_rad)
            self.drag_widget.value_label.setText(f"{dist_m * 3.28084:.1f}")
    @Slot(bool)
    def on_anchor_toggled(self, checked):
        self.anchor_pos_rad = self.current_pos_rad if checked else None
        if not checked: self.drag_widget.value_label.setText("N/A")
    def update_trends(self):
        if len(self.wind_history) > 1:
            diff = self.wind_history[-1][1] - self.wind_history[0][1]; self.wind_speed_widget.trend_label.setText(f"{'▲' if diff > 0 else '▼'} {abs(diff):.1f}*")
        if len(self.pressure_history) > 1:
            diff = self.pressure_history[-1][1] - self.pressure_history[0][1]; self.pressure_widget.trend_label.setText(f"{'▲' if diff > 0 else '▼'} {abs(diff):.0f}*")