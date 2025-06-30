# views/standard_view.py
import math
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene,
    QGraphicsLineItem
)
from PySide6.QtCore import Qt, QRectF, Slot
from PySide6.QtGui import QColor, QPen, QFont, QPainter, QPainterPath

from theme import LIGHT_THEME, DARK_THEME

class StandardSailView(QWidget):
    def __init__(self):
        super().__init__()
        main_grid_layout = QGridLayout(self)
        main_grid_layout.setContentsMargins(0, 20, 40, 20)
        main_grid_layout.setSpacing(10)

        # --- Left Section: Wind Display ---
        self.wind_scene = QGraphicsScene()
        self.wind_view = QGraphicsView(self.wind_scene)
        self.wind_view.setStyleSheet("background-color: transparent; border: none;")
        self.wind_view.setRenderHint(QPainter.Antialiasing)
        self.wind_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.wind_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view_size = 220
        self.wind_scene.setSceneRect(-view_size/2, -view_size/2, view_size, view_size)
        boat_path = QPainterPath()
        boat_width, boat_height = 65, 108
        bottom_right_x = boat_width / 2 * 0.70
        bottom_left_x = -boat_width / 2 * 0.70
        boat_path.moveTo(0, -boat_height / 2)
        boat_path.cubicTo(boat_width / 2 * 1.1, boat_height * -0.25, boat_width / 2 * 1.1, 0, bottom_right_x, boat_height / 2)
        boat_path.cubicTo(bottom_right_x * 0.4, boat_height / 2 + 10, bottom_left_x * 0.4, boat_height / 2 + 10, bottom_left_x, boat_height / 2)
        boat_path.cubicTo(-boat_width / 2 * 1.1, 0, -boat_width / 2 * 1.1, boat_height * -0.25, 0, -boat_height / 2)
        self.boat_item = self.wind_scene.addPath(boat_path)
        self.boat_wind_speed_text = self.wind_scene.addText("---")
        self.boat_wind_speed_text.setFont(QFont("Oxanium", 40, QFont.Bold))
        self.wind_speed_unit_text = self.wind_scene.addText("kts")
        self.wind_speed_unit_text.setFont(QFont("Oxanium", 10, QFont.Bold))
        arc_radius, arc_width = 63, 10
        arc_rect = QRectF(-arc_radius, -arc_radius, arc_radius * 2, arc_radius * 2)
        red_arc_path = QPainterPath()
        red_arc_path.arcMoveTo(arc_rect, 140)
        red_arc_path.arcTo(arc_rect, 140, -27)
        self.red_arc = self.wind_scene.addPath(red_arc_path, QPen(QColor(255, 0, 0), arc_width, Qt.SolidLine, Qt.RoundCap))
        green_arc_path = QPainterPath()
        green_arc_path.arcMoveTo(arc_rect, 40)
        green_arc_path.arcTo(arc_rect, 40, 27)
        self.green_arc = self.wind_scene.addPath(green_arc_path, QPen(QColor(0, 255, 0), arc_width, Qt.SolidLine, Qt.RoundCap))
        arrow_offset_radius, arrow_length = arc_radius - 15, 15
        self.wind_direction_arrow = QGraphicsLineItem(0, -arrow_offset_radius, 0, -(arrow_offset_radius + arrow_length))
        self.wind_direction_arrow.setTransformOriginPoint(0,0)
        self.wind_scene.addItem(self.wind_direction_arrow)
        self.wind_view.fitInView(self.wind_scene.sceneRect(), Qt.KeepAspectRatio)
        main_grid_layout.addWidget(self.wind_view, 0, 0, 2, 1)

        # --- Right Section: Depth and Speed Displays ---
        right_column_layout = QVBoxLayout()
        right_column_layout.setContentsMargins(0, 0, 0, 0)
        right_column_layout.setSpacing(0)
        right_column_layout.addStretch(1)
        self.depth_title_label = QLabel("DEPTH")
        self.depth_value_label = QLabel("---")
        self.depth_value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.depth_value_label.setFixedWidth(140)
        self.depth_unit_label = QLabel("ft")
        self.depth_unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        depth_layout = QVBoxLayout()
        depth_layout.setSpacing(2)
        depth_layout.addWidget(self.depth_title_label)
        depth_layout.addWidget(self.depth_value_label)
        depth_layout.addSpacing(-8)
        depth_layout.addWidget(self.depth_unit_label)
        depth_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        right_column_layout.addLayout(depth_layout)
        right_column_layout.addSpacing(30)
        self.speed_title_label = QLabel("SPEED")
        self.speed_value_label = QLabel("---")
        self.speed_value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.speed_value_label.setFixedWidth(140)
        self.speed_unit_label = QLabel("kts")
        self.speed_unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        speed_layout = QVBoxLayout()
        speed_layout.setSpacing(2)
        speed_layout.addWidget(self.speed_title_label)
        speed_layout.addWidget(self.speed_value_label)
        speed_layout.addSpacing(-8)
        speed_layout.addWidget(self.speed_unit_label)
        speed_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        right_column_layout.addLayout(speed_layout)
        right_column_layout.addStretch(1)
        main_grid_layout.addLayout(right_column_layout, 0, 1, 2, 1)
        
        self.setTheme(False)

    @Slot(bool)
    def setTheme(self, is_light_mode):
        theme = LIGHT_THEME if is_light_mode else DARK_THEME
        
        self.depth_title_label.setStyleSheet(f"font-family: Oxanium; font-size: 20px; color: {theme['text_secondary']}; font-weight: bold;")
        self.depth_value_label.setStyleSheet(f"font-family: Oxanium; font-size: 70px; color: {theme['text_primary']}; font-weight: bold;")
        self.depth_unit_label.setStyleSheet(f"font-family: Oxanium; font-size: 20px; color: {theme['text_secondary']}; font-weight: bold;")
        self.speed_title_label.setStyleSheet(f"font-family: Oxanium; font-size: 20px; color: {theme['text_secondary']}; font-weight: bold;")
        self.speed_value_label.setStyleSheet(f"font-family: Oxanium; font-size: 70px; color: {theme['text_primary']}; font-weight: bold;")
        self.speed_unit_label.setStyleSheet(f"font-family: Oxanium; font-size: 20px; color: {theme['text_secondary']}; font-weight: bold;")

        self.boat_item.setPen(QPen(theme['boat'], 3))
        self.wind_direction_arrow.setPen(QPen(theme['arrow'], 8, Qt.SolidLine, Qt.RoundCap))
        self.boat_wind_speed_text.setDefaultTextColor(QColor(theme['text_primary']))
        self.wind_speed_unit_text.setDefaultTextColor(QColor(theme['text_secondary']))

    @Slot(float, float, str)
    def update_wind_display(self, speed_mps, angle_rad, reference):
        speed_knots = speed_mps * 1.94384
        self.boat_wind_speed_text.setPlainText(f"{speed_knots:.0f}")
        y_offset = 10 
        current_speed_num_rect = self.boat_wind_speed_text.boundingRect()
        self.boat_wind_speed_text.setPos(
            -current_speed_num_rect.width() / 2,
            -current_speed_num_rect.height() / 2 + y_offset
        )
        kts_unit_rect = self.wind_speed_unit_text.boundingRect()
        kts_y_pos = current_speed_num_rect.height() / 2 + 5
        self.wind_speed_unit_text.setPos(
            -kts_unit_rect.width() / 2,
            kts_y_pos + y_offset/2
        )
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