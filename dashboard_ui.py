# dashboard_ui.py
import os
import math
import time
from collections import deque
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel,
                               QCheckBox, QPushButton, QGridLayout, QHBoxLayout, QListWidget,
                               QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QSize, QPointF, QUrl
from PySide6.QtGui import QKeyEvent, QPainter, QColor, QPolygonF, QBrush, QPen
from PySide6.QtMultimedia import QSoundEffect

# --- (Helper functions and widgets remain the same) ---
def haversine_distance(lat1_rad, lon1_rad, lat2_rad, lon2_rad):
    R = 6371000; dlat = lat2_rad - lat1_rad; dlon = lon2_rad - lon1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

class ArrowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0; self.setMinimumSize(QSize(75, 75)); self.arrow_color = QColor("white")
        self.arrow_polygon = QPolygonF([QPointF(0, -28), QPointF(19, 10), QPointF(-19, 10)])
    def setAngle(self, angle):
        if self.angle != angle: self.angle = angle; self.update()
    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#888")); pen.setWidth(4); pen.setCapStyle(Qt.RoundCap); painter.setPen(pen)
        painter.drawLine(self.width() / 2, 5, self.width() / 2, 15)
        painter.translate(self.width() / 2, self.height() / 2); painter.rotate(self.angle)
        painter.setBrush(QBrush(self.arrow_color)); painter.setPen(Qt.NoPen); painter.drawPolygon(self.arrow_polygon)

class DataWidget(QWidget):
    def __init__(self, title, unit="", title_size=18, value_size=64, unit_size=18):
        super().__init__(); layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(-25)
        self.title_label = QLabel(title); self.title_label.setStyleSheet(f"font-family: Oxanium; font-weight: bold; font-size: {title_size}px; color: #888;")
        self.value_label = QLabel("N/A"); self.value_label.setStyleSheet(f"font-family: Oxanium; font-weight: bold; font-size: {value_size}px; color: white;")
        self.unit_label = QLabel(unit); self.unit_label.setStyleSheet(f"font-family: Oxanium; font-size: {unit_size}px; color: #888;")
        layout.addWidget(self.title_label); layout.addWidget(self.value_label); layout.addWidget(self.unit_label)

class DirectionalDataWidget(QWidget):
    def __init__(self, title, unit="°"):
        super().__init__(); main_layout=QVBoxLayout(self); main_layout.setSpacing(5)
        self.title_label=QLabel(title); self.title_label.setStyleSheet("font-family:Oxanium;font-weight:bold;font-size:30px;color:#888;")
        value_layout=QHBoxLayout(); value_layout.setSpacing(20)
        self.value_label=QLabel("N/A"); self.value_label.setStyleSheet("font-family:Oxanium;font-weight:bold;font-size:106px;color:white;")
        self.value_label.setFixedWidth(160); self.value_label.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.arrow_widget=ArrowWidget(); value_layout.addWidget(self.value_label); value_layout.addWidget(self.arrow_widget)
        self.unit_label=QLabel(unit); self.unit_label.setStyleSheet("font-family:Oxanium;font-size:30px;color:#888;")
        main_layout.addWidget(self.title_label); main_layout.addLayout(value_layout); main_layout.addWidget(self.unit_label)
    def setValueText(self,text): self.value_label.setText(text)
    def setArrowAngle(self,angle): self.arrow_widget.setAngle(angle)

class TrendDataWidget(QWidget):
    def __init__(self, title, unit=""):
        super().__init__(); main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0,0,0,0); main_layout.setSpacing(5)
        self.title_label=QLabel(title); self.title_label.setStyleSheet("font-family:Oxanium;font-weight:bold;font-size:18px;color:#888;")
        value_layout=QHBoxLayout(); value_layout.setSpacing(15)
        self.value_label=QLabel("N/A"); self.value_label.setStyleSheet("font-family:Oxanium;font-weight:bold;font-size:64px;color:white;")
        self.trend_label=QLabel(""); self.trend_label.setStyleSheet("font-family:Oxanium;font-weight:bold;font-size:25px;color:#888; padding-bottom: 10px;")
        value_layout.addWidget(self.value_label); value_layout.addWidget(self.trend_label, alignment=Qt.AlignBottom); value_layout.addStretch()
        self.unit_label=QLabel(unit); self.unit_label.setStyleSheet("font-family:Oxanium;font-size:18px;color:#888;")
        main_layout.addWidget(self.title_label); main_layout.addLayout(value_layout); main_layout.addWidget(self.unit_label)

class DashboardUI(QWidget):
    race_selected = Signal(str)
    view_changed = Signal(int)
    discoverable_clicked = Signal()
    theme_changed = Signal(bool)
    exit_app_clicked = Signal()
    escape_pressed = Signal()
    test_banner_requested = Signal() # Add this new signal
    show_test_banner_requested = Signal()
    hide_test_banner_requested = Signal()
    delete_trip_requested = Signal(str)
    set_people_requested = Signal(str, int)
    trip_type_changed = Signal(str)
    trip_course_changed = Signal(str)
    anchor_drift_alarm = Signal(bool)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_B and not event.isAutoRepeat():
            self.show_test_banner_requested.emit()
        elif event.key() == Qt.Key.Key_Escape:
            self.escape_pressed.emit()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_B and not event.isAutoRepeat():
            self.hide_test_banner_requested.emit()
        else:
            super().keyReleaseEvent(event)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sailing Dashboard"); self.setGeometry(0,0,1024,600)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.wind_history=deque(maxlen=300); self.pressure_history=deque(maxlen=300)
        self.anchor_pos_rad=None; self.current_pos_rad=None; layout=QVBoxLayout(self)
        self.tabs=QTabWidget(); self.tabs.setTabPosition(QTabWidget.South)
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background: #282828;
                color: white;
                padding: 15px;
                font-family: Oxanium;
                font-size: 18px;
                font-weight: bold;
                margin-right: 4px;
            }
            QTabBar::tab:first {
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
            }
            QTabBar::tab:last {
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                margin-right: 0px;
            }
            QTabBar::tab:selected {
                background: #8AE2F8;
                color: black;
                border-top: none;
            }
        """)

        self.dashboard_tab=QWidget(); self.log_tab = QWidget(); self.settings_tab=QWidget()
        self.tabs.addTab(self.dashboard_tab,"Dashboard"); self.tabs.addTab(self.log_tab, "Ships log") ;self.tabs.addTab(self.settings_tab,"Settings")
        layout.addWidget(self.tabs); self._setup_dashboard_grid(); self._setup_log_panel(); self._setup_settings_panel()
        self.trend_timer=QTimer(self); self.trend_timer.timeout.connect(self.update_trends); self.trend_timer.start(5000)

        self.alarm_sound = QSoundEffect()
        script_dir = os.path.dirname(__file__)
        sound_file_path = os.path.join(script_dir, "beep.wav") # Using .wav is more reliable
        self.alarm_sound.setSource(QUrl.fromLocalFile(sound_file_path))
        self.alarm_sound.setLoopCount(-2)


    def _setup_dashboard_grid(self):
        dashboard_layout = QVBoxLayout(self.dashboard_tab)
        dashboard_layout.setContentsMargins(0, 0, 0, 0)
        dashboard_layout.setSpacing(0)

        self.drift_alarm_banner = QWidget(self.dashboard_tab)
        banner_layout = QHBoxLayout(self.drift_alarm_banner)
        banner_label = QLabel("ANCHOR DRIFTING!")
        banner_label.setStyleSheet("font-size: 24px; font-weight: bold; color: black;")
        dismiss_button = QPushButton("Dismiss")
        dismiss_button.setStyleSheet("""
            QPushButton {
                font-family: Oxanium;
                font-size: 18px;
                font-weight: bold;
                color: black;
                background-color: #F28B82;
                border: 1px solid black;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
                color: white;
            }
        """)
        banner_layout.addWidget(banner_label, alignment=Qt.AlignLeft)
        banner_layout.addWidget(dismiss_button, alignment=Qt.AlignRight)
        self.drift_alarm_banner.setStyleSheet("background-color: #F28B82; padding: 10px; border-radius: 8px;")
        self.drift_alarm_banner.hide()
        dismiss_button.clicked.connect(self.on_dismiss_alarm)

        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(60, 50, 60, 50)
        grid_layout.setVerticalSpacing(50)
        grid_layout.setHorizontalSpacing(80)

        self.depth_widget = DataWidget("DEPTH", "feet")
        self.depth_widget.layout().setContentsMargins(0, 20, 0, 0)
        self.trip_dist_widget = DataWidget("TRIP DISTANCE", "miles")
        self.trip_time_widget = DataWidget("TRIP TIME", "")
        grid_layout.addWidget(self.depth_widget, 0, 0, alignment=Qt.AlignTop)
        grid_layout.addWidget(self.trip_dist_widget, 1, 0, alignment=Qt.AlignTop)
        grid_layout.addWidget(self.trip_time_widget, 2, 0, alignment=Qt.AlignTop)
        self.wind_dir_widget = DirectionalDataWidget("WIND DIR.", "")
        self.heading_widget = DirectionalDataWidget("HEADING", "°")
        self.wind_speed_widget = TrendDataWidget("AP. WIND SPEED", "knots")
        self.pressure_widget = TrendDataWidget("PRESSURE", "Pascal")
        grid_layout.addWidget(self.wind_dir_widget, 0, 1, alignment=Qt.AlignTop)
        grid_layout.addWidget(self.wind_speed_widget, 1, 1, alignment=Qt.AlignTop)
        grid_layout.addWidget(self.pressure_widget, 2, 1, alignment=Qt.AlignTop)
        self.position_widget = DataWidget("POSITION", "", value_size=30)
        self.drag_widget = DataWidget("DRAG / DRIFT", "ft")
        drag_layout = QHBoxLayout()
        self.anchor_button = QPushButton("Set")
        self.anchor_button.setCheckable(True)
        self.anchor_button.setStyleSheet("""
            QPushButton {
                font-family: Oxanium;
                font-size: 18px;
                font-weight: bold;
                color: white;
                background-color: #282828;
                border: none;
                padding: 15px;
                margin-bottom: 5px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """)
        drag_layout.addWidget(self.drag_widget, alignment=Qt.AlignTop)
        drag_layout.addWidget(self.anchor_button, alignment=Qt.AlignTop)
        drag_container = QWidget()
        drag_container.setLayout(drag_layout)
        grid_layout.addWidget(self.heading_widget, 0, 2, alignment=Qt.AlignTop)
        grid_layout.addWidget(self.position_widget, 1, 2, alignment=Qt.AlignTop)
        grid_layout.addWidget(drag_container, 2, 2, alignment=Qt.AlignTop)
        self.anchor_button.toggled.connect(self.on_anchor_toggled)
        
        dashboard_layout.addWidget(self.drift_alarm_banner)
        dashboard_layout.addWidget(grid_widget)


    def _setup_log_panel(self):
        log_layout = QVBoxLayout(self.log_tab)
        log_layout.setContentsMargins(20, 20, 20, 20)
        log_header = QLabel("Ships Log")
        log_header.setStyleSheet("font-family: Oxanium; font-size: 24px; font-weight: bold; padding-bottom: 10px; color: #BDC1C6;")
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(10)
        self.log_table.setHorizontalHeaderLabels(["Trip ID", "Date", "Duration", "Type", "Course", "Distance\n(mi)", "Wind Dir.", "Wind\n(Min/Max) kts", "Boat\n(Min/Max) kts", "People"])
        self.log_table.setColumnHidden(0, True) # Hide the Trip ID column
        header = self.log_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignLeft)
        for i in range(self.log_table.columnCount()):
            self.log_table.setColumnWidth(i, 150) # Adjust as needed
        self.log_table.setColumnWidth(1, 200) # Date column
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.verticalHeader().setDefaultSectionSize(40) # Increased row height
        self.log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.log_table.setShowGrid(False)
        self.log_table.setStyleSheet("""
            QTableWidget {
                font-size: 16px;
                border: none;
            }
            QTableWidget::item {
                border-top: 1px solid #80868B;
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #8AE2F8;
                color: black;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
        """)

        button_layout = QHBoxLayout()
        button_style = """
            QPushButton {
                font-family: Oxanium;
                font-size: 18px;
                font-weight: bold;
                color: white;
                background-color: #282828;
                border: none;
                padding: 15px;
                margin-bottom: 5px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """
        add_people_button = QPushButton("Set People")
        add_people_button.setStyleSheet(button_style)
        add_people_button.clicked.connect(self.on_set_people)
        delete_button = QPushButton("Delete Trip")
        delete_button.setStyleSheet(button_style)
        delete_button.clicked.connect(self.on_delete_trip)
        button_layout.addWidget(add_people_button)
        button_layout.addWidget(delete_button)
        button_layout.addStretch()

        log_layout.addWidget(log_header)
        log_layout.addWidget(self.log_table)
        log_layout.addLayout(button_layout)


    def _setup_settings_panel(self):
        main_settings_layout=QGridLayout(self.settings_tab)
        main_settings_layout.setContentsMargins(20, 20, 20, 20)

        header_style = "font-size:24px;font-family:Oxanium;font-weight:bold;padding-bottom:10px;color:#BDC1C6;"
        sub_header_style = "font-size:24px;font-family:Oxanium;font-weight:bold;padding-bottom:10px;color:#BDC1C6; margin-top: 24px;"
        label_style = "font-size:18px;font-family:Oxanium;color:#BDC1C6;"

        ui_config_layout=QVBoxLayout();
        ui_config_label=QLabel("Sail UI Dashboard")
        ui_config_label.setStyleSheet(header_style)
        self.ui_config_list=QListWidget()
        QListWidgetItem("Standard View",self.ui_config_list); QListWidgetItem("Standard (No Wind Arrow)", self.ui_config_list); QListWidgetItem("Race Mode", self.ui_config_list)
        self.ui_config_list.setCurrentRow(0)

        race_courses_layout=QVBoxLayout()
        self.race_courses_label=QLabel("Race Courses")
        self.race_courses_label.setStyleSheet(header_style)
        self.race_courses_list=QListWidget()
        self.populate_race_courses()

        list_stylesheet="QListWidget{font-size:18px;font-family:Oxanium;border:none;}QListWidget::item{padding:15px;margin-bottom:5px;}QListWidget::item:selected{background-color:#ffffff;color:#252525;border-radius:8px;}"
        self.ui_config_list.setStyleSheet(list_stylesheet); self.race_courses_list.setStyleSheet(list_stylesheet)
        ui_config_layout.addWidget(ui_config_label); ui_config_layout.addWidget(self.ui_config_list); race_courses_layout.addWidget(self.race_courses_label); race_courses_layout.addWidget(self.race_courses_list)

        general_settings_layout=QVBoxLayout()
        general_settings_label=QLabel("Settings")
        general_settings_label.setStyleSheet(header_style)
        light_dark_label=QLabel("Light/Dark Mode")
        light_dark_label.setStyleSheet(sub_header_style)
        self.theme_checkbox=QCheckBox("Enable Light Mode")
        self.theme_checkbox.setStyleSheet(label_style)

        bt_connection_label=QLabel("Bluetooth Connection")
        bt_connection_label.setStyleSheet(sub_header_style)
        self.bt_status_label=QLabel("Status: Checking...")
        self.bt_status_label.setStyleSheet(label_style)
        self.bt_status_label.setFixedWidth(250); self.bt_status_label.setWordWrap(True)

        button_style = """
            QPushButton {
                font-family: Oxanium;
                font-size: 18px;
                font-weight: bold;
                color: white;
                background-color: #282828;
                border: none;
                padding: 15px;
                margin-bottom: 5px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """
        exit_button_style = """
            QPushButton {
                font-family: Oxanium;
                font-size: 18px;
                font-weight: bold;
                color: black;
                background-color: #F28B82;
                border: none;
                padding: 15px;
                margin-bottom: 5px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
                color: white;
            }
        """

        discoverable_button=QPushButton("Make Discoverable")
        discoverable_button.setStyleSheet(button_style)
        exit_button=QPushButton("Exit Sailing App")
        exit_button.setStyleSheet(exit_button_style)

        general_settings_layout.addWidget(general_settings_label); general_settings_layout.addWidget(light_dark_label); general_settings_layout.addWidget(self.theme_checkbox)
        general_settings_layout.addWidget(bt_connection_label); general_settings_layout.addWidget(self.bt_status_label); general_settings_layout.addWidget(discoverable_button)
        general_settings_layout.addStretch(); general_settings_layout.addWidget(exit_button)
        main_settings_layout.addLayout(ui_config_layout,0,0); main_settings_layout.addLayout(race_courses_layout,0,1); main_settings_layout.addLayout(general_settings_layout,0,2)
        main_settings_layout.setColumnStretch(0,1); main_settings_layout.setColumnStretch(1,1); main_settings_layout.setColumnStretch(2,1)
        self.ui_config_list.currentItemChanged.connect(self.on_ui_config_changed); self.race_courses_list.currentItemChanged.connect(self.on_race_course_changed)
        self.theme_checkbox.stateChanged.connect(self.on_theme_toggled); discoverable_button.clicked.connect(self.discoverable_clicked.emit); exit_button.clicked.connect(self.exit_app_clicked.emit)
        self.on_ui_config_changed(self.ui_config_list.currentItem())

    def populate_race_courses(self):
        races_dir="races"; base_path=os.path.dirname(os.path.abspath(__file__)); full_races_dir=os.path.join(base_path,races_dir)
        if os.path.isdir(full_races_dir):
            for race_name in os.listdir(full_races_dir):
                if os.path.isdir(os.path.join(full_races_dir,race_name)):
                    item=QListWidgetItem(race_name.replace("_"," ").title()); item.setData(Qt.UserRole,race_name); self.race_courses_list.addItem(item)

    @Slot(QListWidgetItem)
    def on_race_course_changed(self, item):
        if item:
            race_dir_name = item.data(Qt.UserRole)
            print(f"DEBUG (dashboard_ui): Race selected: '{race_dir_name}'. Emitting signal.")
            self.race_selected.emit(race_dir_name)
            self.trip_course_changed.emit(race_dir_name)


    @Slot(QListWidgetItem)
    def on_ui_config_changed(self,current_item):
        is_race_mode=current_item.text()=="Race Mode"
        self.race_courses_label.setEnabled(is_race_mode)
        self.race_courses_list.setEnabled(is_race_mode)
        enabled_stylesheet="QListWidget{font-size:18px;font-family:Oxanium;border:none;}QListWidget::item{padding:15px;margin-bottom:5px;}QListWidget::item:selected{border-radius:8px;background-color:#ffffff;color:#252525;}"
        disabled_stylesheet="QListWidget{font-size:18px;font-family:Oxanium;border:none;}QListWidget::item{padding:15px;margin-bottom:5px;color:#888;}QListWidget::item:selected{border-radius:8px;background-color:none;color:#888;}"

        if is_race_mode:
            self.trip_type_changed.emit("Race")
            selected_course_item = self.race_courses_list.currentItem()
            if selected_course_item:
                self.trip_course_changed.emit(selected_course_item.data(Qt.UserRole))
            self.race_courses_list.setStyleSheet(enabled_stylesheet)
            self.race_courses_label.setStyleSheet("font-size:24px;font-family:Oxanium;font-weight:bold;padding-bottom:10px;color:#BDC1C6;")
        else:
            self.trip_type_changed.emit("Cruise")
            self.trip_course_changed.emit(None)
            self.race_courses_list.setStyleSheet(disabled_stylesheet)
            self.race_courses_label.setStyleSheet("font-size:24px;font-family:Oxanium;font-weight:bold;padding-bottom:10px;color:#BDC1C6;")


    def keyPressEvent(self,event:QKeyEvent):
        if event.key()==Qt.Key.Key_Escape: self.escape_pressed.emit()
        else: super().keyPressEvent(event)
    
    @Slot(str)
    def update_bluetooth_status(self,status): self.bt_status_label.setText(f"Status: {status}")
    @Slot(int)
    def on_theme_toggled(self,state): self.theme_changed.emit(bool(state))
    @Slot(float)
    def update_depth_display(self,depth_m): self.depth_widget.value_label.setText(f"{depth_m*3.28084:.1f}")
    @Slot(float,float)
    def update_trip_display(self,dist_m,time_s):
        self.trip_dist_widget.value_label.setText(f"{dist_m/1609.34:.1f}"); h,rem=divmod(time_s,3600); m,_=divmod(rem,60)
        self.trip_time_widget.value_label.setText(f"{int(h):02}:{int(m):02}")
    @Slot(float,float,str)
    def update_wind_display(self,speed_mps,angle_rad,ref):
        dirs=["N","NE","E","SE","S","SW","W","NW"]; angle_deg=math.degrees(angle_rad); idx=round(angle_deg/45)%8
        self.wind_dir_widget.setValueText(dirs[idx]); self.wind_dir_widget.setArrowAngle(angle_deg); speed_knots=speed_mps*1.94384
        self.wind_speed_widget.value_label.setText(f"{speed_knots:.0f}"); self.wind_history.append((time.time(),speed_knots))
    @Slot(float)
    def update_pressure_display(self,pressure_pa):
        self.pressure_widget.value_label.setText(f"{pressure_pa:.0f}"); self.pressure_history.append((time.time(),pressure_pa))
    @Slot(float)
    def update_heading_display(self,heading_deg):
        self.heading_widget.setValueText(f"{heading_deg:.0f}"); self.heading_widget.setArrowAngle(heading_deg)
    @Slot(float,float)
    def update_position_display(self,lat_rad,lon_rad):
        self.current_pos_rad=(lat_rad,lon_rad)
        self.position_widget.value_label.setText(f"{math.degrees(lat_rad):.4f}°    {math.degrees(lon_rad):.4f}°"); self.position_widget.unit_label.setText("Latitude / Longitude")
        if self.anchor_pos_rad:
            dist_m=haversine_distance(self.anchor_pos_rad[0],self.anchor_pos_rad[1],lat_rad,lon_rad)
            self.drag_widget.value_label.setText(f"{dist_m*3.28084:.1f}")
            if dist_m > 22.86: # 75 feet in meters
                self.anchor_drift_alarm.emit(True)
            else:
                self.anchor_drift_alarm.emit(False)

    @Slot(bool)
    def on_anchor_toggled(self,checked):
        self.anchor_pos_rad=self.current_pos_rad if checked else None
        if not checked:
            self.drag_widget.value_label.setText("N/A")
            self.anchor_button.setText("Set")
            self.anchor_drift_alarm.emit(False)
        else:
            self.anchor_button.setText("Unset")

    def update_trends(self):
        if len(self.wind_history)>1:
            diff=self.wind_history[-1][1]-self.wind_history[0][1]
            self.wind_speed_widget.trend_label.setText(f"{'▲' if diff > 0 else '▼'} {abs(diff):.1f}*")
        if len(self.pressure_history)>1:
            diff=self.pressure_history[-1][1]-self.pressure_history[0][1]
            self.pressure_widget.trend_label.setText(f"{'▲' if diff > 0 else '▼'} {abs(diff):.0f}*")

    def populate_log_table(self, trips):
        self.log_table.setRowCount(0) # Clear the table first
        sorted_trips = sorted(trips, key=lambda x: x['start_time'], reverse=True)
        self.log_table.setRowCount(len(sorted_trips))
        for row, trip in enumerate(sorted_trips):
            start_time_str = datetime.fromtimestamp(trip['start_time']).strftime('%b %d, %Y')
            duration_h = 0
            if trip['end_time']:
                duration_s = trip['end_time'] - trip['start_time']
                duration_h, rem = divmod(duration_s, 3600)
                duration_m, _ = divmod(rem, 60)
            else:
                duration_m = 0

            self.log_table.setItem(row, 0, QTableWidgetItem(trip['id']))
            self.log_table.setItem(row, 1, QTableWidgetItem(start_time_str))
            self.log_table.setItem(row, 2, QTableWidgetItem(f"{int(duration_h)}hr {int(duration_m):02}mins"))
            self.log_table.setItem(row, 3, QTableWidgetItem(trip.get('type', 'Cruise')))
            self.log_table.setItem(row, 4, QTableWidgetItem(trip.get('course', 'N/A') or 'N/A'))
            self.log_table.setItem(row, 5, QTableWidgetItem(f"{trip['distance'] / 1609.34:.1f}"))
            self.log_table.setItem(row, 6, QTableWidgetItem(trip.get('wind_direction', 'N/A')))
            self.log_table.setItem(row, 7, QTableWidgetItem(f"{trip['max_wind_speed']:.1f} / {trip['min_wind_speed']:.1f}"))
            self.log_table.setItem(row, 8, QTableWidgetItem(f"{trip['max_boat_speed']:.1f} / {trip['min_boat_speed']:.1f}"))
            self.log_table.setItem(row, 9, QTableWidgetItem(str(trip['people']) if trip['people'] is not None else "N/A"))


    def on_delete_trip(self):
        selected_items = self.log_table.selectedItems()
        if selected_items:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Confirm Deletion")
            msg_box.setText("Are you sure you want to delete this trip log?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1e1e1e;
                    font-family: Oxanium;
                }
                QMessageBox QLabel {
                    color: white;
                    font-size: 18px;
                }
                QMessageBox QPushButton {
                    font-family: Oxanium;
                    font-size: 16px;
                    font-weight: bold;
                    color: white;
                    background-color: #282828;
                    border: none;
                    padding: 10px;
                    min-width: 80px;
                    border-radius: 8px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #3c3c3c;
                }
            """)

            if msg_box.exec() == QMessageBox.Yes:
                trip_id = self.log_table.item(selected_items[0].row(), 0).text()
                self.delete_trip_requested.emit(trip_id)

    def on_set_people(self):
        selected_items = self.log_table.selectedItems()
        if selected_items:
            trip_id = self.log_table.item(selected_items[0].row(), 0).text()
            num_people, ok = QInputDialog.getInt(self, "Set People", "Enter number of people:")
            if ok:
                self.set_people_requested.emit(trip_id, num_people)

    @Slot(bool)
    def on_anchor_drift_alarm(self, is_drifting):
        if is_drifting:
            self.drift_alarm_banner.show()
            self.drift_alarm_banner.raise_()
            if self.alarm_sound.source().isEmpty() or not os.path.exists(self.alarm_sound.source().toLocalFile()):
                print("Alarm sound file not found.")
                return
            if not self.alarm_sound.isPlaying():
                self.alarm_sound.play()
        else:
            self.drift_alarm_banner.hide()
            self.alarm_sound.stop()
            
    def on_dismiss_alarm(self):
        self.anchor_button.setChecked(False)