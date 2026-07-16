# -*- coding: utf-8 -*-
"""
Per-layer sculpt edit-mode entry/exit for the Atlas Shot Sculptor tool.

Author: Clement Daures
Website: clementdaures.com
"""

from __future__ import annotations

import maya.cmds as cmds

# atlas_sculptor/core/...

from atlas_sculptor.core.models.layers import get_layer_frame_time
from atlas_sculptor.core.node import find_shot_sculpt_node_for_mesh


def enter_edit_mode(mesh: str, layer_index: int) -> None:
    """Put Maya into sculpt-target edit mode for the given layer.

    Sets the timeline to the layer's stored frame time, forces the blendShape
    weight to 1.0, activates ``sculptTarget``, and switches to the Sculpt
    Mesh tool. This deliberately selects the managed meshes -- that is the
    point of entering edit mode -- so, unlike most functions in this
    package, it does *not* restore the prior selection.

    Args:
        mesh (str): Any mesh managed by the target node.
        layer_index (int): Layer/target index to edit.
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        cmds.error("No Atlas Sculptor node found for this object.")
        return

    bs_list = cmds.listConnections(f"{node}.blendShapes", source=True, destination=False) or []
    if not bs_list:
        cmds.error("Atlas Sculptor node has no mesh data.")
        return

    frame_time = get_layer_frame_time(mesh, layer_index)
    if frame_time is None:
        cmds.error(f"Unknown layer index {layer_index}.")
        return
    cmds.currentTime(frame_time)

    mesh_bs_indices = cmds.getAttr(f"{node}.origMeshes", multiIndices=True) or []
    meshes_to_select = []
    for i in mesh_bs_indices:
        mesh_conns = cmds.listConnections(
            f"{node}.origMeshes[{i}]", source=True, destination=False
        ) or []
        bs_conns = cmds.listConnections(
            f"{node}.blendShapes[{i}]", source=True, destination=False
        ) or []
        if not mesh_conns or not bs_conns:
            continue
        m  = mesh_conns[0]
        bs = bs_conns[0]
        meshes_to_select.append(m)

        attr = f"{bs}.weight[{layer_index}]"
        if cmds.objExists(attr):
            cmds.setAttr(attr, 1.0)

    if meshes_to_select:
        cmds.select(meshes_to_select, replace=True)

    if bs_list:
        cmds.sculptTarget(bs_list[0], edit=True, target=layer_index)

    try:
        cmds.setToolTo("SculptMeshTool")
    except Exception:
        pass


def exit_edit_mode(mesh: str, layer_index: int) -> None:
    """Exit sculpt-target edit mode for the given layer.

    Args:
        mesh (str): Any mesh managed by the target node.
        layer_index (int): Layer/target index being finished.
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        return

    bs_list = cmds.listConnections(f"{node}.blendShapes", source=True, destination=False) or []
    for bs in bs_list:
        cmds.sculptTarget(bs, edit=True, target=-1)