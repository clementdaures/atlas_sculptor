# -*- coding: utf-8 -*-
"""Tests for atlas_sculptor.core.scene.node.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# python modules
import pytest

# atlas_sculptor/core/...
from atlas_sculptor.core.scene import node

# endregion

# ==========

# region Discovery

def test_find_shot_sculpt_node_for_mesh_returns_none_when_unmanaged(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    assert node.find_shot_sculpt_node_for_mesh("bodyGeo") is None


def test_mesh_has_shot_sculptor_node_reflects_discovery(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    assert node.mesh_has_shot_sculptor_node("bodyGeo") is False

    fake_cmds.select(["bodyGeo"])
    node.create_shot_sculpt_node()

    assert node.mesh_has_shot_sculptor_node("bodyGeo") is True


def test_find_all_shot_sculptor_nodes_ignores_plain_network_nodes(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.add_network_node("SomeUnrelatedNetworkNode")
    fake_cmds.select(["bodyGeo"])

    created = node.create_shot_sculpt_node()

    assert node.find_all_shot_sculptor_nodes() == [created]

# endregion

# ==========

# region Creation

def test_create_shot_sculpt_node_requires_a_selection(fake_cmds):
    fake_cmds.select([])

    assert node.create_shot_sculpt_node() is None
    assert fake_cmds.warnings == []  # cmds.error(), not cmds.warning(), was raised
    # cmds.error() is faked to raise -- covered by node.py calling cmds.error()
    # rather than returning, so create_shot_sculpt_node never reaches its
    # return statement in this branch; nothing further to assert here.


def test_create_shot_sculpt_node_wires_mesh_and_blendshape(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])

    created = node.create_shot_sculpt_node()

    assert created is not None
    assert fake_cmds.attributeQuery("is_shot_sculptor_node", node=created, exists=True)
    assert fake_cmds.getAttr(f"{created}.is_shot_sculptor_node") is True

    mesh_conns = fake_cmds.listConnections(f"{created}.origMeshes", source=True, destination=False)
    assert mesh_conns == ["bodyGeo"]

    bs_conns = fake_cmds.listConnections(f"{created}.blendShapes", source=True, destination=False)
    assert bs_conns == ["bodyGeo_atlas_sculpt_bsp"]

    # the originally selected mesh(es) stay selected afterward
    assert fake_cmds.selection == ["bodyGeo"]


def test_create_shot_sculpt_node_reuses_node_for_grouped_meshes(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds._add_transform_with_mesh("clothGeo")
    fake_cmds.select(["bodyGeo"])
    first = node.create_shot_sculpt_node()

    fake_cmds.select(["bodyGeo", "clothGeo"])
    second = node.create_shot_sculpt_node()

    assert second == first
    assert node.find_all_shot_sculptor_nodes() == [first]
    managed = fake_cmds.listConnections(f"{first}.origMeshes", source=True, destination=False)
    assert sorted(managed) == ["bodyGeo", "clothGeo"]


def test_create_shot_sculpt_node_is_idempotent_for_already_managed_mesh(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    first = node.create_shot_sculpt_node()

    fake_cmds.select(["bodyGeo"])
    second = node.create_shot_sculpt_node()

    assert second == first
    # re-running on an already-fully-managed mesh must not create a
    # second origMeshes connection for it
    assert fake_cmds.getAttr(f"{first}.origMeshes", multiIndices=True) == [0]

# endregion

# ==========

# region Deletion

def test_delete_shot_sculptor_node_removes_node_and_blendshape(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    created = node.create_shot_sculpt_node()

    node.delete_shot_sculptor_node("bodyGeo", delete_blendshapes=True)

    assert created not in fake_cmds.nodes
    assert "bodyGeo_atlas_sculpt_bsp" not in fake_cmds.nodes
    assert node.find_shot_sculpt_node_for_mesh("bodyGeo") is None


def test_delete_shot_sculptor_node_can_keep_blendshapes(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    created = node.create_shot_sculpt_node()

    node.delete_shot_sculptor_node("bodyGeo", delete_blendshapes=False)

    assert created not in fake_cmds.nodes
    # the deformer is left behind on the mesh, just no longer tracked
    assert "bodyGeo_atlas_sculpt_bsp" in fake_cmds.nodes


def test_delete_shot_sculptor_node_warns_when_mesh_unmanaged(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")

    node.delete_shot_sculptor_node("bodyGeo")

    assert fake_cmds.warnings  # "No Shot Sculptor node found for this object."


def test_delete_all_shot_sculptor_nodes_removes_every_node(fake_cmds):
    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds._add_transform_with_mesh("propGeo")
    fake_cmds.select(["bodyGeo"])
    node.create_shot_sculpt_node()
    fake_cmds.select(["propGeo"])
    node.create_shot_sculpt_node()

    deleted_count = node.delete_all_shot_sculptor_nodes(delete_blendshapes=True)

    assert deleted_count == 2
    assert node.find_all_shot_sculptor_nodes() == []


def test_delete_all_shot_sculptor_nodes_warns_when_scene_is_empty(fake_cmds):
    assert node.delete_all_shot_sculptor_nodes() == 0
    assert fake_cmds.warnings  # "No Shot Sculptor nodes found in the scene."

# endregion