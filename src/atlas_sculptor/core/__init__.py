# -*- coding: utf-8 -*-
"""
Core logic package for the Atlas Shot Sculptor tool.

All Maya operations live here, split across focused submodules with zero
UI dependencies, so they can be imported and unit-tested without a running
Qt application. Layout:

    core/
        scene/      Imperative Maya scene-graph operations: node discovery
                     & lifecycle (node.py), selection helpers (selection.py),
                     and frame-level create/list/delete (frames.py).
        models/      Data-shaped concerns: per-layer bookkeeping storage
                     (config.py), layer CRUD (layers.py), and per-layer
                     animation/curve settings (animation.py).
        states/      Transient tool state machines, e.g. sculpt edit-mode
                     entry/exit (edit_mode.py).
        legacy/      Superseded, unused monolithic implementation kept only
                     for reference during the ongoing refactor. Do not
                     import from here; see legacy/logic.py's module
                     docstring.

Typical usage:
    from atlas_sculptor.core.scene import node, selection, frames
    from atlas_sculptor.core.models import layers, animation, config
    from atlas_sculptor.core.states import edit_mode

Author: Clement Daures
Website: clementdaures.com
"""
