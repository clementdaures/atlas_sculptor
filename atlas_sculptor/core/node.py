# -*- coding: utf-8 -*-
"""
Node discovery, creation and deletion for the Atlas Shot Sculptor tool.

Author: Clement Daures
Website: clementdaures.com
"""

import maya.cmds as cmds

from .selection import get_selected_meshes


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
