from PyQt5.QtCore import QSize

APP_NAME = "brsrk.s"
APP_WINDOW_TITLE = "brsrk.s"

THUMB_SIZE = QSize(180, 270)
LARGE_SIZE = QSize(400, 600)
CATALOG_CELL_SIZE = QSize(220, 390)
BATCH_SIZE = 100
MAX_LOADED = 2000

COLORS = {
    "bg_primary": "#1e1e2e",
    "bg_secondary": "#313244",
    "bg_tertiary": "#45475a",
    "accent": "#cba6f7",
    "accent_hover": "#b4befe",
    "text_primary": "#cdd6f4",
    "text_secondary": "#bac2de",
    "border": "#585b70",
    "success": "#a6e3a1",
    "warning": "#f9e2af",
    "error": "#f38ba8",
}


def get_stylesheet():
    return f"""
    QMainWindow, QWidget {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }}
    QLineEdit {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        color: {COLORS['text_primary']};
    }}
    QLineEdit:focus {{
        border-color: {COLORS['accent']};
        background-color: {COLORS['bg_tertiary']};
    }}
    QComboBox {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        color: {COLORS['text_primary']};
        min-width: 120px;
    }}
    QComboBox:hover {{
        border-color: {COLORS['accent_hover']};
        background-color: {COLORS['bg_tertiary']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {COLORS['text_secondary']};
    }}
    QSpinBox {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px;
        font-size: 14px;
        color: {COLORS['text_primary']};
        min-width: 60px;
    }}
    QSpinBox:focus {{
        border-color: {COLORS['accent']};
        background-color: {COLORS['bg_tertiary']};
    }}
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                   stop:0 {COLORS['accent']},
                                   stop:1 #9d7cd8);
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: bold;
        color: white;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                   stop:0 {COLORS['accent_hover']},
                                   stop:1 #a78bfa);
    }}
    QPushButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                   stop:0 #8b5cf6,
                                   stop:1 #7c3aed);
    }}
    QLabel {{
        color: {COLORS['text_primary']};
        font-size: 14px;
        font-weight: 500;
    }}
    QListWidget {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 12px;
        padding: 10px;
        selection-background-color: transparent;
    }}
    QScrollArea {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 12px;
    }}
    QScrollBar:vertical {{
        background-color: {COLORS['bg_tertiary']};
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background-color: {COLORS['accent']};
        border-radius: 6px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['accent_hover']};
    }}
    QSplitter::handle {{
        background-color: {COLORS['border']};
        width: 2px;
    }}
    .stats-label {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 {COLORS['bg_tertiary']},
                                   stop:1 {COLORS['bg_secondary']});
        border: 2px solid {COLORS['border']};
        border-radius: 10px;
        padding: 12px;
        font-size: 16px;
        font-weight: bold;
        color: {COLORS['text_primary']};
    }}
    .card-widget {{
        background-color: {COLORS['bg_secondary']};
        border: 2px solid {COLORS['border']};
        border-radius: 12px;
        padding: 8px;
    }}
    .card-widget:hover {{
        border-color: {COLORS['accent']};
        background-color: {COLORS['bg_tertiary']};
    }}
    .card-widget-insufficient {{
        background-color: {COLORS['error']};
        border: 2px solid {COLORS['error']};
        border-radius: 12px;
        padding: 8px;
    }}
    .card-widget-insufficient:hover {{
        border-color: {COLORS['error']};
        background-color: #f87171;
    }}
    QCheckBox {{
        color: {COLORS['text_primary']};
        font-size: 12px;
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        background-color: {COLORS['bg_secondary']};
    }}
    QCheckBox::indicator:hover {{
        border-color: {COLORS['accent_hover']};
        background-color: {COLORS['bg_tertiary']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent']};
        border-color: {COLORS['accent']};
    }}
    QGroupBox {{
        color: {COLORS['text_primary']};
        font-size: 14px;
        font-weight: bold;
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 8px;
    }}
    """
