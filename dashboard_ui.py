from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QListWidget, QCheckBox, QPushButton
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QKeyEvent

class DashboardUI(QWidget):
    # Signals to communicate with the main application
    view_changed = Signal(int)
    theme_changed = Signal(bool)
    discoverable_clicked = Signal()
    exit_app_clicked = Signal()
    escape_pressed = Signal() # Signal for the Escape key

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secondary Dashboard")
        self.setGeometry(100, 100, 610, 343)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        layout = QVBoxLayout(self)

        # --- Tab Widget Setup ---
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.South)
        self.tabs.setStyleSheet("""
            QTabBar::tab { background: #282828; color: white; padding: 10px; font-size: 16px; border-top: 2px solid #282828; }
            QTabBar::tab:selected { background: #3c3c3c; border-top: 2px solid #007acc; }
            QTabWidget::pane { border: 1px solid #3c3c3c; }
        """)
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tabs.addTab(self.tab1, "Engine")
        self.tabs.addTab(self.tab2, "Navigation")
        self.tabs.addTab(self.tab3, "Music")
        self.tabs.addTab(self.tab4, "Settings")

        # --- Setup the Music Tab ---
        music_layout = QVBoxLayout(self.tab3)
        music_layout.setAlignment(Qt.AlignCenter)
        status_label = QLabel("BLUETOOTH STATUS")
        status_label.setStyleSheet("font-size: 16px; color: grey; font-family: Oxanium; font-weight: bold;")
        self.bt_status_value = QLabel("Checking...")
        self.bt_status_value.setStyleSheet("font-size: 24px; font-family: Oxanium;")
        discoverable_button = QPushButton("Make Discoverable")
        discoverable_button.setStyleSheet("font-size: 16px; font-family: Oxanium; padding: 10px;")
        discoverable_button.clicked.connect(self.discoverable_clicked.emit)
        music_layout.addWidget(status_label, alignment=Qt.AlignCenter)
        music_layout.addWidget(self.bt_status_value, alignment=Qt.AlignCenter)
        music_layout.addSpacing(20)
        music_layout.addWidget(discoverable_button, alignment=Qt.AlignCenter)
        
        # --- Setup other tabs ---
        self.tab1.setLayout(QVBoxLayout())
        self.tab1.layout().addWidget(QLabel("Engine Data (Placeholder)"))
        self.tab2.setLayout(QVBoxLayout())
        self.tab2.layout().addWidget(QLabel("Navigation View (Placeholder)"))

        # --- Setup the Settings Tab ---
        settings_layout = QVBoxLayout(self.tab4)
        view_label = QLabel("Display View")
        view_label.setStyleSheet("font-size: 20px; font-family: Oxanium; padding-bottom: 10px;")
        self.view_list = QListWidget()
        self.view_list.setStyleSheet("font-size: 16px; font-family: Oxanium;")
        self.view_list.addItems(["Standard View", "Racing View"])
        self.view_list.currentRowChanged.connect(self.on_view_selected)
        theme_label = QLabel("Theme")
        theme_label.setStyleSheet("font-size: 20px; font-family: Oxanium; padding-top: 20px; padding-bottom: 10px;")
        self.theme_checkbox = QCheckBox("Enable Light Mode")
        self.theme_checkbox.setStyleSheet("font-size: 16px; font-family: Oxanium;")
        self.theme_checkbox.stateChanged.connect(self.on_theme_toggled)
        exit_button = QPushButton("Exit Sailing App")
        exit_button.setStyleSheet("""
            QPushButton {
                font-size: 16px; font-family: Oxanium; padding: 10px;
                background-color: #a94442; color: white; border-radius: 5px; margin-top: 30px;
            }
            QPushButton:hover { background-color: #c95452; }
        """)
        exit_button.clicked.connect(self.exit_app_clicked.emit)
        settings_layout.addWidget(view_label)
        settings_layout.addWidget(self.view_list)
        settings_layout.addWidget(theme_label)
        settings_layout.addWidget(self.theme_checkbox)
        settings_layout.addStretch()
        settings_layout.addWidget(exit_button)
        self.view_list.setCurrentRow(0)

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events to exit on Escape."""
        if event.key() == Qt.Key.Key_Escape:
            self.escape_pressed.emit()
        else:
            super().keyPressEvent(event)

    @Slot(str)
    def update_bluetooth_status(self, status_text):
        self.bt_status_value.setText(status_text)
        
    @Slot(int)
    def on_view_selected(self, index):
        self.view_changed.emit(index)

    @Slot(int)
    def on_theme_toggled(self, state):
        is_light_mode = bool(state)
        self.theme_changed.emit(is_light_mode)
