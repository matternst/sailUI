# log_manager.py
import json
import os
import time
from datetime import datetime

class LogManager:
    """
    Manages trip log data, including creation, storage, and retrieval.
    """
    def __init__(self, log_file='trips.json'):
        self.log_file = log_file
        self.trips = self.load_trips()
        self.current_trip = None

    def load_trips(self):
        """Loads trip data from a JSON file."""
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                return json.load(f)
        return []

    def save_trips(self):
        """Saves trip data to a JSON file."""
        with open(self.log_file, 'w') as f:
            json.dump(self.trips, f, indent=4)

    def start_new_trip(self):
        """Starts a new trip log entry."""
        trip_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.current_trip = {
            "id": trip_id,
            "start_time": time.time(),
            "end_time": None,
            "distance": 0,
            "max_wind_speed": 0,
            "min_wind_speed": 999,
            "max_boat_speed": 0,
            "min_boat_speed": 999,
            "wind_direction": None,
            "people": None,
            "type": "Cruise",  # New field
            "course": None     # New field
        }
        self.trips.append(self.current_trip)
        return trip_id

    def end_current_trip(self):
        """Finalizes and saves the current trip log."""
        if self.current_trip:
            self.current_trip['end_time'] = time.time()
            self.save_trips()
            self.current_trip = None

    def update_trip_data(self, distance, wind_speed, wind_direction, boat_speed):
        """Updates the data for the current trip."""
        if self.current_trip:
            self.current_trip['distance'] = distance
            if wind_speed > self.current_trip['max_wind_speed']:
                self.current_trip['max_wind_speed'] = wind_speed
            if wind_speed < self.current_trip['min_wind_speed']:
                self.current_trip['min_wind_speed'] = wind_speed
            self.current_trip['wind_direction'] = wind_direction
            if boat_speed > self.current_trip['max_boat_speed']:
                self.current_trip['max_boat_speed'] = boat_speed
            if boat_speed < self.current_trip['min_boat_speed']:
                self.current_trip['min_boat_speed'] = boat_speed

    def get_all_trips(self):
        """Returns all saved trip logs."""
        return self.trips

    def delete_trip(self, trip_id):
        """Deletes a specific trip log."""
        self.trips = [trip for trip in self.trips if trip['id'] != trip_id]
        self.save_trips()

    def set_people(self, trip_id, num_people):
        """Sets the number of people for a specific trip."""
        for trip in self.trips:
            if trip['id'] == trip_id:
                trip['people'] = num_people
                break
        self.save_trips()

    def set_trip_type(self, trip_type):
        """Sets the type of the current trip (e.g., 'Race' or 'Cruise')."""
        if self.current_trip:
            self.current_trip['type'] = trip_type

    def set_trip_course(self, course_name):
        """Sets the course for the current trip."""
        if self.current_trip:
            self.current_trip['course'] = course_name