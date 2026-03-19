"""Security tests — red team audit fixes."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nostr_profile.types import Profile
from nostr_profile.publish import publish_profile, update_profile, _validate_relay_url
from nostr_profile.read import get_profile, _validate_relay_url as _validate_relay_url_read


# ---------------------------------------------------------------------------
# URL regex hardening (Finding 1)
# ---------------------------------------------------------------------------

def test_url_rejects_angle_brackets():
    with pytest.raises(ValueError, match="HTTP/HTTPS URL"):
        Profile(name="X", picture="https://evil.com/<script>alert(1)</script>")


def test_url_rejects_double_quotes():
    with pytest.raises(ValueError, match="HTTP/HTTPS URL"):
        Profile(name="X", picture='https://evil.com/" onclick="alert(1)')


def test_url_rejects_single_quotes():
    with pytest.raises(ValueError, match="HTTP/HTTPS URL"):
        Profile(name="X", website="https://evil.com/' onload='alert(1)")


def test_url_rejects_backtick():
    with pytest.raises(ValueError, match="HTTP/HTTPS URL"):
        Profile(name="X", banner="https://evil.com/`injection`")


def test_url_accepts_clean_url():
    p = Profile(name="X", picture="https://example.com/pic.png?size=100&format=webp")
    assert p.picture == "https://example.com/pic.png?size=100&format=webp"


def test_from_metadata_drops_xss_url():
    data = {"name": "X", "picture": "https://x\"><img src=x onerror=alert(1)>"}
    p = Profile.from_metadata(data)
    assert p.picture == ""


# ---------------------------------------------------------------------------
# Non-string field handling (Finding 2)
# ---------------------------------------------------------------------------

def test_from_metadata_non_string_about():
    data = {"name": "X", "about": 99999}
    p = Profile.from_metadata(data)
    assert p.about == ""


def test_from_metadata_non_string_picture():
    data = {"name": "X", "picture": ["list", "of", "urls"]}
    p = Profile.from_metadata(data)
    assert p.picture == ""


def test_from_metadata_non_string_nip05():
    data = {"name": "X", "nip05": {"nested": "object"}}
    p = Profile.from_metadata(data)
    assert p.nip05 == ""


def test_from_metadata_non_string_lud16():
    data = {"name": "X", "lud16": True}
    p = Profile.from_metadata(data)
    assert p.lud16 == ""


def test_from_metadata_non_string_website():
    data = {"name": "X", "website": 42}
    p = Profile.from_metadata(data)
    assert p.website == ""


def test_from_metadata_non_string_banner():
    data = {"name": "X", "banner": None}
    p = Profile.from_metadata(data)
    assert p.banner == ""


def test_from_metadata_non_string_name_raises():
    data = {"name": 12345}
    with pytest.raises(ValueError, match="name"):
        Profile.from_metadata(data)


# ---------------------------------------------------------------------------
# Relay URL validation (Finding 3)
# ---------------------------------------------------------------------------

def test_relay_url_rejects_ws():
    with pytest.raises(ValueError, match="wss://"):
        _validate_relay_url("ws://relay.example.com")


def test_relay_url_rejects_http():
    with pytest.raises(ValueError, match="wss://"):
        _validate_relay_url("http://relay.example.com")


def test_relay_url_rejects_ssrf():
    with pytest.raises(ValueError, match="wss://"):
        _validate_relay_url("ws://169.254.169.254/latest/meta-data/")


def test_relay_url_rejects_non_string():
    with pytest.raises(ValueError, match="wss://"):
        _validate_relay_url(12345)


def test_relay_url_accepts_wss():
    _validate_relay_url("wss://relay.example.com")


@pytest.mark.asyncio
async def test_publish_rejects_insecure_relay():
    identity = MagicMock()
    profile = Profile(name="X")
    with pytest.raises(ValueError, match="wss://"):
        await publish_profile(identity, profile, "ws://relay.example.com")


@pytest.mark.asyncio
async def test_get_profile_rejects_insecure_relay():
    with pytest.raises(ValueError, match="wss://"):
        await get_profile("ab" * 32, "ws://relay.example.com")


# ---------------------------------------------------------------------------
# Content size limit (Finding 7)
# ---------------------------------------------------------------------------

def _mock_relay_with_events(events):
    """Patch RelayClient for read.py so subscribe yields events."""
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
async def test_get_profile_rejects_oversized_content():
    huge_content = json.dumps({"name": "X", "about": "A" * 100_000})
    event = SimpleNamespace(content=huge_content)

    with _mock_relay_with_events([event]):
        with pytest.raises(ValueError, match="too large"):
            await get_profile("ab" * 32, "wss://relay.example.com")


@pytest.mark.asyncio
async def test_get_profile_accepts_normal_content():
    event = SimpleNamespace(content=json.dumps({"name": "X", "about": "normal bio"}))

    with _mock_relay_with_events([event]):
        profile = await get_profile("ab" * 32, "wss://relay.example.com")

    assert profile.name == "X"


# ---------------------------------------------------------------------------
# Error message truncation (Finding 9)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pubkey_error_truncates_value():
    """Error messages should not leak full input values."""
    long_input = "x" * 1000
    with pytest.raises(ValueError) as exc_info:
        await get_profile(long_input, "wss://relay.example.com")
    # The error message should NOT contain the full 1000-char input
    assert len(str(exc_info.value)) < 200
