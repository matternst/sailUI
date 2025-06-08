import sys
from PySide6.QtWidgets import QApplication

# Make sure all your custom modules are imported
from nmea_reader import NMEA2000Reader
from sail_ui import SailUI
from dashboard_ui import DashboardUI
from bluetooth_manager import BluetoothManager

class MainApplication:
    def __init__(self):
        """Initializes the main application, UI windows, and connections."""
        self.app = QApplication(sys.argv)

        # --- Screen Detection ---
        # This logic detects primary and secondary displays to position windows
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

        # --- Connect Signals and Slots ---
        # Connect NMEA data to the main sailing UI
        self.nmea_thread.wind_data_received.connect(self.sail_ui.update_wind_display)
        self.nmea_thread.depth_data_received.connect(self.sail_ui.update_depth_display)
        self.nmea_thread.speed_data_received.connect(self.sail_ui.update_speed_display)
        
        # Connect dashboard controls to the main sailing UI
        self.dashboard_ui.view_changed.connect(self.sail_ui.setView)
        self.dashboard_ui.theme_changed.connect(self.sail_ui.setTheme)
        
        # Connect dashboard bluetooth controls to the bluetooth manager
        self.dashboard_ui.discoverable_clicked.connect(self.bt_manager.make_discoverable)
        self.bt_manager.connection_status_changed.connect(self.dashboard_ui.update_bluetooth_status)

        # Connect the exit button from the dashboard to the application's quit method
        self.dashboard_ui.exit_app_clicked.connect(self.app.quit)

        # Connect the Escape key press from the main UI to the application's quit method
        self.sail_ui.escape_pressed.connect(self.app.quit)
        self.dashboard_ui.escape_pressed.connect(self.app.quit)

        # --- Show Windows on Appropriate Screens ---
        self.sail_ui.show()
        if primary_screen:
             # Move the main UI to the primary screen
             self.sail_ui.move(primary_screen.geometry().topLeft())

        if self.dashboard_ui:
            self.dashboard_ui.show()
            if secondary_screen:
                # If a second screen exists, move the dashboard there
                self.dashboard_ui.move(secondary_screen.geometry().topLeft())

        # Start reading NMEA data
        self.nmea_thread.start()

    def run(self):
        """Executes the application's main loop."""
        return self.app.exec()

    def cleanup(self):
        """Stops background threads cleanly."""
        print("Cleaning up and stopping threads...")
        self.nmea_thread.stop()

if __name__ == "__main__":
    main_app = MainApplication()
    exit_code = main_app.run()
    main_app.cleanup()
    sys.exit(exit_code)
