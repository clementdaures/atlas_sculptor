# -*- coding: utf-8 -*-
"""
Layer data accessors, creation, rename, delete & reordering for the Atlas
Shot Sculptor tool.

A **layer** is one blendShape target index (``weight[i]``), scoped to one
AtlasShotSculptor node. Every layer gets its own, node-local unique index --
layers never share an index within a node, even if they belong to the same
frame. (Two *different* nodes may reuse the same index number independently;
that's fine, since everything is looked up per-node.) Several layers can
share the same frame time.

Every frame's *first* layer is its **base layer** (``is_base``). It is
always pinned to the bottom of that frame's layer stack -- the other layers
of the frame are sculpted refinements on top of it, and can be freely
reordered among themselves via ``order``.

Author: Clement Daures
Website: clementdaures.com
"""

from __future__ import annotations

import maya.cmds as cmds

from .config import (
    DEFAULT_LAYER_SETTINGS,
    load_layer_data,
    save_layer_data,
    next_layer_index,
    next_order,
)
from .node import find_shot_sculpt_node_for_mesh
from .selection import restore_selection


# ---------------------------------------------------------------------------
# Data accessors
# ---------------------------------------------------------------------------

def get_layer_entries(mesh: str, frame_time: int) -> list[tuple[int, str, bool, bool]]:
    """Return every layer belonging to *frame_time*, display-ordered.

    Non-base layers come first, ordered by their ``order`` value (lowest on
    top); the frame's base layer is always last, regardless of its stored
    order -- it is pinned to the bottom of the stack.

    Args:
        mesh (str): Any mesh managed by the node to query.
        frame_time (int): Timeline frame to look up.

    Returns:
        list[tuple[int, str, bool, bool]]:
            ``(layer_index, display_name, enabled, is_base)`` tuples.
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        return []

    data = load_layer_data(node)

    entries: list[tuple[int, str, bool, bool, int]] = []
    for key, info in data["layers"].items():
        if int(info.get("frame_time", -1)) == frame_time:
            entries.append((
                int(key),
                info.get("name", f"Layer {key}"),
                bool(info.get("enabled", True)),
                bool(info.get("is_base", False)),
                int(info.get("order", 0)),
            ))
    # is_base sorts last (False < True); ties break on order, then index.
    entries.sort(key=lambda e: (e[3], e[4], e[0]))
    return [(idx, name, enabled, is_base) for idx, name, enabled, is_base, _order in entries]


def get_layer_settings(mesh: str, layer_index: int) -> dict:
    """Return the stored animation settings for a single layer.

    Args:
        mesh (str): Any mesh managed by the node the layer belongs to.
        layer_index (int): Layer/target index.

    Returns:
        dict: Animation settings, falling back to :data:`DEFAULT_LAYER_SETTINGS`
            for any missing keys.
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        return dict(DEFAULT_LAYER_SETTINGS)

    data = load_layer_data(node)
    info = data["layers"].get(str(layer_index), {})
    settings = dict(DEFAULT_LAYER_SETTINGS)
    settings.update({k: info[k] for k in DEFAULT_LAYER_SETTINGS if k in info})
    return settings


def get_layer_frame_time(mesh: str, layer_index: int) -> int | None:
    """Return the frame time a given layer belongs to.

    Args:
        mesh (str): Any mesh managed by the node the layer belongs to.
        layer_index (int): Layer/target index.

    Returns:
        int | None: The frame time, or ``None`` if the layer is unknown.
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        return None
    data = load_layer_data(node)
    info = data["layers"].get(str(layer_index))
    return int(info["frame_time"]) if info else None


# ---------------------------------------------------------------------------
# Layer creation
# ---------------------------------------------------------------------------

def _capture_layer_pose(node: str, new_index: int, frame_time: int) -> None:
    """Duplicate each managed mesh at *frame_time* and wire it up as a new
    blendShape target at *new_index*, then key a neutral 0-1-0 pulse.

    Restores the caller's original current time and selection afterward --
    ``duplicate()`` in particular tends to select the new duplicate, which
    would otherwise leak out as a spurious selection change.

    Args:
        node (str): AtlasShotSculptor node name.
        new_index (int): Freshly-allocated layer/target index.
        frame_time (int): Timeline frame the layer's target pose is captured at.
    """
    original_time = cmds.currentTime(query=True)
    original_selection = cmds.ls(selection=True) or []
    cmds.currentTime(frame_time)

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

        target_name = f"{mesh}_frame{frame_time}_layer{new_index}"
        temp_dup = cmds.duplicate(mesh, name=target_name)[0]

        cmds.blendShape(bs, edit=True, target=(mesh, new_index, target_name, 1.0))
        cmds.delete(temp_dup)
        cmds.blendShape(bs, edit=True, resetTargetDelta=(0, new_index))

        weight_attr = f"{bs}.weight[{new_index}]"
        cmds.setKeyframe(weight_attr, value=0.0, t=(frame_time - 1))
        cmds.setKeyframe(weight_attr, value=1.0, t=frame_time)
        cmds.setKeyframe(weight_attr, value=0.0, t=(frame_time + 1))
        cmds.keyTangent(
            weight_attr,
            time=(frame_time - 1, frame_time + 1),
            ott="linear", itt="linear",
        )

    cmds.currentTime(original_time)
    restore_selection(original_selection)


def add_layer_to_frame(
    mesh: str,
    frame_time: int,
    name: str | None = None,
    is_base: bool = False,
) -> int | None:
    """Add a new layer (independent blendShape target) to an existing or new frame.

    Multiple layers may share *frame_time*; each still gets its own,
    node-local unique target index. Non-base layers are appended to the top
    of the frame's stack (i.e. above any existing non-base layers, but
    still below -- visually above, in list terms -- the pinned base layer).

    Args:
        mesh (str): Any mesh managed by the target node.
        frame_time (int): Timeline frame the new layer should live at.
        name (str | None): Optional custom display name. Defaults to
            ``"Base <frame_time>"`` for base layers, ``"Layer <index>"`` otherwise.
        is_base (bool): Whether this is the frame's base layer -- pinned to
            the bottom of the stack. Only :func:`atlas_sculptor.core.frames.create_sculpt_frame`
            should normally pass ``True``.

    Returns:
        int | None: The new layer's index, or ``None`` on failure.
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        cmds.error("No Atlas Sculptor node found for this object. Please initialize it first.")
        return None

    bs_list = cmds.listConnections(f"{node}.blendShapes", source=True, destination=False) or []
    if not bs_list:
        cmds.error("Atlas Sculptor node has no mesh data.")
        return None

    data = load_layer_data(node)
    new_index = next_layer_index(node, bs_list, data)

    _capture_layer_pose(node, new_index, frame_time)

    if name:
        layer_name = name
    elif is_base:
        layer_name = f"Base {frame_time}"
    else:
        layer_name = f"Layer {new_index}"

    order_value = 0 if is_base else next_order(frame_time, data)

    data["layers"][str(new_index)] = {
        "frame_time": int(frame_time),
        "name": layer_name,
        "enabled": True,
        "is_base": bool(is_base),
        "order": order_value,
        **DEFAULT_LAYER_SETTINGS,
    }
    save_layer_data(node, data)

    # Activate sculpt target on the first blendShape so the user can start sculpting
    cmds.sculptTarget(bs_list[0], edit=False, target=new_index)

    return new_index


# ---------------------------------------------------------------------------
# Layer enable/disable (mute)
# ---------------------------------------------------------------------------

def set_layer_enabled(mesh: str, layer_index: int, enabled: bool) -> None:
    """Mute or unmute a layer's blendShape weight, keeping its keys intact.

    Uses ``cmds.mute`` so the underlying animation curve (and hence the
    layer's Ease/Hold/Key-Type keys) is fully preserved and can be toggled
    back on later.

    Args:
        mesh (str): Any mesh managed by the target node.
        layer_index (int): Layer/target index to toggle.
        enabled (bool): ``True`` to unmute (bsp active), ``False`` to mute
            (bsp bypassed / effectively "off").
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        return

    bs_list = cmds.listConnections(f"{node}.blendShapes", source=True, destination=False) or []
    for bs in bs_list:
        weight_attr = f"{bs}.weight[{layer_index}]"
        if not cmds.objExists(weight_attr):
            continue
        try:
            is_muted = bool((cmds.mute(weight_attr, query=True) or [False])[0])
        except Exception:
            is_muted = False
        try:
            if enabled and is_muted:
                cmds.mute(weight_attr, disable=True)
            elif not enabled and not is_muted:
                cmds.mute(weight_attr)
        except Exception as exc:
            cmds.warning(f"Atlas Sculptor: could not toggle layer {layer_index} on {bs}: {exc}")

    data = load_layer_data(node)
    key = str(layer_index)
    if key in data["layers"]:
        data["layers"][key]["enabled"] = bool(enabled)
        save_layer_data(node, data)


# ---------------------------------------------------------------------------
# Layer reordering
# ---------------------------------------------------------------------------

def reorder_layers(mesh: str, frame_time: int, ordered_layer_indices: list[int]) -> None:
    """Re-number the stacking order of a frame's non-base layers.

    The base layer is always excluded and stays pinned to the bottom
    regardless of its position in *ordered_layer_indices*.

    Args:
        mesh (str): Any mesh managed by the target node.
        frame_time (int): Timeline frame whose layers are being reordered.
        ordered_layer_indices (list[int]): Layer indices in their desired
            top-to-bottom display order (base layer entries, if present,
            are ignored).
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        return

    data = load_layer_data(node)
    order = 0
    for layer_index in ordered_layer_indices:
        key = str(layer_index)
        info = data["layers"].get(key)
        if not info or int(info.get("frame_time", -1)) != frame_time or info.get("is_base"):
            continue
        info["order"] = order
        order += 1
    save_layer_data(node, data)


# ---------------------------------------------------------------------------
# Layer rename & delete
# ---------------------------------------------------------------------------

def rename_layer(mesh: str, layer_index: int, new_name: str) -> None:
    """Store a custom display name for a single layer.

    Args:
        mesh (str): Any mesh managed by the target node.
        layer_index (int): Layer/target index.
        new_name    (str): Non-empty string to use as the display name.
    """
    new_name = new_name.strip()
    if not new_name:
        return
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        return
    data = load_layer_data(node)
    key = str(layer_index)
    if key not in data["layers"]:
        return
    data["layers"][key]["name"] = new_name
    save_layer_data(node, data)


def delete_layer(mesh: str, layer_index: int) -> None:
    """Remove a single layer's blendShape target and its bookkeeping record.

    If the deleted layer was its frame's base layer and other layers remain
    for that frame, the remaining layer with the lowest ``order`` is
    promoted to base so the frame always keeps a pinned bottom layer.

    Args:
        mesh (str): Any mesh managed by the target node.
        layer_index (int): Layer/target index to remove.
    """
    node = find_shot_sculpt_node_for_mesh(mesh)
    if not node:
        return

    data = load_layer_data(node)
    info = data["layers"].get(str(layer_index))
    frame_time = info.get("frame_time") if info else None
    was_base = bool(info.get("is_base")) if info else False

    bs_list = cmds.listConnections(f"{node}.blendShapes", source=True, destination=False) or []
    for bs in bs_list:
        attr = f"{bs}.weight[{layer_index}]"
        if cmds.objExists(attr):
            try:
                cmds.removeMultiInstance(attr, b=True)
            except Exception as exc:
                cmds.warning(f"Could not remove target {layer_index} from {bs}: {exc}")

    data["layers"].pop(str(layer_index), None)

    if was_base and frame_time is not None:
        remaining = [
            (int(k), v) for k, v in data["layers"].items()
            if v.get("frame_time") == frame_time
        ]
        if remaining:
            remaining.sort(key=lambda pair: int(pair[1].get("order", 0)))
            promote_key = str(remaining[0][0])
            data["layers"][promote_key]["is_base"] = True

    save_layer_data(node, data)