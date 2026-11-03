"""Оформлення вікна: кольорові теми та таблиця стилів Qt (QSS)."""

THEMES = {
    "dark": {
        "bg": "#14161B",
        "panel": "#1A1D24",
        "field": "#1F232B",
        "border": "#2A2F3A",
        "text": "#E6E8EB",
        "muted": "#8D95A3",
        "accent": "#4C8DFF",
        "accent_hover": "#6AA0FF",
        "accent_text": "#FFFFFF",
        "selection": "#25447A",
        "hover": "#232833",
        "danger": "#F0616D",
    },
    "light": {
        "bg": "#F4F5F8",
        "panel": "#FFFFFF",
        "field": "#FFFFFF",
        "border": "#DCDFE6",
        "text": "#1B1F27",
        "muted": "#667085",
        "accent": "#2F6FED",
        "accent_hover": "#255BC4",
        "accent_text": "#FFFFFF",
        "selection": "#D8E6FF",
        "hover": "#EDEFF4",
        "danger": "#D6303F",
    },
}

DEFAULT_THEME = "dark"


def label_colors(theme: str) -> dict:
    """Кольори підписів авторів у чаті."""
    t = THEMES[theme]
    return {"Ти": t["accent"], "DocChat": t["text"], "Помилка": t["danger"]}


def stylesheet(theme: str) -> str:
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    return f"""
QMainWindow, QWidget {{
    background-color: {t['bg']};
    color: {t['text']};
}}

QLabel {{ background: transparent; }}
QLabel#brand {{ font-size: 20px; font-weight: 700; padding: 4px 2px 2px 2px; }}
QLabel#section {{ color: {t['muted']}; font-size: 11px; font-weight: 600; padding-top: 6px; }}
QLabel#muted {{ color: {t['muted']}; }}

QListWidget {{
    background-color: {t['panel']};
    border: 1px solid {t['border']};
    border-radius: 10px;
    padding: 6px;
    outline: 0;
}}
QListWidget::item {{ padding: 8px 10px; border-radius: 6px; }}
QListWidget::item:hover {{ background-color: {t['hover']}; }}
QListWidget::item:selected {{ background-color: {t['selection']}; color: {t['text']}; }}

QTextBrowser {{
    background-color: {t['panel']};
    border: 1px solid {t['border']};
    border-radius: 12px;
    padding: 12px;
    font-size: 14px;
    selection-background-color: {t['selection']};
}}

QLineEdit {{
    background-color: {t['field']};
    border: 1px solid {t['border']};
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 14px;
    selection-background-color: {t['selection']};
}}
QLineEdit:focus {{ border: 1px solid {t['accent']}; }}

QPushButton {{
    background-color: {t['panel']};
    border: 1px solid {t['border']};
    border-radius: 10px;
    padding: 9px 16px;
}}
QPushButton:hover {{ background-color: {t['hover']}; }}
QPushButton:disabled {{ color: {t['muted']}; }}
QPushButton[primary="true"] {{
    background-color: {t['accent']};
    border: 1px solid {t['accent']};
    color: {t['accent_text']};
    font-weight: 600;
}}
QPushButton[primary="true"]:hover {{ background-color: {t['accent_hover']}; }}
QPushButton[primary="true"]:disabled {{ background-color: {t['border']}; border-color: {t['border']}; color: {t['muted']}; }}
QPushButton[flat="true"] {{ background: transparent; border: 1px solid transparent; color: {t['muted']}; }}
QPushButton[flat="true"]:hover {{ background-color: {t['hover']}; color: {t['text']}; }}

QComboBox {{
    background-color: {t['field']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 6px 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {t['panel']};
    border: 1px solid {t['border']};
    selection-background-color: {t['selection']};
    selection-color: {t['text']};
    outline: 0;
}}

QProgressBar {{
    background-color: {t['field']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    text-align: center;
    min-height: 14px;
}}
QProgressBar::chunk {{ background-color: {t['accent']}; border-radius: 5px; }}

QStatusBar {{ background-color: {t['bg']}; color: {t['muted']}; }}
QStatusBar::item {{ border: 0; }}

QSplitter::handle {{ background-color: {t['bg']}; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {t['muted']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
"""
