# -*- coding: utf-8 -*-
"""
Dialog UI for the Atlas Shot Sculptor tool.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# pyside modules
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QDoubleValidator

# atlas_sculptor/ui/...
from atlas_sculptor.ui.views.main_window import AtlasShotSculptorUi

# endregion

# ==========

# region Launcher UI Logic

def _delete_existing(object_name: str):
    """
    Close and delete any existing widget with a given object name.

    Useful for ensuring a single instance of a dialog in Maya/Qt environments.

    Args:
        object_name (str): The `QObject.objectName()` to search for.

    Side Effects:
        - Closes matching widgets and schedules them for deletion.
    """
    for w in QtWidgets.QApplication.allWidgets():
        if w.objectName() == object_name:
            w.close()
            w.deleteLater()


DIALOG_ATTR = "_atlasShotSculptorDlg"


def _maya_main_window():
    import maya.OpenMayaUI as omui
    from shiboken6 import wrapInstance
    ptr = omui.MQtUtil.mainWindow()
    from PySide6.QtWidgets import QWidget
    return wrapInstance(int(ptr), QWidget) if ptr else None


def _install_dialog_ref(dlg):
    """Store the dialog on Maya's main window; clean up when destroyed."""
    main = _maya_main_window()
    if not main:
        return
    # close an existing one if present
    old = getattr(main, DIALOG_ATTR, None)
    if old and old is not dlg:
        try:
            old.close()
            old.deleteLater()
        except RuntimeError:
            pass
    # store the new one
    setattr(main, DIALOG_ATTR, dlg)

    # when dlg is destroyed, clear the reference
    from PySide6 import QtCore
    dlg.destroyed.connect(lambda *_: setattr(main, DIALOG_ATTR, None))


def _get_existing_dialog():
    main = _maya_main_window()
    return getattr(main, DIALOG_ATTR, None) if main else None


def show():
    """Show the Atlas Shot Sculptor UI with error handling."""
    try:
        print("Starting show() function...")

        main = _maya_main_window()
        print(f"Maya main window: {main}")

        # Reuse if it exists
        existing = _get_existing_dialog()
        if existing:
            print(f"Found existing dialog: {existing}")
            existing.show()
            existing.raise_()
            existing.activateWindow()
            return existing

        # Create the UI directly (it's already a QMainWindow)
        print("Creating new dialog...")
        dlg = AtlasShotSculptorUi(parent=main)
        print(f"Dialog created: {dlg}")

        _install_dialog_ref(dlg)
        print("Dialog reference installed")

        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

        print("Dialog should be visible now!")
        return dlg

    except Exception as e:
        import traceback
        print(f"Error in show(): {e}")
        traceback.print_exc()
        return None

# endregion