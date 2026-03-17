# nostr-profile

Nostr profile management for OpenClaw AI agents. Part of the huje.tools ecosystem.

## Build & Test

```bash
pip install -e ".[dev]"
pytest -v
```

## Structure

- `src/nostr_profile/` — package source
  - `types.py` — Profile dataclass, field validation, metadata serialization, diff
  - `publish.py` — publish_profile, update_profile (kind 0 replaceable events)
  - `read.py` — get_profile (fetch kind 0 from relay)
- `tests/` — pytest suite
- `clawhub/` — OpenClaw skill metadata
- `examples/` — runnable examples

## Conventions

- Python 3.10+, hatchling build, ruff linter (100 char line length)
- Dependency: `nostrkey>=0.1.1` only
- Import matches package name: `pip install nostr-profile` → `from nostr_profile import Profile`
- Kind 0 metadata is a replaceable event — publishing overwrites the previous profile
- `update_profile` fetches current, merges changes, republishes (no field clobbering)
- `from_metadata` tolerates both `name` and `display_name` keys (client compatibility)
- URLs validated as HTTP/HTTPS, capped at 2048 chars
- NIP-05 and lud16 validated as user@domain.tld format
- Name max 100 chars, about max 2000 chars
- Relay queries capped at 100 events
- `to_metadata` only includes non-empty fields
- Version must be bumped in 3 places: pyproject.toml, __init__.py, clawhub/metadata.json
