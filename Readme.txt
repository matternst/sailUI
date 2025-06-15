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
Bash

cd ~/Sites/SailUI
(This assumes your project folder is SailUI inside your Sites directory.)

Activate your Python virtual environment:

Bash

source venv/bin/activate
You'll know it's active when your terminal prompt shows (venv) at the beginning, like (venv) matthewernst-mac:SailUI matthewernst$.

Run your main application script:

Bash

python main_app.py


- - - - - - - - - - - - - - - - - - - - - - - 

SSH ONTO RASBERRY PI 

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