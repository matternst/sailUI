import subprocess
import re
from PySide6.QtCore import QObject, Signal, QTimer

class BluetoothManager(QObject):
    connection_status_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Timer to periodically check connection status
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_connection_status)
        self.timer.start(5000) # Check every 5 seconds

    def check_connection_status(self):
        """
        Calls bluetoothctl info to see if a device is connected.
        """
        try:
            # Run the command to get info on all known bluetooth devices
            result = subprocess.run(['bluetoothctl', 'info'], capture_output=True, text=True, timeout=5)
            output = result.stdout
            
            # Use regex to find the Name and if it's connected
            name_match = re.search(r"Name: (.+)", output)
            connected_match = re.search(r"Connected: yes", output)
            
            if name_match and connected_match:
                device_name = name_match.group(1)
                status_text = f"Connected: {device_name}"
            else:
                status_text = "Disconnected"
                
            self.connection_status_changed.emit(status_text)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.connection_status_changed.emit("Error: bluetoothctl not found or timed out")

    def make_discoverable(self, duration=60):
        """
        Makes the Pi discoverable for a short period.
        """
        try:
            subprocess.run(['bluetoothctl', 'discoverable on'], timeout=2)
            print(f"Bluetooth discoverable for {duration} seconds.")
            # In a real implementation, you might turn it off after a duration
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("Could not make device discoverable.")