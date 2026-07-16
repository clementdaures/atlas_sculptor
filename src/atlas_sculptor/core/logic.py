# -*- coding: utf-8 -*-
"""
Core logic for the Atlas Shot Sculptor tool.

All Maya operations live here. This module has zero UI dependencies and can
be imported and unit-tested without a running Qt application.

Author: Clement Daures
Website: clementdaures.com
"""

import maya.cmds as cmds


# ---------------------------------------------------------------------------
# Selection helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Node discovery
# ---------------------------------------------------------------------------

def find_shot_sculpt_node() -> str | None:
    """Search the scene for the AtlasShotSculptor network node.

    The node is identified by the presence of a custom ``is_shot_sculptor_node``
    attribute rather than by name, so renames do not break discovery.

    Returns:
        str | None: Node name, or ``None`` if not found.
    """
    for node in cmds.ls(type="network") or []:
        if cmds.attributeQuery("is_shot_sculptor_node", node=node, exists=True):
            return node
    return None


# ---------------------------------------------------------------------------
# Group / node creation & deletion
# ---------------------------------------------------------------------------

def create_shot_sculpt_node() -> str | None:
    """Create the AtlasShotSculptor node and one blendShape deformer per selected mesh.

    If a node already exists the selected meshes are appended to it (duplicates
    are skipped).  The blendShape is inserted *frontOfChain* so it runs before
    the skinCluster.

    Returns:
        str | None: Name of the AtlasShotSculptor node, or ``None`` on failure.

    Raises:
        RuntimeError: Via ``cmds.error`` when no valid meshes are selected.
    """
    meshes = get_selected_meshes()
    if not meshes:
        cmds.error("Please select one or more skinned mesh objects to create a Shot-Sculpt group.")
        return None

    node = find_shot_sculpt_node()
    if node:
        cmds.warning("Atlas Sculptor node already exists. Adding meshes to the existing group.")
    else:
        node = cmds.createNode("network", name="AtlasShotSculptorNode#")
        cmds.addAttr(node, longName="is_shot_sculptor_node", attributeType="bool", hidden=True)
        cmds.setAttr(f"{node}.is_shot_sculptor_node", True)
        cmds.addAttr(node, longName="origMeshes",  attributeType="message", multi=True)
        cmds.addAttr(node, longName="blendShapes", attributeType="message", multi=True)
        cmds.addAttr(node, longName="frameList",   attributeType="long",    multi=True)
        cmds.addAttr(node, longName="frameNames",  dataType="string",       multi=True)

    existing_meshes = (
        cmds.listConnections(f"{node}.origMeshes", source=True, destination=False) or []
    )

    for mesh in meshes:
        if mesh in existing_meshes:
            continue

        bs_node = cmds.blendShape(mesh, name=f"{mesh}_atlas_sculpt_bsp", frontOfChain=True)[0]

        indices = cmds.getAttr(f"{node}.origMeshes", multiIndices=True) or []
        new_index = (max(indices) + 1) if indices else 0

        cmds.connectAttr(f"{mesh}.message",    f"{node}.origMeshes[{new_index}]",  force=True)
        cmds.connectAttr(f"{bs_node}.message", f"{node}.blendShapes[{new_index}]", force=True)

    return node


def delete_shot_sculptor_node() -> None:
    """Delete the AtlasShotSculptor node, its stored blendShape deformers, and all connections."""
    node = find_shot_sculpt_node()
    if not node:
        cmds.warning("No Shot Sculptor node to delete.")
        return

    # Disconnect origMeshes
    for i in cmds.getAttr(f"{node}.origMeshes", multiIndices=True) or []:
        conns = cmds.listConnections(
            f"{node}.origMeshes[{i}]", source=True, destination=False, plugs=True
        )
        if conns:
            try:
                cmds.disconnectAttr(conns[0], f"{node}.origMeshes[{i}]")
            except Exception as exc:
                cmds.warning(f"Failed to disconnect origMesh[{i}]: {exc}")

    # Disconnect blendShapes, then delete them
    for i in cmds.getAttr(f"{node}.blendShapes", multiIndices=True) or []:
        conns = cmds.listConnections(
            f"{node}.blendShapes[{i}]", source=True, destination=False, plugs=True
        )
        if conns:
            bs_node = conns[0].split(".")[0]
            try:
                cmds.disconnectAttr(conns[0], f"{node}.blendShapes[{i}]")
            except Exception as exc:
                cmds.warning(f"Failed to disconnect blendShape[{i}]: {exc}")
            if cmds.objExists(bs_node) and cmds.nodeType(bs_node) == "blendShape":
                try:
                    cmds.delete(bs_node)
                except Exception as exc:
                    cmds.warning(f"Failed to delete blendShape {bs_node}: {exc}")

    try:
        cmds.delete(node)
    except Exception as exc:
        cmds.warning(f"Failed to delete AtlasShotSculptor node: {exc}")


# ---------------------------------------------------------------------------
# Frame data accessors
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Frame creation
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Frame editing
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Animation curve management
# ---------------------------------------------------------------------------

def update_frame_animation(
    frame_index: int,
    ease_in:  int = 1,
    ease_out: int = 1,
    hold_in:  int = 0,
    hold_out: int = 0,
    key_type: str = "linear",
) -> None:
    """Re-key the blendShape weight curve for a sculpt frame.

    Removes all keys in the affected range and lays down four new keys:

    * ``start_zero``  – weight = 0 (ease starts)
    * ``start_full``  – weight = 1 (hold starts)
    * ``end_full``    – weight = 1 (hold ends)
    * ``end_zero``    – weight = 0 (ease ends)

    Args:
        frame_index (int): Multi-attribute index of the frame.
        ease_in  (int): Frames to ramp up before the hold.
        ease_out (int): Frames to ramp down after the hold.
        hold_in  (int): Frames of full weight before the main frame.
        hold_out (int): Frames of full weight after the main frame.
        key_type (str): ``"linear"``, ``"spline"``, or ``"stepped"``.
    """
    node = find_shot_sculpt_node()
    if not node:
        return

    frame_time = cmds.getAttr(f"{node}.frameList[{frame_index}]")
    bs_list = cmds.listConnections(f"{node}.blendShapes", source=True, destination=False) or []
    if not bs_list:
        return

    ease_in  = max(int(ease_in),  0)
    ease_out = max(int(ease_out), 0)
    hold_in  = max(int(hold_in),  0)
    hold_out = max(int(hold_out), 0)

    start_full = frame_time - hold_in
    end_full   = frame_time + hold_out
    start_zero = start_full - ease_in
    end_zero   = end_full   + ease_out

    for bs in bs_list:
        weight_attr = f"{bs}.weight[{frame_index}]"

        cmds.cutKey(weight_attr, time=(start_zero - 1, end_zero + 1), option="keys")

        cmds.setKeyframe(weight_attr, value=0.0, t=start_zero)
        cmds.setKeyframe(weight_attr, value=1.0, t=start_full)
        cmds.setKeyframe(weight_attr, value=1.0, t=end_full)
        cmds.setKeyframe(weight_attr, value=0.0, t=end_zero)

        if key_type == "linear":
            cmds.keyTangent(weight_attr, time=(start_zero, end_zero), itt="linear", ott="linear")
        elif key_type == "spline":
            cmds.keyTangent(weight_attr, time=(start_zero, end_zero), itt="auto",   ott="auto")
        elif key_type == "stepped":
            cmds.keyTangent(weight_attr, time=(start_full, end_full), ott="step")
            cmds.keyTangent(weight_attr, time=(start_zero, end_zero), itt="step")


# ---------------------------------------------------------------------------
# Frame rename & delete
# ---------------------------------------------------------------------------

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