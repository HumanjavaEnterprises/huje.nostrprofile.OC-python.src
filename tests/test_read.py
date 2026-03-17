"""Tests for profile reading — validation only (no relay needed)."""

import pytest

from nostr_profile.read import get_profile


@pytest.mark.asyncio
async def test_get_profile_rejects_bad_pubkey():
    with pytest.raises(ValueError, match="64-character"):
        await get_profile("too_short", "wss://relay.example.com")


@pytest.mark.asyncio
async def test_get_profile_rejects_non_string():
    with pytest.raises(ValueError, match="64-character"):
        await get_profile(123, "wss://relay.example.com")


@pytest.mark.asyncio
async def test_get_profile_rejects_uppercase_hex():
    with pytest.raises(ValueError, match="lowercase hex"):
        await get_profile("A" * 64, "wss://relay.example.com")


@pytest.mark.asyncio
async def test_get_profile_rejects_non_hex():
    with pytest.raises(ValueError, match="lowercase hex"):
        await get_profile("x" * 64, "wss://relay.example.com")
