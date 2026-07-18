# -*- coding: utf-8 -*-
"""Tests for atlas_sculptor.core.models.config.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# atlas_sculptor/core/...
from atlas_sculptor.core.models import config

# endregion

# ==========

# region Test Config

def test_ensure_layer_data_attr_only_added_once(fake_cmds):
    node = fake_cmds.add_network_node("AtlasShotSculptorNode1")

    config.ensure_layer_data_attr(node)
    config.ensure_layer_data_attr(node)  # idempotent, should not raise/duplicate

    assert fake_cmds.nodes[node].attrs["layerData"] == "{}"


def test_load_layer_data_returns_empty_shape_when_missing(fake_cmds):
    node = fake_cmds.add_network_node("AtlasShotSculptorNode1")

    assert config.load_layer_data(node) == {"layers": {}}


def test_save_then_load_round_trips(fake_cmds):
    node = fake_cmds.add_network_node("AtlasShotSculptorNode1")
    data = {"layers": {"0": {"frame_time": 1001, "name": "base", "is_base": True}}}

    config.save_layer_data(node, data)

    assert config.load_layer_data(node) == data


def test_load_layer_data_recovers_from_corrupt_json(fake_cmds):
    node = fake_cmds.add_network_node("AtlasShotSculptorNode1")
    config.ensure_layer_data_attr(node)
    fake_cmds.nodes[node].attrs["layerData"] = "{not valid json"

    assert config.load_layer_data(node) == {"layers": {}}
    assert fake_cmds.warnings  # a warning was raised about the bad data


def test_next_layer_index_ignores_existing_indices(fake_cmds):
    node = fake_cmds.add_network_node("AtlasShotSculptorNode1")
    data = {"layers": {"0": {}, "2": {}}}

    assert config.next_layer_index(node, bs_list=[], data=data) == 3


def test_next_order_is_scoped_to_non_base_layers_in_same_frame(fake_cmds):
    data = {
        "layers": {
            "0": {"frame_time": 1001, "is_base": True, "order": 0},
            "1": {"frame_time": 1001, "is_base": False, "order": 0},
            "2": {"frame_time": 1050, "is_base": False, "order": 5},
        }
    }

    assert config.next_order(1001, data) == 1
    assert config.next_order(1050, data) == 6
    assert config.next_order(2000, data) == 0

# endregion