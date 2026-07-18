# Contributing to Atlas Sculptor

Thanks for helping out. This is the pipeline tool for the *Andhakara*
short, so changes should stay safe for artists mid-shot; see below for
what that means in practice.

## Before you start

Read [`docs/architecture.md`](docs/architecture.md). The one rule that
matters most: **`core` never imports from `ui`**. If a change would
require `core` to import PySide6 or a `ui` module, it belongs in `ui`
instead, calling into `core` for the Maya-scene part.

## Branches & commits

- Branch from `main`: `feat/<short-name>`, `fix/<short-name>`,
  `docs/<short-name>`, `chore/<short-name>`.
- Commit messages: `type(scope): summary`, e.g.
  `fix(core.models): guard against a missing layerData attribute`.
  Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`.
- Keep commits focused — a rename/move and a behavior change belong in
  separate commits so the diff is reviewable.

## Where new code goes

- Maya scene-graph operations (`maya.cmds` calls) → `core/scene/`.
- Data shape & persistence (layer/animation settings) → `core/models/`.
- A tool-mode state machine → `core/states/`.
- A new window/dialog → `ui/views/`.
- Behaviour mixed into the main window → `ui/controllers/`.
- A reusable custom widget → `ui/widgets/`.
- Styling or shared constants → `ui/resources/`.

See [`docs/core.md`](docs/core.md) and [`docs/ui.md`](docs/ui.md) for
more detail on each subpackage, including a short checklist for picking
where a new module belongs.

Do not add to `core/legacy/` — it's a frozen, superseded prototype kept
only for reference.

## Code style conventions

Beyond `black`/`ruff`, every module in `atlas_sculptor` follows two
house conventions that aren't enforced by tooling, so please match them
by hand. Both exist for the same reason: this codebase is read a lot
more often than it's written, by artists-turned-TDs skimming for the one
function they need, so the file should read like a table of contents
even before anyone folds anything.

### `# region` / `# endregion` blocks

Every module's body is wrapped in named `# region <Name>` /
`# endregion` blocks. This gives editors with code-folding support
(VS Code, PyCharm, Sublime) a collapsible outline of the file, and gives
everyone else clear landmarks when scanning top-to-bottom.

- The first region is always `# region Imports & Config`, immediately
  after the module docstring, containing every import (see below) —
  and, if the module has any, its top-level constants (e.g.
  `core/models/config.py` gives `LAYER_DATA_ATTR` and
  `DEFAULT_LAYER_SETTINGS` their own nested `# region Constants` right
  after the imports region).
- A `# ==========` separator line follows each `# endregion`, visually
  breaking the file into its top-level sections.
- The rest of the module is split into one or more regions named after
  what they do — e.g. `core/models/layers.py` has separate `# region
  Layer Creation`, `# region Layer Toggle`, `# region Layer Reordering`,
  and `# region Layer Renaming` blocks rather than one giant region.
  Split a region when its current content stops being one cohesive idea
  a reader could summarize in the region's own name.
- Inside a class, regions nest one level deeper (indented to match the
  class body) to group methods — see `ui/views/main_window.py` for a
  class split into `# region Construction`, `# region Layout Builders`,
  `# region Shared Helpers`, and `# region Slots`.

Always write `# region <Name>` and `# endregion` with a space after
`#` — some older modules have a stray `#endregion` with no space; if
you touch one of those lines anyway, fix the spacing while you're
there, but it's not worth a drive-by commit on its own.

```python
# region Imports & Config

# python modules
from __future__ import annotations

# dcc import
import maya.cmds as cmds

# endregion

# ==========

# region <What This Section Does>

def some_function() -> None:
    ...

# endregion
```

### Import grouping comments

Within the `# region Imports & Config` block, imports are grouped into
short, lowercase-labeled clusters, in this order (omit any group a
module doesn't need):

1. `# python modules` — stdlib imports, always led by
   `from __future__ import annotations`.
2. `# pyside modules` — `PySide6` imports (`ui/` modules only).
3. `# dcc import` — `import maya.cmds as cmds`. Always this exact
   phrasing going forward (a few older modules say `# import dcc` —
   fix it if you're already editing that import block, otherwise leave
   it).
4. `# atlas_sculptor/<path>/...` — internal imports, one comment per
   distinct source path, most-specific path first. E.g.
   `core/models/animation.py` imports its sibling
   `core.models.layers` under `# atlas_sculptor/core/models/...`
   *before* the broader `# atlas_sculptor/core/...` comment that covers
   `core.models.config` and `core.scene.node`. When in doubt, order
   groups from the narrowest/most-local import path to the broadest.
5. `# atlas_sculptor/ui/...` — imports from `ui/` (only ever appears
   in other `ui/` modules — `core` never imports from `ui`, see
   [Architecture](docs/architecture.md#the-one-rule)).

```python
# python modules
from __future__ import annotations
import functools

# pyside modules
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

# dcc import
import maya.cmds as cmds

# atlas_sculptor/core/...
from atlas_sculptor.core.scene import frames
from atlas_sculptor.core.models import layers

# atlas_sculptor/ui/...
from atlas_sculptor.ui.widgets.layer_row import LayerRowWidget
```

Use plural `# python modules` even for a single `__future__` import
(a couple of older `core/models/` files say `# python module`
singular — harmless, but plural is the form to copy for new code).

## Before opening a PR

```bash
ruff check .
black .
pytest
```

- Add or update a test in `tests/` for any `core` change (see
  `tests/conftest.py` for the mocked `maya.cmds` fixture).
- Update `docs/` if you moved, renamed, or added a module — the docs are
  the map new contributors use, and a stale map is worse than none.
- Keep the PR description focused on *why*, not just *what* — the diff
  already shows what changed.

## Reporting bugs / requesting features

Use the issue templates under `.github/ISSUE_TEMPLATE/`. For anything
that could affect an in-progress shot (e.g. a change to how `layerData`
is stored), please flag that explicitly in the issue or PR so it can get
extra review.

## Code of conduct

Be respectful and assume good faith — this is a small student/indie
production team, not a large open-source project, and most contributors
are also credited crew on the film.

