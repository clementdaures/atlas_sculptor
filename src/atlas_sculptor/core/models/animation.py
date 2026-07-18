# -*- coding: utf-8 -*-
"""
Per-layer animation curve management for the Atlas Shot Sculptor tool.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# python modules
from __future__ import annotations

# dcc import
import maya.cmds as cmds

# atlas_sculptor/core/models/...
from atlas_sculptor.core.models.layers import get_layer_frame_time

# atlas_sculptor/core/...
from atlas_sculptor.core.models.config import load_layer_data, save_layer_data
from atlas_sculptor.core.scene.node import find_shot_sculpt_node_for_mesh

#endregion

# ==========

# region Animation Logic

def update_layer_animation(
    mesh: str,
    layer_index: int,
    ease_in:  int = 1,
    ease_out: int = 1,
    hold_in:  int = 0,
    hold_out: int = 0,
    key_type: str = "linear",
) -> None:
    """Re-key a single layer's blendShape weight curve and persist the settings.

    Removes all keys in the affected range and lays down four new keys:

    * ``start_zero``  - weight = 0 (ease starts)
    * ``start_full``  - weight = 1 (hold starts)
    * ``end_full``    - weight = 1 (hold ends)
    * ``end_zero``    - weight = 0 (ease ends)

    Args:
        mesh (str): Any mesh managed by the target node.
        layer_index (int): Layer/target index.
        ease_in  (int): Frames to ramp up before the hold.
        ease_out (int): Frames to ramp down after the hold.
        hold_in  (int): Frames of full weight before the layer's frame time.
        hold_out (int): Frames of full weight after the layer's frame time.
        key_type (str): ``"linear"``, ``"spline"``, or ``"stepped"``.
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        return

    frame_time = get_layer_frame_time(mesh, layer_index)
    if frame_time is None:
        return

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
        weight_attr = f"{bs}.weight[{layer_index}]"
        if not cmds.objExists(weight_attr):
            continue

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

    data = load_layer_data(node)
    key = str(layer_index)
    if key in data["layers"]:
        data["layers"][key].update({
            "ease_in": ease_in, "ease_out": ease_out,
            "hold_in": hold_in, "hold_out": hold_out,
            "key_type": key_type,
        })
        save_layer_data(node, data)

#endregion