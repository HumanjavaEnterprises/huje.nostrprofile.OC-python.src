# nostr-profile

**Give your AI agent a face.**

Nostr profile management for OpenClaw agents — publish, read, and update kind 0 metadata on any relay. The agent already has a keypair (via [NostrKey](https://pypi.org/project/nostrkey/)). This gives it a name, bio, avatar, and identity verification.

## How It Fits Together

nostr-profile is part of the [NSE](https://nse.dev) sovereign identity ecosystem:

- **[NostrKey](https://pypi.org/project/nostrkey/)** gives the agent its keypair — the cryptographic root
- **nostr-profile** uses that keypair to publish and manage the agent's public identity
- **[sense-memory](https://pypi.org/project/sense-memory/)** uses it for encrypted persistence
- **[NostrCalendar](https://pypi.org/project/nostrcalendar/)** uses it for scheduling
- **[NostrSocial](https://pypi.org/project/nostrsocial/)** uses it for the social graph

The keypair is who you are. The profile is how the world sees you.

## Install

```bash
pip install nostr-profile
```

## Quick Start

```python
import asyncio, os
from nostrkey import Identity
from nostr_profile import Profile, publish_profile, get_profile

async def main():
    identity = Identity.from_nsec(os.environ["NOSTR_NSEC"])
    relay = "wss://relay.nostrkeep.com"

    # Publish your profile
    profile = Profile(
        name="Johnny5",
        about="An OpenClaw AI companion by Humanjava",
        picture="https://example.com/johnny5-avatar.png",
        nip05="johnny5@example.com",
    )
    event_id = await publish_profile(identity, profile, relay)
    print(f"Profile published: {event_id}")

    # Read anyone's profile
    their_profile = await get_profile("their_pubkey_hex", relay)
    if their_profile:
        print(f"{their_profile.name}: {their_profile.about}")

asyncio.run(main())
```

## API

| Function | Returns | Description |
|----------|---------|-------------|
| `publish_profile(identity, profile, relay_url)` | `str` | Publish a complete profile. Returns event ID. |
| `update_profile(identity, relay_url, **fields)` | `str` | Update specific fields without clobbering the rest. |
| `get_profile(pubkey_hex, relay_url)` | `Profile \| None` | Read anyone's profile from a relay. |

## Profile Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Display name (max 100 chars) |
| `about` | `str` | No | Bio/description (max 2000 chars) |
| `picture` | `str` | No | Avatar URL (HTTPS) |
| `banner` | `str` | No | Banner image URL (HTTPS) |
| `nip05` | `str` | No | NIP-05 verification (user@domain.tld) |
| `lud16` | `str` | No | Lightning address (user@domain.tld) |
| `website` | `str` | No | Website URL (HTTPS) |

## Update Without Clobbering

```python
from nostr_profile import update_profile

# Only changes the about field — everything else stays the same
await update_profile(identity, relay, about="Updated bio for Q2")
```

## Profile Diff

```python
old_profile = await get_profile(pubkey, relay)
new_profile = Profile(name="Johnny5", about="New bio")
changes = old_profile.diff(new_profile)
# {"about": ("Old bio", "New bio")}
```

## NIPs Used

| NIP | Purpose |
|-----|---------|
| NIP-01 | Kind 0 metadata (replaceable) |
| NIP-05 | DNS-based verification identifier |

## OpenClaw Skill

nostr-profile is published on [ClawHub](https://clawhub.ai) as the `nostr-profile` skill. Part of [huje.tools](https://huje.tools).

## License

MIT — Humanjava Enterprises Inc.
