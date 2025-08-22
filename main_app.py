# main_app.py
import sys
import platform
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QTimer, Slot
from PIL import Image

from log_manager import LogManager
from nmea_reader import NMEA2000Reader
from sail_ui import SailUI
from dashboard_ui import DashboardUI
from bluetooth_manager import BluetoothManager

# Import the new server and shared image components
from shared_image import SharedImage
from image_server import create_image_server, run_server

class MainApplication:
    def __init__(self):
        """Initializes the main application, UI windows, and connections."""
        self.app=QApplication(sys.argv)
        primary_screen=self.app.primaryScreen()
        
        self.log_manager = LogManager()
        self.nmea_thread=NMEA2000Reader(self.log_manager)
        self.bt_manager=BluetoothManager()
        self.sail_ui=SailUI()
        self.dashboard_ui=DashboardUI()

        # --- New Server Setup ---
        self.shared_image = SharedImage()
        self.image_server_app = create_image_server(self.shared_image)
        run_server(self.image_server_app) # Start the server in a background thread

        self.connect_signals()
        self.dashboard_ui.show()
        
        # The sail_ui no longer needs to be shown on the Pi 4, but it's useful for debugging on a PC
        if platform.system() != "Linux":
            self.sail_ui.show()

        if primary_screen: self.dashboard_ui.move(primary_screen.geometry().topLeft())
        
        # This timer now updates the shared image, not a physical display
        self.update_timer=QTimer()
        self.update_timer.timeout.connect(self.update_shared_image)
        self.update_timer.start(5000) # Update image every 5 seconds

        self.nmea_thread.start()
        self.dashboard_ui.populate_log_table(self.log_manager.get_all_trips())

    def connect_signals(self):
        """Connects all the signals and slots between components."""
        map_widget = self.sail_ui.race_view.map_widget
        self.dashboard_ui.show_test_banner_requested.connect(map_widget.show_test_banner)
        self.dashboard_ui.hide_test_banner_requested.connect(map_widget.hide_test_banner)
        self.sail_ui.show_test_banner_requested.connect(map_widget.show_test_banner)
        self.sail_ui.hide_test_banner_requested.connect(map_widget.hide_test_banner)
        self.nmea_thread.wind_data_received.connect(self.sail_ui.update_wind_display)
        self.nmea_thread.depth_data_received.connect(self.sail_ui.update_depth_display)
        self.nmea_thread.speed_data_received.connect(self.sail_ui.update_speed_display)
        self.nmea_thread.wind_data_received.connect(self.dashboard_ui.update_wind_display)
        self.nmea_thread.depth_data_received.connect(self.dashboard_ui.update_depth_display)
        self.nmea_thread.pressure_data_received.connect(self.dashboard_ui.update_pressure_display)
        self.nmea_thread.trip_data_received.connect(self.dashboard_ui.update_trip_display)
        self.dashboard_ui.theme_changed.connect(self.sail_ui.setTheme)
        self.dashboard_ui.ui_config_list.currentRowChanged.connect(self.sail_ui.setView)
        self.dashboard_ui.race_selected.connect(self.sail_ui.load_race_course)
        self.dashboard_ui.discoverable_clicked.connect(self.bt_manager.make_discoverable)
        self.bt_manager.connection_status_changed.connect(self.dashboard_ui.update_bluetooth_status)
        self.nmea_thread.position_data_received.connect(map_widget.update_boat_position)
        self.nmea_thread.position_data_received.connect(self.dashboard_ui.update_position_display)
        self.nmea_thread.heading_data_received.connect(map_widget.update_boat_heading)
        self.nmea_thread.heading_data_received.connect(self.dashboard_ui.update_heading_display)
        self.dashboard_ui.exit_app_clicked.connect(self.app.quit)
        self.sail_ui.escape_pressed.connect(self.app.quit)
        self.dashboard_ui.escape_pressed.connect(self.app.quit)
        self.dashboard_ui.delete_trip_requested.connect(self.delete_trip)
        self.dashboard_ui.set_people_requested.connect(self.set_people)
        self.dashboard_ui.trip_type_changed.connect(self.set_trip_type)
        self.dashboard_ui.trip_course_changed.connect(self.set_trip_course)
        self.dashboard_ui.anchor_drift_alarm.connect(self.dashboard_ui.on_anchor_drift_alarm)

    def update_shared_image(self):
        """Renders the SailUI to an image and places it in the shared buffer."""
        pixmap=QPixmap(self.sail_ui.size())
        self.sail_ui.render(pixmap)
        
        qimage=pixmap.toImage()
        # Ensure the format is RGBA for consistency
        qimage = qimage.convertToFormat(QImage.Format_RGBA8888)

        buffer=qimage.bits().tobytes()
        pil_image=Image.frombytes("RGBA",(qimage.width(),qimage.height()),buffer,'raw',"RGBA")
        
        # Convert to black and white for the e-ink display
        bw_image = pil_image.convert("1")
        
        self.shared_image.update_image(bw_image)
        print("Updated shared image buffer.") # Uncomment for debugging

    def run(self):
        """Executes the application's main loop."""
        return self.app.exec()

    def cleanup(self):
        """Stops background threads."""
        print("Cleaning up and stopping threads...")
        self.nmea_thread.stop()

    @Slot(str)
    def delete_trip(self, trip_id):
        self.log_manager.delete_trip(trip_id)
        self.dashboard_ui.populate_log_table(self.log_manager.get_all_trips())

    @Slot(str, int)
    def set_people(self, trip_id, num_people):
        self.log_manager.set_people(trip_id, num_people)
        self.dashboard_ui.populate_log_table(self.log_manager.get_all_trips())

    @Slot(str)
    def set_trip_type(self, trip_type):
        self.log_manager.set_trip_type(trip_type)

    @Slot(str)
    def set_trip_course(self, course_name):
        self.log_manager.set_trip_course(course_name)

if __name__=="__main__":
    main_app=MainApplication()
    exit_code=main_app.run()
    main_app.cleanup()
    sys.exit(exit_code)

