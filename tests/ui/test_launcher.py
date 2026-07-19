# -*- coding: utf-8 -*-
"""Tests for atlas_sculptor.ui.launcher.

``launcher.show()`` and its helpers depend on ``maya.OpenMayaUI`` and
``shiboken6.wrapInstance`` to reach into Maya's real main window, which
this test suite doesn't fake (see module docstring in ``launcher.py`` --
it's Maya-window plumbing, not tool logic). What *is* tested here is the
behaviour that's actually reachable without a real Maya session:
``show()``'s broad error handling, and the plain-Qt widget bookkeeping
helper ``_delete_existing``.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# pyside modules
from PySide6.QtWidgets import QWidget

# atlas_sculptor/ui/...
from atlas_sculptor.ui import launcher

# endregion

# ==========

# region Show

def test_show_returns_none_gracefully_without_a_maya_session(qtbot):
    # No `maya.OpenMayaUI` is installed in this test environment (only
    # `maya.cmds` is faked), so `_maya_main_window()` raises ImportError;
    # `show()` catches broadly and should degrade to `None`, not propagate.
    result = launcher.show()

    assert result is None

# endregion

# ==========

# region Delete Existing

def test_delete_existing_closes_and_marks_matching_widgets_for_deletion(qtbot):
    widget = QWidget()
    widget.setObjectName("atlasSculptorTestWidget")
    qtbot.addWidget(widget)
    widget.show()

    assert widget.isVisible()

    launcher._delete_existing("atlasSculptorTestWidget")

    assert widget.isVisible() is False


def test_delete_existing_ignores_widgets_with_a_different_name(qtbot):
    widget = QWidget()
    widget.setObjectName("someOtherWidget")
    qtbot.addWidget(widget)
    widget.show()

    launcher._delete_existing("atlasSculptorTestWidget")

    assert widget.isVisible()

# endregion
