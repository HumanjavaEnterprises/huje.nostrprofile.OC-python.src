"""nostr-profile — Nostr profile management for OpenClaw AI agents."""

from .types import Profile
from .publish import publish_profile, update_profile
from .read import get_profile

__version__ = "0.1.0"

__all__ = [
    "Profile",
    "publish_profile",
    "update_profile",
    "get_profile",
]
