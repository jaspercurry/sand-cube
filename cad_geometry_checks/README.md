# CAD geometry checks

`cad_geometry_checks` contains model-independent measurement implementations
that produce immutable results and can feed the existing `cad_verification`
contract. It does not define contracts, policies, evidence packets, model
dimensions, or a second schema.

The package root is native-free. Import `cad_geometry_checks.native` explicitly
inside a `cad_runner` worker to measure Build123d/OCP objects. The native
boundary is duck-typed and delays all kernel ownership to its caller, so
lightweight semantic tests can use fake objects without initializing CAD
libraries.

Every result records:

- the `cad_verification.Unit` for each value;
- named, unit-bearing tolerances;
- an operational diagnostic status;
- a machine-readable failure reason when the result is unusable; and
- a detailed diagnostic suitable for a review packet measurement.

Intersection results additionally preserve the exact Boolean outcome:
bounding-box disjoint, no returned shape, explicit empty shape, zero-volume
contact, positive-volume intersection, or invalid/unexpected topology.
Callers must inspect that outcome before consuming the volume. A missing or
empty member of a multi-solid Boolean fails the whole measurement closed;
partial positive results are never reported as complete.

Collection volume, difference, intersection, and protected-material results use
the geometric material union, so duplicate or overlapping solids are not
double-counted. Topology edge adjacency is occurrence-aware for periodic seams.
Protected-surface comparison samples tessellated topological interiors and trim
boundaries rather than the untrimmed UV rectangle. Edge signatures have
separate millimeter and dimensionless tangent tolerances. Normal change is an
unoriented tangent-plane measurement: opposite normals intentionally compare as
zero degrees.

Frozen normalization results own an immutable tuple, but the native shapes
inside it are borrowed mutable kernel objects. Callers must not mutate those
objects during a measurement.

The coordinated synthetic suite is
`tests/fixtures/cad_geometry_checks_native_fixtures.py`. Its direct entry point
self-routes through `cad_runner` before importing Build123d. It writes only an
ignored diagnostic report under `build/cad-geometry-checks/`.
