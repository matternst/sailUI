import sys
import platform
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QTimer

# --- Platform-specific imports ---
IS_RASPBERRY_PI = platform.system() == "Linux"

if IS_RASPBERRY_PI:
    from epaper_display import EpaperDisplay
else:
    # On non-Pi systems (like your Mac), import the mock display
    from mock_epaper_display import MockEpaperDisplay as EpaperDisplay

# --- Core Module Imports ---
from nmea_reader import NMEA2000Reader
from sail_ui import SailUI
from dashboard_ui import DashboardUI
from bluetooth_manager import BluetoothManager


class MainApplication:
    def __init__(self):
        """Initializes the main application, UI windows, and connections."""
        self.app = QApplication(sys.argv)

        # --- Screen Detection ---
        primary_screen = self.app.primaryScreen()

        # --- Initialize Core Components & UI ---
        self.nmea_thread = NMEA2000Reader()
        self.bt_manager = BluetoothManager()
        self.sail_ui = SailUI()
        self.dashboard_ui = DashboardUI()
        
        # --- Initialize E-Paper Display (real or mock) ---
        self.epaper = EpaperDisplay()

        # --- Connect NMEA data to Sail UI ---
        self.nmea_thread.wind_data_received.connect(self.sail_ui.update_wind_display)
        self.nmea_thread.depth_data_received.connect(self.sail_ui.update_depth_display)
        self.nmea_thread.speed_data_received.connect(self.sail_ui.update_speed_display)

        # --- Connect NMEA data to Dashboard UI ---
        self.nmea_thread.wind_data_received.connect(self.dashboard_ui.update_wind_display)
        self.nmea_thread.depth_data_received.connect(self.dashboard_ui.update_depth_display)
        self.nmea_thread.pressure_data_received.connect(self.dashboard_ui.update_pressure_display)
        self.nmea_thread.heading_data_received.connect(self.dashboard_ui.update_heading_display)
        self.nmea_thread.position_data_received.connect(self.dashboard_ui.update_position_display)
        self.nmea_thread.trip_data_received.connect(self.dashboard_ui.update_trip_display)
        
        # --- Connect Dashboard controls ---
        self.dashboard_ui.theme_changed.connect(self.sail_ui.setTheme)
        self.dashboard_ui.ui_config_list.currentRowChanged.connect(self.sail_ui.setView)
        self.dashboard_ui.discoverable_clicked.connect(self.bt_manager.make_discoverable)
        self.bt_manager.connection_status_changed.connect(self.dashboard_ui.update_bluetooth_status)

        # --- Connect Exit signals ---
        self.dashboard_ui.exit_app_clicked.connect(self.app.quit)
        self.sail_ui.escape_pressed.connect(self.app.quit)
        self.dashboard_ui.escape_pressed.connect(self.app.quit)

        # --- Show Windows ---
        self.dashboard_ui.show()
        if not IS_RASPBERRY_PI:
             self.sail_ui.show()

        if primary_screen:
            self.dashboard_ui.move(primary_screen.geometry().topLeft())
        
        # --- Timer to update the e-paper display ---
        if IS_RASPBERRY_PI:
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_epaper_display)
            self.update_timer.start(5000)

        # Start reading NMEA data
        self.nmea_thread.start()

    def update_epaper_display(self):
        """Renders the SailUI to an image and displays it on the e-paper."""
        pixmap = QPixmap(self.sail_ui.size())
        self.sail_ui.render(pixmap)
        
        qimage = pixmap.toImage()
        buffer = qimage.bits().tobytes()
        
        from PIL import Image
        pil_image = Image.frombytes("RGBA", (qimage.width(), qimage.height()), buffer, 'raw', "RGBA")
        
        self.epaper.display_image(pil_image)

    def run(self):
        """Executes the application's main loop."""
        return self.app.exec()

    def cleanup(self):
        """Stops background threads and clears the e-paper display."""
        print("Cleaning up and stopping threads...")
        self.nmea_thread.stop()
        if IS_RASPBERRY_PI:
            self.epaper.clear()
            self.epaper.sleep()

if __name__ == "__main__":
    main_app = MainApplication()
    exit_code = main_app.run()
    main_app.cleanup()
    sys.exit(exit_code)