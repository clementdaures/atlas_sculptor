# -*- coding: utf-8 -*-
"""
Frame data accessors, creation, rename & delete for the Atlas Shot Sculptor tool.

Author: Clement Daures
Website: clementdaures.com
"""

import maya.cmds as cmds

from .node import find_shot_sculpt_node


def get_frame_entries() -> list[tuple[int, int, str]]:
    """Return all sculpt frames stored on the AtlasShotSculptor node.

    Returns:
        list[tuple[int, int, str]]:
            Each element is ``(attr_index, frame_time, display_label)`` where
            *attr_index* is the Maya multi-attribute index (stable across deletions).
    """
    node = find_shot_sculpt_node()
    if not node:
        return []

    entries: list[tuple[int, int, str]] = []

    for idx in cmds.getAttr(f"{node}.frameList", multiIndices=True) or []:
        frame_time = int(cmds.getAttr(f"{node}.frameList[{idx}]"))
        default_label = f"Frame {frame_time}"

        try:
            custom_name: str = cmds.getAttr(f"{node}.frameNames[{idx}]") or ""
        except Exception:
            custom_name = ""

        if custom_name and custom_name != default_label:
            label = f"{default_label}  |  {custom_name}"
        else:
            label = default_label

        entries.append((idx, frame_time, label))
    return entries


def create_sculpt_frame() -> int | None:
    """Capture the current mesh pose as a new blendShape sculpt target.

    Adds one keyed blendShape target per mesh (weight 0→1→0 over three frames)
    and records the frame in the AtlasShotSculptor node.

    Returns:
        int | None: The new frame's attribute index, or ``None`` on failure.

    Raises:
        RuntimeError: Via ``cmds.error`` when preconditions are not met.
    """
    node = find_shot_sculpt_node()
    if not node:
        cmds.error("No Atlas Sculptor node found. Please create a Shot-Sculpt group first.")
        return None

    current_time = int(cmds.currentTime(query=True))
    mesh_list = cmds.listConnections(f"{node}.origMeshes", source=True, destination=False) or []
    bs_list   = cmds.listConnections(f"{node}.blendShapes", source=True, destination=False) or []

    if not mesh_list or not bs_list:
        cmds.error("Atlas Sculptor node has no meshes. Create the Shot-Sculpt group first.")
        return None

    frame_indices = cmds.getAttr(f"{node}.frameList", multiIndices=True) or []
    new_index = (max(frame_indices) + 1) if frame_indices else 0

    mesh_bs_indices = cmds.getAttr(f"{node}.origMeshes", multiIndices=True) or []
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

        target_name = f"{mesh}_frame{current_time}"
        temp_dup = cmds.duplicate(mesh, name=target_name)[0]

        cmds.blendShape(bs, edit=True, target=(mesh, new_index, target_name, 1.0))
        cmds.delete(temp_dup)
        cmds.blendShape(bs, edit=True, resetTargetDelta=(0, new_index))

        weight_attr = f"{bs}.weight[{new_index}]"
        cmds.setKeyframe(weight_attr, value=0.0, t=(current_time - 1))
        cmds.setKeyframe(weight_attr, value=1.0, t=current_time)
        cmds.setKeyframe(weight_attr, value=0.0, t=(current_time + 1))
        cmds.keyTangent(
            weight_attr,
            time=(current_time - 1, current_time + 1),
            ott="linear", itt="linear",
        )

    if not cmds.attributeQuery("frameNames", node=node, exists=True):
        cmds.addAttr(node, longName="frameNames", dataType="string", multi=True)

    cmds.setAttr(f"{node}.frameList[{new_index}]", current_time)

    cmds.setAttr(f"{node}.frameNames[{new_index}]", f"Frame {current_time}", type="string")

    # Activate sculpt target on the first blendShape
    if bs_list:
        cmds.sculptTarget(bs_list[0], edit=False, target=new_index)

    return new_index


def rename_frame(frame_index: int, new_name: str) -> None:
    """Store a custom display name for a sculpt frame.

    Args:
        frame_index (int): Multi-attribute index of the frame.
        new_name    (str): Non-empty string to use as the display name.
    """
    node = find_shot_sculpt_node()
    if not node:
        return
    cmds.setAttr(f"{node}.frameNames[{frame_index}]", new_name.strip(), type="string")


def delete_sculpt_frame(frame_index: int) -> None:
    """Remove a sculpt frame's blendShape target and its node record.

    Args:
        frame_index (int): Multi-attribute index of the frame to remove.
    """
    node = find_shot_sculpt_node()
    if not node:
        return

    bs_list = cmds.listConnections(f"{node}.blendShapes", source=True, destination=False) or []
    for bs in bs_list:
        try:
            cmds.removeMultiInstance(f"{bs}.weight[{frame_index}]", b=True)
        except Exception as exc:
            cmds.warning(f"Could not remove target {frame_index} from {bs}: {exc}")

    cmds.removeMultiInstance(f"{node}.frameList[{frame_index}]",  b=True)
    cmds.removeMultiInstance(f"{node}.frameNames[{frame_index}]", b=True)


def get_frame_time(frame_index: int) -> int | None:
    """Return the stored frame time for a given attribute index.

    Args:
        frame_index (int): Multi-attribute index.

    Returns:
        int | None: Frame time, or ``None`` if the node/attr does not exist.
    """
    node = find_shot_sculpt_node()
    if not node:
        return None
    try:
        return int(cmds.getAttr(f"{node}.frameList[{frame_index}]"))
    except Exception:
        return None
