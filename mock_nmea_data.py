import time
import math
import random
from threading import Thread, Event

# Haversine formula to calculate distance between two lat/lon points
# Returns distance in meters
def haversine_distance(lat1_rad, lon1_rad, lat2_rad, lon2_rad):
    R = 6371000 # Earth radius in meters
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

class MockNMEA2000:
    def __init__(self):
        self._callbacks = {}
        self._stop_event = Event()
        self._thread = None

        # Simulated Wind Data
        self.wind_speed = 5.0 # m/s
        self.wind_angle = 0.0 # radians (0 = straight ahead)
        self.wind_reference = "Apparent"

        # Simulated Depth Data
        self.depth = 10.0 # meters

        # Simulated GPS Data
        self.gps_latitude_deg = 34.052235 # Starting latitude (e.g., Los Angeles)
        self.gps_longitude_deg = -118.243683 # Starting longitude
        self.speed_mps = 0.0 # Calculated speed in m/s
        self.last_gps_time = time.time()
        self.last_gps_pos = (math.radians(self.gps_latitude_deg), math.radians(self.gps_longitude_deg))

         # --- NEW: Simulated Pressure Data ---
        self.pressure_pa = 101325.0 # Pascals

    def add_callback(self, pgn, func):
        # Register callbacks for specific PGNs
        self._callbacks[pgn] = func

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = Thread(target=self._simulate_data)
            self._thread.daemon = True
            self._stop_event.clear()
            self._thread.start()
            print("Mock NMEA2000 data simulation started.")

    def stop(self):
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=2)
            print("Mock NMEA2000 data simulation stopped.")

    def _simulate_data(self):
        cycle_time = 0.1 # seconds, how often to update internal state
        emit_interval = 1.0 # seconds, how often to emit 'new' data
        last_emit_time = time.time()

        while not self._stop_event.is_set():
            current_time = time.time()

            # --- Simulate Wind Data (PGN 130306) ---
            self.wind_speed = 5.0 + 1.0 * math.sin(current_time / 5)
            self.wind_angle = (current_time / 20) * (2 * math.pi) % (2 * math.pi)
            if random.random() < 0.01:
                self.wind_speed += random.uniform(-2, 2)
                self.wind_angle += random.uniform(-math.pi/4, math.pi/4)
                self.wind_speed = max(0, self.wind_speed)
                self.wind_angle %= (2 * math.pi)

            # --- Simulate Depth Data (PGN 128267) ---
            self.depth = 10.0 + 2.0 * math.sin(current_time / 7) # Oscillate depth
            self.depth = max(0.5, self.depth) # Ensure depth is positive

            # --- Simulate Pressure Data (PGN 130314) ---
            self.pressure_pa = 101325.0 + 150 * math.sin(current_time / 60) # Slow oscillation for pressure
            if random.random() < 0.02: # Add some noise
                self.pressure_pa += random.uniform(-25, 25)

            # --- Simulate GPS Position Data (PGN 129025) ---
            # Simulate slow movement (e.g., 5 m/s or ~10 knots)
            # 1 degree of latitude is approx 111,000 meters
            # 1 degree of longitude varies, but roughly 111,000 * cos(latitude)
            simulated_speed_mps = 5.0 # meters/second
            dt = current_time - self.last_gps_time
            if dt > 0:
                # Move slightly to the east and north
                delta_lat_rad = (simulated_speed_mps * dt / 111000) / (111000 / (2 * math.pi * 6371000) * 360 / (2 * math.pi)) # Approximate conversion
                delta_lon_rad = (simulated_speed_mps * dt / (111000 * math.cos(math.radians(self.gps_latitude_deg)))) / (111000 / (2 * math.pi * 6371000) * 360 / (2 * math.pi)) # Approximate conversion

                self.gps_latitude_deg += random.uniform(-0.00001, 0.00001) + (simulated_speed_mps * dt / 111000) * 0.00001 # Small random walk + drift
                self.gps_longitude_deg += random.uniform(-0.00001, 0.00001) + (simulated_speed_mps * dt / (111000 * math.cos(math.radians(self.gps_latitude_deg)))) * 0.00001 # Small random walk + drift

            current_gps_pos_rad = (math.radians(self.gps_latitude_deg), math.radians(self.gps_longitude_deg))

            # Emit data at intervals
            if current_time - last_emit_time >= emit_interval:
                last_emit_time = current_time

                # Emit Wind Data
                wind_data = {
                    'PGN': 130306,
                    'WindSpeed': self.wind_speed,
                    'WindAngle': self.wind_angle,
                    'Reference': self.wind_reference
                }
                if 130306 in self._callbacks:
                    self._callbacks[130306](130306, wind_data)

                # Emit Depth Data
                depth_data = {
                    'PGN': 128267,
                    'Depth': self.depth, # Depth in meters
                    'Offset': 0.0 # Assuming 0 offset for simplicity in mock
                }
                if 128267 in self._callbacks:
                    self._callbacks[128267](128267, depth_data)

                # Emit GPS Position Data
                gps_data = {
                    'PGN': 129025,
                    'Latitude': current_gps_pos_rad[0], # Radians
                    'Longitude': current_gps_pos_rad[1], # Radians
                    'GPSQuality': 1, # Mock value
                    'HDOP': 1.0, # Mock value
                    'NumberOfSatellites': 8 # Mock value
                }
                if 129025 in self._callbacks:
                    self._callbacks[129025](129025, gps_data)

            time.sleep(cycle_time)
            self.last_gps_time = current_time # Update last GPS time for next iteration

if __name__ == "__main__":
    # Example of how to use the mock data source
    import sys
    import PySide6.QtWidgets as QtWidgets
    from PySide6.QtCore import QTimer, Slot # For GUI testing

    def print_data(pgn, data):
        if pgn == 130306:
            speed = data.get('WindSpeed')
            angle_rad = data.get('WindAngle')
            reference = data.get('Reference')
            if speed is not None and angle_rad is not None:
                angle_deg = math.degrees(angle_rad)
                print(f"Mock Wind: Speed={speed:.2f} m/s, Angle={angle_deg:.1f}° ({reference})")
        elif pgn == 128267:
            depth = data.get('Depth')
            if depth is not None:
                print(f"Mock Depth: {depth:.2f} meters")
        elif pgn == 129025:
            lat_rad = data.get('Latitude')
            lon_rad = data.get('Longitude')
            if lat_rad is not None and lon_rad is not None:
                print(f"Mock GPS: Lat={math.degrees(lat_rad):.6f}°, Lon={math.degrees(lon_rad):.6f}°")


    class TestApp(QtWidgets.QWidget):
        def __init__(self, mock_n2k):
            super().__init__()
            self.mock_n2k = mock_n2k
            self.mock_n2k.add_callback(130306, self.update_wind_display)
            self.mock_n2k.add_callback(128267, self.update_depth_display)
            self.mock_n2k.add_callback(129025, self.update_gps_display) # GPS will be processed in NMEA2000Reader

            self.wind_speed_label = QtWidgets.QLabel("Wind Speed: --")
            self.wind_angle_label = QtWidgets.QLabel("Wind Angle: --")
            self.depth_label = QtWidgets.QLabel("Depth: --")
            self.gps_label = QtWidgets.QLabel("GPS: --")

            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(self.wind_speed_label)
            layout.addWidget(self.wind_angle_label)
            layout.addWidget(self.depth_label)
            layout.addWidget(self.gps_label)
            self.setLayout(layout)

            self.last_gps_pos = None
            self.last_gps_time = None
            self.current_speed_mps = 0.0

        @Slot(int, dict)
        def update_wind_display(self, pgn, data):
            speed = data.get('WindSpeed')
            angle_rad = data.get('WindAngle')
            reference = data.get('Reference')
            if speed is not None and angle_rad is not None:
                speed_knots = speed * 1.94384
                angle_deg = math.degrees(angle_rad)
                self.wind_speed_label.setText(f"Wind Speed: {speed_knots:.1f} knots")
                self.wind_angle_label.setText(f"Wind Angle: {angle_deg:.1f}° ({reference})")

        @Slot(int, dict)
        def update_depth_display(self, pgn, data):
            depth_m = data.get('Depth')
            if depth_m is not None:
                depth_ft = depth_m * 3.28084
                self.depth_label.setText(f"Depth: {depth_ft:.1f} ft")

        @Slot(int, dict)
        def update_gps_display(self, pgn, data):
            lat_rad = data.get('Latitude')
            lon_rad = data.get('Longitude')
            current_time = time.time()

            if lat_rad is not None and lon_rad is not None:
                current_pos_rad = (lat_rad, lon_rad)
                if self.last_gps_pos and self.last_gps_time:
                    distance_m = haversine_distance(self.last_gps_pos[0], self.last_gps_pos[1], current_pos_rad[0], current_pos_rad[1])
                    time_diff_s = current_time - self.last_gps_time
                    if time_diff_s > 0:
                        self.current_speed_mps = distance_m / time_diff_s
                        speed_knots = self.current_speed_mps * 1.94384
                        self.gps_label.setText(f"GPS Speed: {speed_knots:.1f} knots")
                    else:
                        self.gps_label.setText(f"GPS: Lat={math.degrees(lat_rad):.6f}°, Lon={math.degrees(lon_rad):.6f}° (No speed yet)")
                else:
                    self.gps_label.setText(f"GPS: Lat={math.degrees(lat_rad):.6f}°, Lon={math.degrees(lon_rad):.6f}° (No previous position)")

                self.last_gps_pos = current_pos_rad
                self.last_gps_time = current_time


    app = QtWidgets.QApplication(sys.argv)
    mock_n2k_instance = MockNMEA2000()
    mock_n2k_instance.start()

    main_window = TestApp(mock_n2k_instance)
    main_window.show()

    try:
        sys.exit(app.exec())
    finally:
        mock_n2k_instance.stop()