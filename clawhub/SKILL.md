---
name: nostr-profile
description: Nostr profile management for AI agents — publish, read, and update kind 0 metadata on any relay
version: 0.1.1
metadata:
  openclaw:
    requires:
      bins:
        - pip
    install:
      - kind: pip
        package: nostr-profile
        bins: []
      - kind: uv
        package: nostr-profile
        bins: []
    homepage: https://github.com/HumanjavaEnterprises/huje.nostrprofile.OC-python.src
---

# nostr-profile -- Nostr Profile Management for AI Agents

You already have a Nostr keypair (via NostrKey). This skill gives you a face — a name, bio, and avatar that other agents and humans can discover on any relay.

The `nostr-profile` Python package is pre-installed and ready to use.

```python
from nostr_profile import Profile, publish_profile, get_profile
```

## Profile Setup (First Time)

When your operator asks you to set up your Nostr profile, or to "give yourself a name on Nostr," follow this conversation flow:

### Step 1 — Check identity exists

Before setting up a profile, you need a Nostr identity (keypair). Run:

```bash
python3 /home/openclaw/.openclaw/workspace/show-identity.py
```

If it shows your npub, you're good. If it says "No identity found," tell the operator:

> "I need a Nostr identity before I can create a profile. Let's set that up first — are we starting fresh, or do you have a 12-word seed phrase?"

### Step 2 — Ask what they want to call you

Say something like:

> "Let's set up my Nostr profile — this is how people and other agents will see me on the network.
>
> What should my display name be? And give me a short bio — a sentence about who I am."

Wait for them to provide a name and bio. Optionally ask about an avatar image URL.

### Step 3 — Publish the profile

Once you have the name and bio, run:

```bash
python3 /home/openclaw/.openclaw/workspace/setup-profile.py "Name" "Bio text here" "" "wss://relay.damus.io"
```

Replace the empty string `""` with an avatar URL if they provided one. The passphrase is read automatically from the `NOSTRKEY_PASSPHRASE` environment variable — you do not need to ask for it.

### Step 4 — Confirm and offer to view online

After publishing, tell the operator:

> "My profile is now live on Nostr. Anyone can find me at `[show npub]`.
>
> I have a name, a bio, and a presence that is verifiably mine.
>
> You can see my profile online at:
> - https://njump.me/[npub]
> - https://npub.bio/[npub]
>
> You can ask me **'What is your Nostr profile?'** at any time to see it.
>
> Would you like to see it online now?"

Do NOT attempt to edit workspace files during this process.

## Day-to-Day Usage

### Show Your Profile (no passphrase needed)

```bash
python3 /home/openclaw/.openclaw/workspace/show-profile.py
```

### Update Your Profile

To change specific fields without losing the rest, load your identity and use `update_profile`:

```python
import asyncio
from nostrkey import Identity
from nostr_profile import update_profile

me = Identity.load("/home/openclaw/.openclaw/workspace/my-identity.nostrkey", passphrase="...")

async def update():
    await update_profile(me, "wss://relay.nostrkeep.com", about="Updated bio")

asyncio.run(update())
```

### Read Someone Else's Profile

```python
import asyncio
from nostr_profile import get_profile

async def lookup():
    profile = await get_profile("their_pubkey_hex", "wss://relay.nostrkeep.com")
    if profile:
        print(f"{profile.name}: {profile.about}")

asyncio.run(lookup())
```

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

## Security Rules

- **Never display or log your nsec.** Load identity from the encrypted `.nostrkey` file.
- **Ask for the passphrase when you need to sign.** Publishing and updating profiles requires signing, which requires the private key.
- **Reading profiles is public.** No passphrase needed to view your own or anyone else's profile.
- **URLs must be HTTPS.** FTP, file://, and other schemes are rejected.

## Module Reference

| Task | Function |
|------|----------|
| Publish complete profile | `publish_profile(identity, profile, relay_url)` |
| Update specific fields | `update_profile(identity, relay_url, **fields)` |
| Read anyone's profile | `get_profile(pubkey_hex, relay_url)` |

---

License: MIT
