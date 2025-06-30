# theme.py
from PySide6.QtGui import QColor

DARK_THEME = {
    "bg": "#282828",
    "text_primary": "white",
    "text_secondary": "grey",
    "boat": QColor(150, 150, 150),
    "arrow": QColor(255, 255, 255)
}

LIGHT_THEME = {
    "bg": "#F0F0F0",
    "text_primary": "black",
    "text_secondary": "#505050",
    "boat": QColor(80, 80, 80),
    "arrow": QColor(0, 0, 0)
}