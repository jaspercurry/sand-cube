# Joint-coupon pre-integration baseline

This directory preserves the joint-coupon source, parameters, and measured
geometry that were present in the working-tree snapshot supplied to the
integration session before the verification adapter was added. It is an
immutable comparison fixture, not an executable model owner.

`measurements.json` is compared with every staged coupon run. The comparison
is geometric and tolerance-based; it intentionally does not claim byte-identical
STEP output because STEP headers and entity ordering may vary across exports.
Viewer URLs are transient local navigation aids and are not portable evidence.
