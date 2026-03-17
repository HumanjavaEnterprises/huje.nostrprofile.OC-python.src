"""Data types for nostr-profile — Nostr kind 0 metadata."""

import re
from dataclasses import dataclass, field
from typing import Optional

# Kind 0 — replaceable metadata event (NIP-01)
KIND_METADATA = 0

# Validation limits
MAX_NAME_LENGTH = 100
MAX_ABOUT_LENGTH = 2000
MAX_URL_LENGTH = 2048
MAX_FIELD_LENGTH = 500

_NIP05_RE = re.compile(r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
_URL_RE = re.compile(r"^https?://\S+$")
_LUD16_RE = re.compile(r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _validate_url(value: str, name: str) -> None:
    """Validate an optional URL field."""
    if not value:
        return
    if len(value) > MAX_URL_LENGTH:
        raise ValueError(f"{name} URL too long ({len(value)} chars). Maximum is {MAX_URL_LENGTH}.")
    if not _URL_RE.match(value):
        raise ValueError(f"{name} must be an HTTP/HTTPS URL, got {value!r}")


def _validate_nip05(value: str) -> None:
    """Validate NIP-05 identifier format (user@domain.tld)."""
    if not value:
        return
    if len(value) > MAX_FIELD_LENGTH:
        raise ValueError(f"NIP-05 identifier too long ({len(value)} chars).")
    if not _NIP05_RE.match(value):
        raise ValueError(
            f"NIP-05 must be in user@domain.tld format, got {value!r}"
        )


def _validate_lud16(value: str) -> None:
    """Validate Lightning address format (user@domain.tld)."""
    if not value:
        return
    if len(value) > MAX_FIELD_LENGTH:
        raise ValueError(f"Lightning address too long ({len(value)} chars).")
    if not _LUD16_RE.match(value):
        raise ValueError(
            f"lud16 must be in user@domain.tld format, got {value!r}"
        )


@dataclass
class Profile:
    """A Nostr profile (kind 0 metadata).

    Maps to the NIP-01 kind 0 event content JSON. All fields are optional
    except display_name — an agent needs at least a name.

    Attributes:
        name: Display name (max 100 chars).
        about: Bio/description (max 2000 chars).
        picture: Avatar URL (HTTPS).
        banner: Banner image URL (HTTPS).
        nip05: NIP-05 verification identifier (user@domain.tld).
        lud16: Lightning address for payments (user@domain.tld).
        website: Personal/project website URL.
    """
    name: str
    about: str = ""
    picture: str = ""
    banner: str = ""
    nip05: str = ""
    lud16: str = ""
    website: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Profile name must be a non-empty string")
        if len(self.name) > MAX_NAME_LENGTH:
            raise ValueError(
                f"Profile name too long ({len(self.name)} chars). "
                f"Maximum is {MAX_NAME_LENGTH}."
            )
        if len(self.about) > MAX_ABOUT_LENGTH:
            raise ValueError(
                f"About too long ({len(self.about)} chars). "
                f"Maximum is {MAX_ABOUT_LENGTH}."
            )
        _validate_url(self.picture, "picture")
        _validate_url(self.banner, "banner")
        _validate_url(self.website, "website")
        _validate_nip05(self.nip05)
        _validate_lud16(self.lud16)

    def to_metadata(self) -> dict:
        """Convert to NIP-01 kind 0 content dict.

        Only includes non-empty fields to keep the event clean.
        """
        meta: dict = {"name": self.name}
        if self.about:
            meta["about"] = self.about
        if self.picture:
            meta["picture"] = self.picture
        if self.banner:
            meta["banner"] = self.banner
        if self.nip05:
            meta["nip05"] = self.nip05
        if self.lud16:
            meta["lud16"] = self.lud16
        if self.website:
            meta["website"] = self.website
        return meta

    @classmethod
    def from_metadata(cls, data: dict) -> "Profile":
        """Parse from a kind 0 content dict.

        Tolerant of missing and malformed fields — only name is required.
        Fields that fail validation (e.g. malformed URLs from other clients)
        are silently dropped rather than crashing the entire parse.
        """
        name = data.get("name") or data.get("display_name") or ""
        if not name:
            raise ValueError("Profile metadata must contain a 'name' or 'display_name' field")

        # Truncate name if too long (relay data may exceed our limits)
        if len(name) > MAX_NAME_LENGTH:
            name = name[:MAX_NAME_LENGTH]

        about = data.get("about", "")
        if len(about) > MAX_ABOUT_LENGTH:
            about = about[:MAX_ABOUT_LENGTH]

        # Validate optional fields — drop silently if malformed
        def _safe_url(val: str) -> str:
            try:
                _validate_url(val, "field")
                return val
            except ValueError:
                return ""

        def _safe_nip05(val: str) -> str:
            try:
                _validate_nip05(val)
                return val
            except ValueError:
                return ""

        def _safe_lud16(val: str) -> str:
            try:
                _validate_lud16(val)
                return val
            except ValueError:
                return ""

        return cls(
            name=name,
            about=about,
            picture=_safe_url(data.get("picture", "")),
            banner=_safe_url(data.get("banner", "")),
            nip05=_safe_nip05(data.get("nip05", "")),
            lud16=_safe_lud16(data.get("lud16", "")),
            website=_safe_url(data.get("website", "")),
        )

    def diff(self, other: "Profile") -> dict[str, tuple]:
        """Compare two profiles and return what changed.

        Returns a dict mapping field name to (old_value, new_value)
        for fields that differ.
        """
        changes: dict[str, tuple] = {}
        for field_name in ("name", "about", "picture", "banner", "nip05", "lud16", "website"):
            old_val = getattr(self, field_name)
            new_val = getattr(other, field_name)
            if old_val != new_val:
                changes[field_name] = (old_val, new_val)
        return changes
