# -*- coding: utf-8 -*-
"""
Small reusable row widgets for the Atlas Shot Sculptor tool's layer list.

Author: Clement Daures
Website: clementdaures.com
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QToolButton
from PySide6.QtCore import Signal

from . import styles


class EditableLabel(QWidget):
    """A label that turns into an inline QLineEdit on double-click."""

    renamed = Signal(str)

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(text)
        self._label.setStyleSheet("font-size: 10px; color: #dddddd;")
        layout.addWidget(self._label)

        self._edit = QLineEdit(text)
        self._edit.setStyleSheet("""
            QLineEdit {
                background-color: #1c1c1c; color: white;
                border: 1px solid #7a53cf; padding: 1px; font-size: 10px;
            }
        """)
        self._edit.hide()
        self._edit.editingFinished.connect(self._finish_edit)
        layout.addWidget(self._edit)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self._start_edit()
        event.accept()

    def _start_edit(self) -> None:
        self._edit.setText(self._label.text())
        self._label.hide()
        self._edit.show()
        self._edit.setFocus()
        self._edit.selectAll()

    def _finish_edit(self) -> None:
        if self._edit.isHidden():
            return
        new_text = self._edit.text().strip()
        self._edit.hide()
        self._label.show()
        if new_text and new_text != self._label.text():
            self._label.setText(new_text)
            self.renamed.emit(new_text)


class LayerRowWidget(QWidget):
    """One row in the layer list: mute toggle, editable name, up/down
    re-order buttons, and an explicit sculpt-edit toggle. The frame's base
    layer gets a "BASE" tag instead of move buttons, since it is always
    pinned to the bottom of the layer stack.
    """

    toggled = Signal(bool)
    renamed = Signal(str)
    edit_clicked = Signal()
    move_up_clicked = Signal()
    move_down_clicked = Signal()

    def __init__(
        self,
        name: str,
        enabled: bool,
        is_base: bool,
        is_editing: bool,
        can_move_up: bool,
        can_move_down: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(4)

        self._enabled_check = QCheckBox()
        self._enabled_check.setChecked(enabled)
        self._enabled_check.setToolTip("Toggle this layer's blendShape target on/off")
        self._enabled_check.toggled.connect(self.toggled.emit)
        row.addWidget(self._enabled_check)

        self._name_label = EditableLabel(name)
        self._name_label.renamed.connect(self.renamed.emit)
        row.addWidget(self._name_label, stretch=1)

        if is_base:
            base_tag = QLabel("BASE")
            base_tag.setStyleSheet("""
                color: #7a53cf; font-size: 8px; font-weight: bold;
                border: 1px solid #7a53cf; border-radius: 3px; padding: 1px 4px;
            """)
            base_tag.setToolTip("The base layer always stays at the bottom of the stack.")
            row.addWidget(base_tag)
        else:
            up_btn = QToolButton()
            up_btn.setText("\u25B2")
            up_btn.setEnabled(can_move_up)
            up_btn.setFixedSize(16, 16)
            up_btn.setToolTip("Move layer up")
            up_btn.clicked.connect(self.move_up_clicked.emit)
            row.addWidget(up_btn)

            down_btn = QToolButton()
            down_btn.setText("\u25BC")
            down_btn.setEnabled(can_move_down)
            down_btn.setFixedSize(16, 16)
            down_btn.setToolTip("Move layer down")
            down_btn.clicked.connect(self.move_down_clicked.emit)
            row.addWidget(down_btn)

        self._edit_btn = QToolButton()
        self._edit_btn.setText("\u23FB")  # toggle
        self._edit_btn.setCheckable(True)
        self._edit_btn.setChecked(is_editing)
        self._edit_btn.setFixedSize(20, 20)
        self._edit_btn.setToolTip("Enter/finish sculpt edit mode for this layer")
        self._edit_btn.setStyleSheet(styles.edit_toggle_button_style())
        self._edit_btn.clicked.connect(self.edit_clicked.emit)
        row.addWidget(self._edit_btn)