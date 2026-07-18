# Getting Started

## Requirements

- Autodesk Maya 2025 (Python 3.11, PySide6) to actually run the tool.
- Python 3.11+ on its own is enough to lint, format, and run the `core`
  unit tests, since `core` never imports Maya's `PySide6` build and
  `maya.cmds` is mocked in tests (see below).

## Loading the tool in Maya

Atlas Sculptor is a plain importable package under `src/`; it has no
`.mod` file or plug-in registration. Point Maya at it by adding `src/`
to `PYTHONPATH` (e.g. via `Maya.env` or `userSetup.py`), then:

```python
from atlas_sculptor.ui import launcher
launcher.show()
```

This `PYTHONPATH` route is the one to use for active development, since
it points Maya straight at the repo -- no re-copying after every change.
If you just want the tool running with the least setup (e.g. as an
artist, not actively editing the code), see
[Maya Setup](maya_setup.md) for the copy-into-`scripts`-folder
alternative instead; both end up doing the same import.

## Dev environment (linting / tests, no Maya required)

```bash
python -m venv .venv
source .venv/bin/activate      # .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

`pip install -e ".[dev]"` installs Atlas Sculptor in editable mode plus
the dev tools declared in `pyproject.toml` (`pytest`, `ruff`, `black`).
It does **not** install PySide6 or Maya — those aren't available outside
Maya's own interpreter, which is exactly why `core` is required to stay
Maya-`cmds`-only and UI-free (see [Architecture](architecture.md)).

## Running the tests

```bash
pytest
```

`tests/conftest.py` installs a lightweight fake `maya.cmds` module into
`sys.modules` before any `atlas_sculptor.core` module is imported, so
`core` can be tested without Maya installed. `ui/` is not covered by this
fake (it needs a real PySide6 + Qt event loop) and is presently exercised
manually inside Maya; see [`tests/README.md`](../tests/README.md) if
you'd like to help change that.

## Linting & formatting

```bash
ruff check .
black --check .
```

Both run in CI (`.github/workflows/ci.yml`) on every pull request.

## Where to go next

- [Maya Setup](maya_setup.md) for the copy-to-`scripts` alternative to
  the `PYTHONPATH` method above.
- [User Guide](user_guide.md) for the artist-facing workflow once the
  tool is loaded.
- [Architecture](architecture.md) for the `core`/`ui` split and the rule
  that keeps them decoupled.
- [`core/`](core.md) and [`ui/`](ui.md) for a module-by-module map, and
  the [Developer Guide](developer_guide.md) for a deeper dive into the
  trickier logic.
- [Contributing](../CONTRIBUTING.md) before opening a PR.
