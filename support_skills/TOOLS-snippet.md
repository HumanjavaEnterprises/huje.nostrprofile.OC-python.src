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

- **Set up your profile (first time):**
  `python3 /home/openclaw/.openclaw/workspace/setup-profile.py "Name" "Bio" "auto" "auto" "wss://relay.damus.io"`
  Publishes your profile to a Nostr relay. Uses "auto" for avatar (DiceBear robot face) and banner (DiceBear shapes). Pass a custom image URL instead of "auto" if the operator provides one.

- **Update specific fields:**
  `python3 /home/openclaw/.openclaw/workspace/update-profile.py --name "New Name"`
  `python3 /home/openclaw/.openclaw/workspace/update-profile.py --about "New bio"`
  `python3 /home/openclaw/.openclaw/workspace/update-profile.py --picture "https://example.com/photo.jpg"`
  Only changes the fields you pass. Everything else stays the same.

**About images:** Profile pictures and banners must be URLs to images already hosted on the internet. Nostr does not support uploading images — only links to images that are already online. Use "auto" for a DiceBear-generated image if you don't have a hosted URL.

**Important:** Passphrase is read from NOSTRKEY_PASSPHRASE env var — you never need to ask for it.

**Full SDK reference:** `/home/openclaw/.openclaw/workspace/nostr-profile-SKILL.md`
```
