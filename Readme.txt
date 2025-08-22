sail-ui/
├── main_app.py               # Main application entry point
├── sail_ui.py                # The primary e-ink sailing display UI
├── dashboard_ui.py           # The secondary dashboard UI with tabs
├── nmea_reader.py            # NMEA2000 data reader thread
├── bluetooth_manager.py      # Handles Bluetooth audio streaming
├── mock_nmea_data.py         # The existing mock data generator
└── assets/
    └── boat-outline.svg      # (Optional) For storing image assets

- - - - - - - - - - - - - - - - - - - - - - - 

TESTING LOCALLY

- - - - - - - - - - - - - - - - - - - - - - - 

To view your Python app in its standalone window, you need to first activate your virtual environment and then run the main application script.

Here are the terminal commands:

Navigate to your project directory:

Bash:
cd ~/Sites/SailUI

(This assumes your project folder is SailUI inside your Sites directory.)

Activate your Python virtual environment:

Bash:
source venv/bin/activate

You'll know it's active when your terminal prompt shows (venv) at the beginning, like (venv) matthewernst-mac:SailUI matthewernst$.

Run your main application script:

Bash:
python main_app.py



- - - - - - - - - - - - - - - - - - - - - - - 

COMMITING TO GITHUB

- - - - - - - - - - - - - - - - - - - - - - - 

Bash:
git add .

Bash:
git commit -m ""

Bash:
git push origin main

- - - - - - - - - - - - - - - - - - - - - - - 

SSH ONTO RASBERRY PI 

- - - - - - - - - - - - - - - - - - - - - - - 


FAKE DATA: To Start with Fake Data (for UI Testing)
Navigate to the project directory:

Bash:
cd ~/sailui

Activate the virtual environment:

Bash:
source venv/bin/activate

Run the application, telling it to appear on your monitor:

Bash:
DISPLAY=:0 python main_app.py

- - 

REAL DATA: To Start with Real Data (from CAN HAT)
Use these commands when you have your CAN hardware connected and want to see live data.

Navigate to the project directory:

Bash:
cd ~/sailui

Activate the can0 hardware interface. (This is required after every reboot).

Bash:
sudo ip link set can0 up type can bitrate 250000

Activate the virtual environment:

Bash:
source venv/bin/activate

Run the application, telling it to appear on your monitor:

Bash:
DISPLAY=:0 python main_app.py


- - 

To kill the app

Bash:
cd ~/sailui



bash:
sudo pkill -f main_app.py


- - - - - - - - - - - - - - - - - - - - - - - 

INSTAL AND SETUP

- - - - - - - - - - - - - - - - - - - - - - - 


SailUI NMEA 2000 Display
SailUI is a Python application designed for Raspberry Pi to display NMEA 2000 data, such as wind speed, depth, and vessel speed, on a connected display. It features a primary sailing interface and a secondary dashboard for controls.

This guide provides step-by-step instructions to install, configure, and run the SailUI application on a Raspberry Pi.

Prerequisites
Before you begin, ensure you have the following hardware:

A Raspberry Pi (tested on a model running a Debian-based OS like Raspberry Pi OS).
An SD card with Raspberry Pi OS installed and configured with user access.
A CAN (Controller Area Network) HAT for Raspberry Pi (e.g., one based on the MCP2515 chip).
A monitor connected to the Raspberry Pi's HDMI port.
An internet connection on the Raspberry Pi.
Installation and Setup
Follow these steps on your Raspberry Pi. You can do this either directly with a keyboard and mouse or by connecting via SSH from another computer.

Step 1: Clone the Repository
Open a terminal on your Raspberry Pi and clone this repository into your home directory.

Bash

git clone https://github.com/matternst/sailui.git
cd sailui
Step 2: Set Up Python Virtual Environment
It is best practice to use a virtual environment to manage dependencies.

Bash

python3 -m venv venv
source venv/bin/activate
You will need to run source venv/bin/activate every time you open a new terminal to work on this project.

Step 3: Install Required Libraries
Install the necessary Python libraries using pip.

Bash

pip install PySide6 python-can nmea2000
Step 4: Configure for Real vs. Fake Data
The application can run in two modes:

Real Data Mode: Reads live data from the CAN HAT.
Fake Data Mode: Generates simulated data for UI testing without hardware.
To toggle between these modes, edit nmea_reader.py:

Bash

nano nmea_reader.py
Find the line IS_RASPBERRY_PI = False and change it:

For real data, set it to: IS_RASPBERRY_PI = True
For fake data, set it to: IS_RASPBERRY_PI = False
Step 5: Enable CAN Hardware (for Real Data Mode only)
If you plan to use a CAN HAT for real data, you must configure the Raspberry Pi to recognize it.

Edit the system configuration file:

Bash

sudo nano /boot/firmware/config.txt
(Note: On older Raspberry Pi OS versions, this file may be at /boot/config.txt)

Add the following lines to the bottom of the file. This enables the SPI interface and loads the driver for the CAN controller.

dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
Save the file (Ctrl+X, then Y, Enter) and reboot the Raspberry Pi:

Bash

sudo reboot
Running the Application
To Run Manually (for Testing)
This is the best way to test the application before setting up autostart.

Activate the virtual environment:
Bash

cd ~/sailui
source venv/bin/activate
(For Real Data Mode Only) Activate the can0 interface. This command is needed after every reboot.
Bash

sudo ip link set can0 up type can bitrate 250000
Run the application, telling it which display to use:
Bash

DISPLAY=:0 python main_app.py
The UI should appear on the monitor connected to the Pi. Press Ctrl+C in the terminal to stop the application.
Setting Up Automatic Startup (Recommended)
To make the application launch automatically when the Raspberry Pi desktop loads, follow these steps. This is the most reliable method for GUI applications.

Step 1: Create a Launcher Script
Create a new script file:

Bash

nano ~/sailui/launch_sailui.sh
Add the following content to the script. This ensures the correct environment is set up before the app runs.

Bash

#!/bin/bash
sleep 3
cd /home/matternst/sailui
source venv/bin/activate
python main_app.py
(Note: Replace matternst with your actual username if it is different.)

Save the file (Ctrl+X, Y, Enter) and make it executable:

Bash

chmod +x ~/sailui/launch_sailui.sh
Step 2: Create a Desktop Autostart File
Create the autostart directory if it doesn't exist:

Bash

mkdir -p ~/.config/autostart
Create a new .desktop file:

Bash

nano ~/.config/autostart/sailui.desktop
Add the following configuration to the file. This tells the desktop to run your launcher script on startup.

Ini, TOML

[Desktop Entry]
Name=SailUI
Exec=/home/matternst/sailui/launch_sailui.sh
Type=Application
(Note: Replace matternst with your username.)

Save the file (Ctrl+X, Y, Enter).

Step 3: Reboot
Reboot the Raspberry Pi. When the desktop loads, your application should launch automatically and be visible on the monitor.

Bash

sudo reboot
Troubleshooting
Here are solutions to some common errors encountered during setup.

GUI does not appear on the monitor
Symptom: You run the app from an SSH terminal, it appears to be running, but nothing shows up on the physically connected monitor.
Cause: The application doesn't know which display to draw its window on.
Solution: You must specify the display by prepending DISPLAY=:0 to the command.

Bash

# Manual launch example
DISPLAY=:0 python main_app.py

# For autostart, the recommended .desktop file method handles this automatically.
# If you were using a systemd service, you would need to add:
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/matternst/.Xauthority"
ModuleNotFoundError: No module named 'NMEA2000_PY'
Symptom: The application fails to start with this specific error.
Cause: A typo in the original nmea_reader.py code.
Solution: You need to install the correct library and fix the import statement.

Install the correct package: pip install nmea2000
Edit nmea_reader.py and change import NMEA2000_PY as n2k to import nmea2000 as n2k.
AttributeError: module 'nmea2000' has no attribute 'NMEA2000'
Symptom: The application fails after fixing the first ModuleNotFoundError.
Cause: The public nmea2000 library is a simple decoder and does not contain the NMEA2000 class the original code expected.
Solution: The code in nmea_reader.py needs to be replaced with a version that uses python-can's Notifier to listen for messages and a custom parser to decode them. The corrected code is now in the main repository.

Could not access SocketCAN device can0
Symptom: The application fails with [Errno 19] No such device.
Cause: The CAN HAT has not been configured in the Raspberry Pi's boot settings, so the can0 hardware interface does not exist.
Solution: Follow Step 5: Enable CAN Hardware in the setup guide to edit /boot/firmware/config.txt and enable the dtoverlay. A reboot is required after this change.

Git error: Your local changes... would be overwritten by merge
Symptom: git pull fails because you have edited a file (like nmea_reader.py) directly on the Raspberry Pi.
Cause: Git is protecting you from losing your local, uncommitted changes.
Solution: If you want to discard the local changes and download the version from GitHub, use git reset:

Bash

# WARNING: This will delete any unsaved changes in the directory.
git reset --hard
git pull
SSH error: Permission denied (publickey)
Symptom: You cannot log in to the Pi from a new terminal window.
Cause: You are trying to log in with the wrong username (e.g., pi instead of your actual username matternst).
Solution: Ensure you use the correct username that is configured with your SSH keys.

Bash

# Correct format
ssh your_username@your_pi_ip_address







- - - - - - - - - - - - - - - - - - - - - - - 

SETUP eINK monitor

- - - - - - - - - - - - - - - - - - - - - - - 


1. Enable SPI on your Raspberry Pi
First, you need to enable the SPI interface on your Raspberry Pi, which the e-ink display uses to communicate.

Open a terminal on your Raspberry Pi and run sudo raspi-config.

Navigate to Interfacing Options > SPI.

Select Yes to enable the SPI interface.

Reboot your Raspberry Pi.

2. Install the Waveshare E-Paper Library
Next, you'll need to install the Python library to control the e-ink display.

Clone the Waveshare e-Paper GitHub repository:

Bash

git clone https://github.com/waveshare/e-Paper.git
Install the necessary Python libraries:

Bash

sudo apt-get update
sudo apt-get install python3-pip python3-pil python3-numpy
sudo pip3 install RPi.GPIO spidev
3. Create a New E-Paper Display File
To keep your code organized, create a new file named epaper_display.py in the same directory as your other SailUI files. This file will handle the communication with the e-ink display.

Python

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
4. Modify main_app.py
Now, you need to modify your main_app.py file to render the SailUI to an image and send it to the e-ink display.

Python

# main_app.py

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer

# Make sure all your custom modules are imported
from nmea_reader import NMEA2000Reader
from sail_ui import SailUI
from dashboard_ui import DashboardUI
from bluetooth_manager import BluetoothManager
from epaper_display import EpaperDisplay # Import the new EpaperDisplay class

class MainApplication:
    def __init__(self):
        """Initializes the main application, UI windows, and connections."""
        self.app = QApplication(sys.argv)

        # --- Screen Detection ---
        screens = self.app.screens()
        primary_screen = self.app.primaryScreen()
        secondary_screen = None
        if len(screens) > 1:
            for screen in screens:
                if screen != primary_screen:
                    secondary_screen = screen
                    break

        # --- Initialize Core Components & UI ---
        self.nmea_thread = NMEA2000Reader()
        self.bt_manager = BluetoothManager()
        self.sail_ui = SailUI()
        self.dashboard_ui = DashboardUI()
        
        # --- Initialize E-Paper Display ---
        self.epaper = EpaperDisplay()

        # --- Connect Signals and Slots ---
        # (Your existing signal and slot connections remain the same)
        self.nmea_thread.wind_data_received.connect(self.sail_ui.update_wind_display)
        self.nmea_thread.depth_data_received.connect(self.sail_ui.update_depth_display)
        self.nmea_thread.speed_data_received.connect(self.sail_ui.update_speed_display)
        
        self.dashboard_ui.view_changed.connect(self.sail_ui.setView)
        self.dashboard_ui.theme_changed.connect(self.sail_ui.setTheme)
        
        self.dashboard_ui.discoverable_clicked.connect(self.bt_manager.make_discoverable)
        self.bt_manager.connection_status_changed.connect(self.dashboard_ui.update_bluetooth_status)

        self.dashboard_ui.exit_app_clicked.connect(self.app.quit)

        self.sail_ui.escape_pressed.connect(self.app.quit)
        self.dashboard_ui.escape_pressed.connect(self.app.quit)

        # --- Show Windows ---
        # The dashboard will now be the primary UI on the main monitor
        self.dashboard_ui.show()

        if primary_screen:
            self.dashboard_ui.move(primary_screen.geometry().topLeft())
        
        # --- Timer to update the e-paper display ---
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_epaper_display)
        self.update_timer.start(5000) # Update every 5 seconds

        # Start reading NMEA data
        self.nmea_thread.start()

    def update_epaper_display(self):
        """Renders the SailUI to an image and displays it on the e-paper."""
        pixmap = QPixmap(self.sail_ui.size())
        self.sail_ui.render(pixmap)
        
        # Convert QPixmap to PIL Image
        qimage = pixmap.toImage()
        buffer = qimage.bits().tobytes()
        pil_image = Image.frombytes("RGBA", (qimage.width(), qimage.height()), buffer, 'raw', "RGBA")
        
        # Display the image
        self.epaper.display_image(pil_image)


    def run(self):
        """Executes the application's main loop."""
        return self.app.exec()

    def cleanup(self):
        """Stops background threads and clears the e-paper display."""
        print("Cleaning up and stopping threads...")
        self.nmea_thread.stop()
        self.epaper.clear()
        self.epaper.sleep()


if __name__ == "__main__":
    main_app = MainApplication()
    exit_code = main_app.run()
    main_app.cleanup()
    sys.exit(exit_code)




    The Fix: Install the Pillow Library
Make sure your virtual environment is still active. You should see (venv) at the start of your command prompt. If not, run source venv/bin/activate again.

Install the Pillow library with this command:

Bash:
pip install Pillow






The Fix: Install the waveshare_epd Library
Let's ensure the library is installed directly into your project's virtual environment.

Activate the virtual environment (if it's not already active):

Bash:
source venv/bin/activate

Install the library directly from the e-Paper directory:

Bash:
pip install ../e-Paper/RaspberryPi_JetsonNano/python

This command tells pip to install the library from the specified directory, ensuring it's placed within your active virtual environment.

Verify the installation:

Bash:
pip list | grep waveshare



The Fix: Install gpiozero
Make sure your virtual environment is still active.

Install the gpiozero library using pip:

Bash:
pip install gpiozero

Once the installation is complete, run your application one last time:



The Fix: Install the RPi.GPIO Library
We will install RPi.GPIO, which is the most common library for this purpose. This will provide gpiozero with the stable driver it needs to communicate with the hardware correctly.

Make sure your virtual environment is still active ((venv) should be at the start of your prompt).

Install the RPi.GPIO library using pip:

Bash:
pip install RPi.GPIO





5. Run the Application
Now you are ready to run your updated SailUI application.

Make sure you are in the sailui directory and have your virtual environment activated.

Run the main application:

Bash
python main_app.py
Your dashboard_ui should appear on your primary monitor, and the sail_ui should now be displayed on your new e-ink monitor, updating every 5 seconds.




********** ********** ********** ********** ********** ********** 



********** Raspberry Pi 7.5-inch e-Paper HAT Setup Guide ********** ********** 
A complete list of commands to set up the Waveshare 7.5-inch e-Paper HAT on a fresh Raspberry Pi OS installation.

Step 1: Enable SPI Interface
This opens the Raspberry Pi configuration tool to enable the SPI hardware interface, which is required for the display to communicate with the Pi. A reboot is necessary for the changes to take effect.

BASH:

sudo raspi-config

(Navigate to Interfacing Options > SPI > Yes, then finish and reboot)

Step 2: Install Git
Installs the git version control system, which is needed to download software from GitHub repositories.

BASH:

sudo apt-get update && sudo apt-get install git -y

Step 3: Install BCM2835 Library
Downloads and installs the BCM2835 C library, which provides low-level access to the Raspberry Pi's GPIO pins.

BASH:

wget [http://www.airspayce.com/mikem/bcm2835/bcm2835-1.71.tar.gz](http://www.airspayce.com/mikem/bcm2835/bcm2835-1.71.tar.gz)
tar zxvf bcm2835-1.71.tar.gz
cd bcm2835-1.71/
sudo ./configure && sudo make && sudo make check && sudo make install
cd ..

Step 4: Install WiringPi Library
Downloads the source code for the (deprecated but still necessary) WiringPi library and builds it from source.

BASH:

git clone [https://github.com/WiringPi/WiringPi](https://github.com/WiringPi/WiringPi)
cd WiringPi
./build
cd ..

Step 5: Install lgpio Library
Installs the lgpio development library using the apt package manager. This was a missing dependency required for the Waveshare code to compile correctly.

BASH:

sudo apt-get install liblgpio-dev -y

Step 6: Download Waveshare Demo Code
Clones the official Waveshare e-Paper repository from GitHub, which contains the example code needed to test the display.

BASH:

git clone [https://github.com/waveshare/e-Paper.git](https://github.com/waveshare/e-Paper.git)

Step 7: Compile and Run the Test Demo
Navigates into the C examples directory, cleans any previous build attempts, and compiles the code specifically for the 7.5-inch V2 e-Paper model. Finally, it runs the compiled program to display the demo.

BASH:

cd e-Paper/RaspberryPi_JetsonNano/c
sudo make clean && sudo make EPD=epd7in5V2
sudo ./epd
