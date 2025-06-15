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


Step 1: Clone the Git Repository
First, you need to clone the application's repository from GitHub. Open a terminal on your Raspberry Pi and run the following command:

Bash:
git clone https://github.com/matternst/sailui.git

This will download the application code into a new directory named sailui.


- - 


Step 2: Set Up a Virtual Environment
Navigate into the newly created directory:

Bash:
cd sailui

It is good practice to use a virtual environment to manage project dependencies. Create a new virtual environment:

Bash:
python3 -m venv venv

Now, activate the virtual environment:

Bash:
source venv/bin/activate

Your terminal prompt should now be prefixed with (venv), indicating that the virtual environment is active.


- - 


Step 3: Install Dependencies
Next, you'll need to install the required Python libraries. Based on the application's code, you need to install PySide6, python-can, and nmea2000:

Bash:
pip install PySide6 python-can nmea2000


- - 


Step 4: Configure the Application for Raspberry Pi
The application has a specific setting that needs to be enabled for it to work correctly on a Raspberry Pi. Open the nmea_reader.py file in a text editor:

Bash:
nano nmea_reader.py

Find the following line near the top of the file:

IS_RASPBERRY_PI = False
Change False to True

Save the file and exit the editor by pressing Ctrl+X, then Y, and then Enter.


- - 


Step 5: Install and correct NMEA2000 package

1. Install the Correctly Named Package
The package you need is actually called nmea2000. Install it with this command:

Bash:
pip install nmea2000


2. Correct the Import in the Code
Now, you need to fix the typo in the nmea_reader.py file. Open it for editing:

Bash:
nano nmea_reader.py

Find this line:

Python

import NMEA2000_PY as n2k

And change it to:

import nmea2000 as n2k

Save the file and exit the editor by pressing Ctrl+X, then Y, and then Enter.


- - 


Step 6: Configure the Raspberry Pi to Recognize the HAT

You need to enable the SPI interface and tell the operating system to load the driver for the CAN controller.

6A: Edit the configuration file:
Open the /boot/config.txt file using nano:

Bash:
sudo nano /boot/config.txt

Add the overlay configuration:
Scroll to the bottom of the file and add the following lines. This configuration is standard for most MCP2515-based CAN hats with a 16MHz oscillator. If your HAT's documentation specifies a different oscillator, change the number accordingly.

dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
Save and Reboot:
Press Ctrl+X, then Y, then Enter to save the file. Now, reboot your Raspberry Pi for the changes to take effect:

Bash:
sudo reboot


- 

After the Raspberry Pi reboots, log back in via SSH. The can0 device should now exist, but it needs to be configured and enabled.


6B: Set the bitrate and bring the interface up:
Run the following command to configure the can0 interface with a standard bitrate of 500,000 bps. If your NMEA 2000 network uses a different speed, you'll need to adjust this value.

Bash:
sudo ip link set can0 up type can bitrate 250000

Note: NMEA 2000 standard bitrate is 250,000 bps, not 500,000. I have corrected the command above.

- 

6C: Verify the interface:
Check if the can0 interface is up and running by using the ifconfig command:

Bash:
ifconfig can0

If successful, you will see details for the can0 interface, and it should show UP RUNNING. EXAMPLE BELOW:
can0: flags=193<UP,RUNNING,NOARP>  mtu 16
        unspec 00-00-00-00-00-00-00-00-00-00-00-00-00-00-00-00  txqueuelen 10  (UNSPEC)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

- 

6D: Test the Application Again
Now that the can0 interface is configured and active, try running your application one more time from within its directory:

Bash:
cd ~/sailui
source venv/bin/activate
python main_app.py


- - 



Step 7: 


- - 


Step 8: Run the Application
Now you are ready to run the application. From the sailui directory, with your virtual environment still active, execute the main script:

Bash:
python main_app.py

The application's user interface should now appear on your screen.


- - 

























Step 6: Set Up the Application to Run on Boot
To make the application start automatically when your Raspberry Pi boots up, you can create a systemd service.

Create a Service File

Create a new service file with the following command:

Bash:
sudo nano /etc/systemd/system/sailui.service

Add the Service Configuration

Copy and paste the following configuration into the editor. Make sure to replace /home/pi with your actual home directory if it's different.

[Unit]
Description=SailUI Service
After=multi-user.target

[Service]
ExecStart=/home/pi/sailui/venv/bin/python /home/pi/sailui/main_app.py
WorkingDirectory=/home/pi/sailui
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
Save and exit the editor.

Enable and Start the Service

Now, reload the systemd daemon to recognize the new service:

Bash

sudo systemctl daemon-reload
Enable the service to start on boot:

Bash

sudo systemctl enable sailui.service
Finally, you can start the service immediately to test it:

Bash

sudo systemctl start sailui.service
