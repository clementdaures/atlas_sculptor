# -*- coding: utf-8 -*-
"""
PySide6 UI for the Atlas Shot Sculptor tool.

All Maya operations are delegated to :mod:`atlas_sculptor.core`.
This module is responsible only for the Qt layer: widgets, signals, and state.

Author: Clement Daures
Website: clementdaures.com
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QLineEdit, QComboBox,
    QGroupBox, QListWidget, QListWidgetItem, QMessageBox,
    QMenuBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

import maya.cmds as cmds

from atlas_sculptor.core import animation, edit_mode, frames, node, selection


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class AtlasShotSculptorUi(QMainWindow):
    """Main window for the Atlas Shot Sculptor tool.

    Owns all UI state (``is_editing``, ``current_edit_index``) and routes every
    user interaction to the stateless helpers in :mod:`core`.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # --- Internal state ---
        self._is_editing: bool = False
        self._current_edit_index: int | None = None

        # --- Window chrome ---
        self.setWindowTitle("Atlas Sculptor 1.0.0 - Maya")
        self.setMinimumWidth(320)
        self.setStyleSheet(self._stylesheet())

        # --- Build layout ---
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        self._build_menubar(root)
        self._build_group_buttons(root)
        self._build_frame_buttons(root)
        self._build_frame_list(root)
        self._build_edit_button(root)
        self._build_animation_settings(root)
        self._build_rename_row(root)
        self._build_status(root)

        root.addStretch()

        # --- Initial state ---
        self._refresh_frame_list()

    # ------------------------------------------------------------------
    # Layout builders (each adds widgets to *layout*)
    # ------------------------------------------------------------------

    def _build_menubar(self, layout: QVBoxLayout) -> None:
        menubar = QMenuBar()
        file_menu = menubar.addMenu("Edit")
        help_menu = menubar.addMenu("Help")
        file_menu.addAction(QAction("Save settings",  self))
        file_menu.addAction(QAction("Reset settings", self))
        help_menu.addAction(QAction("Help on Atlas Autorig", self))
        layout.setMenuBar(menubar)

    def _build_group_buttons(self, layout: QVBoxLayout) -> None:
        col = QVBoxLayout()
        col.setContentsMargins(5, 5, 5, 5)
        col.setSpacing(4)

        create_group = QPushButton("Create Shot Sculpt Group")
        create_group.clicked.connect(self._on_create_group)
        col.addWidget(create_group)

        delete_node = QPushButton("Delete Shot Sculpt Node")
        delete_node.clicked.connect(self._on_delete_node)
        col.addWidget(delete_node)

        layout.addLayout(col)

    def _build_frame_buttons(self, layout: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(5, 0, 5, 0)
        row.setSpacing(4)

        self._create_frame_btn = QPushButton("Create Sculpt Frame")
        self._create_frame_btn.setStyleSheet("""
            QPushButton {
                background-color: #3C7837; color: white;
                border: none; padding: 8px;
                font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #4a9445; }
        """)
        self._create_frame_btn.clicked.connect(self._on_create_frame)
        row.addWidget(self._create_frame_btn)

        self._delete_frame_btn = QPushButton("Delete Sculpt Frame")
        self._delete_frame_btn.setStyleSheet("""
            QPushButton {
                background-color: #C44848; color: white;
                border: none; padding: 8px;
                font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #8d4040; }
        """)
        self._delete_frame_btn.clicked.connect(self._on_delete_frame)
        row.addWidget(self._delete_frame_btn)

        layout.addLayout(row)

    def _build_frame_list(self, layout: QVBoxLayout) -> None:
        """Replace the placeholder QFrame with a real QListWidget."""
        self._frame_list = QListWidget()
        self._frame_list.setMinimumHeight(150)
        self._frame_list.setStyleSheet("""
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
        """)
        self._frame_list.currentRowChanged.connect(self._on_frame_selected)
        layout.addWidget(self._frame_list)

    def _build_edit_button(self, layout: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(5, 0, 5, 0)

        self._edit_btn = QPushButton("Edit Frame")
        self._edit_btn.setEnabled(False)
        self._edit_btn.clicked.connect(self._on_edit_frame)
        row.addWidget(self._edit_btn)

        layout.addLayout(row)

    def _build_animation_settings(self, layout: QVBoxLayout) -> None:
        group = QGroupBox("Animation Settings")
        group.setStyleSheet("""
            QGroupBox {
                color: #cccccc; border: 1px solid #7a53cf;
                border-radius: 5px; margin-top: 10px;
                padding: 4px; font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 5px;
            }
        """)
        inner = QVBoxLayout(group)

        # Labels row
        labels_row = QHBoxLayout()
        for text in ("Ease In:", "Ease Out:", "Hold In:", "Hold Out:"):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #cccccc; font-size: 10px;")
            lbl.setAlignment(Qt.AlignCenter)
            labels_row.addWidget(lbl)
        inner.addLayout(labels_row)

        # Spinboxes row
        spinbox_row = QHBoxLayout()
        spinbox_style = """
            QSpinBox {
                background-color: #3a3a3a; color: white;
                border: 1px solid #555555; padding: 3px; font-size: 8px;
            }
            QSpinBox:hover { border: 1px solid #7a53cf; }
        """
        defaults = (1, 1, 0, 0)
        self._ease_in_spin, self._ease_out_spin, self._hold_in_spin, self._hold_out_spin = (
            QSpinBox() for _ in defaults
        )
        for spin, val in zip(
            (self._ease_in_spin, self._ease_out_spin, self._hold_in_spin, self._hold_out_spin),
            defaults,
        ):
            spin.setValue(val)
            spin.setMinimum(0)
            spin.setMaximum(999)
            spin.setStyleSheet(spinbox_style)
            spin.valueChanged.connect(self._on_easing_changed)
            spinbox_row.addWidget(spin)
        inner.addLayout(spinbox_row)
        inner.addSpacing(8)

        # Key type row
        key_row = QHBoxLayout()
        key_lbl = QLabel("Key Type:")
        key_lbl.setStyleSheet("color: #cccccc; font-size: 10px;")
        self._key_type_combo = QComboBox()
        self._key_type_combo.addItems(["linear", "spline", "stepped"])
        self._key_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a; color: white;
                border: 1px solid #555555; padding: 3px; font-size: 10px;
            }
            QComboBox:hover { border: 1px solid #7a53cf; }
            QComboBox QAbstractItemView {
                background-color: #262626; color: #ddd;
                selection-background-color: #7a53cf;
            }
        """)
        self._key_type_combo.currentTextChanged.connect(self._on_easing_changed)
        key_row.addWidget(key_lbl)
        key_row.addWidget(self._key_type_combo)
        inner.addLayout(key_row)

        layout.addWidget(group)

    def _build_rename_row(self, layout: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(5, 0, 5, 0)

        self._rename_field = QLineEdit()
        self._rename_field.setPlaceholderText("New frame name…")
        self._rename_field.setStyleSheet("""
            QLineEdit {
                background-color: #262626; color: white;
                border: 1px solid #555555; padding: 5px; font-size: 10px;
            }
            QLineEdit:hover { border: 1px solid #7a53cf; }
        """)
        # Allow pressing enter to rename
        self._rename_field.returnPressed.connect(self._on_rename_frame)
        row.addWidget(self._rename_field, stretch=1)

        rename_btn = QPushButton("Rename Frame")
        rename_btn.clicked.connect(self._on_rename_frame)
        row.addWidget(rename_btn, stretch=1)

        layout.addLayout(row)

    def _build_status(self, layout: QVBoxLayout) -> None:
        self._status_label = QLabel("No frame selected")
        self._status_label.setStyleSheet("""
            QLabel { color: #888888; padding: 5px; font-size: 10px; }
        """)
        layout.addWidget(self._status_label)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _stylesheet() -> str:
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

    def _set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def _refresh_frame_list(self) -> None:
        """Repopulate the QListWidget from the Atlas Shot Sculptor node data."""
        self._frame_list.blockSignals(True)
        self._frame_list.clear()

        for idx, frame_time, label in frames.get_frame_entries():
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, idx)
            self._frame_list.addItem(item)

        self._frame_list.blockSignals(False)
        self._edit_btn.setEnabled(False)
        self._set_status("No frame selected")

    def _selected_item_index(self) -> int | None:
        """Return the Atlas Shot Sculptor attribute index of the currently selected list item.

        Returns:
            int | None: Attribute index stored in ``Qt.UserRole``, or ``None``.
        """
        item = self._frame_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _apply_curve_changes(self) -> None:
        """Read all animation-settings widgets and push them to Maya."""
        frame_index = self._selected_item_index()
        if frame_index is None:
            return
        animation.update_frame_animation(
            frame_index,
            ease_in  = self._ease_in_spin.value(),
            ease_out = self._ease_out_spin.value(),
            hold_in  = self._hold_in_spin.value(),
            hold_out = self._hold_out_spin.value(),
            key_type = self._key_type_combo.currentText(),
        )

    # ------------------------------------------------------------------
    # Slots — group / node level
    # ------------------------------------------------------------------

    def _on_create_group(self) -> None:
        """Slot: Create Shot Sculpt Group button."""
        node.create_shot_sculpt_node()
        self._refresh_frame_list()

    def _on_delete_node(self) -> None:
        """Slot: Delete Shot Sculpt Node button — asks for confirmation first."""
        answer = QMessageBox.question(
            self,
            "Delete Sculpt Node",
            "Are you sure you want to delete the Shot Sculptor node and all associated blendShapes?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if answer == QMessageBox.Yes:
            # If we were mid-edit, reset state to avoid stale indices.
            self._is_editing = False
            self._current_edit_index = None
            self._edit_btn.setText("Edit Frame")
            node.delete_shot_sculptor_node()
            self._refresh_frame_list()

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Edit-mode helpers
    # ------------------------------------------------------------------

    def _exit_current_edit(self) -> None:
        """Exit edit mode on whatever frame is currently active, if any.

        Safe to call when not editing — does nothing in that case.
        """
        if not self._is_editing or self._current_edit_index is None:
            return
        edit_mode.exit_edit_mode(self._current_edit_index)
        self._apply_curve_changes()
        self._is_editing = False
        self._current_edit_index = None
        self._edit_btn.setText("Edit Frame")

    def _enter_edit_for(self, frame_index: int) -> None:
        """Exit any active edit then enter edit mode for *frame_index*.

        Args:
            frame_index (int): Attribute index of the frame to activate.
        """
        if self._is_editing and self._current_edit_index == frame_index:
            return  # Already editing this frame, nothing to do.

        self._exit_current_edit()

        frame_time = frames.get_frame_time(frame_index)
        edit_mode.enter_edit_mode(frame_index)
        self._is_editing = True
        self._current_edit_index = frame_index
        self._edit_btn.setText("Finish Editing")
        self._set_status(f"Editing Frame {frame_time}  (target {frame_index})")

    # ------------------------------------------------------------------
    # Slots — frame level
    # ------------------------------------------------------------------

    def _on_create_frame(self) -> None:
        """Slot: Create Sculpt Frame button."""
        new_index = frames.create_sculpt_frame()
        self._refresh_frame_list()

        if new_index is not None:
            # Select the new row — triggers _on_frame_selected which auto-enters
            # edit mode, so no explicit enter_edit_for call needed here.
            for row in range(self._frame_list.count()):
                item = self._frame_list.item(row)
                if item is not None and item.data(Qt.UserRole) == new_index:
                    self._frame_list.setCurrentItem(item)
                    break

    def _on_delete_frame(self) -> None:
        """Slot: Delete Sculpt Frame button."""
        frame_index = self._selected_item_index()
        if frame_index is None:
            cmds.warning("No sculpt frame selected to delete.")
            return

        if self._is_editing and frame_index == self._current_edit_index:
            self._exit_current_edit()

        frames.delete_sculpt_frame(frame_index)
        self._refresh_frame_list()

    def _on_frame_selected(self, row: int) -> None:
        """Slot: QListWidget selection changed.

        Automatically switches the blendShape sculpt target to the newly
        selected frame, exiting the previous edit cleanly first.
        """
        if row < 0:
            self._exit_current_edit()
            self._edit_btn.setEnabled(False)
            self._set_status("No frame selected")
            return

        frame_index = self._selected_item_index()
        if frame_index is None:
            return

        self._edit_btn.setEnabled(True)
        self._enter_edit_for(frame_index)

    def _on_edit_frame(self) -> None:
        """Slot: Edit Frame / Finish Editing button.

        Since selecting a frame already enters edit mode automatically, this
        button is primarily used to explicitly finish (lock in) the current edit.
        """
        frame_index = self._selected_item_index()
        if frame_index is None:
            cmds.warning("No sculpt frame selected to edit.")
            return

        if self._is_editing and self._current_edit_index == frame_index:
            frame_time = frames.get_frame_time(frame_index)
            self._exit_current_edit()
            self._set_status(f"Selected Frame {frame_time}  (target {frame_index})")
        else:
            self._enter_edit_for(frame_index)

    def _on_rename_frame(self) -> None:
        """Slot: Rename Frame button (also triggered by Return in the text field)."""
        frame_index = self._selected_item_index()
        if frame_index is None:
            cmds.warning("No frame selected to rename.")
            return

        new_name = self._rename_field.text().strip()
        if not new_name:
            cmds.warning("Please enter a non-empty name.")
            return

        frames.rename_frame(frame_index, new_name)
        self._rename_field.clear()
        self._refresh_frame_list()

    def _on_easing_changed(self) -> None:
        """Slot: any animation-settings widget changed its value."""
        self._apply_curve_changes()