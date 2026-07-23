# Front Baffle V1 source

The clean builder starts from one immutable, approved CAD input and applies one
final feature set:

1. `inputs/front_baffle_v1_approved_pre_fin.step` is the accepted baffle before
   print-support fins.
2. `generate_front_baffle_v1.py` creates the four conformal, bed-grown fins.
3. `front_baffle_v1_parameters.json` is the frozen math and print specification.

`inputs/front_baffle_v1_bed_oriented_mesh.3mf` is the exact watertight generic
mesh that was wrapped into the native Bambu project. It is retained as a source
input rather than promoted as a user deliverable because Bambu Studio correctly
identifies it as a non-native 3MF.

The files in `provenance/` are byte-for-byte snapshots of the original fin,
mesh, and native-project generators plus their Bambu packaging helper. Their
old experiment paths are intentionally left unchanged so the historical record
is honest. Use the isolated release builder for future verification.
