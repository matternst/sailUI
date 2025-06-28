# main_app.py

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer

# Make sure all your custom modules are imported
from nmea_reader import NMEA2000Reader
from sail_ui import SailUI
from dashboard_ui import DashboardUI
from bluetooth_manager import BluetoothManager
from epaper_display import EpaperDisplay # Import the new EpaperDisplay class

class MainApplication:
    def __init__(self):
        """Initializes the main application, UI windows, and connections."""
        self.app = QApplication(sys.argv)

        # --- Screen Detection ---
        screens = self.app.screens()
        primary_screen = self.app.primaryScreen()
        secondary_screen = None
        if len(screens) > 1:
            for screen in screens:
                if screen != primary_screen:
                    secondary_screen = screen
                    break

        # --- Initialize Core Components & UI ---
        self.nmea_thread = NMEA2000Reader()
        self.bt_manager = BluetoothManager()
        self.sail_ui = SailUI()
        self.dashboard_ui = DashboardUI()
        
        # --- Initialize E-Paper Display ---
        self.epaper = EpaperDisplay()

        # --- Connect Signals and Slots ---
        # (Your existing signal and slot connections remain the same)
        self.nmea_thread.wind_data_received.connect(self.sail_ui.update_wind_display)
        self.nmea_thread.depth_data_received.connect(self.sail_ui.update_depth_display)
        self.nmea_thread.speed_data_received.connect(self.sail_ui.update_speed_display)
        
        self.dashboard_ui.view_changed.connect(self.sail_ui.setView)
        self.dashboard_ui.theme_changed.connect(self.sail_ui.setTheme)
        
        self.dashboard_ui.discoverable_clicked.connect(self.bt_manager.make_discoverable)
        self.bt_manager.connection_status_changed.connect(self.dashboard_ui.update_bluetooth_status)

        self.dashboard_ui.exit_app_clicked.connect(self.app.quit)

        self.sail_ui.escape_pressed.connect(self.app.quit)
        self.dashboard_ui.escape_pressed.connect(self.app.quit)

        # --- Show Windows ---
        # The dashboard will now be the primary UI on the main monitor
        self.dashboard_ui.show()

        if primary_screen:
            self.dashboard_ui.move(primary_screen.geometry().topLeft())
        
        # --- Timer to update the e-paper display ---
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_epaper_display)
        self.update_timer.start(5000) # Update every 5 seconds

        # Start reading NMEA data
        self.nmea_thread.start()

    def update_epaper_display(self):
        """Renders the SailUI to an image and displays it on the e-paper."""
        pixmap = QPixmap(self.sail_ui.size())
        self.sail_ui.render(pixmap)
        
        # Convert QPixmap to PIL Image
        qimage = pixmap.toImage()
        buffer = qimage.bits().tobytes()
        pil_image = Image.frombytes("RGBA", (qimage.width(), qimage.height()), buffer, 'raw', "RGBA")
        
        # Display the image
        self.epaper.display_image(pil_image)


    def run(self):
        """Executes the application's main loop."""
        return self.app.exec()

    def cleanup(self):
        """Stops background threads and clears the e-paper display."""
        print("Cleaning up and stopping threads...")
        self.nmea_thread.stop()
        self.epaper.clear()
        self.epaper.sleep()


if __name__ == "__main__":
    main_app = MainApplication()
    exit_code = main_app.run()
    main_app.cleanup()
    sys.exit(exit_code)