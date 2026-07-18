# Developer Guide

[`architecture.md`](architecture.md), [`core.md`](core.md), and
[`ui.md`](ui.md) map *what lives where*. This note is the complement:
*how the trickier bits actually work* -- the parts of the codebase where
reading a single function in isolation doesn't tell you why it's written
that way. Read the three docs above first if you haven't; this assumes
the `core`/`ui` split and the module map are already familiar.

## The data model, precisely

One `AtlasShotSculptorNode` (a Maya `network` node) per managed object
(or group of objects initialized together):

```
AtlasShotSculptorNode
├── is_shot_sculptor_node : bool   (hidden marker attr, existence = "this is one of ours")
├── origMeshes[]  : message, multi  -> connected mesh transforms
├── blendShapes[] : message, multi  -> one blendShape deformer per mesh, same index as origMeshes
└── layerData     : string          -> JSON: {"layers": {"<index>": {...}}}
```

`origMeshes[i]` and `blendShapes[i]` always share the same index `i` --
that's how [`core/scene/node.py`](../src/atlas_sculptor/core/scene/node.py)
pairs a mesh with its own blendShape deformer without storing the pairing
twice. Everything that needs "the deformer for this mesh" walks both
multi-attrs at the same indices (see `_capture_layer_pose` and
`enter_edit_mode`, below).

A **layer** is a single blendShape target index (`weight[i]` on *every*
blendShape the node owns -- see [Multi-mesh groups](#multi-mesh-groups-one-index-many-deformers)
below). Its record in `layerData["layers"]`:

```json
{
  "frame_time": 1032,
  "name": "Layer 4",
  "enabled": true,
  "is_base": false,
  "order": 1,
  "ease_in": 1, "ease_out": 1, "hold_in": 0, "hold_out": 0, "key_type": "linear"
}
```

`core/models/config.py` is the *only* module that touches the
`layerData` attribute directly (`ensure_layer_data_attr`,
`load_layer_data`, `save_layer_data`) -- every other module reads/writes
layer data by calling into `config.py`, never `cmds.getAttr`/`setAttr`
on `layerData` itself. Keep it that way: it's what makes the JSON
schema a one-place change.

## Layer index allocation (`config.next_layer_index`)

Every layer needs a target index that's unique *within its node*, and
that index doubles as the blendShape target/weight index in Maya. Two
things could go stale and cause a collision if index allocation only
looked at one of them:

- the JSON bookkeeping (if a save was interrupted, or hand-edited), or
- the live blendShape's actual weight indices (if a target was added or
  removed outside Atlas Sculptor).

`next_layer_index` guards against both by taking the max of *both*
sources and adding one:

```python
candidates = [-1]
candidates.extend(int(k) for k in data["layers"].keys())
for bs in bs_list:
    candidates.extend(cmds.getAttr(f"{bs}.weight", multiIndices=True) or [])
return max(candidates) + 1
```

The `[-1]` seed means an empty node correctly allocates index `0`. If
you ever add a second way to create targets outside this function,
route it through here too, or this invariant (JSON and live blendShape
indices always agree) breaks silently.

## Layer ordering & the pinned base layer

Two related but separate concepts, both stored per-layer:

- `is_base` -- exactly one layer per frame should have this `True`. It's
  always sorted to the *bottom* of that frame's stack, regardless of
  its `order` value.
- `order` -- only meaningful for non-base layers; the relative stacking
  position among *them*.

`layers.get_layer_entries` produces the display order for a frame in
one sort call:

```python
entries.sort(key=lambda e: (e[3], e[4], e[0]))  # (is_base, order, index)
```

`is_base` sorts `False` before `True` in Python, so base always lands
last no matter what `order` says -- that's the entire pinning mechanism,
no special-casing needed elsewhere. `order` is the tiebreaker among
non-base layers, and `index` is the final tiebreaker (stable ordering
even if two layers somehow share an `order`).

**Base-layer promotion on delete.** If the deleted layer was the base
and other layers remain in that frame, `layers.delete_layer` promotes
whichever remaining layer has the lowest `order` to `is_base = True`:

```python
remaining.sort(key=lambda pair: int(pair[1].get("order", 0)))
data["layers"][str(remaining[0][0])]["is_base"] = True
```

This guarantees every non-empty frame always has exactly one base layer
-- callers (the UI's layer list, `get_layer_entries`'s sort) never have
to handle "zero base layers in a non-empty frame" as a case.

## Capturing a layer's sculpt target (`layers._capture_layer_pose`)

This is the function that actually turns "the mesh's current shape at
frame N" into a blendShape target, for every mesh the node manages:

1. Snapshot the current time and selection (both get mutated below).
2. Jump to `frame_time`.
3. For each `(origMeshes[i], blendShapes[i])` pair:
   a. `cmds.duplicate` the mesh -- this bakes its *current* deformed
      shape (cache playback included) into a static duplicate.
   b. Wire that duplicate in as the new blendShape target at
      `new_index`, at full (`1.0`) weight.
   c. Delete the duplicate -- the target shape is now owned by the
      blendShape node itself, the duplicate was just a delivery vehicle.
   d. `resetTargetDelta` -- with no sculpting done yet, the target
      should currently equal the base mesh (delta = zero); this clears
      any incidental delta the duplicate/target dance might have
      introduced, so the layer starts as a true no-op until the artist
      actually sculpts it.
   e. Key the *weight* curve with a neutral 0→1→0 pulse
      (`frame_time - 1`, `frame_time`, `frame_time + 1`, linear
      tangents) -- a placeholder curve so the layer has *some* shape
      immediately, later fully replaced by whatever the artist sets in
      Animation Settings (step 6 of the [User Guide](user_guide.md)).
4. Restore the original time and selection.

Restoring the selection here (and in most `core` functions) matters
because `duplicate()` selects its result as a side effect -- if that
selection change reached the UI's selection-changed listener, it would
look like the artist selected a random duplicate mesh mid-operation. See
[Selection-sync suppression](#selection-sync-suppression-the-trickiest-part-of-the-ui-layer)
for how the UI layer additionally guards against this.

## Multi-mesh groups: one index, many deformers

When a node manages several meshes (e.g. body + cloth initialized
together), a single layer index refers to *the same logical layer* on
every mesh, but each mesh has its own blendShape deformer and hence its
own `weight[index]` plug. Anywhere a layer is toggled, keyed, or
sculpted, the code loops every `bs` in `bs_list` and applies the change
identically:

- `layers.set_layer_enabled` mutes/unmutes `weight[layer_index]` on
  every deformer.
- `animation.update_layer_animation` re-keys `weight[layer_index]` on
  every deformer with the *same* curve.
- `edit_mode.enter_edit_mode` forces `weight[layer_index] = 1.0` on
  every deformer before activating the sculpt tool.

This is why the JSON bookkeeping only stores one record per layer index
rather than per-mesh: the settings are meant to apply uniformly across
the whole group. If you ever need per-mesh independent settings within
a group, that's a schema change (`layerData` would need to key on
`(mesh, layer_index)` or nest per-mesh), not a small tweak.

## Animation curve keying math (`models/animation.update_layer_animation`)

Four keyframes bound the layer's weight curve around its frame time,
computed directly from the four widget values:

```
start_zero = frame_time - hold_in - ease_in     (weight 0, ease begins)
start_full = frame_time - hold_in               (weight 1, hold begins)
end_full   = frame_time + hold_out               (weight 1, hold ends)
end_zero   = frame_time + hold_out + ease_out    (weight 0, ease ends)
```

Every call first does `cmds.cutKey(weight_attr, time=(start_zero - 1,
end_zero + 1))` to clear the *entire* previous curve in that range before
laying down the new four keys -- so changing, say, Ease In from 3 down
to 1 doesn't leave stray old keys sitting between the new, tighter
bounds. The `±1` padding on the cut range exists because `cutKey`'s
`time` range is a closed interval in Maya's key-time units; without the
padding, a key sitting exactly on `start_zero` or `end_zero` from a
*previous* call could survive the cut and collide with the new key at
the same time.

`key_type` changes only the tangents, not the four times:

- `linear` -- straight ramps both ways (the tightest, most literal
  reading of the Ease In/Out values).
- `spline` (`auto` tangents) -- smoothed ease in/out.
- `stepped` -- `ott="step"` at the hold boundaries and `itt="step"` at
  the ease boundaries, i.e. a hard on/off cut with no interpolation at
  all, regardless of the Ease In/Out values (they still control *where*
  the step lands, just not how it blends).

## Selection-sync suppression -- the trickiest part of the UI layer

`ui/controllers/selection_sync.py`'s whole job is: keep the window's
upper page and hint text in sync with Maya's actual selection, *without*
reacting to selection changes the tool itself causes as a side effect
of running a `core` function (`duplicate`, `select`, entering edit mode,
...). Getting this wrong either tears down sculpt edit mode every time
`_capture_layer_pose` duplicates a mesh, or leaves the UI stale after a
real user selection change.

The mechanism is `_suppressed_selection_sync()`, a context manager every
`core`-calling slot wraps its call in:

```python
with self._suppressed_selection_sync():
    node.create_shot_sculpt_node()
```

Two layers of defense are needed simultaneously, because Maya's
`SelectionChanged` scriptJob is not guaranteed to fire synchronously
inside the triggering `cmds.select()` call -- delivery can land on the
next idle tick instead of immediately:

1. **The flag itself is released one idle tick late**, via
   `cmds.evalDeferred`, not immediately when the `with` block exits.
   This covers the case where the scriptJob callback is already queued
   for "later this tick" when the block exits -- releasing the flag
   synchronously would let that queued callback slip through the gap
   between "block exited" and "callback actually runs."
2. **Regardless of the flag's state**, `_on_selection_changed` also
   compares the *live* selection against a snapshot
   (`_maya_selection_set_by_us`) taken right as the suppressed block
   finished. If they still match, it's treated as a late echo of the
   tool's own change rather than a real user click, and the method
   returns early without tearing down edit mode or rebuilding the
   lists.

```python
@contextmanager
def _suppressed_selection_sync(self):
    self._suppress_selection_sync = True
    try:
        yield
    finally:
        self._maya_selection_set_by_us = set(cmds.ls(selection=True) or [])
        def _release():
            self._suppress_selection_sync = False
        cmds.evalDeferred(_release)
```

If you add a new `core`-calling slot that might change the Maya
selection as a side effect, wrap it the same way -- forgetting this is
the single most common way to introduce a bug where sculpting a layer
(which selects the managed meshes on purpose) spuriously kicks the UI
back to the Initialize page mid-operation.

`_force_selection_resync()` (in `main_window.py`) is the escape hatch
for the inverse problem: operations that change whether a mesh is
*managed* (create/delete node) without necessarily changing the raw
Maya selection at all, so the `SelectionChanged` scriptJob has nothing
to fire on. It manually resets the suppression state and re-invokes
`_on_selection_changed()` to force a recompute.

## Node creation & reuse (`scene/node.create_shot_sculpt_node`)

Selecting several meshes and clicking **Initialize Blendshape** doesn't
always create a new node: it first checks whether *any* of the selected
meshes already belongs to a node, and if so, adds the rest of the
selection to that existing node instead of creating a second one:

```python
for m in meshes:
    candidate = find_shot_sculpt_node_for_mesh(m)
    if candidate:
        node = candidate
        break
```

This is what makes "select an already-managed body plus a new,
unmanaged prop, then Initialize again" the supported way to grow a
group after the fact, rather than a special "add to group" button.
Meshes already connected to the node (`existing_meshes`) are skipped
when wiring up new `blendShape`s, so re-running this on an
already-fully-managed selection is a safe no-op.

## Node deletion (`scene/node._delete_node`)

Shared by both "delete for this selection" and "delete all" (the two
Tools-menu actions). Order matters:

1. Disconnect every `origMeshes[i]` connection.
2. Disconnect every `blendShapes[i]` connection, and -- only if
   `delete_blendshapes=True` -- delete the blendShape node itself
   *after* disconnecting it (disconnecting first avoids Maya trying to
   clean up the network node's plug as part of deleting the blendShape,
   which gets complicated with multi-attrs).
3. Delete the network node last.

Every disconnect/delete is individually wrapped in `try/except` with a
`cmds.warning` rather than letting one failure abort the whole cleanup
-- a partially-broken node is far more confusing to debug later than a
warning about one stale connection that didn't disconnect cleanly.

## Testing `core` without Maya

`tests/conftest.py`'s `FakeCmds` is intentionally minimal -- it grows
only as new tests need more of `cmds`, rather than modeling all of Maya
up front (see [`tests/README.md`](../tests/README.md) for what's
currently covered). The one subtlety worth knowing before you extend
it: `install_fake_maya()` keeps the *same* `maya`/`maya.cmds` module
*objects* across calls and only rebinds their attributes, rather than
creating fresh module objects each time:

```python
if _cmds_module is None:
    _maya_module = types.ModuleType("maya")
    _cmds_module = types.ModuleType("maya.cmds")
    ...
for attr_name in dir(fake_cmds):
    setattr(_cmds_module, attr_name, getattr(fake_cmds, attr_name))
```

`atlas_sculptor.core` modules do `import maya.cmds as cmds` once, at
their own import time, binding their local `cmds` name to a specific
module *object*. If `install_fake_maya()` swapped in a brand-new module
object on a later call (e.g. via the `fake_cmds` fixture, once per
test), already-imported `core` modules would keep talking to the first,
stale module -- since Python only imports a module once per process,
regardless of how many tests run. Keeping the module object's identity
stable and only swapping what it points to is what makes each test get
a fresh, isolated `FakeCmds` state without needing to re-import
`atlas_sculptor.core` between tests.

## Where to go next

- [Architecture](architecture.md) and the [`core`](core.md) /
  [`ui`](ui.md) module maps, if you haven't read those yet.
- [Contributing](../CONTRIBUTING.md) for branch/commit conventions and
  the `# region` / import-comment style used throughout the codebase.
- [User Guide](user_guide.md) to see the artist-facing side of the
  behaviour described here.
