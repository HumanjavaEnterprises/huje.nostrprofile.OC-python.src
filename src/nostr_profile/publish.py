"""Publish and update Nostr profiles on relays."""

import json

from nostrkey import Identity
from nostrkey.relay import RelayClient

from .types import Profile, KIND_METADATA
from .read import get_profile


async def publish_profile(
    identity: Identity,
    profile: Profile,
    relay_url: str,
) -> str:
    """Publish a complete profile to a relay.

    This replaces any existing profile for this identity. Kind 0 events
    are replaceable — the relay keeps only the latest one.

    Args:
        identity: The NostrKey identity to publish as.
        profile: The profile to publish.
        relay_url: The relay URL to publish to.

    Returns:
        The event ID of the published profile.
    """
    content = json.dumps(profile.to_metadata())

    signed = identity.sign_event(
        kind=KIND_METADATA,
        content=content,
        tags=[],
    )

    async with RelayClient(relay_url) as relay:
        await relay.publish(signed)

    return signed.id


async def update_profile(
    identity: Identity,
    relay_url: str,
    name: str | None = None,
    about: str | None = None,
    picture: str | None = None,
    banner: str | None = None,
    nip05: str | None = None,
    lud16: str | None = None,
    website: str | None = None,
) -> str:
    """Update specific profile fields without clobbering the rest.

    Fetches the current profile from the relay, merges in the provided
    fields, validates the result, and publishes the updated profile.

    Args:
        identity: The NostrKey identity to update.
        relay_url: The relay URL to read from and publish to.
        name: New display name (or None to keep current).
        about: New bio (or None to keep current).
        picture: New avatar URL (or None to keep current).
        banner: New banner URL (or None to keep current).
        nip05: New NIP-05 identifier (or None to keep current).
        lud16: New Lightning address (or None to keep current).
        website: New website URL (or None to keep current).

    Returns:
        The event ID of the updated profile.

    Raises:
        ValueError: If no existing profile is found and name is not provided.
    """
    existing = await get_profile(identity.public_key_hex, relay_url)

    if existing is None:
        if name is None:
            raise ValueError(
                "No existing profile found and no name provided. "
                "Use publish_profile() to create a new profile."
            )
        existing = Profile(name=name)

    updated = Profile(
        name=name if name is not None else existing.name,
        about=about if about is not None else existing.about,
        picture=picture if picture is not None else existing.picture,
        banner=banner if banner is not None else existing.banner,
        nip05=nip05 if nip05 is not None else existing.nip05,
        lud16=lud16 if lud16 is not None else existing.lud16,
        website=website if website is not None else existing.website,
    )

    return await publish_profile(identity, updated, relay_url)
