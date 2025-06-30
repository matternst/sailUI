# mock_nmea_data.py
import time
import math
import random
from threading import Thread, Event

# This function is not used by the simplified mock data, but is kept for compatibility
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

        # --- Simulated Boat State ---
        self.wind_speed = 5.0 # m/s
        self.wind_angle = 0.0 # radians
        self.wind_reference = "Apparent"
        self.depth = 10.0 # meters
        self.pressure_pa = 101325.0 # Pascals
        
        # --- GPS State ---
        self.gps_latitude_deg = 34.052235
        self.gps_longitude_deg = -118.243683
        
    def add_callback(self, pgn, func):
        self._callbacks[pgn] = func

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = Thread(target=self._simulate_data)
            self._thread.daemon = True
            self._stop_event.clear()
            self._thread.start()
            print("MOCK_NMEA: Simple data simulation started.")

    def stop(self):
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=2)
            print("MOCK_NMEA: Data simulation stopped.")

    def _simulate_data(self):
        """
        A simple, robust loop that reliably generates changing data every second.
        """
        while not self._stop_event.is_set():
            # --- Update All Simulated Values ---

            # Wind oscillates smoothly
            self.wind_speed = 5.0 + 1.0 * math.sin(time.time() / 5)
            self.wind_angle = (time.time() / 20) * (2 * math.pi) % (2 * math.pi)

            # Depth oscillates smoothly
            self.depth = 10.0 + 2.0 * math.sin(time.time() / 7)

            # --- THE SIMPLEST POSSIBLE BOAT MOVEMENT ---
            # Move the boat north-east by a tiny, fixed amount each second.
            # This guarantees movement and will allow you to test your UI.
            self.gps_latitude_deg += 0.00005
            self.gps_longitude_deg += 0.00005
            
            # --- Emit all data packets ---
            if 130306 in self._callbacks:
                self._callbacks[130306](130306, {'WindSpeed': self.wind_speed, 'WindAngle': self.wind_angle, 'Reference': "Apparent"})
            if 128267 in self._callbacks:
                self._callbacks[128267](128267, {'Depth': self.depth})
            if 129025 in self._callbacks:
                self._callbacks[129025](129025, {'Latitude': math.radians(self.gps_latitude_deg), 'Longitude': math.radians(self.gps_longitude_deg)})
            if 130314 in self._callbacks:
                 self._callbacks[130314](130314, {'Pressure': self.pressure_pa})

            # Wait for 1 second before the next update
            time.sleep(1)

if __name__ == "__main__":
    # This part is for testing this file directly
    def print_data(pgn, data):
        if pgn == 129025:
            lat = math.degrees(data['Latitude'])
            lon = math.degrees(data['Longitude'])
            print(f"Mock GPS: Lat={lat:.6f}, Lon={lon:.6f}")

    mock = MockNMEA2000()
    mock.add_callback(129025, print_data)
    mock.start()

    try:
        time.sleep(60)
    finally:
        mock.stop()