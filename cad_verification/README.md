# CAD verification core

`cad_verification` is a standard-library-only contract and review-packet core.
It deliberately does not import Build123d, OCP, `cad_runner`, Viewer code, or a
repository model.  Production integrations provide measurements and artifact
observations through the protocols in `protocols.py`.

The Python dataclasses in `model.py` are the authoritative contract and report
representation.  JSON is a deterministic serialization of those classes, not
a second hand-maintained schema.  `policy.py` is the sole vocabulary and policy
catalog for profiles, checks, units, statuses, artifact roles, and evidence
routing. Consumers should inspect `PROFILE_POLICIES`, `CHECK_POLICIES`,
`ARTIFACT_POLICIES`, and `EVIDENCE_POLICIES` instead of copying their meanings.
Evidence references include the exact artifact role and SHA-256 rather than a
mutable path or ID alone. Derived sidecars and render images also reference the
exact STEP hash they came from.

The main flow is:

1. construct or deserialize a `DesignContract` and call
   `assert_valid_contract`;
2. select work with `requirements_for_profile`;
3. let an external adapter measure each requirement and pass its actual value
   to `assess` (or explicitly return `unverified`);
4. construct a `ReviewPacket` and call `assert_valid_review_packet`;
5. persist it with `review_packet_to_json` and use `review_packet_status` for
   the validation- and job-aware profile outcome.

`review_packet_status` is the terminal PASS/FAIL/UNVERIFIED API. Low-level
result aggregation does not certify a review packet or release job.

`examples.py` provides a complete synthetic contract and release review packet
without touching native CAD.
