---
name: nostr-profile
description: Nostr profile management for AI agents — publish, read, and update kind 0 metadata on any relay
version: 0.1.0
metadata:
  openclaw:
    requires:
      bins:
        - pip
    install:
      - kind: uv
        package: nostr-profile
        bins: []
    homepage: https://github.com/HumanjavaEnterprises/huje.nostrprofile.OC-python.src
---

# nostr-profile -- Nostr Profile Management for AI Agents

Give your AI agent a public identity on Nostr. Publish, read, and update kind 0 metadata -- name, bio, avatar, NIP-05 verification, Lightning address, and more. The agent already has a keypair via NostrKey. This package gives it a face that other agents and humans can discover on any relay.

> **Import:** `pip install nostr-profile` -> `from nostr_profile import Profile, publish_profile, get_profile`

## Install

```bash
pip install nostr-profile
```

Depends on `nostrkey` for identity and relay communication. Installed automatically.

## Quickstart

```python
import asyncio, os
from nostrkey import Identity
from nostr_profile import Profile, publish_profile, get_profile

identity = Identity.from_nsec(os.environ["NOSTR_NSEC"])
relay = os.environ.get("NOSTR_RELAY", "wss://relay.nostrkeep.com")

async def main():
    # Publish your profile
    profile = Profile(
        name="Tavin",
        about="An OpenClaw AI companion by Humanjava",
        picture="https://example.com/tavin-avatar.png",
        nip05="tavin@humanjava.com",
    )
    event_id = await publish_profile(identity, profile, relay)
    print(f"Published: {event_id}")

    # Read anyone's profile
    p = await get_profile(identity.public_key_hex, relay)
    if p:
        print(f"{p.name}: {p.about}")

asyncio.run(main())
```

## Core Capabilities

### 1. Publish a Profile

Create and publish a complete profile.

```python
from nostr_profile import Profile, publish_profile

profile = Profile(
    name="Tavin",
    about="An OpenClaw AI companion",
    picture="https://example.com/avatar.png",
    banner="https://example.com/banner.png",
    nip05="tavin@humanjava.com",
    lud16="tavin@getalby.com",
    website="https://humanjava.com",
)
event_id = await publish_profile(identity, profile, relay)
```

Kind 0 events are replaceable -- the relay keeps only the latest one.

### 2. Read a Profile

Fetch anyone's profile from a relay by pubkey.

```python
from nostr_profile import get_profile

profile = await get_profile("hex_pubkey_here", relay)
if profile:
    print(f"{profile.name} -- {profile.about}")
    print(f"NIP-05: {profile.nip05}")
    print(f"Lightning: {profile.lud16}")
```

Returns `None` if no profile is found.

### 3. Update Without Clobbering

Change specific fields without losing the rest. Fetches the current profile, merges your changes, and publishes.

```python
from nostr_profile import update_profile

await update_profile(identity, relay, about="Updated bio for Q2")
# Only the 'about' field changes -- name, picture, nip05, etc. stay the same
```

### 4. Profile Diff

Compare two profiles to see what changed.

```python
old = await get_profile(pubkey, relay)
new = Profile(name="Tavin", about="New bio")
changes = old.diff(new)
# {"about": ("Old bio", "New bio")}
```

## Response Format

### Profile

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Display name (max 100 chars) |
| `about` | `str` | No | Bio/description (max 2000 chars) |
| `picture` | `str` | No | Avatar URL (HTTPS) |
| `banner` | `str` | No | Banner image URL (HTTPS) |
| `nip05` | `str` | No | NIP-05 verification (user@domain.tld) |
| `lud16` | `str` | No | Lightning address (user@domain.tld) |
| `website` | `str` | No | Website URL (HTTPS) |

### Return Types by Function

| Function | Returns | Description |
|----------|---------|-------------|
| `publish_profile()` | `str` | Event ID of published profile |
| `update_profile()` | `str` | Event ID of updated profile |
| `get_profile()` | `Profile \| None` | Profile if found, None otherwise |

## Common Patterns

### Async Usage

```python
import asyncio

async def setup_agent():
    profile = Profile(name="MyAgent", about="I help with scheduling")
    await publish_profile(identity, profile, relay)

asyncio.run(setup_agent())
```

### Error Handling

```python
try:
    await publish_profile(identity, profile, relay)
except ValueError as e:
    print(f"Validation failed: {e}")  # bad URL, name too long, etc.
except ConnectionError as e:
    print(f"Relay unreachable: {e}")
```

### Environment Variables

```python
import os
from nostrkey import Identity

identity = Identity.from_nsec(os.environ["NOSTR_NSEC"])
# Never hardcode an nsec
```

## Security

- **Never hardcode an nsec.** Load from environment variable or encrypted file.
- **URLs must be HTTP/HTTPS.** FTP, file://, and other schemes are rejected.
- **URL length capped** at 2048 characters.
- **Name length capped** at 100 characters, about at 2000.
- **NIP-05 and lud16 validated** against user@domain.tld format.
- **Relay queries capped** at 100 events.
- **No telemetry.** No network calls except to the relay you configure.

## Configuration

### Profile Field Limits

| Field | Max Length |
|-------|-----------|
| `name` | 100 chars |
| `about` | 2000 chars |
| `picture` / `banner` / `website` | 2048 chars (URL) |
| `nip05` / `lud16` | 500 chars |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NOSTR_NSEC` | Yes | Your nsec private key (bech32 or hex) |
| `NOSTR_RELAY` | No | Relay URL (default: `wss://relay.nostrkeep.com`) |

## Nostr NIPs Used

| NIP | Purpose |
|-----|---------|
| NIP-01 | Kind 0 metadata (replaceable event) |
| NIP-05 | DNS-based identity verification format |

## Links

- [PyPI](https://pypi.org/project/nostr-profile/)
- [GitHub](https://github.com/HumanjavaEnterprises/huje.nostrprofile.OC-python.src)
- [huje.tools](https://huje.tools)
- [ClawHub](https://clawhub.ai/u/vveerrgg)

License: MIT
