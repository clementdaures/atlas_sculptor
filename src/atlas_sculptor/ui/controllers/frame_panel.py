# -*- coding: utf-8 -*-
"""
Frame & layer list panel logic for the Atlas Shot Sculptor tool's UI.

Populates the frame and layer ``QListWidget``s from the currently managed
mesh's node data, and implements the Create/Delete Frame and
Add/Rename/Reorder Layer button behaviour.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# python modules
from __future__ import annotations
import functools

# pyside modules
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

# import dcc
import maya.cmds as cmds

# atlas_sculptor/core/...
from atlas_sculptor.core.scene import frames
from atlas_sculptor.core.models import layers

# atlas_sculptor/ui/...
from atlas_sculptor.ui.widgets.layer_row import LayerRowWidget

# endregion

# ==========

# region Frame Panel UI

class FramePanelMixin:
    """Mixin providing frame/layer list population and editing behaviour
    for ``AtlasShotSculptorUi``.

    Assumes the host class also mixes in
    :class:`.edit_controller.EditControllerMixin` (for ``_exit_current_edit``
    / ``_toggle_edit_for``) and :class:`.selection_sync.SelectionSyncMixin`
    (for ``_suppressed_selection_sync``), and stores ``_current_mesh``,
    ``_selected_frame_time``, ``_selected_layer_index`` and
    ``_editing_layer_index``.
    """

    # region Frame List

    def _refresh_frame_list(self) -> None:
        """Repopulate the frame list for ``self._current_mesh``.

        Signals are blocked throughout, including while restoring the
        previously-selected row, so this never re-enters
        :meth:`_on_frame_row_changed` on its own -- callers that need the
        layer list refreshed too must do so explicitly afterward.
        """
        self._frame_list.blockSignals(True)
        self._frame_list.clear()

        restore_row = -1
        if self._current_mesh:
            for frame_time, label in frames.get_frame_entries(self._current_mesh):
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, frame_time)
                self._frame_list.addItem(item)
                if frame_time == self._selected_frame_time:
                    restore_row = self._frame_list.count() - 1

        self._frame_list.setCurrentRow(restore_row)
        self._frame_list.blockSignals(False)

        if restore_row < 0:
            self._selected_frame_time = None
            self._selected_layer_index = None
            self._delete_frame_btn.setEnabled(False)
            self._add_layer_btn.setEnabled(False)
            self._refresh_layer_list()
        else:
            self._delete_frame_btn.setEnabled(True)
            self._add_layer_btn.setEnabled(True)

    def _selected_frame_time_from_list(self) -> int | None:
        item = self._frame_list.currentItem()
        return item.data(Qt.UserRole) if item is not None else None

    def _on_frame_row_changed(self, row: int) -> None:
        """Slot: frame list selection changed by the user."""
        self._exit_current_edit()

        if row < 0:
            self._selected_frame_time = None
            self._selected_layer_index = None
            self._delete_frame_btn.setEnabled(False)
            self._add_layer_btn.setEnabled(False)
            self._refresh_layer_list()
            self._set_status("No frame selected")
            return

        self._selected_frame_time = self._selected_frame_time_from_list()
        self._selected_layer_index = None
        self._delete_frame_btn.setEnabled(True)
        self._add_layer_btn.setEnabled(True)
        self._refresh_layer_list()
        self._set_status(f"Frame {self._selected_frame_time} selected")

    def _on_create_frame_clicked(self) -> None:
        """Slot: Create Sculpt Frame button."""
        if not self._current_mesh:
            cmds.warning("No managed mesh selected.")
            return

        with self._suppressed_selection_sync():
            result = frames.create_sculpt_frame(self._current_mesh)
        if result is None:
            return

        frame_time, layer_index = result
        self._selected_frame_time = frame_time
        self._selected_layer_index = layer_index
        self._refresh_frame_list()
        self._refresh_layer_list()
        self._select_layer_row(layer_index)
        self._set_status(f"Created frame {frame_time}")

    def _on_delete_frame_clicked(self) -> None:
        """Slot: Delete Sculpt Frame button."""
        if not self._current_mesh or self._selected_frame_time is None:
            cmds.warning("No sculpt frame selected to delete.")
            return

        self._exit_current_edit()
        with self._suppressed_selection_sync():
            frames.delete_frame(self._current_mesh, self._selected_frame_time)

        self._selected_frame_time = None
        self._selected_layer_index = None
        self._refresh_frame_list()
        self._set_status("Frame deleted")

    # endregion

    # ==========

    # region Layer list

    def _refresh_layer_list(self) -> None:
        """Repopulate the layer list for the currently selected frame."""
        self._layer_list.clear()

        if not self._current_mesh or self._selected_frame_time is None:
            self._anim_group.setEnabled(False)
            return

        entries = layers.get_layer_entries(self._current_mesh, self._selected_frame_time)
        for position, (layer_index, name, enabled, is_base) in enumerate(entries):
            can_move_up = (not is_base) and position > 0 and not entries[position - 1][3]
            can_move_down = (
                (not is_base) and position < len(entries) - 1 and not entries[position + 1][3]
            )

            row_widget = LayerRowWidget(
                name=name,
                enabled=enabled,
                is_base=is_base,
                is_editing=(layer_index == self._editing_layer_index),
                can_move_up=can_move_up,
                can_move_down=can_move_down,
            )
            row_widget.toggled.connect(functools.partial(self._on_layer_toggled, layer_index))
            row_widget.renamed.connect(functools.partial(self._on_layer_renamed, layer_index))
            row_widget.edit_clicked.connect(functools.partial(self._on_layer_edit_clicked, layer_index))
            row_widget.move_up_clicked.connect(functools.partial(self._on_move_layer, layer_index, -1))
            row_widget.move_down_clicked.connect(functools.partial(self._on_move_layer, layer_index, 1))

            item = QListWidgetItem()
            item.setData(Qt.UserRole, layer_index)
            item.setSizeHint(row_widget.sizeHint())
            self._layer_list.addItem(item)
            self._layer_list.setItemWidget(item, row_widget)

        self._anim_group.setEnabled(self._editing_layer_index is not None)

    def _select_layer_row(self, layer_index: int) -> None:
        """Highlight *layer_index*'s row in the layer list, if present."""
        for row in range(self._layer_list.count()):
            item = self._layer_list.item(row)
            if item is not None and item.data(Qt.UserRole) == layer_index:
                self._layer_list.setCurrentRow(row)
                self._selected_layer_index = layer_index
                return

    def _on_add_layer_clicked(self) -> None:
        """Slot: + Add Layer button -- adds a non-base layer to the selected frame."""
        if not self._current_mesh or self._selected_frame_time is None:
            cmds.warning("No sculpt frame selected.")
            return

        with self._suppressed_selection_sync():
            new_index = layers.add_layer_to_frame(self._current_mesh, self._selected_frame_time)
        if new_index is None:
            return

        self._selected_layer_index = new_index
        self._refresh_frame_list()
        self._refresh_layer_list()
        self._select_layer_row(new_index)
        self._set_status(f"Added layer {new_index}")

    def _on_layer_toggled(self, layer_index: int, enabled: bool) -> None:
        """Slot: a layer row's mute checkbox was toggled."""
        if not self._current_mesh:
            return
        layers.set_layer_enabled(self._current_mesh, layer_index, enabled)

    def _on_layer_renamed(self, layer_index: int, new_name: str) -> None:
        """Slot: a layer row's inline label was renamed (double-click)."""
        if not self._current_mesh:
            return
        layers.rename_layer(self._current_mesh, layer_index, new_name)

    def _on_rename_layer_clicked(self) -> None:
        """Slot: Rename Layer button (also triggered by Return in the field)."""
        if not self._current_mesh or self._selected_layer_index is None:
            cmds.warning("No layer selected to rename.")
            return

        new_name = self._rename_field.text().strip()
        if not new_name:
            cmds.warning("Please enter a non-empty name.")
            return

        layers.rename_layer(self._current_mesh, self._selected_layer_index, new_name)
        self._rename_field.clear()
        self._refresh_layer_list()
        self._select_layer_row(self._selected_layer_index)

    def _on_move_layer(self, layer_index: int, direction: int) -> None:
        """Slot: a layer row's up/down re-order button was clicked.

        Args:
            layer_index (int): The layer being moved.
            direction (int): ``-1`` to move up (earlier), ``1`` to move down.
        """
        if not self._current_mesh or self._selected_frame_time is None:
            return

        entries = layers.get_layer_entries(self._current_mesh, self._selected_frame_time)
        non_base_order = [idx for idx, _name, _enabled, is_base in entries if not is_base]

        try:
            pos = non_base_order.index(layer_index)
        except ValueError:
            return
        new_pos = pos + direction
        if not (0 <= new_pos < len(non_base_order)):
            return

        non_base_order[pos], non_base_order[new_pos] = non_base_order[new_pos], non_base_order[pos]
        layers.reorder_layers(self._current_mesh, self._selected_frame_time, non_base_order)
        self._refresh_layer_list()
        self._select_layer_row(layer_index)

    def _on_layer_edit_clicked(self, layer_index: int) -> None:
        """Slot: a layer row's pencil (sculpt-edit) toggle was clicked."""
        self._selected_layer_index = layer_index
        self._toggle_edit_for(layer_index)
        self._refresh_layer_list()
        self._select_layer_row(layer_index)

    # endregion

# endregion