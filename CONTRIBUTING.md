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

