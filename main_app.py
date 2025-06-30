# main_app.py
import sys
import platform
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer
IS_RASPBERRY_PI=platform.system()=="Linux"
if IS_RASPBERRY_PI: from epaper_display import EpaperDisplay
else: from mock_epaper_display import MockEpaperDisplay as EpaperDisplay
from nmea_reader import NMEA2000Reader
from sail_ui import SailUI
from dashboard_ui import DashboardUI
from bluetooth_manager import BluetoothManager

class MainApplication:
    def __init__(self):
        self.app=QApplication(sys.argv)
        primary_screen=self.app.primaryScreen()
        self.nmea_thread=NMEA2000Reader(); self.bt_manager=BluetoothManager()
        self.sail_ui=SailUI(); self.dashboard_ui=DashboardUI(); self.epaper=EpaperDisplay()
        self.connect_signals()
        self.dashboard_ui.show()
        if not IS_RASPBERRY_PI: self.sail_ui.show()
        if primary_screen: self.dashboard_ui.move(primary_screen.geometry().topLeft())
        if IS_RASPBERRY_PI:
            self.update_timer=QTimer(); self.update_timer.timeout.connect(self.update_epaper_display)
            self.update_timer.start(5000)
        self.nmea_thread.start()

    def connect_signals(self):
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

    def update_epaper_display(self):
        pixmap=QPixmap(self.sail_ui.size()); self.sail_ui.render(pixmap)
        from PIL import Image; qimage=pixmap.toImage(); buffer=qimage.bits().tobytes()
        pil_image=Image.frombytes("RGBA",(qimage.width(),qimage.height()),buffer,'raw',"RGBA")
        self.epaper.display_image(pil_image)
    def run(self): return self.app.exec()
    def cleanup(self):
        print("Cleaning up and stopping threads..."); self.nmea_thread.stop()
        if IS_RASPBERRY_PI: self.epaper.clear(); self.epaper.sleep()

if __name__=="__main__":
    main_app=MainApplication(); exit_code=main_app.run(); main_app.cleanup(); sys.exit(exit_code)