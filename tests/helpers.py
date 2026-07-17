"""Shared test helpers: genuinely signed Nostr events and mocked relays.

get_profile now verifies kind, author, and signature of every event a relay
returns, so test fixtures must be real signed events — not bare namespaces.
"""

import json
import time
from unittest.mock import AsyncMock, patch

from nostrkey import generate_keypair
from nostrkey.events import UnsignedEvent, sign_event

# Stable keypairs for the whole test session.
OWNER_PRIV, OWNER_PUB = generate_keypair()
ATTACKER_PRIV, ATTACKER_PUB = generate_keypair()


def make_signed_event(private_key_hex, content, kind=0, created_at=None, tags=None):
    """Sign a real Nostr event. *content* may be a dict (JSON-encoded) or str."""
    if not isinstance(content, str):
        content = json.dumps(content)
    unsigned = UnsignedEvent(
        kind=kind,
        content=content,
        tags=tags or [],
        created_at=created_at if created_at is not None else int(time.time()),
    )
    return sign_event(private_key_hex, unsigned)


def mock_relay(events, target="nostr_profile.read.RelayClient"):
    """Patch a RelayClient so subscribe yields *events*. Returns (patcher, relay)."""
    relay = AsyncMock()
    relay.publish = AsyncMock()

    async def _subscribe(filters):
        for ev in events:
            yield ev

    relay.subscribe = _subscribe

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=relay)
    ctx.__aexit__ = AsyncMock(return_value=False)

    return patch(target, return_value=ctx), relay
