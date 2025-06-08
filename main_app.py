import sys
from PySide6.QtWidgets import QApplication

from nmea_reader import NMEA2000Reader
from sail_ui import SailUI
from dashboard_ui import DashboardUI
from bluetooth_manager import BluetoothManager

class MainApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        # ... (screen detection is unchanged)
        screens = self.app.screens()
        primary_screen = self.app.primaryScreen()
        secondary_screen = None
        if len(screens) > 1:
            for screen in screens:
                if screen != primary_screen:
                    secondary_screen = screen
                    break

        self.nmea_thread = NMEA2000Reader()
        self.bt_manager = BluetoothManager()
        self.sail_ui = SailUI()
        self.dashboard_ui = DashboardUI()

        # --- Connect Signals and Slots ---
        self.nmea_thread.wind_data_received.connect(self.sail_ui.update_wind_display)
        self.nmea_thread.depth_data_received.connect(self.sail_ui.update_depth_display)
        self.nmea_thread.speed_data_received.connect(self.sail_ui.update_speed_display)
        
        self.dashboard_ui.view_changed.connect(self.sail_ui.setView)
        self.dashboard_ui.theme_changed.connect(self.sail_ui.setTheme)
        
        # ** NEW BLUETOOTH CONNECTIONS **
        self.dashboard_ui.discoverable_clicked.connect(self.bt_manager.make_discoverable)
        self.bt_manager.connection_status_changed.connect(self.dashboard_ui.update_bluetooth_status)

        # --- Show Windows ---
        # ... (showing windows is unchanged)
        self.sail_ui.show()
        if primary_screen:
             self.sail_ui.move(primary_screen.geometry().topLeft())

        if secondary_screen and self.dashboard_ui:
            self.dashboard_ui.show()
            self.dashboard_ui.move(secondary_screen.geometry().topLeft())
        elif self.dashboard_ui:
            self.dashboard_ui.show()

        self.nmea_thread.start()

    def run(self):
        return self.app.exec()

    def cleanup(self):
        self.nmea_thread.stop()
        # self.bt_manager.stop_service() # No longer needed as it's not a service

if __name__ == "__main__":
    main_app = MainApplication()
    exit_code = main_app.run()
    main_app.cleanup()
    sys.exit(exit_code)