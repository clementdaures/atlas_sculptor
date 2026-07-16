# -*- coding: utf-8 -*-
"""
Per-node layer bookkeeping storage for the Atlas Shot Sculptor tool.

Layer data (frame time, name, base flag, stacking order, enabled flag, and
per-layer animation settings) is persisted as a single JSON string stored
directly on each AtlasShotSculptor network node, via the ``layerData``
attribute.

Storing it on the node itself (rather than a sidecar file next to the
scene) means the bookkeeping:

* travels automatically with the Maya file -- survives renames, copies,
  and scenes that have never been saved;
* is deleted for free whenever the node is deleted -- no separate cleanup
  step needed, and no sidecar file that can be left behind or lost.

Author: Clement Daures
Website: clementdaures.com
"""

from __future__ import annotations

import json

import maya.cmds as cmds


LAYER_DATA_ATTR = "layerData"

DEFAULT_LAYER_SETTINGS = {
    "ease_in": 1,
    "ease_out": 1,
    "hold_in": 0,
    "hold_out": 0,
    "key_type": "linear",
}


def ensure_layer_data_attr(node: str) -> None:
    """Add the ``layerData`` string attribute to *node* if it isn't there yet.

    Args:
        node (str): AtlasShotSculptor network node name.
    """
    if not cmds.attributeQuery(LAYER_DATA_ATTR, node=node, exists=True):
        cmds.addAttr(node, longName=LAYER_DATA_ATTR, dataType="string")
        cmds.setAttr(f"{node}.{LAYER_DATA_ATTR}", "{}", type="string")


def load_layer_data(node: str) -> dict:
    """Load *node*'s layer bookkeeping, tolerating a missing/corrupt attribute.

    Args:
        node (str): AtlasShotSculptor network node name.

    Returns:
        dict: ``{"layers": {"<index>": {...}}}`` -- always well-formed.
    """
    raw = ""
    if cmds.attributeQuery(LAYER_DATA_ATTR, node=node, exists=True):
        raw = cmds.getAttr(f"{node}.{LAYER_DATA_ATTR}") or ""

    if not raw:
        return {"layers": {}}
    try:
        data = json.loads(raw)
    except Exception as exc:
        cmds.warning(f"Atlas Sculptor: could not parse layer data on {node} ({exc}). Starting fresh.")
        return {"layers": {}}

    if not isinstance(data, dict) or not isinstance(data.get("layers"), dict):
        return {"layers": {}}
    return data


def save_layer_data(node: str, data: dict) -> None:
    """Write *data* back to *node*'s ``layerData`` attribute.

    Args:
        node (str): AtlasShotSculptor network node name.
        data (dict): The full per-node config dict, as returned by
            :func:`load_layer_data`.
    """
    ensure_layer_data_attr(node)
    try:
        cmds.setAttr(f"{node}.{LAYER_DATA_ATTR}", json.dumps(data), type="string")
    except Exception as exc:
        cmds.warning(f"Atlas Sculptor: failed to save layer data on {node} ({exc}).")


def next_layer_index(node: str, bs_list: list[str], data: dict) -> int:
    """Compute the next free layer/target index, unique within *node*.

    Looks at both the JSON bookkeeping and the live blendShape weight
    indices so a corrupt or stale JSON can't cause an index collision.

    Args:
        node (str): AtlasShotSculptor network node name.
        bs_list (list[str]): Connected blendShape deformer names.
        data (dict): Loaded config dict for *node* (see :func:`load_layer_data`).

    Returns:
        int: Next unused layer index for *node*.
    """
    candidates = [-1]
    candidates.extend(int(k) for k in data["layers"].keys())
    for bs in bs_list:
        indices = cmds.getAttr(f"{bs}.weight", multiIndices=True) or []
        candidates.extend(indices)
    return max(candidates) + 1


def next_order(frame_time: int, data: dict) -> int:
    """Compute the next free stacking order for a non-base layer in *frame_time*.

    Args:
        frame_time (int): Timeline frame being appended to.
        data (dict): Loaded config dict for the node.

    Returns:
        int: Next order value (existing non-base layers keep theirs).
    """
    existing = [
        int(info.get("order", 0))
        for info in data["layers"].values()
        if info.get("frame_time") == frame_time and not info.get("is_base")
    ]
    return (max(existing) + 1) if existing else 0