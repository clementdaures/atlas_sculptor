# -*- coding: utf-8 -*-
"""Tests for atlas_sculptor.core.scene.frames.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# python modules
import pytest

# atlas_sculptor/core/...
from atlas_sculptor.core.scene import frames
from atlas_sculptor.core.models import layers

# endregion

# ==========

# region Get Frame Entries

def test_get_frame_entries_empty_when_mesh_unmanaged(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    assert frames.get_frame_entries("bodyGeo") == []


def test_get_frame_entries_empty_when_no_layers_yet(wired_mesh):
    assert frames.get_frame_entries(wired_mesh) == []


def test_get_frame_entries_groups_and_labels_by_frame(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    frames.create_sculpt_frame(wired_mesh)
    layers.add_layer_to_frame(wired_mesh, 1001)  # second layer, same frame
    fake_cmds.currentTime(1050)
    frames.create_sculpt_frame(wired_mesh)

    entries = frames.get_frame_entries(wired_mesh)

    assert entries == [
        (1001, "Frame 1001  (2 layers)"),
        (1050, "Frame 1050  (1 layer)"),
    ]

# endregion

# ==========

# region Create Sculpt Frame

def test_create_sculpt_frame_requires_a_node(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    with pytest.raises(RuntimeError):
        frames.create_sculpt_frame("bodyGeo")


def test_create_sculpt_frame_uses_current_time_and_creates_base_layer(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1024)

    result = frames.create_sculpt_frame(wired_mesh)

    assert result is not None
    frame_time, layer_index = result
    assert frame_time == 1024

    entries = layers.get_layer_entries(wired_mesh, 1024)
    assert len(entries) == 1
    idx, _name, _enabled, is_base = entries[0]
    assert idx == layer_index
    assert is_base is True

# endregion

# ==========

# region Delete Frame

def test_delete_frame_removes_every_layer_for_that_frame(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    frames.create_sculpt_frame(wired_mesh)
    layers.add_layer_to_frame(wired_mesh, 1001)
    fake_cmds.currentTime(1050)
    frames.create_sculpt_frame(wired_mesh)

    frames.delete_frame(wired_mesh, 1001)

    assert layers.get_layer_entries(wired_mesh, 1001) == []
    assert len(layers.get_layer_entries(wired_mesh, 1050)) == 1


def test_delete_frame_is_a_noop_for_unknown_frame(wired_mesh):
    # Should not raise even though no layer exists at this frame time.
    frames.delete_frame(wired_mesh, 9999)

    assert frames.get_frame_entries(wired_mesh) == []

# endregion
