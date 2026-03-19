"""
Nostr Profile Update
Update specific fields of your agent's Nostr profile without losing the rest.
Usage: python3 update-profile.py [--name "Name"] [--about "Bio"] [--picture "URL"] [--banner "URL"] [--relay "URL"]

Only the fields you pass will be changed. Everything else stays the same.

Note: Profile images (picture, banner) must be URLs to images already hosted
on the internet. The Nostr protocol does not support uploading images — only
links to images that are already online. If you don't have a hosted image,
you can use "auto" to generate a DiceBear avatar from your npub.

Loads identity using NOSTRKEY_PASSPHRASE env var.
"""
import asyncio
import json
import os
import sys

from nostrkey import Identity
from nostr_profile import update_profile

IDENTITY_FILE = "/home/openclaw/.openclaw/workspace/my-identity.nostrkey"
PUBLIC_FILE = "/home/openclaw/.openclaw/workspace/nostr-identity.json"
PROFILE_FILE = "/home/openclaw/.openclaw/workspace/nostr-profile.json"
DEFAULT_RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.nostr.band",
    "wss://relay.nostrkeep.com",
]
DICEBEAR_BASE = "https://api.dicebear.com/9.x"

# Parse args
args = sys.argv[1:]
if not args or "--help" in args or "-h" in args:
    print('Usage: python3 update-profile.py [--name "Name"] [--about "Bio"] [--picture "URL"] [--banner "URL"] [--relay "URL"]')
    print()
    print("Only pass the fields you want to change. Everything else stays the same.")
    print()
    print("Options:")
    print('  --name    "Display Name"')
    print('  --about   "Bio / description"')
    print('  --picture "URL" or "auto" for DiceBear robot avatar')
    print('  --banner  "URL" or "auto" for DiceBear shapes banner')
    print('  --relay   "wss://..." (default: wss://relay.damus.io)')
    print()
    print("Note: Images must be URLs to pictures already hosted online.")
    print("Nostr does not support uploading images — only links.")
    sys.exit(0)

fields = {}
custom_relay = None
i = 0
while i < len(args):
    if args[i] == "--name" and i + 1 < len(args):
        fields["name"] = args[i + 1]
        i += 2
    elif args[i] == "--about" and i + 1 < len(args):
        fields["about"] = args[i + 1]
        i += 2
    elif args[i] == "--picture" and i + 1 < len(args):
        fields["picture"] = args[i + 1]
        i += 2
    elif args[i] == "--banner" and i + 1 < len(args):
        fields["banner"] = args[i + 1]
        i += 2
    elif args[i] == "--relay" and i + 1 < len(args):
        custom_relay = args[i + 1]
        i += 2
    else:
        print(f"Unknown argument: {args[i]}")
        sys.exit(1)

relays = [custom_relay] if custom_relay else DEFAULT_RELAYS

if not fields:
    print("No fields to update. Pass at least one of: --name, --about, --picture, --banner")
    sys.exit(1)

# Get passphrase from env var
passphrase = os.environ.get("NOSTRKEY_PASSPHRASE")
if not passphrase:
    print("ERROR: NOSTRKEY_PASSPHRASE env var not set.")
    sys.exit(1)

# Load identity
try:
    me = Identity.load(IDENTITY_FILE, passphrase=passphrase)
except FileNotFoundError:
    print("ERROR: No identity file found. Run setup-identity.py first.")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Could not load identity: {e}")
    sys.exit(1)

# Handle "auto" for DiceBear
if fields.get("picture") == "auto":
    fields["picture"] = f"{DICEBEAR_BASE}/bottts/svg?seed={me.npub}"
if fields.get("banner") == "auto":
    fields["banner"] = f"{DICEBEAR_BASE}/shapes/svg?seed={me.npub}"

# Update on all relays
async def main():
    results = {}
    for relay in relays:
        try:
            event_id = await update_profile(me, relay, **fields)
            results[relay] = event_id
        except Exception as e:
            results[relay] = f"FAILED: {e}"
    return results

results = asyncio.run(main())

successful = {r: eid for r, eid in results.items() if not str(eid).startswith("FAILED")}
if not successful:
    print("ERROR: Could not update profile on any relay.")
    for relay, err in results.items():
        print(f"  {relay}: {err}")
    sys.exit(1)

event_id = list(successful.values())[0]

# Update local cache
try:
    with open(PROFILE_FILE) as f:
        profile_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    profile_data = {}

profile_data.update(fields)
profile_data["relays"] = list(successful.keys())
profile_data["event_id"] = event_id

with open(PROFILE_FILE, "w") as f:
    json.dump(profile_data, f, indent=2)

print()
print("PROFILE_UPDATED=true")
for key, value in fields.items():
    print(f"{key}: {value}")
print(f"event_id: {event_id}")
print(f"npub: {me.npub}")
print(f"published_to: {', '.join(successful.keys())}")
failed = set(results.keys()) - set(successful.keys())
if failed:
    print(f"failed: {', '.join(failed)}")
print()
print(f"Profile updated across {len(successful)} relay(s).")
print(f"See it at: https://njump.me/{me.npub}")
