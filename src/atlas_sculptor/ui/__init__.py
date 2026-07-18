# -*- coding: utf-8 -*-
"""
Qt (PySide6) front end for the Atlas Shot Sculptor tool.

All widgets talk to Maya only through ``atlas_sculptor.core``; nothing in
``core`` imports from this package. Layout:

    ui/
        launcher.py      Singleton entry point: show() creates/raises the
                         dockable AtlasShotSculptorUi window under Maya's
                         main window.
        views/           Top-level Qt windows/dialogs.
            main_window.py    AtlasShotSculptorUi (QMainWindow), assembled
                               from the controllers/ mixins below.
            dlg_delete_node.py  DeleteNodeDialog confirmation dialog.
        controllers/     Mixins implementing AtlasShotSculptorUi's
                         behaviour, kept out of main_window.py to keep
                         each concern testable/readable on its own:
            selection_sync.py  Mirrors Maya's active selection into the UI.
            frame_panel.py     Builds/refreshes the frame & layer list.
            edit_controller.py Sculpt edit-mode entry/exit + curve settings.
        widgets/         Small reusable custom Qt widgets.
            layer_row.py      EditableLabel, LayerRowWidget.
        resources/       Static UI resources: stylesheet.py, constants.py.

Author: Clement Daures
Website: clementdaures.com
"""
