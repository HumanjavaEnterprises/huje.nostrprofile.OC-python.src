"""
Nostr Profile Info
Show your agent's current Nostr profile. No passphrase needed.
Usage: python3 show-profile.py [relay_url]

Reads the profile from the local cache or fetches it from a relay.
"""
import asyncio
import json
import sys

PROFILE_FILE = "/home/openclaw/.openclaw/workspace/nostr-profile.json"
PUBLIC_FILE = "/home/openclaw/.openclaw/workspace/nostr-identity.json"
DEFAULT_RELAY = "wss://relay.nostrkeep.com"

relay = sys.argv[1] if len(sys.argv) > 1 else None

# Try local cache first
try:
    with open(PROFILE_FILE) as f:
        profile = json.load(f)
    print(f"name: {profile.get('name', '(not set)')}")
    print(f"about: {profile.get('about', '(not set)')}")
    if profile.get("picture"):
        print(f"picture: {profile['picture']}")
    print(f"relay: {profile.get('relay', DEFAULT_RELAY)}")
    if profile.get("event_id"):
        print(f"event_id: {profile['event_id']}")

    # Also show npub from identity file
    try:
        with open(PUBLIC_FILE) as f:
            identity = json.load(f)
        print(f"npub: {identity['npub']}")
    except FileNotFoundError:
        pass

except FileNotFoundError:
    # No local cache — try fetching from relay
    if not relay:
        # Check if we have an npub to fetch with
        try:
            with open(PUBLIC_FILE) as f:
                identity = json.load(f)
            pubkey_hex = identity.get("public_key_hex")
            relay = DEFAULT_RELAY
        except FileNotFoundError:
            print("No profile found. Run setup-profile.py first to create your Nostr profile.")
            sys.exit(1)

    if pubkey_hex:
        try:
            from nostr_profile import get_profile

            async def fetch():
                return await get_profile(pubkey_hex, relay)

            profile = asyncio.run(fetch())
            if profile:
                print(f"name: {profile.name}")
                print(f"about: {profile.about}")
                if profile.picture:
                    print(f"picture: {profile.picture}")
                print(f"relay: {relay}")
                print(f"npub: {identity['npub']}")
            else:
                print(f"No profile found on {relay}. Run setup-profile.py to create one.")
        except Exception as e:
            print(f"Error fetching profile: {e}")
    else:
        print("No profile found. Run setup-profile.py first to create your Nostr profile.")
        sys.exit(1)
