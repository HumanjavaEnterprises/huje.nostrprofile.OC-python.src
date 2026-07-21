# Changelog

## 0.2.2 — 2026-07-21

### Security

- **Transitive `cryptography` CVE fix.** `cryptography` reaches this package
  only via `nostrkey`, which previously capped `cryptography<45.0` and shipped
  the vulnerable 44.0.3 (four advisories: PYSEC-2026-35, PYSEC-2026-2141,
  GHSA-537c-gmf6-5ccf, and a related OpenSSL fix). The `nostrkey` floor is
  raised to `>=0.3.5`, whose lifted ceiling resolves `cryptography` 49.0.0.

### Changed

- `nostrkey` dependency floor raised from `>=0.3.0` to `>=0.3.5`. Verified
  against the local nostrkey 0.3.5 build: full suite and `pip-audit` green on
  `cryptography` 49.

## 0.2.1 — 2026-07-19

### Reconciliation

- Reconciled the local repo with PyPI, which was ahead at `0.2.0`. The
  published `0.2.0` (built from earlier March work) introduced `ProfileClient`
  but did **not** contain the July `get_profile` verify-before-use security
  fix. This release merges both: it adds `ProfileClient` **and** keeps the
  relay event verification.

### Added

- `ProfileClient` — stateful convenience wrapper holding an identity + relay
  URL, exposing `publish`, `update`, and `get`. Its `__repr__` is redacted
  (truncated pubkey + relay URL only) so identity secrets never leak in logs
  or tracebacks. `get()` delegates to the verified `get_profile`.

### Changed

- `nostrkey` dependency floor raised to `>=0.3.0` (required for
  `nostrkey.events.verify_event`, used by the July security fix).

## 0.1.10 — 2026-07-17

### Security

- `get_profile` now verifies every event a relay returns before trusting it:
  the event must be kind 0, authored by the requested pubkey, and carry a
  valid id and signature (`nostrkey.events.verify_event`). Events failing any
  check are skipped; if none survive, `get_profile` returns `None`.
  Previously the first event returned by the relay was parsed blindly, so a
  malicious or buggy relay could substitute an arbitrary event as the
  "profile" — and because `update_profile` merges the fetched profile and
  re-signs it under the caller's key, forged relay data (e.g. a scam `lud16`
  or `nip05`) could be re-published under the agent's own identity.
- Among valid events, the newest `created_at` wins (kind 0 is replaceable).
- `update_profile` is protected automatically since it consumes
  `get_profile`'s verified output. No API signature or return-type changes.
