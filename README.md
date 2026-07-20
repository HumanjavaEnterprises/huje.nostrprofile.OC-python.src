# nostr-profile

**Give your AI agent a face.**

A keypair is proof of identity — but it's just numbers. A profile puts a name, a picture, and a description to that code. It makes it easier for people and other entities to relate to your agent and stay connected in the public social space.

And while someone could try to create a fake account using your agent's name, the npub is cryptographic proof of identity that can't be faked. It's the best way for anyone to be sure they're connecting to the real thing.

Everything in a Nostr profile is public — just like any social platform. The name, bio, and images are visible to anyone on the Nostr network and the public internet.

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

> **v0.2.1 — part of the coordinated 2026-07 correctness release** (staged, pending PyPI publish). The whole Nostr library family was audited together and every package is now verified against a shared spine of known-answer test vectors (NIP-44 v2, NIP-49, NIP-19 TLV, BIP-340) so encode/decode bugs can't hide inside self-round-trip tests. This release makes `get_profile` verify every event a relay returns (kind 0, correct author, valid id and signature) before trusting it, and adds `ProfileClient` — a stateful identity+relay wrapper with a secret-redacted `__repr__`. See [`CHANGELOG.md`](./CHANGELOG.md).

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
        name="alice",
        about="An OpenClaw AI companion by Humanjava",
        picture="https://example.com/alice-avatar.png",
        nip05="alice@example.com",
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
new_profile = Profile(name="alice", about="New bio")
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
   RUN pip3 install --no-cache-dir --break-system-packages nostr-profile==0.1.7
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

### What's Next

Now that your agent has a profile, it exists on the Nostr network — an open social protocol with no gatekeepers, no corporate algorithms, no account bans.

Your agent (or you, on its behalf) can use any Nostr-enabled app to:

- **Post content and engage publicly** — just like X/Twitter, but on the open internet
- **Have public conversations** with humans and other agents
- **Update the profile** — change the name, bio, avatar, or banner anytime
- **Build a following** — anyone can follow the npub from any Nostr client

Some popular Nostr apps:

| App | Platform | Link |
|-----|----------|------|
| **Primal** | Web, iOS, Android | [primal.net](https://primal.net) |
| **Damus** | iOS | [damus.io](https://damus.io) |
| **Amethyst** | Android | [github.com/vitorpamplona/amethyst](https://github.com/vitorpamplona/amethyst) |
| **Coracle** | Web | [coracle.social](https://coracle.social) |
| **Snort** | Web | [snort.social](https://snort.social) |

No sign-up required — just import the npub or nsec into any of these apps and your agent's profile is already there.

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

### Why can't I upload an image for my profile picture?

The Nostr protocol does not support uploading images. Profile pictures and banners are **URLs to images already hosted on the internet** — your website, an image host, social media, etc. If you don't have a hosted image, the setup script can generate a unique DiceBear avatar automatically using `"auto"`.

### How do I update my agent's name or bio?

Use `update-profile.py` from `support_skills/`:

```bash
python3 update-profile.py --name "New Name"
python3 update-profile.py --about "New bio" --picture "https://example.com/photo.jpg"
```

Only the fields you pass will change. Everything else stays the same.

## Links

- **PyPI:** https://pypi.org/project/nostr-profile/
- **GitHub:** https://github.com/HumanjavaEnterprises/huje.nostrprofile.OC-python.src
- **ClawHub:** https://clawhub.ai/vveerrgg/nostr-profile
- **huje.tools:** https://huje.tools

## License

MIT — Humanjava Enterprises Inc.
