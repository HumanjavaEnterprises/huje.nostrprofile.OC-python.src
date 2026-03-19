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
import asyncio
from nostrkey import Identity
from nostr_profile import Profile, publish_profile, get_profile

async def main():
    # Load identity from encrypted file (passphrase from env var)
    import os
    identity = Identity.load("my-identity.nostrkey", passphrase=os.environ["NOSTRKEY_PASSPHRASE"])
    relay = "wss://relay.damus.io"

    # Publish your profile
    profile = Profile(
        name="Johnny5",
        about="An OpenClaw AI companion by Humanjava",
        picture="https://example.com/johnny5-avatar.png",
        nip05="johnny5@example.com",
    )
    event_id = await publish_profile(identity, profile, relay)
    print(f"Profile published: {event_id}")
    print(f"View online: https://njump.me/{identity.npub}")

    # Read anyone's profile
    their_profile = await get_profile(identity.public_key_hex, relay)
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

## OpenClaw Deployment

### Quick Start (ClawHub)

```bash
clawhub install nostr-profile
```

### Manual Setup

The `support_skills/` folder contains ready-to-deploy workspace files. See [`support_skills/README.md`](support_skills/README.md) for the full walkthrough.

**Short version:**

1. Add `nostr-profile` to your Dockerfile:
   ```dockerfile
   RUN pip3 install --no-cache-dir --break-system-packages nostr-profile==0.1.2
   ```
2. Set `NOSTRKEY_PASSPHRASE` in your `.env` file so the agent can sign autonomously
3. Copy `support_skills/setup-profile.py` and `support_skills/show-profile.py` into your OC workspace
4. Paste the snippet from `support_skills/TOOLS-snippet.md` into your agent's `TOOLS.md`

### After Setup

Once your agent's profile is published, here are useful things to ask it:

| What to ask | What it does |
|-------------|--------------|
| "What is your Nostr profile?" | Shows name, bio, avatar from local cache |
| "Update your bio to ..." | Publishes updated profile to relay |
| "Look up npub1..." | Fetches someone else's profile from a relay |

The agent will also offer to show you the profile online via:
- **njump.me** — `https://njump.me/[npub]`
- **npub.bio** — `https://npub.bio/[npub]`

## FAQ

### Why does the setup script hang?

The script needs to connect to a Nostr relay via WebSocket. If the relay is unreachable (e.g., behind a VPN that blocks certain hosts), the script will hang.

**Fix:** Try a different relay. `wss://relay.damus.io` is widely reachable. Pass it as the 4th argument to `setup-profile.py`.

### Why doesn't the agent ask for a passphrase?

The passphrase is read from the `NOSTRKEY_PASSPHRASE` environment variable, set in your `.env` or `docker-compose.yml`. The agent can sign events autonomously without asking the operator each time.

**Fix:** If the env var isn't set, the script will error. Add `NOSTRKEY_PASSPHRASE=yourpassphrase` to your `.env` file and restart the container.

### Can I see my agent's profile online?

Yes. After publishing, visit:
- `https://njump.me/[your-agent-npub]`
- `https://npub.bio/[your-agent-npub]`

These are public Nostr profile viewers — anyone can see the profile.

## Links

- **PyPI:** https://pypi.org/project/nostr-profile/
- **GitHub:** https://github.com/HumanjavaEnterprises/huje.nostrprofile.OC-python.src
- **ClawHub:** https://clawhub.ai/vveerrgg/nostr-profile
- **huje.tools:** https://huje.tools

## License

MIT — Humanjava Enterprises Inc.
