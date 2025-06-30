# mock_epaper_display.py

class MockEpaperDisplay:
    """A mock display that does nothing, for use on non-Raspberry Pi systems."""
    def __init__(self):
        print("Initialized Mock E-Paper Display.")

    def display_image(self, image):
        # This mock function would simply pass, or you could save the image for debugging
        print("Mock display: Skipping image display.")
        # To see what would be displayed, you could uncomment the following line:
        # image.show() 

    def clear(self):
        print("Mock display: Clearing.")

    def sleep(self):
        print("Mock display: Going to sleep.")