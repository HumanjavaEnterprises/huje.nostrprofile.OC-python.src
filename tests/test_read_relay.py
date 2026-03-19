"""Tests for get_profile relay interaction with mocked RelayClient."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from nostr_profile.read import get_profile


VALID_PUBKEY = "ab" * 32
RELAY_URL = "wss://relay.example.com"


def _make_event(content_dict: dict) -> SimpleNamespace:
    return SimpleNamespace(content=json.dumps(content_dict))


def _mock_relay(events):
    """Patch RelayClient so subscribe yields the given events."""
    relay = AsyncMock()

    async def _subscribe(filters):
        for ev in events:
            yield ev

    relay.subscribe = _subscribe

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=relay)
    ctx.__aexit__ = AsyncMock(return_value=False)

    return patch("nostr_profile.read.RelayClient", return_value=ctx)


@pytest.mark.asyncio
async def test_get_profile_returns_profile():
    event = _make_event({"name": "Johnny5", "about": "AI bot"})

    with _mock_relay([event]):
        profile = await get_profile(VALID_PUBKEY, RELAY_URL)

    assert profile is not None
    assert profile.name == "Johnny5"
    assert profile.about == "AI bot"


@pytest.mark.asyncio
async def test_get_profile_returns_none_when_no_events():
    with _mock_relay([]):
        profile = await get_profile(VALID_PUBKEY, RELAY_URL)

    assert profile is None


@pytest.mark.asyncio
async def test_get_profile_parses_full_metadata():
    event = _make_event({
        "name": "Johnny5",
        "about": "AI companion",
        "picture": "https://example.com/pic.png",
        "banner": "https://example.com/banner.png",
        "nip05": "j5@example.com",
        "lud16": "j5@example.com",
        "website": "https://example.com",
    })

    with _mock_relay([event]):
        profile = await get_profile(VALID_PUBKEY, RELAY_URL)

    assert profile.picture == "https://example.com/pic.png"
    assert profile.nip05 == "j5@example.com"
    assert profile.website == "https://example.com"


@pytest.mark.asyncio
async def test_get_profile_raises_on_bad_json():
    event = SimpleNamespace(content="not-valid-json{{{")

    with _mock_relay([event]):
        with pytest.raises(ValueError, match="Failed to parse"):
            await get_profile(VALID_PUBKEY, RELAY_URL)


@pytest.mark.asyncio
async def test_get_profile_tolerates_malformed_urls():
    """Malformed URLs in relay data should be silently dropped."""
    event = _make_event({
        "name": "Johnny5",
        "picture": "javascript:alert(1)",
        "website": "ftp://bad.protocol",
    })

    with _mock_relay([event]):
        profile = await get_profile(VALID_PUBKEY, RELAY_URL)

    assert profile.name == "Johnny5"
    assert profile.picture == ""
    assert profile.website == ""


@pytest.mark.asyncio
async def test_get_profile_uses_first_event_only():
    """Even if relay returns multiple events, we use the first one."""
    event1 = _make_event({"name": "First"})
    event2 = _make_event({"name": "Second"})

    with _mock_relay([event1, event2]):
        profile = await get_profile(VALID_PUBKEY, RELAY_URL)

    assert profile.name == "First"
