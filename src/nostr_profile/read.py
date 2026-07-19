"""Read Nostr profiles from relays."""

import asyncio
import re
import json

from nostrkey.events import verify_event
from nostrkey.relay import RelayClient

from .types import Profile, KIND_METADATA

_PUBKEY_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

# Safety limits
_MAX_EVENTS = 100
_MAX_CONTENT_SIZE = 65_536  # 64 KB — generous for kind 0
_RELAY_TIMEOUT = 15  # seconds


def _validate_relay_url(relay_url: str) -> None:
    """Reject relay URLs that are not secure WebSocket."""
    if not isinstance(relay_url, str) or not relay_url.startswith("wss://"):
        raise ValueError(
            f"relay_url must start with wss://, got {str(relay_url)[:40]!r}"
        )


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
            f"pubkey_hex must be a 64-character lowercase hex string, "
            f"got {str(pubkey_hex)[:20]!r}"
        )

    _validate_relay_url(relay_url)

    filters = {
        "kinds": [KIND_METADATA],
        "authors": [pubkey_hex],
        "limit": 1,
    }

    async def _fetch():
        events = []
        async with RelayClient(relay_url) as relay:
            async for event in relay.subscribe([filters]):
                events.append(event)
                if len(events) >= _MAX_EVENTS:
                    break
        return events

    events = await asyncio.wait_for(_fetch(), timeout=_RELAY_TIMEOUT)

    # Never trust relay data blindly: only accept events that are actually
    # kind 0, actually authored by the requested pubkey, and carry a valid
    # id + signature. Kind 0 is replaceable, so among the survivors the
    # newest created_at wins. Anything else (forged, mismatched, tampered)
    # is skipped — a malicious relay must not be able to poison the profile.
    best = None
    for event in events:
        try:
            if event.kind != KIND_METADATA:
                continue
            if event.pubkey != pubkey_hex:
                continue
            if not verify_event(event):
                continue
        except (AttributeError, TypeError, ValueError):
            continue
        if best is None or event.created_at > best.created_at:
            best = event

    if best is None:
        return None

    content = best.content
    if len(content) > _MAX_CONTENT_SIZE:
        raise ValueError(
            f"Profile event content too large ({len(content)} bytes). "
            f"Maximum is {_MAX_CONTENT_SIZE}."
        )

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse profile event content as JSON: {exc}"
        ) from exc

    return Profile.from_metadata(data)
