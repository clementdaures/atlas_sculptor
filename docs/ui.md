# `ui/`

PySide6 front end. Talks to Maya only through `atlas_sculptor.core` — see
[Architecture](architecture.md#the-one-rule).

## `launcher.py`

The singleton entry point. `show()` closes any existing instance
(`_delete_existing`/`_get_existing_dialog`), then creates and parents a
fresh `AtlasShotSculptorUi` under Maya's main window. This is what a
shelf button or `userSetup.py` should call:

```python
from atlas_sculptor.ui import launcher
launcher.show()
```

## `views/` — top-level windows & dialogs

| Module | Owns |
|---|---|
| `main_window.py` | `AtlasShotSculptorUi(QMainWindow)` — builds the two-page stacked layout (State A: "Initialize Blendshape" vs. State B: frame displayer) and assembles the `controllers/` mixins below onto it. |
| `delete_dialog.py` | `DeleteNodeDialog` — confirmation dialog asking whether to also delete the underlying blendShape deformers when removing an Atlas Sculptor node. |

## `controllers/` — window behaviour

Mixed into `AtlasShotSculptorUi` in `views/main_window.py`. Split out of
the window class so each concern can be read (and eventually tested)
independently:

| Module | Owns |
|---|---|
| `selection_sync.py` | Listens for Maya selection-changed events and mirrors them into the UI (which of the two pages is shown, which mesh is "current"). |
| `frame_panel.py` | Builds and refreshes the frame list and layer list, and wires up add/delete/rename/reorder/toggle actions to `core.scene.frames` and `core.models.layers`. |
| `edit_controller.py` | Sculpt edit-mode entry/exit for the panel: toggling a layer's edit state via `core.states.edit_mode`, and pushing the Animation Settings widgets' values to the active layer via `core.models.animation`. |

## `widgets/` — reusable custom widgets

| Module | Owns |
|---|---|
| `layer_row.py` | `EditableLabel` (click-to-rename label) and `LayerRowWidget` (one row in the layer list: name, enabled checkbox, edit/move/delete buttons). |

## `resources/` — static resources

| Module | Owns |
|---|---|
| `stylesheet.py` | The tool's Qt stylesheet. |
| `constants.py` | Shared UI constants, e.g. the `PAGE_INITIALIZE` / `PAGE_FRAME_DISPLAYER` stacked-widget page indices. |

## Adding a new UI module

- A new top-level window or dialog → `views/`.
- Behaviour mixed into `AtlasShotSculptorUi` → `controllers/`.
- A reusable widget used in more than one place → `widgets/`.
- Anything static (styling, string/index constants) → `resources/`.
