import sys
import math
import time

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsTextItem,
    QGraphicsLineItem
)
from PySide6.QtCore import QThread, Signal, Slot, Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QTransform, QPolygonF, QFont, QPainter, QPainterPath

# --- Conditional NMEA2000 Import ---
IS_RASPBERRY_PI = False # <--- REMEMBER TO SET THIS TO True FOR RASPBERRY PI DEPLOYMENT

if IS_RASPBERRY_PI:
    import can
    import NMEA2000_PY as n2k
    print("Using real NMEA2000_PY (for Raspberry Pi)")
else:
    from mock_nmea_data import MockNMEA2000
    print("Using MockNMEA2000 (for local development)")

# --- Utility Function: Haversine Distance ---
def haversine_distance(lat1_rad, lon1_rad, lat2_rad, lon2_rad):
    R = 6371000 # Earth radius in meters
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c # distance in meters
    return distance

# --- NMEA2000 Data Reader Thread ---
class NMEA2000Reader(QThread):
    wind_data_received = Signal(float, float, str)
    depth_data_received = Signal(float)
    speed_data_received = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bus = None
        self.n2k_parser = None
        self._running = True
        self.last_gps_pos = None
        self.last_gps_time = None

    def run(self):
        try:
            if IS_RASPBERRY_PI:
                self.bus = can.interface.Bus(channel='can0', bustype='socketcan')
                self.n2k_parser = n2k.NMEA2000(self.bus)
            else:
                self.n2k_parser = MockNMEA2000()

            self.n2k_parser.add_callback(130306, self._on_wind_data)
            self.n2k_parser.add_callback(128267, self._on_depth_data)
            self.n2k_parser.add_callback(129025, self._on_gps_data)

            self.n2k_parser.start()

            while self._running:
                self.msleep(100)
        except Exception as e:
            print(f"ERROR: NMEA2000 Thread encountered an error: {e}")
        finally:
            if self.n2k_parser:
                self.n2k_parser.stop()
            if self.bus:
                self.bus.shutdown()
            print("NMEA2000 thread stopped.")

    def stop(self):
        self._running = False

    @Slot(int, dict)
    def _on_wind_data(self, pgn, data):
        wind_speed_mps = data.get('WindSpeed')
        wind_angle_rad = data.get('WindAngle')
        wind_reference = data.get('Reference')
        if wind_speed_mps is not None and wind_angle_rad is not None:
            self.wind_data_received.emit(wind_speed_mps, wind_angle_rad, wind_reference)

    @Slot(int, dict)
    def _on_depth_data(self, pgn, data):
        depth_meters = data.get('Depth')
        if depth_meters is not None:
            self.depth_data_received.emit(depth_meters)

    @Slot(int, dict)
    def _on_gps_data(self, pgn, data):
        lat_rad = data.get('Latitude')
        lon_rad = data.get('Longitude')
        current_time = time.time()

        if lat_rad is not None and lon_rad is not None:
            current_pos_rad = (lat_rad, lon_rad)

            if self.last_gps_pos and self.last_gps_time:
                distance_m = haversine_distance(self.last_gps_pos[0], self.last_gps_pos[1],
                                                current_pos_rad[0], current_pos_rad[1])
                time_diff_s = current_time - self.last_gps_time

                if time_diff_s > 0.5:
                    speed_mps = distance_m / time_diff_s
                    speed_knots = speed_mps * 1.94384
                    self.speed_data_received.emit(speed_knots)

            self.last_gps_pos = current_pos_rad
            self.last_gps_time = current_time


# --- Wind Display UI ---
class WindDisplay(QWidget):
    def __init__(self):
        super().__init__()
        # Adjusted for 155mm x 87mm screen at ~100 DPI (610x343 pixels)
        self.setWindowTitle("Sail UI Display")
        self.setGeometry(100, 100, 610, 343)
        self.setStyleSheet("background-color: #282828; color: white;")

        main_grid_layout = QGridLayout(self)
        main_grid_layout.setContentsMargins(20, 20, 20, 20) # Reduced margins
        main_grid_layout.setSpacing(20) # Reduced spacing

        # --- Left Section: Wind Display (Boat Icon with Speed and Arcs) ---
        self.wind_scene = QGraphicsScene()
        self.wind_view = QGraphicsView(self.wind_scene)
        self.wind_view.setStyleSheet("background-color: transparent; border: none;")
        self.wind_view.setRenderHint(QPainter.Antialiasing)
        self.wind_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.wind_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Adjusted for smaller view size
        view_size = 220 # Scaled down from 300
        self.wind_scene.setSceneRect(-view_size/2, -view_size/2, view_size, view_size)

        # Boat Outline (with narrower bottom)
        boat_path = QPainterPath()
        boat_width = 65 # Scaled down from 110
        boat_height = 108 # Scaled down from 175

        side_curve_x_factor = 1.1
        side_curve_y_factor_top = -0.25
        side_curve_y_factor_bottom = 0

        bottom_width_factor = 0.70
        bottom_curve_control_x_factor = 0.4
        bottom_curve_offset_y = 10 # Scaled down from 15

        bottom_right_x = boat_width / 2 * bottom_width_factor
        bottom_left_x = -boat_width / 2 * bottom_width_factor
        bottom_cp1_x = bottom_right_x * bottom_curve_control_x_factor
        bottom_cp2_x = bottom_left_x * bottom_curve_control_x_factor
        bottom_cp_y = boat_height / 2 + bottom_curve_offset_y

        boat_path.moveTo(0, -boat_height / 2)
        boat_path.cubicTo(boat_width / 2 * side_curve_x_factor, boat_height * side_curve_y_factor_top,
                          boat_width / 2 * side_curve_x_factor, boat_height * side_curve_y_factor_bottom,
                          bottom_right_x, boat_height / 2)
        boat_path.cubicTo(bottom_cp1_x, bottom_cp_y,
                          bottom_cp2_x, bottom_cp_y,
                          bottom_left_x, boat_height / 2)
        boat_path.cubicTo(-boat_width / 2 * side_curve_x_factor, boat_height * side_curve_y_factor_bottom,
                          -boat_width / 2 * side_curve_x_factor, boat_height * side_curve_y_factor_top,
                          0, -boat_height / 2)

        self.boat_item = self.wind_scene.addPath(boat_path)
        self.boat_item.setPen(QPen(QColor(150, 150, 150), 3)) # Scaled down pen width from 5

        # Wind Speed Text inside the boat
        self.boat_wind_speed_text = self.wind_scene.addText("---")
        wind_speed_font = QFont("Inter", 48, QFont.Bold) # Scaled down font from 72
        self.boat_wind_speed_text.setFont(wind_speed_font)
        self.boat_wind_speed_text.setDefaultTextColor(QColor(255, 255, 255))

        # Add "kts" label below wind speed
        self.wind_speed_unit_text = self.wind_scene.addText("kts")
        kts_font = QFont("Inter", 12, QFont.Bold) # Scaled down font from 18
        self.wind_speed_unit_text.setFont(kts_font)
        self.wind_speed_unit_text.setDefaultTextColor(QColor(150, 150, 150))

        # Arc Indicators
        arc_radius = 63 # Scaled down from 125
        arc_width = 10 # Scaled down from 15
        arc_pen_red = QPen(QColor(255, 0, 0), arc_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        arc_pen_green = QPen(QColor(0, 255, 0), arc_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        arc_rect = QRectF(-arc_radius, -arc_radius, arc_radius * 2, arc_radius * 2)

        red_arc_path = QPainterPath()
        red_arc_path.arcMoveTo(arc_rect, 140)
        red_arc_path.arcTo(arc_rect, 140, -27)
        self.red_arc = self.wind_scene.addPath(red_arc_path, arc_pen_red)

        green_arc_path = QPainterPath()
        green_arc_path.arcMoveTo(arc_rect, 40)
        green_arc_path.arcTo(arc_rect, 40, 27)
        self.green_arc = self.wind_scene.addPath(green_arc_path, arc_pen_green)

        # Wind Direction Arrow
        arrow_offset_radius = arc_radius - 15 # Scaled down from 25
        arrow_length = 15 # Scaled down from 20
        arrow_pen = QPen(QColor(255, 255, 255), 8, Qt.SolidLine, Qt.RoundCap) # Scaled down pen width from 15

        start_x_arrow = arrow_offset_radius * math.sin(0)
        start_y_arrow = -arrow_offset_radius * math.cos(0)
        end_x_arrow = (arrow_offset_radius + arrow_length) * math.sin(0)
        end_y_arrow = -(arrow_offset_radius + arrow_length) * math.cos(0)

        self.wind_direction_arrow = QGraphicsLineItem(start_x_arrow, start_y_arrow, end_x_arrow, end_y_arrow)
        self.wind_direction_arrow.setPen(arrow_pen)
        self.wind_direction_arrow.setTransformOriginPoint(0,0)

        self.wind_scene.addItem(self.wind_direction_arrow)

        # Fit the scene into the view, keeping aspect ratio immediately after adding items
        self.wind_view.fitInView(self.wind_scene.sceneRect(), Qt.KeepAspectRatio)

        main_grid_layout.addWidget(self.wind_view, 0, 0, 2, 1)


        # --- Right Section: Depth and Speed Displays ---
        right_column_layout = QVBoxLayout()
        right_column_layout.setContentsMargins(0, 0, 0, 0)
        # Use setSpacing(0) here or a small number, as we'll use addSpacing for precise gaps
        right_column_layout.setSpacing(0) 

        # Add a stretch at the top to push content down and center it vertically
        right_column_layout.addStretch(1) 

        # Depth Display
        self.depth_title_label = QLabel("DEPTH")
        self.depth_title_label.setStyleSheet("font-size: 16px; color: grey; font-weight: bold;")
        self.depth_value_label = QLabel("---")
        self.depth_value_label.setStyleSheet("font-size: 55px; color: white; font-weight: bold;")
        self.depth_value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.depth_value_label.setFixedWidth(140)

        self.depth_unit_label = QLabel("ft")
        self.depth_unit_label.setStyleSheet("font-size: 16px; color: grey; font-weight: bold;")
        self.depth_unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        depth_layout = QVBoxLayout()
        depth_layout.setSpacing(2) # Spacing between title, value, and unit
        depth_layout.addWidget(self.depth_title_label)
        depth_layout.addWidget(self.depth_value_label)
        depth_layout.addSpacing(-8)
        depth_layout.addWidget(self.depth_unit_label)

        depth_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        right_column_layout.addLayout(depth_layout)

        # Add a fixed spacing between Depth and Speed
        # Adjust this value (e.g., 20, 30, 40) for the gap between the two data blocks
        right_column_layout.addSpacing(30) 

        # Speed Display
        self.speed_title_label = QLabel("SPEED")
        self.speed_title_label.setStyleSheet("font-size: 16px; color: grey; font-weight: bold;")
        self.speed_value_label = QLabel("---")
        self.speed_value_label.setStyleSheet("font-size: 55px; color: white; font-weight: bold;")
        self.speed_value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.speed_value_label.setFixedWidth(140)

        self.speed_unit_label = QLabel("kts")
        self.speed_unit_label.setStyleSheet("font-size: 16px; color: grey; font-weight: bold;")
        self.speed_unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        speed_layout = QVBoxLayout()
        speed_layout.setSpacing(2) # Spacing between title, value, and unit
        speed_layout.addWidget(self.speed_title_label)
        speed_layout.addWidget(self.speed_value_label)
        speed_layout.addSpacing(-8)
        speed_layout.addWidget(self.speed_unit_label)

        speed_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        right_column_layout.addLayout(speed_layout)

        # Add a stretch at the bottom to push content up and center it vertically
        right_column_layout.addStretch(1) 

        main_grid_layout.addLayout(right_column_layout, 0, 1, 2, 1)


        self.n2k_reader_thread = NMEA2000Reader()
        self.n2k_reader_thread.wind_data_received.connect(self.update_wind_display)
        self.n2k_reader_thread.depth_data_received.connect(self.update_depth_display)
        self.n2k_reader_thread.speed_data_received.connect(self.update_speed_display)
        self.n2k_reader_thread.start()

    def resizeEvent(self, event):
        self.wind_view.fitInView(self.wind_scene.sceneRect(), Qt.KeepAspectRatio)
        super().resizeEvent(event)

    @Slot(float, float, str)
    def update_wind_display(self, speed_mps, angle_rad, reference):
        speed_knots = speed_mps * 1.94384
        self.boat_wind_speed_text.setPlainText(f"{speed_knots:.0f}")

        current_speed_num_rect = self.boat_wind_speed_text.boundingRect()
        self.boat_wind_speed_text.setPos(-current_speed_num_rect.width()/2, -current_speed_num_rect.height()/2)

        kts_unit_rect = self.wind_speed_unit_text.boundingRect()
        kts_y_pos = current_speed_num_rect.height() / 2 + 5 # Small padding, needs careful adjustment for tiny screen
        self.wind_speed_unit_text.setPos(-kts_unit_rect.width()/2, kts_y_pos)

        angle_deg = math.degrees(angle_rad)
        self.wind_direction_arrow.setRotation(angle_deg)

        self.wind_scene.update()

    @Slot(float)
    def update_depth_display(self, depth_meters):
        depth_feet = depth_meters * 3.28084
        self.depth_value_label.setText(f"{depth_feet:.1f}")

    @Slot(float)
    def update_speed_display(self, speed_knots):
        self.speed_value_label.setText(f"{speed_knots:.1f}")

    def closeEvent(self, event):
        if self.n2k_reader_thread:
            self.n2k_reader_thread.stop()
            self.n2k_reader_thread.wait(5000)
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WindDisplay()
    window.show()
    sys.exit(app.exec())