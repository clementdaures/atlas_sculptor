# -*- coding: utf-8 -*-
"""
Shared Qt stylesheets for the Atlas Shot Sculptor tool's UI.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# python modules
from __future__ import annotations

# endregion

# ==========

# region Stylesheet

def main_stylesheet() -> str:
    """Stylesheet applied to the whole main window."""
    return """
        QWidget {
            background-color: #303030;
            color: #ddd;
            font-family: Segoe UI;
            font-size: 8pt;
        }
        QMenuBar::item:selected { background-color: #7a53cf; color: #fff; }
        QMenu::item:selected    { background-color: #7a53cf; color: #fff; }
        QPushButton {
            background-color: #404040;
            border: 1px solid #262626;
            border-radius: 4px;
            padding: 4px 8px;
        }
        QPushButton:hover {
            background-color: #404040;
            border: 1px solid #7a53cf;
        }
        QPushButton:disabled {
            background-color: #383838;
            color: #666;
            border: 1px solid #303030;
        }
        QGroupBox {
            border: 1px solid #7a53cf;
            border-radius: 5px;
            margin-top: 6px;
            padding: 4px;
            font-weight: bold;
        }
    """


def groupbox_style() -> str:
    """Stylesheet applied to each individual QGroupBox."""
    return """
        QGroupBox {
            color: #cccccc; border: 1px solid #7a53cf;
            border-radius: 5px; margin-top: 10px;
            padding: 4px; font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin; left: 10px; padding: 0 5px;
        }
    """


def listwidget_style() -> str:
    """Stylesheet applied to the frame and layer QListWidgets."""
    return """
        QListWidget {
            background-color: #262626;
            border: 1px solid #7a53cf;
            margin: 5px;
            color: #dddddd;
            font-size: 10px;
        }
        QListWidget::item:selected {
            background-color: #7a53cf;
            color: #ffffff;
        }
        QListWidget::item:hover {
            background-color: #3a2e5e;
        }
    """


def spinbox_style() -> str:
    """Stylesheet applied to the Ease/Hold spin boxes."""
    return """
        QSpinBox {
            background-color: #3a3a3a; color: white;
            border: 1px solid #555555; padding: 3px; font-size: 8px;
        }
        QSpinBox:hover { border: 1px solid #7a53cf; }
    """


def combobox_style() -> str:
    """Stylesheet applied to the Key Type combo box."""
    return """
        QComboBox {
            background-color: #3a3a3a; color: white;
            border: 1px solid #555555; padding: 3px; font-size: 10px;
        }
        QComboBox:hover { border: 1px solid #7a53cf; }
        QComboBox QAbstractItemView {
            background-color: #262626; color: #ddd;
            selection-background-color: #7a53cf;
        }
    """


def green_action_button_style() -> str:
    """Stylesheet applied to the "create" style buttons (Initialize, Create Frame)."""
    return """
        QPushButton {
            background-color: #3C7837; color: white;
            border: none; padding: 8px;
            font-size: 10px; font-weight: bold;
        }
        QPushButton:hover { background-color: #4a9445; }
    """


def red_action_button_style() -> str:
    """Stylesheet applied to the "destructive" style buttons (Delete Frame)."""
    return """
        QPushButton {
            background-color: #C44848; color: white;
            border: none; padding: 8px;
            font-size: 10px; font-weight: bold;
        }
        QPushButton:hover { background-color: #8d4040; }
    """


def edit_toggle_button_style() -> str:
    """Stylesheet applied to a layer row's pencil (sculpt-edit) toggle button."""
    return """
        QToolButton { background-color: #404040; border: 1px solid #262626; border-radius: 3px; }
        QToolButton:checked { background-color: #7a53cf; border: 1px solid #a37bf0; color: white; }
    """

# endregion