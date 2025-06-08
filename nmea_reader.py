import sys
import math
import time

from PySide6.QtCore import QThread, Signal, Slot

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
        self.wait(2000)

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