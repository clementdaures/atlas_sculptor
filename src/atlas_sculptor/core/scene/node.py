# -*- coding: utf-8 -*-
"""
Node discovery, creation and deletion for the Atlas Shot Sculptor tool.

Every managed object (or group of objects initialized together) gets its
own, independent AtlasShotSculptor network node. Nothing about frames or
layers is ever shared between two different nodes/objects -- selecting a
different object always shows that object's own frame list, never another's.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# python modules
from __future__ import annotations

# dcc import
import maya.cmds as cmds

# atlas_sculptor/core/...
from atlas_sculptor.core.models.config import ensure_layer_data_attr
from atlas_sculptor.core.scene.selection import get_selected_meshes, restore_selection

# endregion

# ==========

# region Node Logic

def find_shot_sculpt_node_for_mesh(mesh: str) -> str | None:
    """Find the AtlasShotSculptor node that manages *mesh*, if any.

    Every object (or group of objects initialized together) has its own
    node, so this always resolves to the one node relevant to *mesh* --
    never to some other object's node.

    Args:
        mesh (str): Transform name of the mesh to look up.

    Returns:
        str | None: The owning node's name, or ``None`` if *mesh* isn't
            managed by any Atlas Sculptor node.
    """
    for node in cmds.ls(type="network") or []:
        if not cmds.attributeQuery("is_shot_sculptor_node", node=node, exists=True):
            continue
        connected = cmds.listConnections(f"{node}.origMeshes", source=True, destination=False) or []
        if mesh in connected:
            return node
    return None


def find_all_shot_sculptor_nodes() -> list[str]:
    """Find every AtlasShotSculptor node in the scene, regardless of selection.

    Returns:
        list[str]: Names of every network node carrying the
            ``is_shot_sculptor_node`` marker attribute.
    """
    return [
        node for node in (cmds.ls(type="network") or [])
        if cmds.attributeQuery("is_shot_sculptor_node", node=node, exists=True)
    ]


def mesh_has_shot_sculptor_node(mesh: str) -> bool:
    """Return whether *mesh* is already connected to its own AtlasShotSculptor node.

    Used by the UI to decide between State A ("Initialize Blendshape") and
    State B (Frame Displayer) for the currently selected mesh(es).

    Args:
        mesh (str): Transform name of the mesh to check.

    Returns:
        bool: ``True`` if a Shot Sculptor node exists for *mesh*.
    """
    return find_shot_sculpt_node_for_mesh(mesh) is not None


def create_shot_sculpt_node() -> str | None:
    """Create an AtlasShotSculptor node for the currently selected mesh(es).

    If any of the selected meshes already belongs to a node, that node is
    reused and the rest of the selection is appended to it (so selecting a
    body + a piece of cloth together, for example, still creates one shared
    group). Otherwise a brand-new, independent node is created. The
    originally selected meshes remain selected afterward.

    Returns:
        str | None: Name of the AtlasShotSculptor node, or ``None`` on failure.

    Raises:
        RuntimeError: Via ``cmds.error`` when no valid meshes are selected.
    """
    meshes = get_selected_meshes()
    if not meshes:
        cmds.error("Please select one or more skinned mesh objects to create a Shot-Sculpt group.")
        return None

    node = None
    for m in meshes:
        candidate = find_shot_sculpt_node_for_mesh(m)
        if candidate:
            node = candidate
            break

    if node:
        cmds.warning("An Atlas Sculptor node already manages one of the selected meshes. Adding the rest to it.")
    else:
        node = cmds.createNode("network", name="AtlasShotSculptorNode#")
        cmds.addAttr(node, longName="is_shot_sculptor_node", attributeType="bool", hidden=True)
        cmds.setAttr(f"{node}.is_shot_sculptor_node", True)
        cmds.addAttr(node, longName="origMeshes",  attributeType="message", multi=True)
        cmds.addAttr(node, longName="blendShapes", attributeType="message", multi=True)
        ensure_layer_data_attr(node)

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

    restore_selection(meshes)

    return node


def _delete_node(node: str, delete_blendshapes: bool) -> None:
    """Delete one AtlasShotSculptor node, its connections, and optionally its blendShapes.

    Shared implementation behind :func:`delete_shot_sculptor_node` and
    :func:`delete_all_shot_sculptor_nodes`.

    Args:
        node (str): AtlasShotSculptor network node name to delete.
        delete_blendshapes (bool): If ``True``, every blendShape deformer
            wired to this node is deleted along with it (the sculpted
            layers on the mesh are lost). If ``False``, the blendShape
            deformers are left in place on the mesh -- only the Atlas
            Sculptor bookkeeping (the network node and its layer data) is
            removed, and the sculpted shape stays exactly as it currently
            reads, no longer tracked as layers.
    """
    for i in cmds.getAttr(f"{node}.origMeshes", multiIndices=True) or []:
        conns = cmds.listConnections(
            f"{node}.origMeshes[{i}]", source=True, destination=False, plugs=True
        )
        if conns:
            try:
                cmds.disconnectAttr(conns[0], f"{node}.origMeshes[{i}]")
            except Exception as exc:
                cmds.warning(f"Failed to disconnect origMesh[{i}]: {exc}")

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
            if delete_blendshapes and cmds.objExists(bs_node) and cmds.nodeType(bs_node) == "blendShape":
                try:
                    cmds.delete(bs_node)
                except Exception as exc:
                    cmds.warning(f"Failed to delete blendShape {bs_node}: {exc}")

    try:
        cmds.delete(node)
    except Exception as exc:
        cmds.warning(f"Failed to delete AtlasShotSculptor node: {exc}")


def delete_shot_sculptor_node(mesh: str, delete_blendshapes: bool = True) -> None:
    """Delete the AtlasShotSculptor node managing *mesh* and all its connections.

    The node's layer bookkeeping (stored on the node itself, see
    :mod:`.config`) is deleted for free along with the node -- there is no
    separate JSON file to clean up.

    Args:
        mesh (str): Any mesh managed by the node to delete.
        delete_blendshapes (bool): Whether to also delete the blendShape
            deformers this node created. Defaults to ``True`` for backward
            compatibility with existing call sites; the UI should prompt
            the user (see ``atlas_sculptor.ui.delete_dialog``) and pass
            their choice explicitly.
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        cmds.warning("No Shot Sculptor node found for this object.")
        return
    _delete_node(node, delete_blendshapes)


def delete_all_shot_sculptor_nodes(delete_blendshapes: bool = True) -> int:
    """Delete every AtlasShotSculptor node in the scene.

    Args:
        delete_blendshapes (bool): Whether to also delete every blendShape
            deformer created by these nodes. See :func:`delete_shot_sculptor_node`.

    Returns:
        int: How many nodes were deleted.
    """
    nodes = find_all_shot_sculptor_nodes()
    if not nodes:
        cmds.warning("No Shot Sculptor nodes found in the scene.")
        return 0

    for node in nodes:
        if cmds.objExists(node):
            _delete_node(node, delete_blendshapes)

    return len(nodes)

# endregion