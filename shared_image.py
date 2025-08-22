# shared_image.py
from threading import Lock
import io

class SharedImage:
    def __init__(self):
        self.image_bytes = None
        self.lock = Lock()

    def update_image(self, pil_image):
        with self.lock:
            byte_arr = io.BytesIO()
            pil_image.save(byte_arr, format='BMP')
            self.image_bytes = byte_arr.getvalue()

    def get_image_bytes(self):
        with self.lock:
            return self.image_bytes
