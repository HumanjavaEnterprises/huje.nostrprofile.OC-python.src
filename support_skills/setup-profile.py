"""
Nostr Profile Setup
Publish or update your agent's Nostr profile (kind 0 metadata).
Usage: python3 setup-profile.py "Name" "About/bio" [avatar_url] [relay_url]

Loads identity using NOSTRKEY_PASSPHRASE env var — no need to ask the operator.
"""
import asyncio
import json
import os
import sys

from nostrkey import Identity
from nostr_profile import Profile, publish_profile

IDENTITY_FILE = "/home/openclaw/.openclaw/workspace/my-identity.nostrkey"
PUBLIC_FILE = "/home/openclaw/.openclaw/workspace/nostr-identity.json"
PROFILE_FILE = "/home/openclaw/.openclaw/workspace/nostr-profile.json"
DEFAULT_RELAY = "wss://relay.damus.io"

if len(sys.argv) < 3:
    print("Usage: python3 setup-profile.py \"Name\" \"About\" [avatar_url] [relay_url]")
    print()
    print("  Name       — display name (required)")
    print("  About      — bio/description (required)")
    print("  avatar_url — profile picture URL (optional, use \"\" to skip)")
    print("  relay_url  — relay to publish to (optional, default: wss://relay.damus.io)")
    print()
    print("Passphrase is read from NOSTRKEY_PASSPHRASE env var.")
    sys.exit(1)

name = sys.argv[1]
about = sys.argv[2]
picture = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else ""
relay = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else DEFAULT_RELAY

# Get passphrase from env var
passphrase = os.environ.get("NOSTRKEY_PASSPHRASE")
if not passphrase:
    print("ERROR: NOSTRKEY_PASSPHRASE env var not set.")
    print("Set it in your docker-compose.yml or .env file.")
    sys.exit(1)

# Load identity from encrypted file
try:
    me = Identity.load(IDENTITY_FILE, passphrase=passphrase)
except FileNotFoundError:
    print("ERROR: No identity file found. Run setup-identity.py first to create your Nostr identity.")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Could not load identity: {e}")
    sys.exit(1)

# Build profile
profile = Profile(name=name, about=about)
if picture:
    profile.picture = picture

# Publish
async def main():
    event_id = await publish_profile(me, profile, relay)
    return event_id

try:
    event_id = asyncio.run(main())
except Exception as e:
    print(f"ERROR: Could not publish profile: {e}")
    sys.exit(1)

# Save profile locally for reference
profile_data = {"name": name, "about": about, "picture": picture, "relay": relay, "event_id": event_id}
with open(PROFILE_FILE, "w") as f:
    json.dump(profile_data, f, indent=2)

print()
print("PROFILE_PUBLISHED=true")
print(f"name: {name}")
print(f"about: {about}")
if picture:
    print(f"picture: {picture}")
print(f"relay: {relay}")
print(f"event_id: {event_id}")
print(f"npub: {me.npub}")
print()
print(f"My profile is now live on Nostr. Anyone can find me at {me.npub}")
print(f"on {relay}. I have a name, a bio, and a presence that is verifiably mine.")
print()
print("You can see my profile online at:")
print(f"  https://njump.me/{me.npub}")
print(f"  https://npub.bio/{me.npub}")
print()
print("You can ask me 'What is your Nostr profile?' at any time to see it.")
print("Would you like to see your profile online now?")
