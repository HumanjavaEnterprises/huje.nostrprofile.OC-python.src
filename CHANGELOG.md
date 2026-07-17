# Changelog

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
