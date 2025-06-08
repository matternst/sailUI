sail-ui/
├── main_app.py               # Main application entry point
├── sail_ui.py                # The primary e-ink sailing display UI
├── dashboard_ui.py           # The secondary dashboard UI with tabs
├── nmea_reader.py            # NMEA2000 data reader thread
├── bluetooth_manager.py      # Handles Bluetooth audio streaming
├── mock_nmea_data.py         # The existing mock data generator
└── assets/
    └── boat-outline.svg      # (Optional) For storing image assets

    

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