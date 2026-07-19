# -*- coding: utf-8 -*-
"""Tests for atlas_sculptor.ui.views.dlg_delete_node.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# pyside modules
from PySide6.QtWidgets import QDialog

# atlas_sculptor/ui/...
from atlas_sculptor.ui.views.dlg_delete_node import DeleteNodeDialog

# endregion

# ==========

# region Construction

def test_dialog_shows_message_and_defaults_checkbox_unchecked(qtbot):
    dlg = DeleteNodeDialog("Delete the node for \"bodyGeo\"?")
    qtbot.addWidget(dlg)

    assert dlg._delete_bs_check.isChecked() is False
    assert dlg.delete_blendshapes() is False

# endregion

# ==========

# region Delete Blendshapes

def test_delete_blendshapes_reflects_checkbox_state(qtbot):
    dlg = DeleteNodeDialog("Delete?")
    qtbot.addWidget(dlg)

    dlg._delete_bs_check.setChecked(True)

    assert dlg.delete_blendshapes() is True

# endregion

# ==========

# region Ask

def test_ask_returns_none_on_cancel(qtbot, monkeypatch):
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.Rejected)

    result = DeleteNodeDialog.ask("Delete?")

    assert result is None


def test_ask_returns_checkbox_state_on_accept_unchecked(qtbot, monkeypatch):
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.Accepted)

    result = DeleteNodeDialog.ask("Delete?")

    assert result is False


def test_ask_returns_checkbox_state_on_accept_checked(qtbot, monkeypatch):
    def _fake_exec(self):
        self._delete_bs_check.setChecked(True)
        return QDialog.Accepted

    monkeypatch.setattr(QDialog, "exec", _fake_exec)

    result = DeleteNodeDialog.ask("Delete?")

    assert result is True


def test_cancel_button_rejects_dialog(qtbot):
    dlg = DeleteNodeDialog("Delete?")
    qtbot.addWidget(dlg)

    from PySide6.QtWidgets import QPushButton
    cancel_btn = next(b for b in dlg.findChildren(QPushButton) if b.text() == "Cancel")

    with qtbot.waitSignal(dlg.rejected, timeout=1000):
        cancel_btn.click()


def test_delete_button_accepts_dialog(qtbot):
    dlg = DeleteNodeDialog("Delete?")
    qtbot.addWidget(dlg)

    from PySide6.QtWidgets import QPushButton
    delete_btn = next(b for b in dlg.findChildren(QPushButton) if b.text() == "Delete")

    with qtbot.waitSignal(dlg.accepted, timeout=1000):
        delete_btn.click()

# endregion
