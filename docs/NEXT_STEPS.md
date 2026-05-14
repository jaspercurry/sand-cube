# Next Steps

## Phase 0: Repo and Tooling

1. Create the GitHub repository and push `main`.
2. Install `uv`.
3. Sync Python dependencies.
4. Verify local imports for `build123d`, `bd_warehouse`, and `ocp_vscode`.
5. Decide whether build123d-mcp is part of the first working loop or a later
   enhancement.

## Phase 1: Dimension Lock

1. Download and archive the E150HE-44 and E180HE-PR datasheets.
2. Update `params.py` with verified driver and passive radiator dimensions.
3. Add a short BOM document with current live prices and links.

## Phase 2: CAD Skeleton

1. Implement a buildable dual-skin cube.
2. Add diagnostics for bounding box, volume, mass estimate, validity, and solid
   count.
3. Export STEP first, then verify 3MF export in the local build123d version.

## Phase 3: Risky Features First

1. Recessed baffle revolve.
2. Driver and PR cutouts.
3. Reinforcement rings and bonded insert collars.
4. Bracing posts and corner gussets.
5. Connector, strain relief, and fill port.

