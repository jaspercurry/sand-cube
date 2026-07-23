# Canonical working-set scope

This directory is a curated navigation and handoff layer. Read `README.md`,
`lineage.md`, and the selected component's `README.md` and
`source_manifest.md` before changing anything.

1. Files under `links/` are symbolic links to existing owners and hash-bound
   evidence. Do not edit linked `build/` files. Do not replace a link with a
   copied source or STEP file.
2. Existing experiment directories retain their current dependency chain and
   working-tree state. Refactor by creating an explicit new owner, then promote
   only after coordinated validation; do not relocate or flatten ancestors.
3. Keep the removable-front and integral-front enclosure variants independent.
   The flat-bottom baffle belongs only to the removable-front direction; the
   full-perimeter bottom corner belongs to the integral-front direction.
4. Tube and resonator geometry remain deferred until the selected enclosure is
   final and its source, artifacts, hashes, net volume, keepouts, and service
   path are recorded.
5. Rev C resonator geometry is a placement reference. Rev D is the latest
   acoustic/calibration reference and is not production-validated.
6. The current horn is a formula/construction reference. Build a separately
   parameterized smaller horn instead of silently resizing the stable horn.
7. After changing any linked reference or source named in
   `reference_checksums.sha256`, update its component manifest deliberately and
   rerun the checksum file. Follow the repository-level CAD skill and catalog
   rules for all geometry, lifecycle, and artifact work.
