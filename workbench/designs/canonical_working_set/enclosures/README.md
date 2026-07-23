# Enclosure family

The two future enclosures share the nominal 190 × 210 × 190 mm sculpted
package, driver treatment, fill passages, bulkhead intent, and parabolic-G1
exterior lineage. They do **not** share the same service split.

## Removable front baffle

- Main bucket prints rear/GX face down.
- Baffle prints vertically on a flat full-width bottom edge.
- Sculpted seating seam remains on left, right, and top.
- Bottom material ownership transfers to the baffle.
- Front remains serviceable.

## Integral front with bottom hatch

- Enclosure prints bottom down.
- Front is one permanent, seam-free solid.
- Full-perimeter exterior, including the original sculpted bottom corners, is
  preserved.
- The flat-bottom removable baffle is not used.
- Service moves to a separately printed bottom hatch after the monolithic
  front is proven.

Do not make one source serve both variants through ad hoc flags during the
first refactor. Establish independent owners with shared, explicit feature
modules only after the common geometry has been identified and tested.
