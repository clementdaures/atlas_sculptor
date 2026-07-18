# Using Atlas Sculptor

This is the artist-facing guide: what each button does and the order
you'd normally press them in, for fixing up a baked animation cache
without touching the upstream rig or cache. For install steps, see
[Maya Setup](maya_setup.md) or [Getting Started](getting_started.md).
For how it works under the hood, see the [Developer Guide](developer_guide.md).

## What Atlas Sculptor is for

You have a shot with a baked/cached mesh (Alembic, FBX, or otherwise
"frozen") that's *almost* right, but has a problem at one or a few
specific frames -- a collision poke-through, a bad silhouette, a jitter.
Re-simulating or re-animating upstream is overkill for a one-frame fix.
Atlas Sculptor lets you sculpt a corrective shape directly on the cached
mesh, at exactly the frame(s) that need it, and blends that correction
in and back out smoothly around the timeline -- without altering the
baked geometry itself or breaking the pipeline that produced it.

## Opening the tool

```python
from atlas_sculptor.ui import launcher
launcher.show()
```

(Or your shelf button, if you set one up -- see [Maya Setup](maya_setup.md#4-optional-add-a-shelf-button).)

The window docks under Maya's main window and has two pages that swap
automatically based on what you have selected in the viewport -- you
never choose between them yourself.

## 1. Select your mesh

Select the mesh (or meshes) you want to correct in the viewport. The
tool watches your selection continuously, so the window updates the
instant you click something new -- no refresh button needed.

- **Nothing selected, or a selected mesh has no Atlas Sculptor node
  yet** -> you see the **Initialize** page.
- **Selected mesh already has a node** -> you see the **frame list /
  layer list** page directly.

You can select several meshes at once (e.g. a body plus a piece of
cloth) if you want them corrected together as one group -- see step 2.

## 2. Initialize

On the Initialize page, click **Initialize Blendshape**. This:

- Creates one Atlas Sculptor node for the current selection (or adds
  the extra meshes to an existing node, if one of them is already
  managed -- so grouping a body + cloth later still works).
- Wires up a `blendShape` deformer per mesh, ready to receive corrective
  targets.

You only do this once per object (or group of objects). After this, the
window automatically switches to the frame/layer page whenever that
mesh is selected.

> If you select a mesh that was never initialized, you'll see the hint
> *"`<mesh>` has no Atlas Sculptor node yet."* -- that's this page
> telling you it's safe to initialize.

## 3. Create a sculpt frame

Move the Maya timeline to the frame that needs fixing, then click
**Create Sculpt Frame**. This:

- Records the current timeline frame as a new entry in the **frame
  list**.
- Creates that frame's **base layer** automatically (see below) and
  immediately arms it for sculpting -- you can start sculpting right
  away, no extra click.

Frames are listed as `Frame <number> (<N> layers)`, sorted by frame
number. Selecting a different frame in the list swaps the layer list
below it to that frame's layers.

**Delete Sculpt Frame** removes every layer belonging to the currently
selected frame -- use this if you started a fix on the wrong frame, or
no longer need it.

## 4. Layers -- base layer vs. corrective layers

Each frame has a **base layer** (tagged `BASE`, always pinned to the
bottom of the layer list) plus, optionally, one or more additional
corrective layers stacked on top of it.

- The **base layer** is created automatically with the frame -- it's
  your first pass at the fix.
- Click **+ Add Layer** to add another layer on top, if the base layer
  alone isn't enough (e.g. one pass for the big collision fix, another
  for a smaller silhouette touch-up). Extra layers stack additively.

Each layer row has:

| Control | Does |
|---|---|
| Checkbox | Mute/unmute this layer without deleting it. Muted layers keep all their sculpted data and animation keys -- flip it back on any time. |
| Name (double-click) | Rename the layer inline. |
| ▲ / ▼ | Reorder non-base layers within the stack (the base layer always stays at the bottom, so it never gets these buttons). |
| ⏻ (edit toggle) | Enter/finish sculpting this layer -- see step 5. |

## 5. Sculpting a layer

Click a layer's ⏻ button to enter **sculpt edit mode** for it:

- The timeline jumps to that layer's frame.
- The layer's weight is forced to `1.0` so you see (and can sculpt) its
  full effect.
- Maya's **Sculpt Mesh Tool** activates automatically on the managed
  mesh(es) -- you can start sculpting immediately.
- The **Animation Settings** panel becomes active (see step 6).

Sculpt as normal with Maya's tool. Click the same ⏻ button again (or
select a different layer's ⏻) to finish -- this hands the timeline and
tool back and locks in whatever you sculpted as that layer's target
shape.

Only one layer can be in edit mode at a time; entering edit mode on a
new layer automatically finishes the previous one first.

> **Selecting something else in the viewport while sculpting** also
> exits edit mode automatically for you.

## 6. Animation Settings -- blending the fix into the timeline

This panel controls how a layer's correction blends on and off the
timeline around its frame, and is only active while that layer is being
edited (step 5):

| Field | Meaning |
|---|---|
| Ease In | Frames the correction takes to ramp from 0 up to full strength. |
| Ease Out | Frames the correction takes to ramp back down to 0 after its hold. |
| Hold In | Frames held at full strength *before* the layer's frame. |
| Hold Out | Frames held at full strength *after* the layer's frame. |
| Key Type | `linear`, `spline` (smooth ease), or `stepped` (hard cut, no interpolation). |

Changing any of these updates the layer's blendShape weight curve
immediately -- there's no separate "Apply" button. The defaults (Ease
In/Out = 1, Hold In/Out = 0) give the tightest possible correction: one
frame to ramp up, one to ramp down, no hold either side.

Use a wider Ease/Hold window if the problem spans a few frames rather
than a single one; use `stepped` if you deliberately want a hard on/off
cut rather than a blend (e.g. matching a hard cut elsewhere in the
shot).

## 7. Cleaning up -- deleting nodes

Under the **Tools** menu:

- **Delete Custom Node for Selection** -- removes the Atlas Sculptor
  node (and all its frames/layers) for whichever mesh is currently
  selected.
- **Delete All Custom Nodes** -- removes every Atlas Sculptor node in
  the scene, for every object.

Both ask first whether you also want the underlying `blendShape`
deformers deleted:

- **Checked** -- the mesh loses the correction entirely, back to its
  original baked shape.
- **Unchecked** -- the `blendShape` nodes stay on the mesh, frozen at
  whatever shape they currently produce, but are no longer tracked by
  Atlas Sculptor (no more frame/layer list, no more Animation Settings
  for them). Use this if you like the sculpted result but want to stop
  managing it as layers -- e.g. right before a final cache export.

## Tips

- A frame can hold several layers; you don't need a new frame for a
  second corrective pass at the same moment in time -- add a layer to
  the existing frame instead.
- Muting a layer (its checkbox) is non-destructive and instant -- use it
  to A/B a fix against the original bake without deleting anything.
- The base layer can't be reordered or deleted independently while
  other layers exist in its frame; if you delete it anyway, Atlas
  Sculptor automatically promotes the next layer in that frame to base,
  so the frame always keeps a bottom layer.
- If two objects need to move/deform together for a correction (e.g. a
  character and an attached prop), select both before **Initialize
  Blendshape** so they share one node, one frame list, and stay in sync.
