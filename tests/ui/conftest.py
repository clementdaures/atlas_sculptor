# -*- coding: utf-8 -*-
"""Shared setup for ``tests/ui``.

Forces Qt's ``offscreen`` platform plugin so the whole ``ui/`` suite runs
headlessly (no real display / Xvfb required) -- must happen before
``pytest-qt`` creates its session-wide ``QApplication``, hence doing it
here at collection time rather than inside a fixture.

Author: Clement Daures
Website: clementdaures.com
"""

# region Imports & Config

# python modules
from __future__ import annotations
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# endregion
