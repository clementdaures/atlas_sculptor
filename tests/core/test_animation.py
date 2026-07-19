# -*- coding: utf-8 -*-
"""Tests for atlas_sculptor.core.models.animation.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# atlas_sculptor/core/...
from atlas_sculptor.core.models import animation, layers
from atlas_sculptor.core.scene import frames
from atlas_sculptor.core.scene.node import find_shot_sculpt_node_for_mesh

# endregion

# ==========

# region Update Layer Animation

def test_update_layer_animation_noop_for_unmanaged_mesh(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    animation.update_layer_animation("bodyGeo", 0)  # should not raise


def test_update_layer_animation_noop_for_unknown_layer(wired_mesh):
    animation.update_layer_animation(wired_mesh, 999)  # should not raise


def test_update_layer_animation_lays_down_four_keys_around_frame_time(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    frame_time, layer_index = frames.create_sculpt_frame(wired_mesh)

    animation.update_layer_animation(
        wired_mesh, layer_index, ease_in=3, ease_out=2, hold_in=1, hold_out=1,
    )

    node = find_shot_sculpt_node_for_mesh(wired_mesh)
    bs_name = fake_cmds.listConnections(f"{node}.blendShapes", source=True, destination=False)[0]
    weight_attr = f"{bs_name}.weight[{layer_index}]"

    start_full = frame_time - 1
    end_full = frame_time + 1
    start_zero = start_full - 3
    end_zero = end_full + 2

    assert fake_cmds.keyframes[weight_attr] == {
        start_zero: 0.0,
        start_full: 1.0,
        end_full: 1.0,
        end_zero: 0.0,
    }


def test_update_layer_animation_clamps_negative_inputs_to_zero(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    frame_time, layer_index = frames.create_sculpt_frame(wired_mesh)

    animation.update_layer_animation(
        wired_mesh, layer_index, ease_in=-5, ease_out=-5, hold_in=-5, hold_out=-5,
    )

    node = find_shot_sculpt_node_for_mesh(wired_mesh)
    bs_name = fake_cmds.listConnections(f"{node}.blendShapes", source=True, destination=False)[0]
    weight_attr = f"{bs_name}.weight[{layer_index}]"

    # Every offset clamps to 0, so all four keys collapse onto frame_time.
    assert set(fake_cmds.keyframes[weight_attr]) == {frame_time}


def test_update_layer_animation_persists_settings_for_get_layer_settings(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    _frame_time, layer_index = frames.create_sculpt_frame(wired_mesh)

    animation.update_layer_animation(
        wired_mesh, layer_index,
        ease_in=4, ease_out=5, hold_in=6, hold_out=7, key_type="stepped",
    )

    settings = layers.get_layer_settings(wired_mesh, layer_index)
    assert settings == {
        "ease_in": 4, "ease_out": 5, "hold_in": 6, "hold_out": 7, "key_type": "stepped",
    }


def test_update_layer_animation_stepped_sets_step_tangents(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    frame_time, layer_index = frames.create_sculpt_frame(wired_mesh)

    animation.update_layer_animation(wired_mesh, layer_index, key_type="stepped")

    node = find_shot_sculpt_node_for_mesh(wired_mesh)
    bs_name = fake_cmds.listConnections(f"{node}.blendShapes", source=True, destination=False)[0]
    weight_attr = f"{bs_name}.weight[{layer_index}]"

    tangent_kwargs = [t for t in fake_cmds.tangents[weight_attr]]
    assert any(t.get("ott") == "step" for t in tangent_kwargs)
    assert any(t.get("itt") == "step" for t in tangent_kwargs)

# endregion
