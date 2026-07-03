# -*- coding: utf-8 -*-
"""
Selection helpers for the Atlas Shot Sculptor tool.

Author: Clement Daures
Website: clementdaures.com
"""

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
