# Horn-family promotion feedback

## 2026-07-23 — organization requested

- Promote both accepted rollback variants to `main`.
- Put shared source at the family root and angle-specific files in explicit
  variant folders.
- Add a concise README comparing the variants.
- Preserve unrelated uncommitted repository work.

## 2026-07-23 — promoted family checkpoint

- Shared source and parameter schema remain at the family root.
- Variant-owned build, parameter, validation, and review files now live under
  `variants/rollback_140/` and `variants/rollback_160/`.
- The catalog has a separate primary record for each rollback variant.
- Both reorganized builds passed and reproduced the accepted dimensions.
- The STEP audits found one solid, one shell, zero boundary edges, zero
  non-manifold edges, and no self-interference for both variants.
- Current STEP hashes:
  - 140°:
    `3892b70ebf13550881996c886a40a01b1dc89d3132df7162dc935a15d1513fff`
  - 160°:
    `1651e6bb18b7a2a2f9a06475e6611b8fd1d18086f648840fe7772011e7f05408`
- Fresh isometric renders were inspected. Both remain smooth, symmetric, and
  visually consistent with their accepted candidates.
