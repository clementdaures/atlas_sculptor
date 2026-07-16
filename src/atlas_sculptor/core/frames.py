# -*- coding: utf-8 -*-
"""
Frame-level accessors, creation & deletion for the Atlas Shot Sculptor tool.

A **frame** is just a timeline time (int), scoped to one AtlasShotSculptor
node. Several layers (see :mod:`.layers`) can share the same frame time;
this module deals with the frame as a whole -- listing frames, creating a
frame's initial base layer, and deleting every layer that belongs to a frame.

Author: Clement Daures
Website: clementdaures.com
"""

from __future__ import annotations

import maya.cmds as cmds

# atlas_sculptor/core/...
from atlas_sculptor.core.config import load_layer_data
from atlas_sculptor.core.models.layers import add_layer_to_frame, delete_layer, get_layer_entries
from atlas_sculptor.core.node import find_shot_sculpt_node_for_mesh


def get_frame_entries(mesh: str) -> list[tuple[int, str]]:
    """Return every distinct timeline frame that has at least one layer,
    for the object *mesh* belongs to.

    Args:
        mesh (str): Any mesh managed by the node to query.

    Returns:
        list[tuple[int, str]]:
            ``(frame_time, display_label)`` tuples, sorted by frame time.
            *display_label* includes the layer count, e.g. ``"Frame 1001 (2 layers)"``.
            Empty if *mesh* has no Atlas Sculptor node.
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        return []

    data = load_layer_data(node)

    frame_layer_counts: dict[int, int] = {}
    for info in data["layers"].values():
        frame_time = int(info.get("frame_time", 0))
        frame_layer_counts[frame_time] = frame_layer_counts.get(frame_time, 0) + 1

    entries: list[tuple[int, str]] = []
    for frame_time in sorted(frame_layer_counts):
        count = frame_layer_counts[frame_time]
        suffix = "layer" if count == 1 else "layers"
        entries.append((frame_time, f"Frame {frame_time}  ({count} {suffix})"))
    return entries


def create_sculpt_frame(mesh: str) -> tuple[int, int] | None:
    """Create a brand-new timeline frame (at the current time) with one base
    layer, for the object *mesh* belongs to.

    Args:
        mesh (str): Any mesh managed by the target node.

    Returns:
        tuple[int, int] | None: ``(frame_time, layer_index)`` of the new
            frame's base layer, or ``None`` on failure.

    Raises:
        RuntimeError: Via ``cmds.error`` when preconditions are not met.
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        cmds.error("No Atlas Sculptor node found for this object. Please initialize it first.")
        return None

    mesh_list = cmds.listConnections(f"{node}.origMeshes", source=True, destination=False) or []
    bs_list   = cmds.listConnections(f"{node}.blendShapes", source=True, destination=False) or []
    if not mesh_list or not bs_list:
        cmds.error("Atlas Sculptor node has no meshes. Create the Shot-Sculpt group first.")
        return None

    frame_time = int(cmds.currentTime(query=True))
    layer_index = add_layer_to_frame(mesh, frame_time, is_base=True)
    if layer_index is None:
        return None
    return frame_time, layer_index


def delete_frame(mesh: str, frame_time: int) -> None:
    """Remove every layer belonging to *frame_time*.

    Args:
        mesh (str): Any mesh managed by the target node.
        frame_time (int): Timeline frame whose layers should all be deleted.
    """
    for layer_index, _name, _enabled, _is_base in get_layer_entries(mesh, frame_time):
        delete_layer(mesh, layer_index)