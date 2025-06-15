import sys
import math
import time
import struct

from PySide6.QtCore import QThread, Signal, Slot

# =================================================================
#  THE TOGGLE SWITCH:
#  Set to True to use the real CAN bus on the Raspberry Pi.
#  Set to False to use the fake data generator for UI testing.
# =================================================================
IS_RASPBERRY_PI = False 
# =================================================================

if IS_RASPBERRY_PI:
    import can
    print("Running in REAL DATA mode (for Raspberry Pi)")
else:
    from mock_nmea_data import MockNMEA2000
    print("Running in FAKE DATA mode (for local development)")

# --- Utility Function (remains the same) ---
def haversine_distance(lat1_rad, lon1_rad, lat2_rad, lon2_rad):
    R = 6371000
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# --- Custom NMEA 2000 Parser for real data ---
class NMEA2000Parser:
    def __init__(self):
        self.callbacks = {}

    def add_callback(self, pgn, func):
        self.callbacks[pgn] = func

    def handle_message(self, msg):
        pgn = (msg.arbitration_id >> 8) & 0x1FFFF
        if pgn in self.callbacks:
            try:
                data = self.parse_pgn(pgn, msg.data)
                if data:
                    self.callbacks[pgn](pgn, data)
            except Exception as e:
                print(f"Error parsing PGN {pgn}: {e}")

    def parse_pgn(self, pgn, data):
        # Note: This is a simplified parser. Real-world PGNs can be more complex.
        if pgn == 130306: # Wind Data
            if len(data) < 6: return None
            _, speed, angle, ref_raw = struct.unpack('<BHBB', data[:5])
            ref_int = ref_raw & 0x07
            ref_map = ["True (ground ref)", "Magnetic (ground ref)", "Apparent", "True (boat ref)", "True (water ref)"]
            return {'WindSpeed': speed * 0.01, 'WindAngle': angle * 0.0001, 'Reference': ref_map[ref_int] if ref_int < len(ref_map) else "Unknown"}
        elif pgn == 128267: # Water Depth
            if len(data) < 5: return None
            _, depth, _ = struct.unpack('<Bf', data[:5])
            return {'Depth': depth}
        elif pgn == 129025: # Position, Rapid Update
            if len(data) < 8: return None
            lat_deg, lon_deg = struct.unpack('<ii', data)
            return {'Latitude': math.radians(lat_deg * 1e-7), 'Longitude': math.radians(lon_deg * 1e-7)}
        return None

# --- Main Data Reader Thread ---
class NMEA2000Reader(QThread):
    wind_data_received = Signal(float, float, str)
    depth_data_received = Signal(float)
    speed_data_received = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bus = None
        self.notifier = None
        self._running = True
        self.last_gps_pos = None
        self.last_gps_time = None
        
        if IS_RASPBERRY_PI:
            self.n2k_parser = NMEA2000Parser()
            self.n2k_parser.add_callback(130306, self._on_wind_data)
            self.n2k_parser.add_callback(128267, self._on_depth_data)
            self.n2k_parser.add_callback(129025, self._on_gps_data)
        else:
            self.mock_n2k = MockNMEA2000()
            self.mock_n2k.add_callback(130306, self._on_wind_data)
            self.mock_n2k.add_callback(128267, self._on_depth_data)
            self.mock_n2k.add_callback(129025, self._on_gps_data)

    def run(self):
        try:
            if IS_RASPBERRY_PI:
                self.bus = can.interface.Bus(channel='can0', bustype='socketcan')
                self.notifier = can.Notifier(self.bus, [self.n2k_parser.handle_message])
            else:
                self.mock_n2k.start()

            print("NMEA2000 thread started successfully.")
            while self._running:
                self.msleep(1000)

        except Exception as e:
            print(f"ERROR: NMEA2000 Thread encountered an error: {e}")
        finally:
            if self.notifier:
                self.notifier.stop()
            if hasattr(self, 'mock_n2k'):
                self.mock_n2k.stop()
            if self.bus:
                self.bus.shutdown()
            print("NMEA2000 thread stopped.")

    def stop(self):
        self._running = False
        self.wait(2000)

    @Slot(int, dict)
    def _on_wind_data(self, pgn, data):
        # This slot now receives data from EITHER the real parser OR the mock generator
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
                distance_m = haversine_distance(self.last_gps_pos[0], self.last_gps_pos[1], current_pos_rad[0], current_pos_rad[1])
                time_diff_s = current_time - self.last_gps_time
                if time_diff_s > 0.5:
                    speed_mps = distance_m / time_diff_s
                    speed_knots = speed_mps * 1.94384
                    self.speed_data_received.emit(speed_knots)
            self.last_gps_pos = current_pos_rad
            self.last_gps_time = current_time