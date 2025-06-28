# epaper_display.py

import sys
import os
from PIL import Image
from waveshare_epd import epd7in5_V2

class EpaperDisplay:
    def __init__(self):
        self.epd = epd7in5_V2.EPD()
        self.epd.init()
        self.epd.Clear()

    def display_image(self, image):
        # Create a new image with a white background
        black_image = Image.new('1', (self.epd.width, self.epd.height), 255)
        
        # Paste the provided image onto the white background
        black_image.paste(image, (0,0))
        
        # Display the image on the e-paper display
        self.epd.display(self.epd.getbuffer(black_image))

    def clear(self):
        self.epd.Clear()

    def sleep(self):
        self.epd.sleep()