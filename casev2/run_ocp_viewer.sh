#!/bin/bash

# Run OCP CAD Viewer with visualization options enabled
uv run python -m ocp_vscode \
    --theme dark \
    --axes \
    --axes0 \
    --grid_xy \
    --grid_yz \
    --grid_xz \
    --center_grid
