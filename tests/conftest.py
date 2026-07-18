# -*- coding: utf-8 -*-
"""
Shared pytest fixtures.

`atlas_sculptor.core` imports `maya.cmds` at module load time, so a fake
`maya` package must exist in ``sys.modules`` *before* any
``atlas_sculptor.core.*`` module is imported anywhere in the test run.
This file is collected by pytest before test modules, which is exactly
what we need: it installs :class:`FakeCmds` (a small in-memory stand-in
covering the handful of ``cmds`` calls Atlas Sculptor's core uses) as
``maya.cmds`` first, then everything downstream can ``import
atlas_sculptor.core...`` normally, in or out of Maya.

This fake is intentionally minimal -- it grows as tests need more of
``cmds``, rather than trying to model all of Maya up front.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# python modules
from __future__ import annotations
import sys
import types
from dataclasses import dataclass, field

import pytest

# endregion

# ==========

# region Dataclass

@dataclass
class _Node:
    name: str
    node_type: str
    attrs: dict = field(default_factory=dict)
    shapes: list[str] = field(default_factory=list)

# endregion

# ==========

# region Fake Command

class FakeCmds:
    """A minimal in-memory stand-in for ``maya.cmds``.

    Only implements what ``atlas_sculptor.core`` currently calls. Extend
    it as new tests need more coverage -- keep it honest to the real
    ``cmds`` signatures (same kwarg names) so tests reflect real usage.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, _Node] = {}
        self.selection: list[str] = []
        self.warnings: list[str] = []
        self._current_time = 1001

    # scene population helpers (test-only, not part of cmds)

    def _add_transform_with_mesh(self, name: str) -> None:
        shape = f"{name}Shape"
        self.nodes[name] = _Node(name, "transform", shapes=[shape])
        self.nodes[shape] = _Node(shape, "mesh")

    def add_network_node(self, name: str) -> str:
        """Create a bare ``network``-type node (an AtlasShotSculptorNode stand-in)."""
        self.nodes[name] = _Node(name, "network")
        return name

    # selection

    def ls(self, selection=False, type=None):  # noqa: A002 - matches cmds' kwarg
        if selection:
            if type is None:
                return list(self.selection)
            return [n for n in self.selection if self.nodes[n].node_type == type]
        if type is not None:
            return [n.name for n in self.nodes.values() if n.node_type == type]
        return list(self.nodes)

    def select(self, names=None, replace=True, clear=False):
        if clear:
            self.selection = []
        else:
            names = names or []
            if isinstance(names, str):
                names = [names]
            self.selection = list(names)

    def listRelatives(self, name, shapes=False, fullPath=False):  # noqa: N802,A002
        node = self.nodes.get(name)
        if node is None:
            return []
        if shapes:
            return list(node.shapes)
        return []

    def nodeType(self, name):  # noqa: N802
        node = self.nodes.get(name)
        return node.node_type if node else None

    # attributes

    def attributeQuery(self, attr, node, exists=False):  # noqa: N802
        return attr in self.nodes[node].attrs if node in self.nodes else False

    def addAttr(self, node, longName, **kwargs):  # noqa: N802
        self.nodes[node].attrs.setdefault(longName, None)

    def setAttr(self, plug, value, type=None):  # noqa: A002
        node, attr = plug.split(".", 1)
        self.nodes[node].attrs[attr] = value

    def getAttr(self, plug, multiIndices=False):  # noqa: N802
        node, attr = plug.split(".", 1)
        return self.nodes[node].attrs.get(attr)

    def currentTime(self, query=False):
        return self._current_time

    # misc

    def warning(self, message):
        self.warnings.append(message)

    def error(self, message):
        raise RuntimeError(message)


_maya_module: types.ModuleType | None = None
_cmds_module: types.ModuleType | None = None


def install_fake_maya() -> FakeCmds:
    """Install a fresh :class:`FakeCmds` as ``maya.cmds`` and return it.

    Reuses the same ``maya``/``maya.cmds`` module objects across calls
    (only rebinding their attributes to a fresh :class:`FakeCmds`
    instance's methods). This matters: ``atlas_sculptor.core`` modules do
    ``import maya.cmds as cmds`` once, at their own import time, binding
    ``cmds`` to a specific module *object*. If a later call here swapped
    in a brand-new module object, already-imported core modules would
    keep talking to the stale one -- so instead we keep the module
    object identity stable and only swap out what it points to.
    """
    global _maya_module, _cmds_module

    fake_cmds = FakeCmds()

    if _cmds_module is None:
        _maya_module = types.ModuleType("maya")
        _cmds_module = types.ModuleType("maya.cmds")
        _maya_module.cmds = _cmds_module
        sys.modules["maya"] = _maya_module
        sys.modules["maya.cmds"] = _cmds_module

    for attr_name in dir(fake_cmds):
        if not attr_name.startswith("_"):
            setattr(_cmds_module, attr_name, getattr(fake_cmds, attr_name))

    return fake_cmds


# Install immediately at collection time, before any test module (or the
# atlas_sculptor.core modules they import) gets a chance to run
install_fake_maya()


@pytest.fixture
def fake_cmds():
    """A fresh :class:`FakeCmds`, reinstalled as ``maya.cmds`` for this test."""
    return install_fake_maya()

# endregion

