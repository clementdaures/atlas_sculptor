# -*- coding: utf-8 -*-
"""Tests for atlas_sculptor.ui.views.main_window.AtlasShotSculptorUi.

Exercises the three behaviour mixins (SelectionSyncMixin, EditControllerMixin,
FramePanelMixin) together, the same way they run in production -- through
the real, wired-up ``AtlasShotSculptorUi`` window rather than in isolation.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# atlas_sculptor/core/...
from atlas_sculptor.core.scene import node

# atlas_sculptor/ui/...
from atlas_sculptor.ui.resources.constants import PAGE_FRAME_DISPLAYER, PAGE_INITIALIZE
from atlas_sculptor.ui.views.dlg_delete_node import DeleteNodeDialog
from atlas_sculptor.ui.views.main_window import AtlasShotSculptorUi

# endregion

# ==========

# region Helpers

def _make_window(qtbot):
    win = AtlasShotSculptorUi()
    qtbot.addWidget(win)
    return win


def _current_layer_rows(win):
    """Return the live LayerRowWidget for every row in the layer list."""
    return [win._layer_list.itemWidget(win._layer_list.item(i)) for i in range(win._layer_list.count())]

# endregion

# ==========

# region Initial State

def test_starts_on_initialize_page_when_nothing_selected(qtbot, fake_cmds):
    fake_cmds.select([])
    win = _make_window(qtbot)

    assert win._upper_stack.currentIndex() == PAGE_INITIALIZE
    assert win._init_hint_label.text() == "Select a skinned mesh to begin."


def test_selecting_unmanaged_mesh_shows_it_in_the_hint(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)

    assert win._upper_stack.currentIndex() == PAGE_INITIALIZE
    assert "bodyGeo" in win._init_hint_label.text()


def test_selecting_managed_mesh_shows_frame_displayer(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    node.create_shot_sculpt_node()

    win = _make_window(qtbot)

    assert win._upper_stack.currentIndex() == PAGE_FRAME_DISPLAYER
    assert win._current_mesh == "bodyGeo"


def test_script_job_registered_and_fires_on_selection_change(qtbot, fake_cmds):
    fake_cmds.select([])
    win = _make_window(qtbot)
    assert win._selection_script_job is not None

    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    fake_cmds.fire_script_job("SelectionChanged")

    assert win._current_mesh == "bodyGeo"
    assert win._upper_stack.currentIndex() == PAGE_INITIALIZE  # not yet initialized


def test_close_event_unregisters_the_script_job(qtbot, fake_cmds):
    win = _make_window(qtbot)
    assert fake_cmds._script_jobs

    win.close()

    assert win._selection_script_job is None
    assert fake_cmds._script_jobs == {}

# endregion

# ==========

# region Initialize Blendshape

def test_initialize_blendshape_button_creates_node_and_switches_page(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)

    win._on_create_group()

    assert win._upper_stack.currentIndex() == PAGE_FRAME_DISPLAYER
    assert win._current_mesh == "bodyGeo"
    assert node.mesh_has_shot_sculptor_node("bodyGeo") is True

# endregion

# ==========

# region Frame list

def test_create_frame_button_populates_frame_list_and_base_layer(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    fake_cmds.currentTime(1001)

    win._on_create_frame_clicked()

    assert win._frame_list.count() == 1
    assert win._delete_frame_btn.isEnabled()
    assert win._add_layer_btn.isEnabled()
    assert win._layer_list.count() == 1  # the new frame's base layer


def test_create_frame_button_warns_without_a_managed_mesh(qtbot, fake_cmds):
    fake_cmds.select([])
    win = _make_window(qtbot)

    win._on_create_frame_clicked()

    assert fake_cmds.warnings


def test_delete_frame_button_clears_the_frame_and_its_layers(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    fake_cmds.currentTime(1001)
    win._on_create_frame_clicked()

    win._on_delete_frame_clicked()

    assert win._frame_list.count() == 0
    assert win._layer_list.count() == 0
    assert win._delete_frame_btn.isEnabled() is False
    assert win._add_layer_btn.isEnabled() is False


def test_delete_frame_button_warns_when_nothing_selected(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()

    win._on_delete_frame_clicked()  # no frame created/selected yet

    assert fake_cmds.warnings


def test_selecting_a_frame_row_refreshes_layer_list(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    fake_cmds.currentTime(1001)
    win._on_create_frame_clicked()
    fake_cmds.currentTime(1050)
    win._on_create_frame_clicked()

    assert win._frame_list.count() == 2

    win._on_frame_row_changed(-1)

    assert win._selected_frame_time is None
    assert win._layer_list.count() == 0
    assert win._delete_frame_btn.isEnabled() is False

# endregion

# ==========

# region Layer list: add / toggle / rename / reorder / edit

def test_add_layer_button_appends_a_non_base_layer(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    fake_cmds.currentTime(1001)
    win._on_create_frame_clicked()

    win._on_add_layer_clicked()

    assert win._layer_list.count() == 2


def test_add_layer_button_warns_without_a_selected_frame(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()

    win._on_add_layer_clicked()

    assert fake_cmds.warnings


def test_toggling_layer_checkbox_persists_enabled_state(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    fake_cmds.currentTime(1001)
    win._on_create_frame_clicked()

    from atlas_sculptor.core.models import layers
    row = _current_layer_rows(win)[0]

    row._enabled_check.setChecked(False)

    from PySide6.QtCore import Qt
    idx = win._layer_list.item(0).data(Qt.UserRole)
    entries = layers.get_layer_entries("bodyGeo", win._selected_frame_time)
    entry = next(e for e in entries if e[0] == idx)
    assert entry[2] is False  # enabled flag


def test_renaming_layer_via_row_double_click_persists(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    fake_cmds.currentTime(1001)
    win._on_create_frame_clicked()

    row = _current_layer_rows(win)[0]
    row.show()
    row._name_label._start_edit()
    row._name_label._edit.setText("Squash Peak")
    row._name_label._finish_edit()

    from atlas_sculptor.core.models import layers
    entries = layers.get_layer_entries("bodyGeo", win._selected_frame_time)
    assert entries[0][1] == "Squash Peak"


def test_move_layer_buttons_reorder_non_base_layers(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    fake_cmds.currentTime(1001)
    win._on_create_frame_clicked()
    win._on_add_layer_clicked()
    win._on_add_layer_clicked()

    from PySide6.QtCore import Qt
    top_index = win._layer_list.item(0).data(Qt.UserRole)
    second_index = win._layer_list.item(1).data(Qt.UserRole)

    top_row = _current_layer_rows(win)[0]
    top_row.show()
    from PySide6.QtWidgets import QToolButton
    down_btn = next(b for b in top_row.findChildren(QToolButton) if b.text() == "\u25BC")
    down_btn.click()

    new_top_index = win._layer_list.item(0).data(Qt.UserRole)
    assert new_top_index == second_index
    assert new_top_index != top_index


def test_edit_toggle_enters_and_exits_sculpt_edit_mode(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    fake_cmds.currentTime(1001)
    win._on_create_frame_clicked()

    row = _current_layer_rows(win)[0]
    row.show()
    row._edit_btn.click()

    assert win._editing_layer_index is not None
    assert win._anim_group.isEnabled()

    # Re-fetch: _refresh_layer_list() rebuilds the row widgets each time.
    row_after_enter = _current_layer_rows(win)[0]
    row_after_enter.show()
    row_after_enter._edit_btn.click()

    assert win._editing_layer_index is None
    assert win._anim_group.isEnabled() is False


def test_selection_change_while_editing_exits_edit_mode(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    fake_cmds.currentTime(1001)
    win._on_create_frame_clicked()

    row = _current_layer_rows(win)[0]
    row.show()
    row._edit_btn.click()
    assert win._editing_layer_index is not None

    # A real, external selection change (e.g. user clicks empty space in
    # the viewport) should tear down edit mode.
    fake_cmds.select([])
    fake_cmds.fire_script_job("SelectionChanged")

    assert win._editing_layer_index is None


def test_easing_spinbox_change_pushes_settings_while_editing(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    fake_cmds.currentTime(1001)
    win._on_create_frame_clicked()
    row = _current_layer_rows(win)[0]
    row.show()
    row._edit_btn.click()

    win._ease_in_spin.setValue(9)

    from atlas_sculptor.core.models import layers
    settings = layers.get_layer_settings("bodyGeo", win._editing_layer_index)
    assert settings["ease_in"] == 9


def test_easing_spinbox_change_is_a_noop_when_not_editing(qtbot, fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()

    win._ease_in_spin.setValue(9)  # should not raise, nothing to push to

# endregion

# ==========

# region Delete node / delete all (Tools menu)

def test_delete_node_for_selection_removes_the_node_when_confirmed(qtbot, fake_cmds, monkeypatch):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    monkeypatch.setattr(DeleteNodeDialog, "ask", staticmethod(lambda message, parent=None: True))

    win._on_delete_node_for_selection()

    assert node.mesh_has_shot_sculptor_node("bodyGeo") is False
    assert win._upper_stack.currentIndex() == PAGE_INITIALIZE


def test_delete_node_for_selection_does_nothing_when_cancelled(qtbot, fake_cmds, monkeypatch):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    monkeypatch.setattr(DeleteNodeDialog, "ask", staticmethod(lambda message, parent=None: None))

    win._on_delete_node_for_selection()

    assert node.mesh_has_shot_sculptor_node("bodyGeo") is True


def test_delete_node_for_selection_warns_without_a_managed_mesh(qtbot, fake_cmds):
    fake_cmds.select([])
    win = _make_window(qtbot)

    win._on_delete_node_for_selection()

    assert fake_cmds.warnings


def test_delete_all_nodes_removes_every_node_when_confirmed(qtbot, fake_cmds, monkeypatch):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    node.create_shot_sculpt_node()
    fake_cmds._add_transform_with_mesh("clothGeo")
    fake_cmds.select(["clothGeo"])
    node.create_shot_sculpt_node()

    fake_cmds.select([])
    win = _make_window(qtbot)
    monkeypatch.setattr(DeleteNodeDialog, "ask", staticmethod(lambda message, parent=None: False))

    win._on_delete_all_nodes()

    assert node.find_all_shot_sculptor_nodes() == []
    assert "2" in win._status_label.text()


def test_delete_all_nodes_does_nothing_when_cancelled(qtbot, fake_cmds, monkeypatch):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    node.create_shot_sculpt_node()

    fake_cmds.select([])
    win = _make_window(qtbot)
    monkeypatch.setattr(DeleteNodeDialog, "ask", staticmethod(lambda message, parent=None: None))

    win._on_delete_all_nodes()

    assert len(node.find_all_shot_sculptor_nodes()) == 1

# endregion

# ==========

# region Known gap: _on_rename_layer_clicked references a widget that is
# never built (no self._rename_field is constructed anywhere in
# main_window.py, and nothing connects a button to this slot). This test
# documents the current, broken behaviour rather than silently skipping it
# -- see the summary for a suggested fix.

def test_on_rename_layer_clicked_is_currently_broken_missing_rename_field(qtbot, fake_cmds):
    import pytest

    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    win = _make_window(qtbot)
    win._on_create_group()
    fake_cmds.currentTime(1001)
    win._on_create_frame_clicked()

    with pytest.raises(AttributeError):
        win._on_rename_layer_clicked()

# endregion
