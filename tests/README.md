# Tests

`atlas_sculptor.core` has zero UI dependencies by design (see
[`docs/architecture.md`](../docs/architecture.md)), which is what makes
it possible to test here without a Maya install: `conftest.py` installs
a small in-memory `FakeCmds` as `maya.cmds` in `sys.modules` before any
test module (or the `atlas_sculptor.core` module it imports) runs.

```bash
pytest
```

## Layout

```
tests/
├── conftest.py       FakeCmds + the fake_cmds fixture
└── core/             one test module per core/ submodule under test
```

## What's covered, and what isn't

`core/scene/selection.py` and `core/models/config.py` are covered as a
starting example of the pattern. `core/scene/node.py`,
`core/models/layers.py`, `core/models/animation.py`, and
`core/states/edit_mode.py` are not yet covered — `FakeCmds` will need a
few more methods (`blendShape`, `connectAttr`/`disconnectAttr`,
`listConnections`) to exercise them. Extend `FakeCmds` incrementally,
matching real `cmds` kwarg names, rather than trying to model all of
Maya up front.

`ui/` is not covered here at all: it needs a real PySide6 + Qt event
loop, which is a heavier lift than mocking `cmds`. It's currently
exercised manually inside Maya. If you want to take this on, a `pytest-qt`
+ `xvfb` (headless display) setup in CI is the usual approach — open an
issue first so the approach can be agreed on before the CI work lands.
