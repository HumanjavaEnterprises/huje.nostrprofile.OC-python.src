"""Tests for nostr-profile data types."""

import pytest

from nostr_profile.types import Profile


def test_profile_basic():
    p = Profile(name="Johnny5")
    assert p.name == "Johnny5"
    assert p.about == ""
    assert p.picture == ""


def test_profile_full():
    p = Profile(
        name="Johnny5",
        about="An OpenClaw AI companion",
        picture="https://example.com/avatar.png",
        banner="https://example.com/banner.png",
        nip05="johnny5@example.com",
        lud16="johnny5@getalby.com",
        website="https://example.com",
    )
    assert p.name == "Johnny5"
    assert p.nip05 == "johnny5@example.com"
    assert p.lud16 == "johnny5@getalby.com"


def test_profile_rejects_empty_name():
    with pytest.raises(ValueError, match="non-empty"):
        Profile(name="")


def test_profile_rejects_whitespace_name():
    with pytest.raises(ValueError, match="non-empty"):
        Profile(name="   ")


def test_profile_rejects_long_name():
    with pytest.raises(ValueError, match="too long"):
        Profile(name="x" * 101)


def test_profile_rejects_long_about():
    with pytest.raises(ValueError, match="too long"):
        Profile(name="Johnny5", about="x" * 2001)


def test_profile_rejects_non_url_picture():
    with pytest.raises(ValueError, match="HTTP/HTTPS URL"):
        Profile(name="Johnny5", picture="not-a-url")


def test_profile_rejects_non_url_banner():
    with pytest.raises(ValueError, match="HTTP/HTTPS URL"):
        Profile(name="Johnny5", banner="ftp://example.com/banner.png")


def test_profile_rejects_non_url_website():
    with pytest.raises(ValueError, match="HTTP/HTTPS URL"):
        Profile(name="Johnny5", website="example.com")


def test_profile_rejects_bad_nip05():
    with pytest.raises(ValueError, match="user@domain"):
        Profile(name="Johnny5", nip05="not-an-email")


def test_profile_rejects_bad_lud16():
    with pytest.raises(ValueError, match="user@domain"):
        Profile(name="Johnny5", lud16="@missing-user.com")


def test_profile_accepts_empty_optional_fields():
    p = Profile(name="Johnny5")
    assert p.picture == ""
    assert p.nip05 == ""
    assert p.lud16 == ""


def test_to_metadata_only_includes_non_empty():
    p = Profile(name="Johnny5", about="A bot")
    meta = p.to_metadata()
    assert meta == {"name": "Johnny5", "about": "A bot"}
    assert "picture" not in meta
    assert "nip05" not in meta


def test_to_metadata_full():
    p = Profile(
        name="Johnny5",
        about="AI companion",
        picture="https://example.com/avatar.png",
        nip05="johnny5@example.com",
        lud16="johnny5@getalby.com",
        website="https://example.com",
    )
    meta = p.to_metadata()
    assert meta["name"] == "Johnny5"
    assert meta["picture"] == "https://example.com/avatar.png"
    assert meta["nip05"] == "johnny5@example.com"
    assert meta["lud16"] == "johnny5@getalby.com"


def test_from_metadata_basic():
    data = {"name": "Johnny5", "about": "AI companion"}
    p = Profile.from_metadata(data)
    assert p.name == "Johnny5"
    assert p.about == "AI companion"
    assert p.picture == ""


def test_from_metadata_display_name_fallback():
    """Some clients use 'display_name' instead of 'name'."""
    data = {"display_name": "Johnny5"}
    p = Profile.from_metadata(data)
    assert p.name == "Johnny5"


def test_from_metadata_rejects_no_name():
    with pytest.raises(ValueError, match="name"):
        Profile.from_metadata({"about": "no name here"})


def test_from_metadata_tolerates_unknown_fields():
    data = {"name": "Johnny5", "about": "bot", "custom_field": "ignored"}
    p = Profile.from_metadata(data)
    assert p.name == "Johnny5"


def test_diff_detects_changes():
    old = Profile(name="Johnny5", about="v1")
    new = Profile(name="Johnny5", about="v2", picture="https://example.com/new.png")
    changes = old.diff(new)
    assert "about" in changes
    assert changes["about"] == ("v1", "v2")
    assert "picture" in changes
    assert changes["picture"] == ("", "https://example.com/new.png")
    assert "name" not in changes


def test_diff_no_changes():
    p = Profile(name="Johnny5", about="same")
    changes = p.diff(p)
    assert changes == {}


def test_url_length_limit():
    with pytest.raises(ValueError, match="too long"):
        Profile(name="Johnny5", picture="https://example.com/" + "x" * 2048)


def test_from_metadata_drops_malformed_url():
    """Malformed URLs from relay data are silently dropped, not crashed on."""
    data = {"name": "Johnny5", "picture": "javascript:alert(1)", "about": "bot"}
    p = Profile.from_metadata(data)
    assert p.name == "Johnny5"
    assert p.picture == ""  # dropped
    assert p.about == "bot"


def test_from_metadata_drops_bad_nip05():
    data = {"name": "Johnny5", "nip05": "not-valid"}
    p = Profile.from_metadata(data)
    assert p.nip05 == ""


def test_from_metadata_truncates_long_name():
    data = {"name": "x" * 200}
    p = Profile.from_metadata(data)
    assert len(p.name) == 100


def test_from_metadata_truncates_long_about():
    data = {"name": "Johnny5", "about": "x" * 5000}
    p = Profile.from_metadata(data)
    assert len(p.about) == 2000
