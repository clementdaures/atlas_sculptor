# -*- coding: utf-8 -*-
"""Tests for atlas_sculptor.core.scene.selection.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# atlas_sculptor/core/...
from atlas_sculptor.core.scene import selection

# endregion

# ==========

# region Selection Test

def test_get_selected_meshes_filters_to_mesh_transforms(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    NodeCls = type(fake_cmds.nodes["bodyGeo"])
    fake_cmds.nodes["locator1"] = NodeCls("locator1", "transform", shapes=["locator1Shape"])
    fake_cmds.nodes["locator1Shape"] = NodeCls("locator1Shape", "locator")
    fake_cmds.select(["bodyGeo", "locator1"])

    assert selection.get_selected_meshes() == ["bodyGeo"]


def test_restore_selection_reselects_original(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])

    selection.restore_selection(["bodyGeo"])

    assert fake_cmds.selection == ["bodyGeo"]


def test_restore_selection_clears_when_original_was_empty(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])

    selection.restore_selection([])

    assert fake_cmds.selection == []

# endregion