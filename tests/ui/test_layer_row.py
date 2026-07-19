# -*- coding: utf-8 -*-
"""Tests for atlas_sculptor.ui.widgets.layer_row.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# pyside modules
from PySide6.QtCore import Qt

# atlas_sculptor/ui/...
from atlas_sculptor.ui.widgets.layer_row import EditableLabel, LayerRowWidget

# endregion

# ==========

# region EditableLabel

def test_editable_label_starts_showing_the_label(qtbot):
    widget = EditableLabel("Base 1001")
    qtbot.addWidget(widget)

    assert widget._label.text() == "Base 1001"
    assert widget._label.isHidden() is False
    assert widget._edit.isHidden()


def test_editable_label_double_click_starts_editing(qtbot):
    widget = EditableLabel("Base 1001")
    qtbot.addWidget(widget)
    widget.show()

    widget._start_edit()

    assert widget._edit.isVisible()
    assert widget._label.isHidden()
    assert widget._edit.text() == "Base 1001"


def test_editable_label_finish_edit_emits_renamed_on_change(qtbot):
    widget = EditableLabel("Base 1001")
    qtbot.addWidget(widget)
    widget.show()
    widget._start_edit()
    widget._edit.setText("Squash Peak")

    with qtbot.waitSignal(widget.renamed, timeout=1000) as blocker:
        widget._finish_edit()

    assert blocker.args == ["Squash Peak"]
    assert widget._label.text() == "Squash Peak"
    assert widget._edit.isHidden()


def test_editable_label_finish_edit_noop_when_unchanged(qtbot):
    widget = EditableLabel("Base 1001")
    qtbot.addWidget(widget)
    widget.show()
    widget._start_edit()
    # Text left exactly as-is.

    received = []
    widget.renamed.connect(received.append)
    widget._finish_edit()

    assert received == []
    assert widget._label.text() == "Base 1001"


def test_editable_label_finish_edit_noop_when_blank(qtbot):
    widget = EditableLabel("Base 1001")
    qtbot.addWidget(widget)
    widget.show()
    widget._start_edit()
    widget._edit.setText("   ")

    received = []
    widget.renamed.connect(received.append)
    widget._finish_edit()

    assert received == []
    assert widget._label.text() == "Base 1001"


def test_editable_label_double_click_event_triggers_edit(qtbot):
    widget = EditableLabel("Base 1001")
    qtbot.addWidget(widget)
    widget.show()

    qtbot.mouseDClick(widget, Qt.LeftButton)

    assert widget._edit.isVisible()

# endregion

# ==========

# region LayerRowWidget

def test_layer_row_base_layer_shows_tag_not_move_buttons(qtbot):
    row = LayerRowWidget(
        name="Base 1001", enabled=True, is_base=True, is_editing=False,
        can_move_up=False, can_move_down=False,
    )
    qtbot.addWidget(row)

    labels = [c for c in row.findChildren(type(row._name_label._label)) if c.text() == "BASE"]
    assert labels, "expected a BASE tag label for the base layer"

    from PySide6.QtWidgets import QToolButton
    tool_buttons = row.findChildren(QToolButton)
    button_texts = {b.text() for b in tool_buttons}
    assert "\u25B2" not in button_texts  # no up arrow
    assert "\u25BC" not in button_texts  # no down arrow


def test_layer_row_non_base_layer_shows_move_buttons_respecting_flags(qtbot):
    row = LayerRowWidget(
        name="Layer 3", enabled=True, is_base=False, is_editing=False,
        can_move_up=True, can_move_down=False,
    )
    qtbot.addWidget(row)

    from PySide6.QtWidgets import QToolButton
    buttons = {b.text(): b for b in row.findChildren(QToolButton)}
    assert buttons["\u25B2"].isEnabled() is True
    assert buttons["\u25BC"].isEnabled() is False


def test_layer_row_checkbox_reflects_enabled_and_emits_toggled(qtbot):
    row = LayerRowWidget(
        name="Layer 3", enabled=False, is_base=False, is_editing=False,
        can_move_up=True, can_move_down=True,
    )
    qtbot.addWidget(row)

    assert row._enabled_check.isChecked() is False

    with qtbot.waitSignal(row.toggled, timeout=1000) as blocker:
        row._enabled_check.setChecked(True)

    assert blocker.args == [True]


def test_layer_row_edit_button_reflects_is_editing_and_emits_edit_clicked(qtbot):
    row = LayerRowWidget(
        name="Layer 3", enabled=True, is_base=False, is_editing=True,
        can_move_up=False, can_move_down=False,
    )
    qtbot.addWidget(row)

    assert row._edit_btn.isChecked() is True

    with qtbot.waitSignal(row.edit_clicked, timeout=1000):
        row._edit_btn.click()


def test_layer_row_move_buttons_emit_signals(qtbot):
    row = LayerRowWidget(
        name="Layer 3", enabled=True, is_base=False, is_editing=False,
        can_move_up=True, can_move_down=True,
    )
    qtbot.addWidget(row)

    from PySide6.QtWidgets import QToolButton
    buttons = {b.text(): b for b in row.findChildren(QToolButton)}

    with qtbot.waitSignal(row.move_up_clicked, timeout=1000):
        buttons["\u25B2"].click()

    with qtbot.waitSignal(row.move_down_clicked, timeout=1000):
        buttons["\u25BC"].click()


def test_layer_row_rename_bubbles_up_through_name_label(qtbot):
    row = LayerRowWidget(
        name="Layer 3", enabled=True, is_base=False, is_editing=False,
        can_move_up=False, can_move_down=False,
    )
    qtbot.addWidget(row)
    row.show()
    row._name_label._start_edit()
    row._name_label._edit.setText("New Name")

    with qtbot.waitSignal(row.renamed, timeout=1000) as blocker:
        row._name_label._finish_edit()

    assert blocker.args == ["New Name"]

# endregion
