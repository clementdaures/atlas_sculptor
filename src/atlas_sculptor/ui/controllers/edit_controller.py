# -*- coding: utf-8 -*-
"""
Sculpt edit-mode state management for the Atlas Shot Sculptor tool's UI.

Tracks which layer, if any, is currently being sculpted, and routes
entry/exit through :mod:`atlas_sculptor.core.edit_mode`, pushing the
Animation Settings widgets' values to the layer being left via
:mod:`atlas_sculptor.core.animation`.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# python modules
from __future__ import annotations

# dcc import
import maya.cmds as cmds

# atlas_sculptor/core/...
from atlas_sculptor.core.models import animation, layers
from atlas_sculptor.core.states import edit_mode

# endregion

# ==========

# region Edit Controller UI

class EditControllerMixin:
    """Mixin providing sculpt edit-mode entry/exit for ``AtlasShotSculptorUi``.

    Assumes the host class also mixes in
    :class:`.selection_sync.SelectionSyncMixin` (for
    ``_suppressed_selection_sync``, since entering edit mode selects
    meshes) and stores ``_current_mesh`` and ``_editing_layer_index``.
    """

    # Animation-settings <-> layer sync

    def _apply_curve_changes(self) -> None:
        """Push the Animation Settings widgets' values to the layer
        currently being edited, if any. No-op otherwise.
        """
        if not self._current_mesh or self._editing_layer_index is None:
            return
        animation.update_layer_animation(
            self._current_mesh,
            self._editing_layer_index,
            ease_in  = self._ease_in_spin.value(),
            ease_out = self._ease_out_spin.value(),
            hold_in  = self._hold_in_spin.value(),
            hold_out = self._hold_out_spin.value(),
            key_type = self._key_type_combo.currentText(),
        )

    def _load_curve_settings(self, layer_index: int) -> None:
        """Populate the Animation Settings widgets from a layer's stored
        settings, without re-triggering :meth:`_apply_curve_changes`.
        """
        if not self._current_mesh:
            return
        settings = layers.get_layer_settings(self._current_mesh, layer_index)

        for spin, key in (
            (self._ease_in_spin,  "ease_in"),
            (self._ease_out_spin, "ease_out"),
            (self._hold_in_spin,  "hold_in"),
            (self._hold_out_spin, "hold_out"),
        ):
            spin.blockSignals(True)
            spin.setValue(int(settings[key]))
            spin.blockSignals(False)

        self._key_type_combo.blockSignals(True)
        self._key_type_combo.setCurrentText(settings["key_type"])
        self._key_type_combo.blockSignals(False)


    # Edit-mode entry/exit


    def _exit_current_edit(self) -> None:
        """Exit sculpt edit mode on whichever layer is currently active.

        Safe to call when not editing -- does nothing in that case.
        """
        if self._editing_layer_index is None or not self._current_mesh:
            self._editing_layer_index = None
            return

        self._apply_curve_changes()
        edit_mode.exit_edit_mode(self._current_mesh, self._editing_layer_index)
        self._editing_layer_index = None
        self._anim_group.setEnabled(False)

    def _enter_edit_for(self, layer_index: int) -> None:
        """Exit any active edit, then enter sculpt edit mode for *layer_index*.

        Args:
            layer_index (int): Layer/target index to start editing.
        """
        if not self._current_mesh:
            cmds.warning("No managed mesh selected.")
            return
        if self._editing_layer_index == layer_index:
            return  # Already editing this layer.

        self._exit_current_edit()


        with self._suppressed_selection_sync():
            edit_mode.enter_edit_mode(self._current_mesh, layer_index)

        self._editing_layer_index = layer_index
        self._load_curve_settings(layer_index)
        self._anim_group.setEnabled(True)
        self._set_status(f"Editing layer {layer_index}")

    def _toggle_edit_for(self, layer_index: int) -> None:
        """Enter edit mode for *layer_index*, or exit if already active."""
        if self._editing_layer_index == layer_index:
            self._exit_current_edit()
            self._set_status(f"Finished editing layer {layer_index}")
        else:
            self._enter_edit_for(layer_index)

# endregion