"""Read Nostr profiles from relays."""

import re
import json

from nostrkey.relay import RelayClient

from .types import Profile, KIND_METADATA

_PUBKEY_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

# Safety limit for relay queries
_MAX_EVENTS = 100


async def get_profile(
    pubkey_hex: str,
    relay_url: str,
) -> Profile | None:
    """Fetch a user's profile from a relay.

    Args:
        pubkey_hex: The hex public key of the user.
        relay_url: The relay URL to query.

    Returns:
        The Profile if found, None otherwise.
    """
    if not isinstance(pubkey_hex, str) or not _PUBKEY_HEX_RE.match(pubkey_hex):
        raise ValueError(
            f"pubkey_hex must be a 64-character lowercase hex string, got {pubkey_hex!r}"
        )

    filters = {
        "kinds": [KIND_METADATA],
        "authors": [pubkey_hex],
        "limit": 1,
    }

    events = []
    async with RelayClient(relay_url) as relay:
        async for event in relay.subscribe([filters]):
            events.append(event)
            if len(events) >= _MAX_EVENTS:
                break

    if not events:
        return None

    try:
        data = json.loads(events[0].content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse profile event content as JSON: {exc}"
        ) from exc

    return Profile.from_metadata(data)
