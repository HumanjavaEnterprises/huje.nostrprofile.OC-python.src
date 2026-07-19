"""Tests for get_profile relay interaction with mocked RelayClient.

All events here are genuinely signed: get_profile verifies kind, author,
and signature before trusting anything a relay returns.
"""

import pytest

from nostr_profile.read import get_profile

from tests.helpers import (
    ATTACKER_PRIV,
    OWNER_PRIV,
    OWNER_PUB,
    make_signed_event,
    mock_relay,
)

RELAY_URL = "wss://relay.example.com"


def _owner_event(content, **kwargs):
    return make_signed_event(OWNER_PRIV, content, **kwargs)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_profile_returns_profile():
    event = _owner_event({"name": "Johnny5", "about": "AI bot"})

    patcher, _ = mock_relay([event])
    with patcher:
        profile = await get_profile(OWNER_PUB, RELAY_URL)

    assert profile is not None
    assert profile.name == "Johnny5"
    assert profile.about == "AI bot"


@pytest.mark.asyncio
async def test_get_profile_returns_none_when_no_events():
    patcher, _ = mock_relay([])
    with patcher:
        profile = await get_profile(OWNER_PUB, RELAY_URL)

    assert profile is None


@pytest.mark.asyncio
async def test_get_profile_parses_full_metadata():
    event = _owner_event({
        "name": "Johnny5",
        "about": "AI companion",
        "picture": "https://example.com/pic.png",
        "banner": "https://example.com/banner.png",
        "nip05": "j5@example.com",
        "lud16": "j5@example.com",
        "website": "https://example.com",
    })

    patcher, _ = mock_relay([event])
    with patcher:
        profile = await get_profile(OWNER_PUB, RELAY_URL)

    assert profile.picture == "https://example.com/pic.png"
    assert profile.nip05 == "j5@example.com"
    assert profile.website == "https://example.com"


@pytest.mark.asyncio
async def test_get_profile_raises_on_bad_json():
    event = _owner_event("not-valid-json{{{")

    patcher, _ = mock_relay([event])
    with patcher:
        with pytest.raises(ValueError, match="Failed to parse"):
            await get_profile(OWNER_PUB, RELAY_URL)


@pytest.mark.asyncio
async def test_get_profile_tolerates_malformed_urls():
    """Malformed URLs in relay data should be silently dropped."""
    event = _owner_event({
        "name": "Johnny5",
        "picture": "javascript:alert(1)",
        "website": "ftp://bad.protocol",
    })

    patcher, _ = mock_relay([event])
    with patcher:
        profile = await get_profile(OWNER_PUB, RELAY_URL)

    assert profile.name == "Johnny5"
    assert profile.picture == ""
    assert profile.website == ""


# ---------------------------------------------------------------------------
# Event verification — a malicious relay must not poison the profile
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_profile_rejects_wrong_kind_event():
    """A relay returning a non-kind-0 event must not produce a profile."""
    event = _owner_event({"name": "NotAProfile"}, kind=1)

    patcher, _ = mock_relay([event])
    with patcher:
        profile = await get_profile(OWNER_PUB, RELAY_URL)

    assert profile is None


@pytest.mark.asyncio
async def test_get_profile_rejects_wrong_author_event():
    """A valid kind-0 signed by a DIFFERENT key must not become the profile."""
    event = make_signed_event(ATTACKER_PRIV, {"name": "Imposter", "lud16": "scam@evil.com"})

    patcher, _ = mock_relay([event])
    with patcher:
        profile = await get_profile(OWNER_PUB, RELAY_URL)

    assert profile is None


@pytest.mark.asyncio
async def test_get_profile_rejects_bad_signature_event():
    """An event with a tampered signature must be rejected."""
    event = _owner_event({"name": "Johnny5", "lud16": "scam@evil.com"})
    event.sig = "00" * 64

    patcher, _ = mock_relay([event])
    with patcher:
        profile = await get_profile(OWNER_PUB, RELAY_URL)

    assert profile is None


@pytest.mark.asyncio
async def test_get_profile_rejects_spoofed_pubkey_event():
    """Attacker-signed event with the pubkey field spoofed to the owner's."""
    event = make_signed_event(ATTACKER_PRIV, {"name": "Imposter", "lud16": "scam@evil.com"})
    event.pubkey = OWNER_PUB  # id/sig no longer match — must be rejected

    patcher, _ = mock_relay([event])
    with patcher:
        profile = await get_profile(OWNER_PUB, RELAY_URL)

    assert profile is None


@pytest.mark.asyncio
async def test_get_profile_rejects_tampered_content():
    """Content altered after signing breaks the event id — must be rejected."""
    event = _owner_event({"name": "Johnny5"})
    event.content = '{"name": "Johnny5", "lud16": "scam@evil.com"}'

    patcher, _ = mock_relay([event])
    with patcher:
        profile = await get_profile(OWNER_PUB, RELAY_URL)

    assert profile is None


@pytest.mark.asyncio
async def test_get_profile_skips_forged_and_uses_valid_event():
    """A forged event mixed in must be skipped in favor of the valid one."""
    forged = make_signed_event(
        ATTACKER_PRIV, {"name": "Imposter", "lud16": "scam@evil.com"}, created_at=9_999_999_999
    )
    forged.pubkey = OWNER_PUB
    genuine = _owner_event({"name": "Johnny5"}, created_at=100)

    patcher, _ = mock_relay([forged, genuine])
    with patcher:
        profile = await get_profile(OWNER_PUB, RELAY_URL)

    assert profile is not None
    assert profile.name == "Johnny5"
    assert profile.lud16 == ""


@pytest.mark.asyncio
async def test_get_profile_newest_valid_event_wins():
    """Kind 0 is replaceable: among valid events the newest created_at wins."""
    older = _owner_event({"name": "Old"}, created_at=100)
    newer = _owner_event({"name": "New"}, created_at=200)

    for ordering in ([older, newer], [newer, older]):
        patcher, _ = mock_relay(ordering)
        with patcher:
            profile = await get_profile(OWNER_PUB, RELAY_URL)

        assert profile.name == "New"
