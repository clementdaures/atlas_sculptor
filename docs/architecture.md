# Architecture

## The one rule

`core` never imports from `ui`. `core` has zero Qt dependencies and zero
knowledge that a UI exists — every function takes plain arguments (mesh
names, layer indices, frame numbers) and returns plain data. `ui` is the
only package allowed to import `maya.cmds` *and* PySide6 in the same
module; it calls into `core` for anything that touches the Maya scene.

This is what makes `core` unit-testable without a running Maya session
(see [Getting Started](getting_started.md#running-the-tests)) and is the
constraint to preserve when adding new modules: if you're writing Qt
code, it belongs in `ui`; if you're writing scene-graph logic, it belongs
in `core`, even if only one `ui` controller currently calls it.

## Data model

Every mesh (or group of meshes initialized together) gets its own
`AtlasShotSculptorNode`, a Maya `network` node. Nothing about frames or
layers is shared between two nodes — selecting a different object always
shows that object's own frame list.

```
AtlasShotSculptorNode (network node)
├── origMeshes[]      -> connected mesh transforms
├── blendShapes[]     -> one blendShape deformer per mesh
└── layerData         -> JSON string: {"layers": {"<index>": {...}}}
```

A **frame** is a timeline time. Several **layers** (blendShape targets)
can share a frame — e.g. a base layer plus additive corrective layers —
and each layer carries its own ease-in/out, hold-in/out, and key-type
settings for how it blends onto the timeline.

Storing the bookkeeping on the node itself (`core/models/config.py`)
rather than a sidecar file means it travels with the Maya file for free
and is deleted for free when the node is deleted.

## Request flow example

Adding a new corrective layer to an existing frame, end to end:

1. `ui/controllers/frame_panel.py` — `_on_add_layer_clicked` fires when
   the user clicks "Add Layer" and calls
   `core.models.layers.add_layer_to_frame(mesh, frame_time)`.
2. `core/models/layers.py` — resolves the mesh's `AtlasShotSculptorNode`
   via `core.scene.node`, creates the new blendShape target, and
   persists the updated bookkeeping via `core.models.config.save_layer_data`.
3. Control returns to `ui/controllers/frame_panel.py`, which refreshes
   the layer list (rebuilding `ui/widgets/layer_row.py` rows) from
   `core.models.layers.get_layer_entries(mesh, frame_time)`.

At no point does step 2 import anything from `ui`. Creating the *first*
layer of a brand-new frame goes through `core.scene.frames.create_sculpt_frame`
instead, which does the same resolve-node-then-delegate-to-`models.layers`
dance for a frame's initial base layer.

## Subpackage docs

- [`core/`](core.md) — `scene`, `models`, `states`, `legacy`.
- [`ui/`](ui.md) — `views`, `controllers`, `widgets`, `resources`.
