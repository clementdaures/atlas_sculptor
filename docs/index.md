# Atlas Sculptor Docs

Atlas Sculptor is the mesh-correction and animation-cleanup tool for the
*Andhakara* pipeline: a Maya (PySide6) tool for sculpting non-destructive
corrective shapes on top of baked animation caches, and blending those
fixes smoothly across a shot's timeline.

This folder documents the codebase for contributors. For the project
pitch, the film, and the team, see the [root README](../README.md).

## Start here

- **[Getting Started](getting_started.md)** — environment setup, loading
  the tool in Maya, and running the test suite.
- **[Maya Setup](maya_setup.md)** — the quickest way in: copy the
  package into Maya's `scripts` folder and launch it, no `PYTHONPATH`
  editing required.
- **[User Guide](user_guide.md)** — for artists: initializing a mesh,
  creating sculpt frames, layers, and blending a fix into the timeline.
- **[Architecture](architecture.md)** — how `core` and `ui` are split,
  and the rule that keeps them decoupled.
- **[Core package](core.md)** — `scene`, `models`, `states`: what each
  subpackage owns and the data flow between them.
- **[UI package](ui.md)** — `views`, `controllers`, `widgets`,
  `resources`: how the Qt front end is assembled.
- **[Developer Guide](developer_guide.md)** — a deeper dive into the
  trickier logic: index allocation, layer ordering/base-layer pinning,
  the animation-curve math, and the selection-sync suppression trick.
- **[Contributing](../CONTRIBUTING.md)** — branch naming, commit style,
  and what a PR needs before review, including the `# region` and
  import-comment conventions used throughout the codebase.

## Project layout

```
atlas_sculptor/
├── docs/                    you are here
├── src/atlas_sculptor/
│   ├── core/                Maya-facing logic, zero UI dependencies
│   │   ├── scene/           node / selection / frame operations
│   │   ├── models/          layer & animation data + storage
│   │   ├── states/          sculpt edit-mode state machine
│   │   └── legacy/          superseded prototype, reference only
│   └── ui/                  PySide6 front end, zero direct Maya calls
│       ├── views/           top-level windows & dialogs
│       ├── controllers/     mixins implementing window behaviour
│       ├── widgets/         reusable custom Qt widgets
│       └── resources/       stylesheet + constants
├── tests/                   unit tests (maya.cmds is mocked, see conftest.py)
└── pyproject.toml           packaging + lint/format tool config
```

