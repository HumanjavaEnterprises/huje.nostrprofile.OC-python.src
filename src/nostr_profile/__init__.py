"""nostr-profile — Nostr profile management for OpenClaw AI agents."""

from .types import Profile
from .publish import ProfileClient, publish_profile, update_profile
from .read import get_profile

__version__ = "0.2.1"

__all__ = [
    "Profile",
    "ProfileClient",
    "publish_profile",
    "update_profile",
    "get_profile",
]
