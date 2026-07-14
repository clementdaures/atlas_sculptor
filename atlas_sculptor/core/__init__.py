# -*- coding: utf-8 -*-
"""
Core logic package for the Atlas Shot Sculptor tool.

All Maya operations live here, split across focused submodules. This package
has zero UI dependencies and can be imported and unit-tested without a
running Qt application.

Re-exports the full public API so existing call sites can keep doing:
    from core.logic import create_shot_sculpt_node
    import core.logic as logic; logic.create_sculpt_frame()

Author: Clement Daures
Website: clementdaures.com
"""
