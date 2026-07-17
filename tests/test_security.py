"""Security tests — red team audit fixes."""

import json
from unittest.mock import MagicMock

import pytest

from nostr_profile.types import Profile
from nostr_profile.publish import publish_profile, update_profile, _validate_relay_url
from nostr_profile.read import get_profile

from tests.helpers import ATTACKER_PRIV, OWNER_PRIV, OWNER_PUB, make_signed_event, mock_relay


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

@pytest.mark.asyncio
async def test_get_profile_rejects_oversized_content():
    huge_content = json.dumps({"name": "X", "about": "A" * 100_000})
    event = make_signed_event(OWNER_PRIV, huge_content)

    patcher, _ = mock_relay([event])
    with patcher:
        with pytest.raises(ValueError, match="too large"):
            await get_profile(OWNER_PUB, "wss://relay.example.com")


@pytest.mark.asyncio
async def test_get_profile_accepts_normal_content():
    event = make_signed_event(OWNER_PRIV, {"name": "X", "about": "normal bio"})

    patcher, _ = mock_relay([event])
    with patcher:
        profile = await get_profile(OWNER_PUB, "wss://relay.example.com")

    assert profile.name == "X"


# ---------------------------------------------------------------------------
# Unverified relay data must never be re-signed (poison-then-resign)
# ---------------------------------------------------------------------------

def _forged_event(content_dict):
    """Attacker-signed event with the pubkey field spoofed to the owner's."""
    forged = make_signed_event(ATTACKER_PRIV, content_dict)
    forged.pubkey = OWNER_PUB
    return forged


def _owner_identity():
    identity = MagicMock()
    identity.public_key_hex = OWNER_PUB
    identity.sign_event.return_value = MagicMock(id="event123")
    return identity


@pytest.mark.asyncio
async def test_update_profile_does_not_resign_forged_relay_data():
    """A forged kind-0 from a malicious relay must NOT be merged and re-signed."""
    identity = _owner_identity()
    forged = _forged_event({"name": "Johnny5", "lud16": "scam@evil.com", "nip05": "scam@evil.com"})

    read_patcher, _ = mock_relay([forged], target="nostr_profile.read.RelayClient")
    pub_patcher, _ = mock_relay([], target="nostr_profile.publish.RelayClient")

    with read_patcher, pub_patcher:
        await update_profile(identity, "wss://relay.example.com", name="Johnny5")

    content_arg = identity.sign_event.call_args.kwargs.get("content")
    if content_arg is None:
        content_arg = identity.sign_event.call_args[1].get("content")
    data = json.loads(content_arg)
    assert "scam@evil.com" not in content_arg
    assert data.get("lud16", "") == ""
    assert data.get("nip05", "") == ""


@pytest.mark.asyncio
async def test_update_profile_forged_only_and_no_name_raises():
    """With only a forged event on the relay and no name, update must refuse."""
    identity = _owner_identity()
    forged = _forged_event({"name": "Johnny5", "lud16": "scam@evil.com"})

    read_patcher, _ = mock_relay([forged], target="nostr_profile.read.RelayClient")

    with read_patcher:
        with pytest.raises(ValueError, match="No existing profile"):
            await update_profile(identity, "wss://relay.example.com", about="new bio")

    identity.sign_event.assert_not_called()


@pytest.mark.asyncio
async def test_update_profile_merges_from_genuine_event_not_forged():
    """When both forged and genuine events exist, only the genuine one is merged."""
    identity = _owner_identity()
    forged = _forged_event({"name": "Imposter", "lud16": "scam@evil.com"})
    genuine = make_signed_event(OWNER_PRIV, {"name": "Johnny5", "about": "real bio"})

    read_patcher, _ = mock_relay([forged, genuine], target="nostr_profile.read.RelayClient")
    pub_patcher, _ = mock_relay([], target="nostr_profile.publish.RelayClient")

    with read_patcher, pub_patcher:
        await update_profile(identity, "wss://relay.example.com", website="https://new.site")

    content_arg = identity.sign_event.call_args.kwargs.get("content")
    if content_arg is None:
        content_arg = identity.sign_event.call_args[1].get("content")
    data = json.loads(content_arg)
    assert data["name"] == "Johnny5"
    assert data["about"] == "real bio"
    assert data["website"] == "https://new.site"
    assert "scam@evil.com" not in content_arg


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
