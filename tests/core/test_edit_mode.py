# -*- coding: utf-8 -*-
"""Tests for atlas_sculptor.core.states.edit_mode.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# python modules
import pytest

# atlas_sculptor/core/...
from atlas_sculptor.core.states import edit_mode
from atlas_sculptor.core.scene import frames
from atlas_sculptor.core.scene.node import find_shot_sculpt_node_for_mesh

# endregion

# ==========

# region Enter Edit Mode

def test_enter_edit_mode_requires_a_node(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    with pytest.raises(RuntimeError):
        edit_mode.enter_edit_mode("bodyGeo", 0)


def test_enter_edit_mode_errors_on_unknown_layer(wired_mesh):
    with pytest.raises(RuntimeError):
        edit_mode.enter_edit_mode(wired_mesh, 999)


def test_enter_edit_mode_sets_time_selects_mesh_and_activates_sculpt_target(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    frame_time, layer_index = frames.create_sculpt_frame(wired_mesh)
    fake_cmds.currentTime(1500)  # move away so we can prove enter_edit_mode moves it back

    edit_mode.enter_edit_mode(wired_mesh, layer_index)

    assert fake_cmds.currentTime(query=True) == frame_time
    assert fake_cmds.selection == [wired_mesh]

    node = find_shot_sculpt_node_for_mesh(wired_mesh)
    bs_name = fake_cmds.listConnections(f"{node}.blendShapes", source=True, destination=False)[0]
    assert fake_cmds.getAttr(f"{bs_name}.weight[{layer_index}]") == 1.0
    assert fake_cmds.sculpt_state[bs_name] == layer_index
    assert fake_cmds.current_tool == "SculptMeshTool"

# endregion

# ==========

# region Exit Edit Mode

def test_exit_edit_mode_noop_for_unmanaged_mesh(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    edit_mode.exit_edit_mode("bodyGeo", 0)  # should not raise


def test_exit_edit_mode_clears_sculpt_target(wired_mesh, fake_cmds):
    fake_cmds.currentTime(1001)
    _frame_time, layer_index = frames.create_sculpt_frame(wired_mesh)
    edit_mode.enter_edit_mode(wired_mesh, layer_index)

    edit_mode.exit_edit_mode(wired_mesh, layer_index)

    node = find_shot_sculpt_node_for_mesh(wired_mesh)
    bs_name = fake_cmds.listConnections(f"{node}.blendShapes", source=True, destination=False)[0]
    assert fake_cmds.sculpt_state[bs_name] == -1

# endregion
