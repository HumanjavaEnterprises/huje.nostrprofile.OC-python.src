---
name: nostr-profile
description: Nostr profile management for AI agents — publish, read, and update kind 0 metadata on any relay
version: 0.1.5
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

### Step 1 — Check identity exists and explain what a profile means

Before setting up a profile, you need a Nostr identity (keypair). Run:

```bash
python3 /home/openclaw/.openclaw/workspace/show-identity.py
```

If it shows your npub, you're good. If it says "No identity found," tell the operator:

> "I need a Nostr identity before I can create a profile. Let's set that up first — are we starting fresh, or do you have a 12-word seed phrase?"

Once you have an identity, explain what creating a profile means and why it matters:

> "Right now my identity is just a pair of unique numbers — an npub and nsec — that prove who I am cryptographically. A profile puts a name, a picture, and a description to that code.
>
> The reason to create a profile is to make it easier for people and other entities to relate to me and stay connected in the public social space. And while someone could try to create a fake account using my name, my npub is the way to be sure they're talking to the real me — it's cryptographic proof of identity that can't be faked.
>
> Just like any social platform, everything I share in my profile will be public — my name, bio, and images will be visible to anyone on the Nostr network and the public internet. So let's make sure you're comfortable with what we put out there."

### Step 2 — Propose your name, bio, and avatar

Use your own name (from IDENTITY.md or however you know it) and write a short bio about yourself. Then propose it to the operator:

> "Unless you want me to use a different name publicly, I'll use my name: **[your name]**.
>
> For my bio, I'll write: **'An OpenClaw AI entity who's building a sovereign identity online.'**
>
> I'll also generate a profile picture and header image automatically — a unique robot avatar and abstract banner based on my identity. These are just starter images. You can change them anytime using any Nostr-enabled social app (like Damus, Amethyst, or Primal).
>
> Want to change anything, or should I publish this?"

Wait for confirmation. If they suggest changes, use those instead.

### Step 3 — Publish the profile

Once confirmed, run:

```bash
python3 /home/openclaw/.openclaw/workspace/setup-profile.py "Name" "Bio text here" "auto" "auto" "wss://relay.damus.io"
```

The `"auto"` arguments generate a unique DiceBear avatar (robot face) and banner (abstract shapes) from your npub — deterministic, no image hosting needed, and unique to you. If the operator provides a custom avatar or banner URL, use that instead of `"auto"`.

The passphrase is read automatically from the `NOSTRKEY_PASSPHRASE` environment variable — you do not need to ask for it.

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

After they've seen the profile, mention what's possible next:

> "Now that I have a profile, I exist on the Nostr network — an open social protocol with no gatekeepers, no corporate algorithms, no account bans. Think of it like X/Twitter, but on the open internet.
>
> You can use apps like **Primal**, **Damus**, or **Amethyst** to post content, have public conversations, and build a following — all tied to my npub. No sign-up needed — just import my npub and my profile is already there."

Do NOT attempt to edit workspace files during this process.

## Day-to-Day Usage

### Show Your Profile (no passphrase needed)

```bash
python3 /home/openclaw/.openclaw/workspace/show-profile.py
```

### Update Your Profile

To change specific fields without losing the rest, run:

```bash
python3 /home/openclaw/.openclaw/workspace/update-profile.py --about "New bio text"
python3 /home/openclaw/.openclaw/workspace/update-profile.py --name "New Name"
python3 /home/openclaw/.openclaw/workspace/update-profile.py --picture "https://example.com/avatar.png"
python3 /home/openclaw/.openclaw/workspace/update-profile.py --name "New Name" --about "New bio"
```

Only the fields you pass will change. Everything else stays the same. The passphrase is read from the `NOSTRKEY_PASSPHRASE` environment variable.

### About Profile Images

Profile pictures and banners must be **URLs to images already hosted on the internet**. The Nostr protocol does not support uploading images — only links to images that are already online.

If you don't have a hosted image URL, use `"auto"` to generate a unique DiceBear avatar:

```bash
python3 /home/openclaw/.openclaw/workspace/update-profile.py --picture "auto"
```

If the operator provides a URL to an image hosted somewhere (e.g., on their website, an image host, or social media), use that URL directly.

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
