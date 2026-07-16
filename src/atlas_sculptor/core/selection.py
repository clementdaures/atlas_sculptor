# -*- coding: utf-8 -*-
"""
Selection helpers for the Atlas Shot Sculptor tool.

Author: Clement Daures
Website: clementdaures.com
"""

from __future__ import annotations

import maya.cmds as cmds


def get_selected_meshes() -> list[str]:
    """Return selected transform nodes that own at least one polygon mesh shape.

    Returns:
        list[str]: Transform names whose first shape is a ``mesh`` node.
    """
    transforms = cmds.ls(selection=True, type="transform") or []
    meshes: list[str] = []
    for obj in transforms:
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
        if shapes and cmds.nodeType(shapes[0]) == "mesh":
            meshes.append(obj)
    return meshes


def restore_selection(original: list[str]) -> None:
    """Reselect exactly *original*, or clear the selection if it was empty.

    Several Maya commands (``blendShape``, ``duplicate``, ...) change the
    active selection as a side effect. Call this after such a command to
    put the caller's selection back the way it was, so callers (notably the
    UI's selection-changed listener) don't see spurious selection churn.

    Args:
        original (list[str]): Selection snapshot taken before the operation.
    """
    if original:
        cmds.select(original, replace=True)
    else:
        cmds.select(clear=True)