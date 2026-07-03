# -*- coding: utf-8 -*-
"""
Frame editing (enter/exit sculpt-target edit mode) for the Atlas Shot Sculptor tool.

Author: Clement Daures
Website: clementdaures.com
"""

import maya.cmds as cmds

from .node import find_shot_sculpt_node


def enter_edit_mode(frame_index: int) -> None:
    """Put Maya into sculpt-target edit mode for the given frame index.

    Sets the timeline to the stored frame time, forces the blendShape weight to
    1.0, activates ``sculptTarget``, and switches to the Sculpt Mesh tool.

    Args:
        frame_index (int): Multi-attribute index of the frame to edit.
    """
    node = find_shot_sculpt_node()
    if not node:
        cmds.error("No Atlas Sculptor node in the scene.")
        return

    bs_list = cmds.listConnections(f"{node}.blendShapes", source=True, destination=False) or []
    if not bs_list:
        cmds.error("Atlas Sculptor node has no mesh data.")
        return

    frame_time = cmds.getAttr(f"{node}.frameList[{frame_index}]")
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
        mesh = mesh_conns[0]
        bs   = bs_conns[0]
        meshes_to_select.append(mesh)

        attr = f"{bs}.weight[{frame_index}]"
        if cmds.objExists(attr):
            cmds.setAttr(attr, 1.0)

    if meshes_to_select:
        cmds.select(meshes_to_select, replace=True)

    if bs_list:
        cmds.sculptTarget(bs_list[0], edit=True, target=frame_index)

    try:
        cmds.setToolTo("SculptMeshTool")
    except Exception:
        pass


def exit_edit_mode(frame_index: int) -> None:
    """Exit sculpt-target edit mode for the given frame index.

    Args:
        frame_index (int): Multi-attribute index of the frame being finished.
    """
    node = find_shot_sculpt_node()
    if not node:
        return

    bs_list = cmds.listConnections(f"{node}.blendShapes", source=True, destination=False) or []
    for bs in bs_list:
        cmds.sculptTarget(bs, edit=True, target=-1)
