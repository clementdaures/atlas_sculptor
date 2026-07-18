# Setup in Maya (copy-to-`scripts` method)

This is the quickest way to get Atlas Sculptor running inside Maya: copy
the package folder straight into Maya's user `scripts` directory. No
`Maya.env` edit, no `.mod` file, no plug-in registration.

If you'd rather point Maya at the repo in place (e.g. for active
development, so you don't need to re-copy on every change), see
[Getting Started -> Loading the tool in Maya](getting_started.md#loading-the-tool-in-maya)
for the `PYTHONPATH` alternative instead. Both methods end up doing the
same thing: making `atlas_sculptor` importable from Maya's `Script Editor`.

## 1. Locate your Maya `scripts` folder

| OS | Path |
|---|---|
| Windows | `C:\Users\<you>\Documents\maya\2025\scripts` |
| macOS | `~/Library/Preferences/Autodesk/maya/2025/scripts` |
| Linux | `~/maya/2025/scripts` |

Maya adds this folder to its Python path automatically on launch, for
every version-specific folder (`2025` above) -- that's the whole trick
this method relies on. If the folder doesn't exist yet, create it.

## 2. Copy the package in

Copy the **`atlas_sculptor` folder that lives under `src/`** in this
repo -- not the repo root, not `src/` itself -- into that `scripts`
folder:

```
atlas_sculptor/            <- this repo
└── src/
    └── atlas_sculptor/    <- copy THIS folder
        ├── __init__.py
        ├── core/
        └── ui/
```

So that afterward, the `scripts` folder looks like:

```
<maya scripts folder>/
└── atlas_sculptor/
    ├── __init__.py
    ├── core/
    └── ui/
```

`import atlas_sculptor` now resolves to this copy, independent of where
the repo itself lives on disk.

## 3. Launch it

Open Maya's Script Editor (a Python tab) and run:

```python
from atlas_sculptor.ui import launcher
launcher.show()
```

This should raise the Atlas Sculptor window docked under Maya's main
window. Calling `launcher.show()` again reuses the same window instance
instead of stacking duplicates (see [`ui/launcher.py`](../src/atlas_sculptor/ui/launcher.py)).

## 4. (Optional) Add a shelf button

Right-click any shelf tab -> *New Shelf Button*, paste the same snippet
as the Python command, and give it an icon/label. Now the tool is a
one-click launch.

## 5. (Optional) Auto-load on Maya startup

Drop the same two lines into a `userSetup.py` in the same `scripts`
folder (create the file if it doesn't exist):

```python
# userSetup.py
from atlas_sculptor.ui import launcher
```

This only *imports* the package on startup -- it does not pop the window
open automatically. Add a call to `launcher.show()` in there too if you
want the tool to open every time Maya starts (most teams prefer a shelf
button instead, so the window doesn't appear unasked-for on every launch).

## Updating

Since this method works off a copy, updating means re-copying the
`atlas_sculptor` folder over the old one whenever the repo changes
(delete the old copy first, so removed files don't linger). If you find
yourself doing this often, switch to the `PYTHONPATH` method in
[Getting Started](getting_started.md) instead -- it points Maya straight
at the repo, so `git pull` alone is enough.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'atlas_sculptor'`** -- double
  check you copied the *inner* `atlas_sculptor` folder (the one
  containing `__init__.py`), not `src/` itself, and that it landed in
  the Maya-version-specific `scripts` folder above, not a generic one.
- **Old behaviour after updating the copy** -- Maya caches imported
  modules for the session; restart Maya (or `import importlib;
  importlib.reload(...)` each affected submodule) after replacing the
  files.
- **`PySide6` import errors** -- Atlas Sculptor targets Maya 2025, which
  ships PySide6 already; earlier Maya versions bundle PySide2 and are not
  supported (see the [README](../README.md#designed-for)).

## Where to go next

- [Using Atlas Sculptor](user_guide.md) -- the artist-facing workflow,
  once the tool is loaded.
- [Getting Started](getting_started.md) -- the developer environment
  (linting, tests) and the `PYTHONPATH` alternative to this method.
