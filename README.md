# ATLAS SCULPTOR - ANDHAKARA
Pipeline repository for the animated short film Andhakara

## Version
1.00 — 04/09/25

## Designed For
Autodesk Maya 2025 (Python 3.11, PySide6)

## Author
Clement Daures

- support@clementdaures.com (Pipeline TD / Dev / Rigging)

## Team
Léo Barachant (Animation 3D, Editing, Modeling)

Théo Berail (Storyboard, Scenario, Animation 3D)

Nino David (Modeling, Sculpting, Surfacing, Lighting)

Alicia Denux (Concept Art, Animation 3D)

Léa Genieys (Color Script, Lighting, Surfacing, Compositing)

Lilou Huet (Lighting, Modeling, Surfacing, Compositing)

Louna Perer (Grooming, CFX, Modeling, Surfacing)

Pablo Rodriguez (Scenario, Storyboard, FX, Layout)

Estelle Rupprecht (Concept Art, Cloth, CFX, Modeling)

Madelie Vaginay (Concept Art, Modeling, Surfacing, DMP)

## Logline
When her older sister accidentally dies in front of her, a stubborn teenager enters the world of the dead to bring back her soul.

## Repository Purpose
This repository serves as the specialized mesh correction and animation cleanup hub for the technical pipeline of Andhakara. Atlas Sculptor integrates alongside Atlas Manager to streamline post-animation and simulation workflows. It contains:

Non-destructive viewport sculpting tools for animated geometry caches (Alembic/FBX)

Time-aware falloff utilities for blending mesh fixes across custom frame ranges

Interface hooks and brush presets optimized for rapid shot finaling and cleanup

## Tech Highlights
Viewport Sculpt Layering: Apply corrective shapes and delta smoothing directly on top of heavy, baked cache nodes without breaking the upstream pipeline.

Timeline Integration: Sculpt fixes locally on a single frame or automatically interpolate deformations smoothly across shot timelines.

Artist-Centric PySide6 UI: A clean, dockable toolset designed for quick access to sculpt, smooth, and erase functions during shot finaling.

## License
This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

You are free to use, modify, and distribute this software under the terms of the GPL license.

See the full license text here: https://www.gnu.org/licenses/gpl-3.0.html

📌 Notes
Please ensure proper environment setup (Python 3.11, PySide6, Maya 2025) before running the tool initialization scripts within the Andhakara asset pipeline.
