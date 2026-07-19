# -*- coding: utf-8 -*-
"""Tests for atlas_sculptor.core.models.layers.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# python modules
import pytest

# atlas_sculptor/core/...
from atlas_sculptor.core.models import layers
from atlas_sculptor.core.models.config import DEFAULT_LAYER_SETTINGS
from atlas_sculptor.core.scene import frames
from atlas_sculptor.core.scene.node import find_shot_sculpt_node_for_mesh

# endregion

# ==========

# region Get Layers

def test_get_layer_entries_empty_for_unmanaged_mesh(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    assert layers.get_layer_entries("bodyGeo", 1001) == []


def test_get_layer_entries_puts_base_last_and_orders_the_rest(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    _frame_time, base_index = frames.create_sculpt_frame(wired_mesh)
    first_extra = layers.add_layer_to_frame(wired_mesh, 1001)
    second_extra = layers.add_layer_to_frame(wired_mesh, 1001)

    entries = layers.get_layer_entries(wired_mesh, 1001)

    assert [idx for idx, *_ in entries] == [first_extra, second_extra, base_index]
    assert entries[-1][3] is True  # is_base
    assert entries[0][3] is False and entries[1][3] is False


def test_get_layer_settings_defaults_when_layer_unknown(wired_mesh):
    assert layers.get_layer_settings(wired_mesh, 999) == DEFAULT_LAYER_SETTINGS


def test_get_layer_settings_defaults_when_mesh_unmanaged(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    assert layers.get_layer_settings("bodyGeo", 0) == DEFAULT_LAYER_SETTINGS


def test_get_layer_frame_time_returns_none_for_unknown_layer(wired_mesh):
    assert layers.get_layer_frame_time(wired_mesh, 999) is None


def test_get_layer_frame_time_returns_the_stored_frame(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1075)
    _frame_time, layer_index = frames.create_sculpt_frame(wired_mesh)

    assert layers.get_layer_frame_time(wired_mesh, layer_index) == 1075

# endregion

# ==========

# region Add Layers

def test_add_layer_to_frame_requires_a_node(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    with pytest.raises(RuntimeError):
        layers.add_layer_to_frame("bodyGeo", 1001)


def test_add_layer_to_frame_default_names(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    _frame_time, base_index = frames.create_sculpt_frame(wired_mesh)
    extra_index = layers.add_layer_to_frame(wired_mesh, 1001)

    entries = {idx: name for idx, name, _enabled, _is_base in layers.get_layer_entries(wired_mesh, 1001)}
    assert entries[base_index] == "Base 1001"
    assert entries[extra_index] == f"Layer {extra_index}"


def test_add_layer_to_frame_honors_custom_name(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    frames.create_sculpt_frame(wired_mesh)
    extra_index = layers.add_layer_to_frame(wired_mesh, 1001, name="Squash")

    entries = {idx: name for idx, name, _enabled, _is_base in layers.get_layer_entries(wired_mesh, 1001)}
    assert entries[extra_index] == "Squash"


def test_add_layer_to_frame_indices_never_collide(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    frames.create_sculpt_frame(wired_mesh)
    idx_a = layers.add_layer_to_frame(wired_mesh, 1001)
    idx_b = layers.add_layer_to_frame(wired_mesh, 1001)

    assert idx_a != idx_b


def test_add_layer_to_frame_captures_a_duplicate_and_keys_the_weight(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    _frame_time, layer_index = frames.create_sculpt_frame(wired_mesh)

    node = find_shot_sculpt_node_for_mesh(wired_mesh)
    bs_name = fake_cmds.listConnections(f"{node}.blendShapes", source=True, destination=False)[0]
    weight_attr = f"{bs_name}.weight[{layer_index}]"

    assert fake_cmds.keyframes[weight_attr] == {1000: 0.0, 1001: 1.0, 1002: 0.0}
    assert fake_cmds.sculpt_state[bs_name] == layer_index

# endregion

# ==========

# region Set Layer

def test_set_layer_enabled_mutes_and_unmutes(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    _frame_time, layer_index = frames.create_sculpt_frame(wired_mesh)

    layers.set_layer_enabled(wired_mesh, layer_index, False)
    entries = layers.get_layer_entries(wired_mesh, 1001)
    assert entries[0][2] is False  # enabled

    layers.set_layer_enabled(wired_mesh, layer_index, True)
    entries = layers.get_layer_entries(wired_mesh, 1001)
    assert entries[0][2] is True


def test_set_layer_enabled_noop_for_unmanaged_mesh(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    layers.set_layer_enabled("bodyGeo", 0, False)  # should not raise

# endregion

# ==========

# region Reorder Layer

def test_reorder_layers_renumbers_non_base_layers_only(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    _frame_time, base_index = frames.create_sculpt_frame(wired_mesh)
    idx_a = layers.add_layer_to_frame(wired_mesh, 1001)
    idx_b = layers.add_layer_to_frame(wired_mesh, 1001)

    # idx_b currently precedes idx_a (later-added sorts first); flip them.
    layers.reorder_layers(wired_mesh, 1001, [idx_a, idx_b])

    entries = layers.get_layer_entries(wired_mesh, 1001)
    assert [idx for idx, *_ in entries] == [idx_a, idx_b, base_index]


def test_reorder_layers_ignores_indices_from_other_frames(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    frames.create_sculpt_frame(wired_mesh)
    idx_a = layers.add_layer_to_frame(wired_mesh, 1001)
    fake_cmds.currentTime(1050)
    frames.create_sculpt_frame(wired_mesh)
    idx_other_frame = layers.add_layer_to_frame(wired_mesh, 1050)

    # Passing an index from a different frame should simply be skipped.
    layers.reorder_layers(wired_mesh, 1001, [idx_a, idx_other_frame])

    entries_1050 = layers.get_layer_entries(wired_mesh, 1050)
    assert entries_1050[0][0] == idx_other_frame  # untouched

# endregion

# ==========

# region Rename Layer

def test_rename_layer_updates_display_name(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    _frame_time, layer_index = frames.create_sculpt_frame(wired_mesh)

    layers.rename_layer(wired_mesh, layer_index, "  Smile Peak  ")

    entries = layers.get_layer_entries(wired_mesh, 1001)
    assert entries[0][1] == "Smile Peak"


def test_rename_layer_ignores_blank_name(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    _frame_time, layer_index = frames.create_sculpt_frame(wired_mesh)
    original_name = layers.get_layer_entries(wired_mesh, 1001)[0][1]

    layers.rename_layer(wired_mesh, layer_index, "   ")

    assert layers.get_layer_entries(wired_mesh, 1001)[0][1] == original_name


def test_rename_layer_noop_for_unknown_layer(wired_mesh):
    layers.rename_layer(wired_mesh, 999, "Ghost")  # should not raise

# endregion

# ==========

# region Delete Layer

def test_delete_layer_removes_bookkeeping_and_promotes_new_base(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    _frame_time, base_index = frames.create_sculpt_frame(wired_mesh)
    extra_index = layers.add_layer_to_frame(wired_mesh, 1001)

    layers.delete_layer(wired_mesh, base_index)

    entries = layers.get_layer_entries(wired_mesh, 1001)
    assert len(entries) == 1
    idx, _name, _enabled, is_base = entries[0]
    assert idx == extra_index
    assert is_base is True  # promoted


def test_delete_layer_last_layer_leaves_frame_empty(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    _frame_time, base_index = frames.create_sculpt_frame(wired_mesh)

    layers.delete_layer(wired_mesh, base_index)

    assert layers.get_layer_entries(wired_mesh, 1001) == []


def test_delete_layer_noop_for_unmanaged_mesh(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    layers.delete_layer("bodyGeo", 0)  # should not raise

# endregion
