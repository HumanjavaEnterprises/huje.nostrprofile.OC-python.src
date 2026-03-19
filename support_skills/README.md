# Support Skills — nostr-profile for OpenClaw

Ready-to-deploy workspace files for OpenClaw operators whose agents don't support `clawhub install` or lack file-discovery tools.

## Prerequisites

1. Your agent already has a Nostr identity set up via [NostrKey](https://github.com/HumanjavaEnterprises/nostrkey.app.OC-python.src). The identity file (`my-identity.nostrkey`) and public identity (`nostr-identity.json`) must exist in the workspace.

2. `nostr-profile` installed in the container image. Add to your Dockerfile:
   ```dockerfile
   RUN pip3 install --no-cache-dir --break-system-packages nostr-profile==0.1.2
   ```

## What's Here

| File | Purpose | Where to Put It |
|------|---------|-----------------|
| `setup-profile.py` | Publish your agent's Nostr profile (name, bio, avatar) | Copy into OC workspace root |
| `show-profile.py` | Show current profile (no passphrase needed) | Copy into OC workspace root |
| `nostr-profile-SKILL.md` | Agent-facing skill reference | Copy into OC workspace root |
| `TOOLS-snippet.md` | Paste block for your agent's TOOLS.md | Paste into existing TOOLS.md |

## Setup

### Step 1 — Install in Docker image

```dockerfile
RUN pip3 install --no-cache-dir --break-system-packages nostr-profile==0.1.2
```

Rebuild: `docker compose build --no-cache <service> && docker compose up -d <service>`

### Step 2 — Copy scripts to workspace

```bash
docker cp support_skills/setup-profile.py <container>:/path/to/workspace/setup-profile.py
docker cp support_skills/show-profile.py <container>:/path/to/workspace/show-profile.py
docker cp support_skills/nostr-profile-SKILL.md <container>:/path/to/workspace/nostr-profile-SKILL.md
```

### Step 3 — Update TOOLS.md

Paste the contents of `TOOLS-snippet.md` into your agent's `TOOLS.md`.

### Step 4 — Test

Start a new conversation and ask:

> "Set up your Nostr profile. Your name is [name] and your bio is [bio]."
