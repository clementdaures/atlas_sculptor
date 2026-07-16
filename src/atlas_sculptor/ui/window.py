# -*- coding: utf-8 -*-
"""
PySide6 UI for the Atlas Shot Sculptor tool.

All Maya operations are delegated to :mod:`atlas_sculptor.core`.
This module owns widget construction and top-level state; the mixins in
:mod:`.selection_sync`, :mod:`.edit_controller`, and :mod:`.frame_panel`
implement the actual behaviour (selection tracking, sculpt edit mode, and
frame/layer list management, respectively). Node deletion goes through the
Tools menu and a confirmation dialog -- see :mod:`.delete_dialog`.

Author: Clement Daures
Website: clementdaures.com
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QLineEdit, QComboBox,
    QGroupBox, QListWidget, QMessageBox, QMenuBar, QStackedWidget,
)
from PySide6.QtGui import QAction

import maya.cmds as cmds

from atlas_sculptor.core import node

from . import styles
from .delete_dialog import DeleteNodeDialog
from .edit_controller import EditControllerMixin
from .frame_panel import FramePanelMixin
from .selection_sync import SelectionSyncMixin



# Main window


class AtlasShotSculptorUi(SelectionSyncMixin, EditControllerMixin, FramePanelMixin, QMainWindow):
    """Main window for the Atlas Shot Sculptor tool.

    Owns all UI state (current mesh, selected frame/layer, sculpt-edit
    state) and routes every user interaction to the stateless helpers in
    :mod:`atlas_sculptor.core`. Behaviour is split across three mixins:

    * :class:`.selection_sync.SelectionSyncMixin` -- keeps the upper frame
      in sync with the active Maya selection.
    * :class:`.edit_controller.EditControllerMixin` -- sculpt edit-mode
      entry/exit for a single layer.
    * :class:`.frame_panel.FramePanelMixin` -- frame & layer list
      population and the Create/Delete/Add/Rename/Reorder button behaviour.

    Node deletion (Tools menu) is handled directly on this class since it
    concerns the whole window's state (current mesh vs. whole scene), not
    just one panel.
    """


    # Construction


    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # --- Internal state ---
        self._current_mesh: str | None = None
        self._selected_frame_time: int | None = None
        self._selected_layer_index: int | None = None
        self._editing_layer_index: int | None = None

        # Selection-sync bookkeeping (see SelectionSyncMixin).
        self._suppress_selection_sync: bool = False
        self._maya_selection_set_by_us: set[str] | None = None
        self._selection_script_job: int | None = None

        # --- Window chrome ---
        self.setWindowTitle("Atlas Sculptor 1.0.0 - Maya")
        self.setMinimumWidth(340)
        self.setStyleSheet(styles.main_stylesheet())

        # --- Build layout ---
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        self._build_menubar(root)

        self._upper_stack = QStackedWidget()
        self._build_initialize_page()       # -> index PAGE_INITIALIZE
        self._build_frame_displayer_page()  # -> index PAGE_FRAME_DISPLAYER
        root.addWidget(self._upper_stack)

        root.addStretch()

        # --- Selection tracking & initial state ---
        self._register_selection_script_job()
        self._on_selection_changed()


    # Layout builders


    def _build_menubar(self, layout: QVBoxLayout) -> None:
        menubar = QMenuBar()
        file_menu = menubar.addMenu("Edit")
        tools_menu = menubar.addMenu("Tools")
        help_menu = menubar.addMenu("Help")

        file_menu.addAction(QAction("Save settings", self))
        file_menu.addAction(QAction("Reset settings", self))

        delete_selection_action = QAction("Delete Custom Node for Selection", self)
        delete_selection_action.setToolTip(
            "Delete the Shot Sculptor node for the currently selected mesh only."
        )
        delete_selection_action.triggered.connect(self._on_delete_node_for_selection)
        tools_menu.addAction(delete_selection_action)

        delete_all_action = QAction("Delete All Custom Nodes", self)
        delete_all_action.setToolTip(
            "Delete every Shot Sculptor node found anywhere in the scene."
        )
        delete_all_action.triggered.connect(self._on_delete_all_nodes)
        tools_menu.addAction(delete_all_action)

        help_menu.addAction(QAction("Help on Atlas Sculptor", self))
        layout.setMenuBar(menubar)

    def _build_initialize_page(self) -> None:
        """Page shown when the selection has no Atlas Sculptor node yet."""
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(5, 5, 5, 5)
        page_layout.setSpacing(8)

        group = QGroupBox("Initialize")
        group.setStyleSheet(styles.groupbox_style())
        inner = QVBoxLayout(group)

        self._init_hint_label = QLabel("Select a skinned mesh to begin.")
        self._init_hint_label.setWordWrap(True)
        self._init_hint_label.setStyleSheet("color: #999999; font-size: 10px;")
        inner.addWidget(self._init_hint_label)

        create_group_btn = QPushButton("Initialize Blendshape")
        create_group_btn.setStyleSheet(styles.green_action_button_style())
        create_group_btn.clicked.connect(self._on_create_group)
        inner.addWidget(create_group_btn)

        page_layout.addWidget(group)
        page_layout.addStretch()

        self._upper_stack.addWidget(page)

    def _build_frame_displayer_page(self) -> None:
        """Page shown once the selected mesh has an Atlas Sculptor node."""
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(5, 5, 5, 5)
        page_layout.setSpacing(6)

        frame_btn_row = QHBoxLayout()
        frame_btn_row.setSpacing(4)

        self._create_frame_btn = QPushButton("Create Sculpt Frame")
        self._create_frame_btn.setStyleSheet(styles.green_action_button_style())
        self._create_frame_btn.clicked.connect(self._on_create_frame_clicked)
        frame_btn_row.addWidget(self._create_frame_btn)

        self._delete_frame_btn = QPushButton("Delete Sculpt Frame")
        self._delete_frame_btn.setEnabled(False)
        self._delete_frame_btn.setStyleSheet(styles.red_action_button_style())
        self._delete_frame_btn.clicked.connect(self._on_delete_frame_clicked)
        frame_btn_row.addWidget(self._delete_frame_btn)

        page_layout.addLayout(frame_btn_row)

        self._frame_list = QListWidget()
        self._frame_list.setMinimumHeight(90)
        self._frame_list.setStyleSheet(styles.listwidget_style())
        self._frame_list.currentRowChanged.connect(self._on_frame_row_changed)
        page_layout.addWidget(self._frame_list)

        layer_header_row = QHBoxLayout()
        layer_label = QLabel("Layers")
        layer_label.setStyleSheet("font-weight: bold; font-size: 10px; color: #cccccc;")
        layer_header_row.addWidget(layer_label)
        layer_header_row.addStretch()

        self._add_layer_btn = QPushButton("+ Add Layer")
        self._add_layer_btn.setEnabled(False)
        self._add_layer_btn.clicked.connect(self._on_add_layer_clicked)
        layer_header_row.addWidget(self._add_layer_btn)

        page_layout.addLayout(layer_header_row)

        self._layer_list = QListWidget()
        self._layer_list.setMinimumHeight(130)
        self._layer_list.setStyleSheet(styles.listwidget_style())
        page_layout.addWidget(self._layer_list)

        self._build_animation_settings(page_layout)
        self._build_status(page_layout)

        self._upper_stack.addWidget(page)

    def _build_animation_settings(self, layout: QVBoxLayout) -> None:
        self._anim_group = QGroupBox("Animation Settings")
        self._anim_group.setStyleSheet(styles.groupbox_style())
        self._anim_group.setEnabled(False)
        inner = QVBoxLayout(self._anim_group)

        labels_row = QHBoxLayout()
        for text in ("Ease In:", "Ease Out:", "Hold In:", "Hold Out:"):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #cccccc; font-size: 10px;")
            labels_row.addWidget(lbl)
        inner.addLayout(labels_row)

        spinbox_row = QHBoxLayout()
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
            spin.setStyleSheet(styles.spinbox_style())
            spin.valueChanged.connect(self._on_easing_changed)
            spinbox_row.addWidget(spin)
        inner.addLayout(spinbox_row)
        inner.addSpacing(8)

        key_row = QHBoxLayout()
        key_lbl = QLabel("Key Type:")
        key_lbl.setStyleSheet("color: #cccccc; font-size: 10px;")
        self._key_type_combo = QComboBox()
        self._key_type_combo.addItems(["linear", "spline", "stepped"])
        self._key_type_combo.setStyleSheet(styles.combobox_style())
        self._key_type_combo.currentTextChanged.connect(self._on_easing_changed)
        key_row.addWidget(key_lbl)
        key_row.addWidget(self._key_type_combo)
        inner.addLayout(key_row)

        layout.addWidget(self._anim_group)

    def _build_status(self, layout: QVBoxLayout) -> None:
        self._status_label = QLabel("No frame selected")
        self._status_label.setStyleSheet("QLabel { color: #888888; padding: 5px; font-size: 10px; }")
        layout.addWidget(self._status_label)


    # Shared helpers


    def _set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def _on_easing_changed(self) -> None:
        """Slot: any Ease/Hold spinbox or the Key Type combo box changed.

        Connected directly to ``valueChanged``/``currentTextChanged``; Qt
        trims the emitted value since this slot takes no extra arguments.
        """
        self._apply_curve_changes()

    def _force_selection_resync(self) -> None:
        """Recompute the upper-frame state for the current Maya selection.

        Some operations (creating/deleting the Shot Sculptor node) don't
        necessarily change the raw Maya selection, only whether the
        selected mesh is *managed* -- so Maya's ``SelectionChanged``
        scriptJob won't fire on its own. This re-runs the same
        selection-changed logic manually.
        """
        self._suppress_selection_sync = False
        self._maya_selection_set_by_us = None
        self._on_selection_changed()


    # Slots -- group / node level


    def _on_create_group(self) -> None:
        """Slot: Initialize Blendshape button."""
        with self._suppressed_selection_sync():
            node.create_shot_sculpt_node()
        self._force_selection_resync()


    # Slots -- Tools menu (node deletion)


    def _on_delete_node_for_selection(self) -> None:
        """Menu: Tools > Delete Custom Node for Selection.

        Deletes only the Shot Sculptor node that manages the currently
        selected mesh, after asking whether the blendShape deformers
        should go with it.
        """
        if not self._current_mesh:
            cmds.warning("No managed mesh selected.")
            return

        delete_blendshapes = DeleteNodeDialog.ask(
            f'Delete the Shot Sculptor node for "{self._current_mesh}"?',
            parent=self,
        )
        if delete_blendshapes is None:
            return  # Cancelled -- delete nothing.

        self._exit_current_edit()
        with self._suppressed_selection_sync():
            node.delete_shot_sculptor_node(self._current_mesh, delete_blendshapes=delete_blendshapes)
        self._force_selection_resync()

    def _on_delete_all_nodes(self) -> None:
        """Menu: Tools > Delete All Custom Nodes.

        Deletes every Shot Sculptor node in the scene, after asking whether
        the blendShape deformers should go with them.
        """
        delete_blendshapes = DeleteNodeDialog.ask(
            "Delete ALL Shot Sculptor nodes in the scene?",
            parent=self,
        )
        if delete_blendshapes is None:
            return  # Cancelled -- delete nothing.

        self._exit_current_edit()
        with self._suppressed_selection_sync():
            deleted_count = node.delete_all_shot_sculptor_nodes(delete_blendshapes=delete_blendshapes)
        self._force_selection_resync()
        if deleted_count:
            self._set_status(f"Deleted {deleted_count} Shot Sculptor node(s).")