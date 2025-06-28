import sys
import math
import time
import struct
from PySide6.QtCore import QThread, Signal, Slot

IS_RASPBERRY_PI = False 
if IS_RASPBERRY_PI:
    import can
else:
    from mock_nmea_data import MockNMEA2000

def haversine_distance(lat1_rad, lon1_rad, lat2_rad, lon2_rad):
    R = 6371000
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_bearing(lat1_rad, lon1_rad, lat2_rad, lon2_rad):
    dLon = lon2_rad - lon1_rad
    y = math.sin(dLon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dLon)
    bearing_rad = math.atan2(y, x)
    return (math.degrees(bearing_rad) + 360) % 360

class NMEA2000Parser:
    def __init__(self): self.callbacks = {}
    def add_callback(self, pgn, func): self.callbacks[pgn] = func
    def handle_message(self, msg):
        pgn = (msg.arbitration_id >> 8) & 0x1FFFF
        if pgn in self.callbacks:
            data = self.parse_pgn(pgn, msg.data)
            if data: self.callbacks[pgn](pgn, data)
    def parse_pgn(self, pgn, data):
        if pgn == 130306: # Wind
            _, speed, angle, ref_raw = struct.unpack('<BHBB', data[:5])
            ref_map = ["True (ground ref)", "Magnetic (ground ref)", "Apparent"]
            return {'WindSpeed': speed * 0.01, 'WindAngle': angle * 0.0001, 'Reference': ref_map[ref_raw & 0x07]}
        elif pgn == 128267: # Depth
            _, depth, _ = struct.unpack('<Bf', data[:5])
            return {'Depth': depth}
        elif pgn == 129025: # Position
            lat_deg, lon_deg = struct.unpack('<ii', data)
            return {'Latitude': math.radians(lat_deg * 1e-7), 'Longitude': math.radians(lon_deg * 1e-7)}
        elif pgn == 130314: # Pressure
            _, _, pressure_hpa, _ = struct.unpack('<BBHB', data[:5])
            return {'Pressure': pressure_hpa * 100} # hPa to Pa
        return None

class NMEA2000Reader(QThread):
    wind_data_received = Signal(float, float, str)
    depth_data_received = Signal(float)
    speed_data_received = Signal(float)
    position_data_received = Signal(float, float)
    heading_data_received = Signal(float)
    pressure_data_received = Signal(float)
    trip_data_received = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self.last_gps_pos = None
        self.last_gps_time = None
        self.total_distance_m = 0.0
        self.start_time = time.time()
        
        if IS_RASPBERRY_PI:
            self.n2k_parser = NMEA2000Parser()
            self.bus = None
            self.notifier = None
        else:
            self.mock_n2k = MockNMEA2000()
        
        self.setup_callbacks()

    def setup_callbacks(self):
        callbacks = {
            130306: self._on_wind_data,
            128267: self._on_depth_data,
            129025: self._on_gps_data,
            130314: self._on_pressure_data
        }
        if IS_RASPBERRY_PI:
            for pgn, func in callbacks.items(): self.n2k_parser.add_callback(pgn, func)
        else:
            for pgn, func in callbacks.items(): self.mock_n2k.add_callback(pgn, func)

    def run(self):
        try:
            if IS_RASPBERRY_PI:
                self.bus = can.interface.Bus(channel='can0', bustype='socketcan')
                self.notifier = can.Notifier(self.bus, [self.n2k_parser.handle_message])
            else:
                self.mock_n2k.start()
            while self._running: self.msleep(1000)
        finally:
            if IS_RASPBERRY_PI:
                if self.notifier: self.notifier.stop()
                if self.bus: self.bus.shutdown()
            else:
                self.mock_n2k.stop()
            print("NMEA2000 thread stopped.")

    def stop(self):
        self._running = False
        self.wait(2000)

    @Slot(int, dict)
    def _on_wind_data(self, pgn, data):
        self.wind_data_received.emit(data['WindSpeed'], data['WindAngle'], data['Reference'])

    @Slot(int, dict)
    def _on_depth_data(self, pgn, data):
        self.depth_data_received.emit(data['Depth'])

    @Slot(int, dict)
    def _on_pressure_data(self, pgn, data):
        self.pressure_data_received.emit(data['Pressure'])

    @Slot(int, dict)
    def _on_gps_data(self, pgn, data):
        lat_rad, lon_rad = data['Latitude'], data['Longitude']
        current_time = time.time()
        current_pos_rad = (lat_rad, lon_rad)

        if self.last_gps_pos and self.last_gps_time:
            distance_m = haversine_distance(self.last_gps_pos[0], self.last_gps_pos[1], current_pos_rad[0], current_pos_rad[1])
            time_diff_s = current_time - self.last_gps_time
            if time_diff_s > 0.5:
                speed_mps = distance_m / time_diff_s
                self.speed_data_received.emit(speed_mps * 1.94384)
                self.total_distance_m += distance_m
                bearing_deg = calculate_bearing(self.last_gps_pos[0], self.last_gps_pos[1], current_pos_rad[0], current_pos_rad[1])
                self.heading_data_received.emit(bearing_deg)
        
        elapsed_time_s = current_time - self.start_time
        self.trip_data_received.emit(self.total_distance_m, elapsed_time_s)
        self.position_data_received.emit(lat_rad, lon_rad)

        self.last_gps_pos = current_pos_rad
        self.last_gps_time = current_time