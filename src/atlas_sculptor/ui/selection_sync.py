# -*- coding: utf-8 -*-
"""
Selection-tracking mixin for the Atlas Shot Sculptor tool's UI.

Keeps the upper frame in sync with the active Maya selection, and guards
against the UI's own ``logic`` calls (which can change the Maya selection
as a side effect) re-triggering that sync mid-operation.

Author: Clement Daures
Website: clementdaures.com
"""

from __future__ import annotations

from contextlib import contextmanager

import maya.cmds as cmds

from atlas_sculptor.core import node, selection

from .constants import PAGE_FRAME_DISPLAYER, PAGE_INITIALIZE


class SelectionSyncMixin:
    """Mixin providing Maya-selection-changed tracking for ``AtlasShotSculptorUi``.

    Assumes the host class also has :class:`.edit_controller.EditControllerMixin`
    and :class:`.frame_panel.FramePanelMixin` mixed in, since it calls their
    ``_exit_current_edit`` / ``_refresh_frame_list`` methods.
    """

    def _register_selection_script_job(self) -> None:
        """Register a Maya scriptJob that keeps the upper frame in sync
        with the active selection. Cleaned up in :meth:`closeEvent`.
        """
        try:
            self._selection_script_job = cmds.scriptJob(
                event=["SelectionChanged", self._on_selection_changed],
                protected=True,
            )
        except Exception as exc:
            cmds.warning(f"Atlas Sculptor: could not register selection scriptJob: {exc}")
            self._selection_script_job = None

    def closeEvent(self, event) -> None:
        if self._selection_script_job is not None:
            try:
                cmds.scriptJob(kill=self._selection_script_job, force=True)
            except Exception:
                pass
            self._selection_script_job = None
        super().closeEvent(event)

    @contextmanager
    def _suppressed_selection_sync(self):
        """Silence :meth:`_on_selection_changed` for the duration of a
        ``logic`` call that may change the active Maya selection as a side
        effect (creating nodes/frames/layers, entering edit mode, ...).

        Two layers of defense, because Maya's "SelectionChanged" scriptJob
        is not guaranteed to fire synchronously inside the triggering
        ``cmds.select()`` call -- it can land on the next idle tick instead:

        1. The flag itself is cleared one idle cycle late (via
           ``evalDeferred``), so a callback queued during this block still
           sees it as suppressed even if it's actually delivered just after
           the block exits.
        2. Regardless of the flag, :meth:`_on_selection_changed` also
           compares the live selection against the snapshot taken here; if
           they still match, it treats the event as a late echo of our own
           change (e.g. re-selecting the mesh to sculpt it) rather than a
           real user-driven change, and leaves edit mode alone.
        """
        self._suppress_selection_sync = True
        try:
            yield
        finally:
            self._maya_selection_set_by_us = set(cmds.ls(selection=True) or [])

            def _release() -> None:
                try:
                    self._suppress_selection_sync = False
                except RuntimeError:
                    pass  # Window was closed/destroyed before the deferred tick

            try:
                cmds.evalDeferred(_release)
            except Exception:
                _release()

    def _on_selection_changed(self) -> None:
        """Slot: Maya selection changed -- swap the upper frame's state
        between "Initialize Blendshape" and the Frame Displayer for
        whichever object is now selected.
        """
        if self._suppress_selection_sync:
            return

        current_raw_selection = set(cmds.ls(selection=True) or [])
        if (
            self._maya_selection_set_by_us is not None
            and current_raw_selection == self._maya_selection_set_by_us
        ):
            # Late echo of a selection change we made ourselves (see
            # _suppressed_selection_sync) -- nothing actually changed from
            # the user's point of view, so don't tear down edit mode or
            # rebuild the lists over it
            return
        self._maya_selection_set_by_us = None

        self._exit_current_edit()

        meshes = selection.get_selected_meshes()
        managed = [m for m in meshes if node.mesh_has_shot_sculptor_node(m)]

        self._selected_frame_time = None
        self._selected_layer_index = None

        if managed:
            self._current_mesh = managed[0]
            self._upper_stack.setCurrentIndex(PAGE_FRAME_DISPLAYER)
            self._refresh_frame_list()
        else:
            self._current_mesh = meshes[0] if meshes else None
            self._upper_stack.setCurrentIndex(PAGE_INITIALIZE)
            self._refresh_layer_list()
            if not meshes:
                self._init_hint_label.setText("Select a skinned mesh to begin.")
            elif len(meshes) == 1:
                self._init_hint_label.setText(f'"{meshes[0]}" has no Atlas Sculptor node yet.')
            else:
                self._init_hint_label.setText("Selected meshes have no Atlas Sculptor node yet.")