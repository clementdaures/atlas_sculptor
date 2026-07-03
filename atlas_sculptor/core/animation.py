# -*- coding: utf-8 -*-
"""
Animation curve management for the Atlas Shot Sculptor tool.

Author: Clement Daures
Website: clementdaures.com
"""

import maya.cmds as cmds

from .node import find_shot_sculpt_node


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
