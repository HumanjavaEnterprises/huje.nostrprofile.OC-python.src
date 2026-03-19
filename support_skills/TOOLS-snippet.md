# TOOLS.md Snippet — nostr-profile

Paste the block below into your agent's `TOOLS.md` file.

> **Why the full path?** Smaller models (e.g., Qwen3 8B) may not reliably construct
> the correct file path from just a filename. Including the absolute path lets the
> agent's file-read tool find it on the first try.

---

## Paste this into your TOOLS.md:

Replace `/home/openclaw/.openclaw/workspace` with your actual OC workspace path if different.

```markdown
### Nostr Profile — Profile Management

The `nostr-profile` Python package is pre-installed. You can publish and manage your public profile on the Nostr network.

**Scripts in your workspace:**

- **Show your profile (no passphrase needed):**
  `python3 /home/openclaw/.openclaw/workspace/show-profile.py`
  Shows your current name, bio, and avatar. Public data — no secrets involved.

- **Set up or update your profile:**
  `python3 /home/openclaw/.openclaw/workspace/setup-profile.py "Name" "Bio" "avatar_url" "relay_url" "PASSPHRASE"`
  Publishes your profile to a Nostr relay. Ask the operator for the passphrase before running. Avatar URL and relay URL are optional.

**Important:** Publishing a profile requires signing with your private key, so you need the passphrase. Reading profiles is always public — no passphrase needed.

**Full SDK reference:** `/home/openclaw/.openclaw/workspace/nostr-profile-SKILL.md`
```
