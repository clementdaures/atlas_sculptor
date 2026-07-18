# `core/`

Maya-facing logic. Every module here does real `maya.cmds` work but has
zero PySide6 or `ui` imports, so it can be reasoned about (and, with
`maya.cmds` mocked — see [Getting Started](getting_started.md#running-the-tests))
tested without a running Maya session.

## `core/scene/` — scene-graph operations

Imperative operations against the live Maya scene: finding, creating,
and deleting things.

| Module | Owns |
|---|---|
| `node.py` | `AtlasShotSculptorNode` discovery/creation/deletion. Every managed mesh (or group of meshes) gets exactly one node; nothing about frames or layers is ever shared between two nodes. |
| `selection.py` | Reading the current mesh selection, and restoring a selection snapshot after a Maya command mutates it as a side effect (`blendShape`, `duplicate`, ...). |
| `frames.py` | Frame-level operations: listing every distinct timeline frame for a mesh, creating a frame's initial base layer, deleting every layer in a frame. Delegates the actual layer bookkeeping to `core.models.layers`. |

## `core/models/` — data & storage

The shape of the data Atlas Sculptor tracks, and how it's persisted.

| Module | Owns |
|---|---|
| `config.py` | Per-node `layerData` JSON storage: load/save, the default layer-settings schema, and index/order bookkeeping helpers (`next_layer_index`, `next_order`). This is the only module that touches the `layerData` attribute directly. |
| `layers.py` | Layer CRUD: add/delete a layer, list a frame's layers, get/set a layer's settings. Builds on `config.py` for persistence and `scene.node`/`scene.selection` for the Maya-side blendShape work. |
| `animation.py` | Per-layer animation/curve settings (ease in/out, hold in/out, key type) — the values the UI's Animation Settings panel edits. |

## `core/states/` — transient state machines

| Module | Owns |
|---|---|
| `edit_mode.py` | Sculpt edit-mode entry/exit for a single layer: which layer (if any) is currently being sculpted, and the Maya-side setup/teardown for entering and leaving that mode. |

## `core/legacy/`

`logic.py` is the original, monolithic prototype this package was split
out of. It predates the `scene`/`models`/`states` split, nothing imports
it, and it is kept only as a historical reference during the ongoing
refactor — see the module's own docstring. Do not add to it or import
from it; if you find yourself wanting something from it, port the
function into the appropriate `scene`/`models`/`states` module first.

## Adding a new module

Ask which of the three questions it answers:

- *"Do something in the live Maya scene right now"* → `scene/`
- *"What does this data look like, and how is it stored"* → `models/`
- *"Track whether we're currently in some mode"* → `states/`

If it's none of these, it's probably UI logic — see [`ui/`](ui.md).
