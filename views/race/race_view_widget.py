# views/race/race_view_widget.py
import math
import os
import json
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout
from PySide6.QtCore import Qt, Slot, Signal, QSize, QPointF, QRectF
from PySide6.QtGui import QFont, QPainter, QColor, QPolygonF, QBrush, QPen, QPixmap, QPainterPath
from theme import LIGHT_THEME, DARK_THEME

# --- Utility Functions ---
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000; lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1); lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    dlat = lat2_rad - lat1_rad; dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)); return R * c
def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1); lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    dLon = lon2_rad - lon1_rad; y = math.sin(dLon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dLon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

# --- Re-usable Data Widget ---
class DataWidget(QWidget):
    def __init__(self, title, unit="", title_size=18, value_size=48, unit_size=18):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(-15)
        self.title_label = QLabel(title)
        self.value_label = QLabel("---")
        self.unit_label = QLabel(unit)
        self.title_size = title_size
        self.value_size = value_size
        self.unit_size = unit_size
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.unit_label)

    def setTheme(self, theme):
        self.title_label.setStyleSheet(f"font-family: Oxanium; font-weight: bold; font-size: {self.title_size}px; color: {theme['text_secondary']};")
        self.value_label.setStyleSheet(f"font-family: Oxanium; font-weight: bold; font-size: {self.value_size}px; color: {theme['text_primary']};")
        self.unit_label.setStyleSheet(f"font-family: Oxanium; font-size: {self.unit_size}px; color: {theme['text_secondary']};")

class RaceMapWidget(QWidget):
    start_line_data_updated = Signal(float, float)
    def __init__(self):
        super().__init__()
        self.map_pixmap = None; self.buoys = []; self.bounds = {}
        self.boat_position = None; self.boat_heading = 0; self.next_buoy_index = 0
        self.is_in_proximity = False; self.last_distance_to_buoy = float('inf')
        self.race_name = ""; self.start_finish_line = None; self.course_path = []
        self.boat_speed_knots = 0.0
        self.setStyleSheet("border-radius: 10px;")
        self.banner_label = QLabel(self); self.banner_label.setAlignment(Qt.AlignCenter)
        self.banner_label.setStyleSheet("background-color:rgba(0,0,0,0.7);color:white;font-family:Oxanium;font-size:24px;font-weight:bold;padding:10px;")
        self.banner_label.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.banner_label.setGeometry(0, self.height() - 60, self.width(), 60)

    def _check_buoy_proximity(self):
        if not self.boat_position or not self.buoys or self.next_buoy_index >= len(self.buoys): return
        next_buoy = self.buoys[self.next_buoy_index]; boat_lat, boat_lon = self.boat_position
        distance_m = haversine_distance(boat_lat, boat_lon, next_buoy['lat'], next_buoy['lon'])
        PROXIMITY_METERS = 30.48
        if distance_m <= PROXIMITY_METERS:
            if not self.is_in_proximity:
                bearing_to_buoy = calculate_bearing(boat_lat, boat_lon, next_buoy['lat'], next_buoy['lon'])
                heading_diff = abs((self.boat_heading - bearing_to_buoy + 180) % 360 - 180)
                if heading_diff <= 45:
                    self.banner_label.setText(f"Approaching {next_buoy['name']}, round to {next_buoy['rounding_direction']}")
                    self.banner_label.show(); self.is_in_proximity = True
        else:
            if self.is_in_proximity:
                self.next_buoy_index += 1
                if self.next_buoy_index >= len(self.buoys): self.banner_label.setText("Race Finished!"); self.banner_label.show()
                else: self.banner_label.hide()
                self.is_in_proximity = False
        self.last_distance_to_buoy = distance_m

    def _update_start_line_info(self):
        if not self.boat_position or not self.start_finish_line: return
        mid_lat = (self.start_finish_line['start']['lat'] + self.start_finish_line['end']['lat']) / 2
        mid_lon = (self.start_finish_line['start']['lon'] + self.start_finish_line['end']['lon']) / 2
        distance_m = haversine_distance(self.boat_position[0], self.boat_position[1], mid_lat, mid_lon)
        eta_seconds = 0
        if self.boat_speed_knots > 0:
            speed_mps = self.boat_speed_knots * 0.514444
            eta_seconds = distance_m / speed_mps
        self.start_line_data_updated.emit(distance_m, eta_seconds)

    @Slot(float, float)
    def update_boat_position(self, lat_rad, lon_rad):
        self.boat_position = (math.degrees(lat_rad), math.degrees(lon_rad)); self._check_buoy_proximity()
        self._update_start_line_info(); self.update()

    @Slot()
    def show_test_banner(self):
        self.banner_label.setText("TEST BANNER: Rounding Test Mark to Port"); self.banner_label.show()
    @Slot()
    def hide_test_banner(self):
        self.banner_label.hide()
        
    def _gps_to_screen(self, lat, lon, map_rect):
        if not self.bounds or 'min_lat' not in self.bounds or map_rect.isEmpty(): return None
        lon_ratio=(lon-self.bounds['min_lon'])/(self.bounds['max_lon']-self.bounds['min_lon'])
        lat_ratio=(self.bounds['max_lat']-lat)/(self.bounds['max_lat']-self.bounds['min_lat'])
        x=map_rect.x()+lon_ratio*map_rect.width(); y=map_rect.y()+lat_ratio*map_rect.height()
        return QPointF(x,y)
        
    def paintEvent(self,event):
        painter=QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath(); path.addRoundedRect(self.rect(), 10, 10); painter.setClipPath(path)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 127))

        if not self.map_pixmap: return
        scaled_pixmap=self.map_pixmap.scaled(self.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation)
        x=(self.width()-scaled_pixmap.width())/2; y=(self.height()-scaled_pixmap.height())/2
        map_rect=QRectF(x,y,scaled_pixmap.width(),scaled_pixmap.height()); painter.drawPixmap(map_rect.topLeft(),scaled_pixmap)
        
        if self.race_name:
            font = QFont("Oxanium", 48, QFont.Bold); painter.setFont(font); painter.setPen(QColor("white"))
            painter.drawText(map_rect.x() + 15, map_rect.y() + 60, self.race_name)

        if self.start_finish_line:
            start_point = self.start_finish_line['start']; end_point = self.start_finish_line['end']
            pos1 = self._gps_to_screen(start_point['lat'], start_point['lon'], map_rect)
            pos2 = self._gps_to_screen(end_point['lat'], end_point['lon'], map_rect)
            if pos1 and pos2:
                pen = QPen(QColor("#767676"), 2, Qt.DotLine); painter.setPen(pen)
                painter.drawLine(pos1, pos2)
        
        if len(self.course_path) > 1:
            line_pen = QPen(QColor("white"), 2, Qt.SolidLine)
            rounding_pen = QPen(QColor("#FFA500"), 2); rounding_brush = QBrush(QColor("#FFA500"))
            legs = set()
            for i in range(len(self.course_path)):
                if i < len(self.course_path) - 1:
                    start_node = self.course_path[i]; end_node = self.course_path[i+1]
                    pos1 = self._gps_to_screen(start_node['lat'], start_node['lon'], map_rect)
                    pos2 = self._gps_to_screen(end_node['lat'], end_node['lon'], map_rect)
                    if pos1 and pos2:
                        leg_id = tuple(sorted(((start_node['lat'], start_node['lon']), (end_node['lat'], end_node['lon']))))
                        offset_x = 0; offset_y = 0
                        if leg_id in legs:
                            line_vec_x = pos2.x() - pos1.x(); line_vec_y = pos2.y() - pos1.y()
                            norm = math.sqrt(line_vec_x**2 + line_vec_y**2)
                            if norm > 0:
                                perp_vec_x = -line_vec_y / norm; perp_vec_y = line_vec_x / norm
                                offset_x = perp_vec_x * 15; offset_y = perp_vec_y * 15
                        legs.add(leg_id)
                        offset_pos1 = QPointF(pos1.x() + offset_x, pos1.y() + offset_y)
                        offset_pos2 = QPointF(pos2.x() + offset_x, pos2.y() + offset_y)
                        painter.setPen(line_pen); painter.drawLine(offset_pos1, offset_pos2)
                        midpoint_arrow_head = QPolygonF([QPointF(0, 0), QPointF(-10, -5), QPointF(-10, 5)])
                        line_angle = math.atan2(offset_pos2.y() - offset_pos1.y(), offset_pos2.x() - offset_pos1.x())
                        mid_point = QPointF((offset_pos1.x() + offset_pos2.x()) / 2, (offset_pos1.y() + offset_pos2.y()) / 2)
                        painter.save(); painter.translate(mid_point); painter.rotate(math.degrees(line_angle))
                        painter.setBrush(QBrush(QColor("white"))); painter.drawPolygon(midpoint_arrow_head); painter.restore()
                if i > 0 and 'rounding_direction' in self.course_path[i]:
                    current_node = self.course_path[i]
                    pos2 = self._gps_to_screen(current_node['lat'], current_node['lon'], map_rect)
                    if pos2:
                        rounding_dir = current_node.get("rounding_direction", "Port"); rounding_char = "P" if rounding_dir == "Port" else "S"
                        font = QFont("Oxanium", 14, QFont.Bold); painter.setFont(font); painter.setPen(QColor("white"))
                        painter.drawText(pos2.x() -15, pos2.y() + 15, rounding_char)
        
        for buoy in self.buoys:
            pos=self._gps_to_screen(buoy['lat'],buoy['lon'],map_rect)
            if pos: painter.setBrush(QBrush(QColor("#000000"))); painter.setPen(QPen(QColor("white"), 3)); painter.drawEllipse(pos,6,6)
        
        if self.boat_position:
            boat_pos_screen=self._gps_to_screen(self.boat_position[0],self.boat_position[1],map_rect)
            if boat_pos_screen:
                painter.save(); painter.translate(boat_pos_screen); painter.rotate(self.boat_heading)
                boat_poly=QPolygonF([QPointF(0,-12),QPointF(8,10),QPointF(-8,10)])
                painter.setBrush(QBrush(QColor("#007acc"))); painter.setPen(Qt.NoPen); painter.drawPolygon(boat_poly); painter.restore()

    @Slot(float)
    def update_boat_heading(self,heading_deg): self.boat_heading=heading_deg; self.update()

class SmallArrowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle=0
        self.setFixedSize(QSize(63,63))
        self.arrow_color=QColor("white")
        self.arrow_polygon=QPolygonF([QPointF(0,-19),QPointF(13,6),QPointF(-13,6)])

    def setAngle(self,angle):
        if self.angle != angle: self.angle=angle; self.update()

    def paintEvent(self,event):
        painter=QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width()/2,self.height()/2)
        painter.rotate(self.angle)
        painter.setBrush(QBrush(self.arrow_color))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(self.arrow_polygon)

class BoatSpeedWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.max_speed=0.0
        self.min_speed=999.0
        layout=QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)
        self.title=QLabel("BOAT SPEED (kts)")
        self.speed_label=QLabel("---")
        max_min_layout=QGridLayout()
        max_min_layout.setContentsMargins(10, 0, 0, 0)
        self.max_label=QLabel("Max")
        self.max_speed_label=QLabel("---")
        self.min_label=QLabel("Min")
        self.min_speed_label=QLabel("---")
        max_min_layout.addWidget(self.max_label,0,0)
        max_min_layout.addWidget(self.max_speed_label,1,0)
        max_min_layout.addWidget(self.min_label,0,1)
        max_min_layout.addWidget(self.min_speed_label,1,1)
        layout.addWidget(self.title)
        layout.addWidget(self.speed_label)
        layout.addLayout(max_min_layout)
        layout.addStretch()

    def setTheme(self, theme):
        self.title.setStyleSheet(f"font-family: Oxanium; font-size: 24px; color: {theme['text_secondary']}; font-weight: bold;")
        self.speed_label.setStyleSheet(f"font-family: Oxanium; font-size: 110px; color: {theme['text_primary']}; font-weight: bold;")
        self.max_label.setStyleSheet(f"font-family: Oxanium; font-size: 20px; color: {theme['text_secondary']};")
        self.max_speed_label.setStyleSheet(f"font-family: Oxanium; font-size: 36px; color: {theme['text_primary']};")
        self.min_label.setStyleSheet(f"font-family: Oxanium; font-size: 20px; color: {theme['text_secondary']};")
        self.min_speed_label.setStyleSheet(f"font-family: Oxanium; font-size: 36px; color: {theme['text_primary']};")

    @Slot(float)
    def update_speed(self, speed_knots):
        self.speed_label.setText(f"{speed_knots:.1f}")
        if speed_knots > self.max_speed: self.max_speed=speed_knots; self.max_speed_label.setText(f"{self.max_speed:.1f}")
        if 0 < speed_knots < self.min_speed: self.min_speed=speed_knots; self.min_speed_label.setText(f"{self.min_speed:.1f}")

class RaceWindWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Use a QGridLayout for precise cell control
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(25) # Space between columns

        # --- Column 0: Wind Speed Section ---
        self.speed_title_label = QLabel("WIND SPEED")
        
        # Layout for the numeric speed and trend indicator
        speed_data_layout = QHBoxLayout()
        speed_data_layout.setContentsMargins(0,0,0,0)
        speed_data_layout.setSpacing(5)
        self.speed_label = QLabel("---")
        self.trend_label = QLabel("▲0")
        speed_data_layout.addWidget(self.speed_label)
        speed_data_layout.addWidget(self.trend_label, alignment=Qt.AlignBottom)
        speed_data_layout.addStretch()

        # Add speed widgets to the grid
        main_layout.addWidget(self.speed_title_label, 0, 0) # Row 0, Col 0
        main_layout.addLayout(speed_data_layout, 1, 0)     # Row 1, Col 0

        # --- Column 1: Wind Direction Section ---
        self.wind_dir_title_label = QLabel("WIND DIR")
        self.wind_dir_title_label.setAlignment(Qt.AlignCenter)
        
        # Layout for the arrow and direction letter
        direction_data_layout = QVBoxLayout()
        direction_data_layout.setContentsMargins(0,0,0,0)
        direction_data_layout.setSpacing(5)
        self.arrow_widget = SmallArrowWidget()
        self.direction_label = QLabel("N")
        self.direction_label.setAlignment(Qt.AlignCenter)
        direction_data_layout.addWidget(self.arrow_widget, alignment=Qt.AlignCenter)
        direction_data_layout.addWidget(self.direction_label)

        # Add direction widgets to the grid
        main_layout.addWidget(self.wind_dir_title_label, 0, 1, alignment=Qt.AlignCenter) # Row 0, Col 1
        main_layout.addLayout(direction_data_layout, 1, 1, alignment=Qt.AlignTop)      # Row 1, Col 1

        # --- Final layout adjustments ---
        main_layout.setRowStretch(2, 1)      # Pushes everything to the top
        main_layout.setColumnStretch(1, 1)   # Allows column 1 to expand slightly

    def setTheme(self, theme):
        # Apply stylesheets for precise styling
        self.speed_title_label.setStyleSheet(f"font-family: Oxanium; font-size: 24px; color: {theme['text_secondary']}; font-weight: bold;")
        self.speed_label.setStyleSheet(f"font-family: Oxanium; font-size: 64px; color: {theme['text_primary']}; font-weight: bold;")
        self.trend_label.setStyleSheet(f"font-family: Oxanium; font-size: 24px; color: {theme['text_secondary']}; font-weight: bold; padding-bottom: 5px;")
        
        self.wind_dir_title_label.setStyleSheet(f"font-family: Oxanium; font-size: 24px; color: {theme['text_secondary']}; font-weight: bold;")
        self.direction_label.setStyleSheet(f"font-family: Oxanium; font-size: 24px; color: {theme['text_secondary']}; font-weight: bold;")
        
        self.arrow_widget.arrow_color = QColor(theme['arrow'])
        self.arrow_widget.update()

    @Slot(float,float)
    def update_wind(self,speed_mps,angle_rad):
        speed_knots=speed_mps*1.94384
        angle_deg=math.degrees(angle_rad)
        dirs=["N","NE","E","SE","S","SW","W","NW"]
        idx=round(angle_deg/45)%8
        self.speed_label.setText(f"{speed_knots:.0f}")
        self.direction_label.setText(dirs[idx])
        self.arrow_widget.setAngle(angle_deg)

class RaceViewWidget(QWidget):
    def __init__(self):
        super().__init__()
        script_dir = os.path.dirname(__file__)
        self.races_base_path = os.path.abspath(os.path.join(script_dir, '..', '..', 'races'))
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        self.map_widget = RaceMapWidget()
        
        self.dist_to_start_widget = DataWidget("DIST TO START", "ft", title_size=20, value_size=36, unit_size=20)
        self.eta_to_start_widget = DataWidget("ETA TO START", "s", title_size=20, value_size=36, unit_size=20)
        
        self.load_shared_data()
        
        data_layout = QVBoxLayout()
        self.boat_speed_widget = BoatSpeedWidget()
        self.wind_widget = RaceWindWidget()
        
        start_line_layout = QGridLayout()
        start_line_layout.addWidget(self.dist_to_start_widget, 0, 0)
        start_line_layout.addWidget(self.eta_to_start_widget, 0, 1)

        data_layout.addStretch()
        data_layout.addWidget(self.boat_speed_widget)
        data_layout.addStretch(1)
        data_layout.addLayout(start_line_layout)
        data_layout.addStretch(1)
        data_layout.addWidget(self.wind_widget)
        data_layout.addStretch()

        main_layout.addWidget(self.map_widget, 2); main_layout.addLayout(data_layout, 1)
        self.map_widget.start_line_data_updated.connect(self.update_start_line_display)
        self.setTheme(False)

    @Slot(bool)
    def setTheme(self, is_light_mode):
        theme = LIGHT_THEME if is_light_mode else DARK_THEME
        self.dist_to_start_widget.setTheme(theme)
        self.eta_to_start_widget.setTheme(theme)
        self.boat_speed_widget.setTheme(theme)
        self.wind_widget.setTheme(theme)

    def load_shared_data(self):
        map_path = os.path.join(self.races_base_path, "shared_map.png")
        bounds_path = os.path.join(self.races_base_path, "shared_data.json")
        if os.path.exists(map_path): self.map_widget.map_pixmap = QPixmap(map_path)
        if os.path.exists(bounds_path):
            with open(bounds_path, 'r') as f: self.map_widget.bounds = json.load(f).get('bounds', {})
        self.map_widget.update()

    @Slot(str)
    def load_course(self, race_dir):
        data_path = os.path.join(self.races_base_path, race_dir, "race_data.json")
        buoys = []; race_name = ""; start_finish = None; course_path = []
        if os.path.exists(data_path):
            try:
                with open(data_path, 'r') as f:
                    race_data = json.load(f)
                    buoys = race_data.get('buoys', [])
                    race_name = race_data.get('name', '')
                    start_finish = race_data.get('start_finish_line', None)
                    if start_finish:
                        mid_lat = (start_finish['start']['lat'] + start_finish['end']['lat']) / 2
                        mid_lon = (start_finish['start']['lon'] + start_finish['end']['lon']) / 2
                        start_node = {'lat': mid_lat, 'lon': mid_lon}; finish_node = {'lat': mid_lat, 'lon': mid_lon}
                        course_path = [start_node] + buoys + [finish_node]
                    else: course_path = buoys
            except json.JSONDecodeError: print(f"Error decoding JSON from {data_path}")
        
        self.map_widget.buoys = buoys; self.map_widget.race_name = race_name
        self.map_widget.start_finish_line = start_finish
        self.map_widget.course_path = course_path
        self.map_widget.next_buoy_index = 0; self.map_widget.update()

    @Slot(float)
    def update_speed_display(self, speed_knots):
        self.boat_speed_widget.update_speed(speed_knots)
        self.map_widget.boat_speed_knots = speed_knots

    @Slot(float, float)
    def update_start_line_display(self, distance, eta):
        distance_ft = distance * 3.28084
        self.dist_to_start_widget.value_label.setText(f"{distance_ft:.0f}")
        # Format ETA into M:SS
        minutes, seconds = divmod(eta, 60)
        self.eta_to_start_widget.value_label.setText(f"{int(minutes)}:{int(seconds):02}")

    @Slot(float, float, str)
    def update_wind_display(self, speed_mps, angle_rad, reference):
        self.wind_widget.update_wind(speed_mps, angle_rad)