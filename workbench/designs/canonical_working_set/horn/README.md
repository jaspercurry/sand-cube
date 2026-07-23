# Smaller-enclosure horn placeholder

## Intent

The final horn should be recalculated for the smaller enclosure package. The
current stable B&C DE250 horn has an approximately `222.463 mm` outer-mouth
target, so it is not assumed to be the correct external match for the nominal
190 mm enclosure.

No new horn geometry is required during this organization pass. Preserve the
current implementation as the formula and construction reference, then create
a new independently parameterized horn variant after the enclosure package and
mounting interface are accepted.

## Formula source found

No `.xls`, `.xlsx`, or `.ods` horn spreadsheet is stored in this repository.
However, `src/features/horn.py` contains:

- the existing legacy Le Cleac'h/JMLC recurrence; and
- an explicit reproduction of the 2007 `pavillon_JMLC.xls` recurrence,
  including its 4000-row step rule and endpoint-angle solver.

That code is the repository-local calculation baseline. If the original
spreadsheet is supplied later, preserve it as a sourced input and compare its
profile numerically before changing the implementation.

## Local links

| Link | Meaning |
|---|---|
| `links/current_api.py` | Stable current horn API and placement helper |
| `links/profile_geometry.py` | JMLC/Le Cleac'h equations and Build123d geometry |
| `links/shared_parameters.py` | Current horn values inside the legacy shared parameter module |
| `links/jmlc_studies` | Square-baffle/profile study directory |
| `links/horn_work_summary.md` | Existing printing and viewer work summary |

See [source_manifest.md](source_manifest.md) for exact hashes and the future
parameter boundary.
