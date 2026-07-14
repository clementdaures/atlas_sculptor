# -*- coding: utf-8 -*-
"""
Confirmation dialog shown before deleting a Shot Sculptor node.

Deleting the node is always destructive to the Atlas Sculptor bookkeeping,
but the blendShape deformers it created are a separate, optional choice --
this dialog lets the user decide whether those should go too, or be left
on the mesh as plain (untracked) deformers.

Author: Clement Daures
Website: clementdaures.com
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton,
)

from . import styles


class DeleteNodeDialog(QDialog):
    """Modal dialog: confirm node deletion and choose whether to also
    delete the associated blendShape deformers.
    """

    def __init__(self, message: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Delete Shot Sculptor Node")
        self.setModal(True)
        self.setMinimumWidth(340)
        self.setStyleSheet(styles.main_stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        self._delete_bs_check = QCheckBox("Also delete the blendShape deformers")
        self._delete_bs_check.setToolTip(
            "If unchecked, the blendShape nodes stay on the mesh, frozen at\n"
            "their current sculpted shape, but are no longer tracked as layers."
        )
        self._delete_bs_check.setChecked(False)
        layout.addWidget(self._delete_bs_check)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(styles.red_action_button_style())
        delete_btn.clicked.connect(self.accept)
        btn_row.addWidget(delete_btn)

        layout.addLayout(btn_row)

    def delete_blendshapes(self) -> bool:
        """Whether "Also delete the blendShape deformers" was checked."""
        return self._delete_bs_check.isChecked()

    @staticmethod
    def ask(message: str, parent=None) -> bool | None:
        """Show the dialog modally and return the user's choice.

        Args:
            message (str): Confirmation message shown above the checkbox.
            parent: Parent widget for the dialog.

        Returns:
            bool | None: ``True``/``False`` for whether blendShapes should
                also be deleted, if the user confirmed deletion. ``None``
                if the user cancelled -- callers must treat this as "delete
                nothing."
        """
        dlg = DeleteNodeDialog(message, parent=parent)
        result = dlg.exec()
        if result != QDialog.Accepted:
            return None
        return dlg.delete_blendshapes()
