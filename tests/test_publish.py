"""Tests for publish_profile and update_profile with mocked relay."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nostr_profile.types import Profile
from nostr_profile.publish import publish_profile, update_profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_identity(pubkey_hex: str = "ab" * 32) -> MagicMock:
    """Create a mock Identity that returns a signed event."""
    identity = MagicMock()
    identity.public_key_hex = pubkey_hex

    signed = SimpleNamespace(id="event123")
    identity.sign_event.return_value = signed
    return identity


def _mock_relay_client(events=None):
    """Return a patch context that replaces RelayClient with an async mock.

    If *events* is provided, relay.subscribe yields those events.
    """
    relay = AsyncMock()
    relay.publish = AsyncMock()

    async def _subscribe(filters):
        for ev in (events or []):
            yield ev

    relay.subscribe = _subscribe

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=relay)
    ctx.__aexit__ = AsyncMock(return_value=False)

    return patch("nostr_profile.publish.RelayClient", return_value=ctx), relay


# ---------------------------------------------------------------------------
# publish_profile
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_publish_profile_returns_event_id():
    identity = _make_identity()
    profile = Profile(name="Johnny5", about="AI companion")
    patcher, relay = _mock_relay_client()

    with patcher:
        event_id = await publish_profile(identity, profile, "wss://relay.example.com")

    assert event_id == "event123"


@pytest.mark.asyncio
async def test_publish_profile_signs_kind_0():
    identity = _make_identity()
    profile = Profile(name="Johnny5")
    patcher, relay = _mock_relay_client()

    with patcher:
        await publish_profile(identity, profile, "wss://relay.example.com")

    identity.sign_event.assert_called_once()
    call_kwargs = identity.sign_event.call_args
    assert call_kwargs.kwargs.get("kind") == 0 or call_kwargs[1].get("kind") == 0


@pytest.mark.asyncio
async def test_publish_profile_content_is_valid_json():
    identity = _make_identity()
    profile = Profile(name="Johnny5", about="bot", website="https://example.com")
    patcher, relay = _mock_relay_client()

    with patcher:
        await publish_profile(identity, profile, "wss://relay.example.com")

    content_arg = identity.sign_event.call_args.kwargs.get("content")
    if content_arg is None:
        content_arg = identity.sign_event.call_args[1].get("content")
    data = json.loads(content_arg)
    assert data["name"] == "Johnny5"
    assert data["about"] == "bot"
    assert data["website"] == "https://example.com"
    assert "picture" not in data  # empty fields excluded


@pytest.mark.asyncio
async def test_publish_profile_calls_relay_publish():
    identity = _make_identity()
    profile = Profile(name="Johnny5")
    patcher, relay = _mock_relay_client()

    with patcher:
        await publish_profile(identity, profile, "wss://relay.example.com")

    relay.publish.assert_awaited_once()


# ---------------------------------------------------------------------------
# update_profile — merges with existing
# ---------------------------------------------------------------------------

def _make_event(content_dict: dict) -> SimpleNamespace:
    return SimpleNamespace(content=json.dumps(content_dict))


@pytest.mark.asyncio
async def test_update_profile_merges_fields():
    """Updating 'about' should preserve existing name and other fields."""
    identity = _make_identity()
    existing_event = _make_event({"name": "Johnny5", "about": "v1", "picture": "https://example.com/pic.png"})

    with patch("nostr_profile.publish.get_profile", new_callable=AsyncMock) as mock_get, \
         patch("nostr_profile.publish.RelayClient") as mock_rc:

        mock_get.return_value = Profile(
            name="Johnny5", about="v1", picture="https://example.com/pic.png"
        )

        relay = AsyncMock()
        relay.publish = AsyncMock()
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=relay)
        ctx.__aexit__ = AsyncMock(return_value=False)
        mock_rc.return_value = ctx

        await update_profile(identity, "wss://relay.example.com", about="v2")

    # sign_event was called with merged content
    content_arg = identity.sign_event.call_args.kwargs.get("content")
    if content_arg is None:
        content_arg = identity.sign_event.call_args[1].get("content")
    data = json.loads(content_arg)
    assert data["name"] == "Johnny5"
    assert data["about"] == "v2"
    assert data["picture"] == "https://example.com/pic.png"


@pytest.mark.asyncio
async def test_update_profile_no_existing_with_name():
    """When no existing profile, update_profile creates one if name given."""
    identity = _make_identity()

    with patch("nostr_profile.publish.get_profile", new_callable=AsyncMock) as mock_get, \
         patch("nostr_profile.publish.RelayClient") as mock_rc:

        mock_get.return_value = None

        relay = AsyncMock()
        relay.publish = AsyncMock()
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=relay)
        ctx.__aexit__ = AsyncMock(return_value=False)
        mock_rc.return_value = ctx

        event_id = await update_profile(
            identity, "wss://relay.example.com",
            name="NewBot", about="Fresh profile"
        )

    assert event_id == "event123"
    content_arg = identity.sign_event.call_args.kwargs.get("content")
    if content_arg is None:
        content_arg = identity.sign_event.call_args[1].get("content")
    data = json.loads(content_arg)
    assert data["name"] == "NewBot"
    assert data["about"] == "Fresh profile"


@pytest.mark.asyncio
async def test_update_profile_no_existing_no_name_raises():
    """Without existing profile or name, update_profile must raise."""
    identity = _make_identity()

    with patch("nostr_profile.publish.get_profile", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        with pytest.raises(ValueError, match="No existing profile"):
            await update_profile(identity, "wss://relay.example.com", about="orphan bio")


@pytest.mark.asyncio
async def test_update_profile_only_changes_specified_fields():
    """Fields not passed should remain unchanged."""
    identity = _make_identity()

    with patch("nostr_profile.publish.get_profile", new_callable=AsyncMock) as mock_get, \
         patch("nostr_profile.publish.RelayClient") as mock_rc:

        mock_get.return_value = Profile(
            name="Johnny5",
            about="original bio",
            nip05="j5@example.com",
            lud16="j5@example.com",
        )

        relay = AsyncMock()
        relay.publish = AsyncMock()
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=relay)
        ctx.__aexit__ = AsyncMock(return_value=False)
        mock_rc.return_value = ctx

        await update_profile(identity, "wss://relay.example.com", website="https://new.site")

    content_arg = identity.sign_event.call_args.kwargs.get("content")
    if content_arg is None:
        content_arg = identity.sign_event.call_args[1].get("content")
    data = json.loads(content_arg)
    assert data["name"] == "Johnny5"
    assert data["about"] == "original bio"
    assert data["nip05"] == "j5@example.com"
    assert data["lud16"] == "j5@example.com"
    assert data["website"] == "https://new.site"
