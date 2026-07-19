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

    Node attributes (:attr:`_Node.attrs`) double as the multi-attr index
    tracker: a plain key (``"origMeshes"``) marks the attribute's
    existence, and a bracketed key (``"origMeshes[0]"``) marks that a
    given index has been used -- ``getAttr(..., multiIndices=True)``
    simply enumerates the bracketed keys for that attribute. Actual
    connections (what a given index's plug is *wired to*) live
    separately in :attr:`connections`, keyed by the full destination
    plug string (``"<node>.origMeshes[0]"``), so disconnecting a plug
    doesn't remove its index from the multi-attr -- matching real Maya,
    where a multi-attr index sticks around until something explicitly
    removes it (``removeMultiInstance``).
    """

    # region Construction

    def __init__(self) -> None:
        self.nodes: dict[str, _Node] = {}
        self.selection: list[str] = []
        self.warnings: list[str] = []
        self.connections: dict[str, str] = {}
        self.keyframes: dict[str, dict[int, float]] = {}
        self.tangents: dict[str, list[dict]] = {}
        self.muted: dict[str, bool] = {}
        self.sculpt_state: dict[str, int | None] = {}
        self.current_tool: str | None = None
        self._current_time = 1001
        self._script_jobs: dict[int, tuple[str, object]] = {}
        self._next_script_job_id = 1

    # endregion

    # ==========

    # region Scene population helpers (test-only, not part of cmds)

    def _add_transform_with_mesh(self, name: str) -> None:
        shape = f"{name}Shape"
        self.nodes[name] = _Node(name, "transform", shapes=[shape])
        self.nodes[shape] = _Node(shape, "mesh")

    def add_network_node(self, name: str) -> str:
        """Create a bare ``network``-type node (an AtlasShotSculptorNode stand-in)."""
        self.nodes[name] = _Node(name, "network")
        return name

    # endregion

    # ==========

    # region Selection

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

    # endregion

    # ==========

    # region Attributes & multi-attrs

    def attributeQuery(self, attr, node, exists=False):  # noqa: N802
        return attr in self.nodes[node].attrs if node in self.nodes else False

    def addAttr(self, node, longName, **kwargs):  # noqa: N802
        self.nodes[node].attrs.setdefault(longName, None)

    def setAttr(self, plug, value, type=None):  # noqa: A002
        node, attr = plug.split(".", 1)
        self.nodes[node].attrs[attr] = value

    def getAttr(self, plug, multiIndices=False):  # noqa: N802
        node, attr = plug.split(".", 1)
        if node not in self.nodes:
            return [] if multiIndices else None
        node_attrs = self.nodes[node].attrs
        if multiIndices:
            prefix = attr + "["
            indices = []
            for key in node_attrs:
                if key.startswith(prefix) and key.endswith("]"):
                    try:
                        indices.append(int(key[len(prefix):-1]))
                    except ValueError:
                        continue
            return sorted(indices)
        return node_attrs.get(attr)

    def objExists(self, name):  # noqa: N802
        if "." in name:
            node, attr = name.split(".", 1)
            return node in self.nodes and attr in self.nodes[node].attrs
        return name in self.nodes

    # endregion

    # ==========

    # region Connections

    def connectAttr(self, src, dst, force=True):  # noqa: N802
        node, idxattr = dst.split(".", 1)
        self.nodes[node].attrs.setdefault(idxattr, True)
        self.connections[dst] = src

    def disconnectAttr(self, src, dst):  # noqa: N802
        if self.connections.get(dst) == src:
            del self.connections[dst]

    def listConnections(self, plug, source=True, destination=False, plugs=False):  # noqa: N802
        matches = [
            src for dest, src in self.connections.items()
            if dest == plug or dest.startswith(plug + "[")
        ]
        if plugs:
            return matches
        return [m.split(".")[0] for m in matches]

    # endregion

    # ==========

    # region Node lifecycle

    def createNode(self, node_type, name=None):  # noqa: N802
        name = name or node_type
        if name.endswith("#"):
            base = name[:-1]
            i = 1
            candidate = f"{base}{i}"
            while candidate in self.nodes:
                i += 1
                candidate = f"{base}{i}"
            name = candidate
        self.nodes[name] = _Node(name, node_type)
        return name

    def duplicate(self, node_name, **kwargs):
        new_name = kwargs.get("name") or f"{node_name}_dup"
        self.nodes[new_name] = _Node(new_name, "transform")
        return [new_name]

    def delete(self, *args):
        for arg in args:
            names = arg if isinstance(arg, (list, tuple)) else [arg]
            for n in names:
                self.nodes.pop(n, None)

    def removeMultiInstance(self, plug, b=True):  # noqa: N802,A002
        node, idxattr = plug.split(".", 1)
        self.nodes[node].attrs.pop(idxattr, None)
        self.keyframes.pop(plug, None)
        self.tangents.pop(plug, None)
        self.muted.pop(plug, None)

    # endregion

    # ==========

    # region BlendShape & sculpt

    def blendShape(self, *args, **kwargs):  # noqa: N802
        if kwargs.get("edit"):
            bs = args[0]
            target = kwargs.get("target")
            if isinstance(target, tuple) and len(target) == 4:
                _mesh, index, _target_name, _weight = target
                self.nodes[bs].attrs[f"weight[{index}]"] = True
            return [bs]
        mesh = args[0]
        name = kwargs.get("name") or f"{mesh}_blendShape"
        self.nodes[name] = _Node(name, "blendShape")
        return [name]

    def sculptTarget(self, bs, edit=False, target=None):  # noqa: N802
        self.sculpt_state[bs] = target

    def setToolTo(self, tool_name):  # noqa: N802
        self.current_tool = tool_name

    def mute(self, plug, disable=False, query=False):
        if query:
            return [self.muted.get(plug, False)]
        self.muted[plug] = not disable
        return None

    # endregion

    # ==========

    # region Keyframes

    def setKeyframe(self, plug, value=None, t=None):  # noqa: N802
        self.keyframes.setdefault(plug, {})[t] = value

    def cutKey(self, plug, time=None, option="keys"):  # noqa: N802
        if time is None:
            self.keyframes[plug] = {}
            return
        lo, hi = time
        keys = self.keyframes.get(plug, {})
        for t in list(keys):
            if lo <= t <= hi:
                del keys[t]

    def keyTangent(self, plug, time=None, itt=None, ott=None):  # noqa: N802
        self.tangents.setdefault(plug, []).append({"time": time, "itt": itt, "ott": ott})

    # endregion

    # ==========

    # region Time

    def currentTime(self, *args, query=False):  # noqa: N802
        if query:
            return self._current_time
        if args:
            self._current_time = args[0]
            return None
        return self._current_time

    # endregion

    # ==========

    # region Misc

    def warning(self, message):
        self.warnings.append(message)

    def error(self, message):
        raise RuntimeError(message)

    # endregion

    # ==========

    # region Script jobs & deferred eval

    def scriptJob(self, event=None, kill=None, force=False, protected=False):  # noqa: N802
        """Minimal stand-in for ``cmds.scriptJob``.

        Registration (``event=[event_name, callback]``) records the
        callback and returns a fake job id; nothing fires automatically --
        tests trigger events explicitly via :meth:`fire_script_job` to stay
        deterministic. ``kill=<job_id>`` unregisters it, matching real
        ``cmds.scriptJob(kill=..., force=True)`` usage.
        """
        if kill is not None:
            self._script_jobs.pop(kill, None)
            return True
        event_name, callback = event
        job_id = self._next_script_job_id
        self._next_script_job_id += 1
        self._script_jobs[job_id] = (event_name, callback)
        return job_id

    def fire_script_job(self, event_name: str) -> None:
        """Test-only helper: invoke every registered callback for *event_name*."""
        for _job_id, (name, callback) in list(self._script_jobs.items()):
            if name == event_name:
                callback()

    def evalDeferred(self, func, *args, **kwargs):  # noqa: N802
        """Runs *func* immediately -- deterministic stand-in for Maya's
        next-idle-tick deferral.
        """
        return func()

    # endregion


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


@pytest.fixture
def wired_mesh(fake_cmds):
    """A mesh transform ("bodyGeo") with a fully-wired Atlas Sculptor node
    (one origMeshes/blendShapes connection ready).

    Saves every ``layers``/``frames``/``animation``/``edit_mode`` test from
    re-deriving the same "create a node for a mesh" boilerplate that
    ``test_node.py`` already covers in isolation.
    """
    from atlas_sculptor.core.scene import node as node_module

    fake_cmds._add_transform_with_mesh("bodyGeo")
    fake_cmds.select(["bodyGeo"])
    node_module.create_shot_sculpt_node()
    return "bodyGeo"

# endregion