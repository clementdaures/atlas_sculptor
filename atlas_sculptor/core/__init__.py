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

from .selection import get_selected_meshes
from .node import (
    find_shot_sculpt_node,
    create_shot_sculpt_node,
    delete_shot_sculptor_node,
)
from .frames import (
    get_frame_entries,
    create_sculpt_frame,
    rename_frame,
    delete_sculpt_frame,
    get_frame_time,
)
from .edit_mode import enter_edit_mode, exit_edit_mode
from .animation import update_frame_animation

__all__ = [
    "get_selected_meshes",
    "find_shot_sculpt_node",
    "create_shot_sculpt_node",
    "delete_shot_sculptor_node",
    "get_frame_entries",
    "create_sculpt_frame",
    "rename_frame",
    "delete_sculpt_frame",
    "get_frame_time",
    "enter_edit_mode",
    "exit_edit_mode",
    "update_frame_animation",
]
