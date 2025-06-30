from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Slot, Signal, Qt
from PySide6.QtGui import QKeyEvent

# Import the view widgets
from views.standard_view import StandardSailView
from views.no_wind_arrow_view import NoWindArrowView
from views.race.race_view_widget import RaceViewWidget

# Import themes from the dedicated theme.py file
from theme import LIGHT_THEME, DARK_THEME


class SailUI(QWidget):
    escape_pressed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sail UI Display")
        self.setGeometry(100, 100, 1024, 600)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Create instances of our views ---
        self.standard_view = StandardSailView()
        self.no_wind_arrow_view = NoWindArrowView()
        self.race_view = RaceViewWidget()

        # --- The stacked widget now manages the imported views ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.standard_view)
        self.stacked_widget.addWidget(self.no_wind_arrow_view)
        self.stacked_widget.addWidget(self.race_view)

        self.main_layout.addWidget(self.stacked_widget)
        self.setTheme(False)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.escape_pressed.emit()
        else:
            super().keyPressEvent(event)

    @Slot(int)
    def setView(self, index):
        if index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)

    @Slot(bool)
    def setTheme(self, is_light_mode):
        theme = LIGHT_THEME if is_light_mode else DARK_THEME
        self.setStyleSheet(f"background-color: {theme['bg']};")
        # Pass the theme change to all child views that support it
        if hasattr(self.standard_view, 'setTheme'):
            self.standard_view.setTheme(is_light_mode)

    # --- Data Passthrough Slots ---
    @Slot(float, float, str)
    def update_wind_display(self, speed_mps, angle_rad, reference):
        self.standard_view.update_wind_display(speed_mps, angle_rad, reference)
        self.race_view.update_wind_display(speed_mps, angle_rad, reference)

    @Slot(float)
    def update_depth_display(self, depth_meters):
        self.standard_view.update_depth_display(depth_meters)

    @Slot(float)
    def update_speed_display(self, speed_knots):
        self.standard_view.update_speed_display(speed_knots)
        self.race_view.update_speed_display(speed_knots)