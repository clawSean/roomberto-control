from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

import roomberto


def test_cli_has_only_read_only_device_operations() -> None:
    commands = set(roomberto.parser()._subparsers._group_actions[0].choices)
    assert commands == {"setup", "delete-credentials", "discover", "status", "rooms"}


def test_source_does_not_expose_robot_write_methods() -> None:
    source = inspect.getsource(roomberto)
    forbidden = (
        "send_simple_command",
        "clean_regions",
        "pause_mission",
        "resume_mission",
        "end_mission",
        "dock",
        "update_settings",
        "edit_map",
    )
    assert not any(name in source for name in forbidden)


def test_redacted_id_is_stable_and_hides_original() -> None:
    redacted = roomberto._redact_id("roomberto-secret-blid")
    assert redacted.startswith("sha256:")
    assert "roomberto" not in redacted
    assert redacted == roomberto._redact_id("roomberto-secret-blid")


def test_select_blid_requires_exact_choice_for_multiple_robots() -> None:
    account = SimpleNamespace(robots={"a": object(), "b": object()})
    with pytest.raises(ValueError, match="multiple robots"):
        roomberto._select_blid(account, None)
    assert roomberto._select_blid(account, "b") == "b"


def test_select_blid_rejects_unknown_robot() -> None:
    account = SimpleNamespace(robots={"a": object()})
    with pytest.raises(ValueError, match="not present"):
        roomberto._select_blid(account, "wrong")


def test_keychain_write_uses_stdin_not_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = {}

    def fake_security(*args: str, input_text: str | None = None):
        seen["args"] = args
        seen["input"] = input_text
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(roomberto, "_security", fake_security)
    roomberto._keychain_put("password", "very-secret")
    assert "very-secret" not in seen["args"]
    assert seen["input"] == "very-secret\nvery-secret\n"


def test_json_safe_handles_enums_and_nested_values() -> None:
    value = SimpleNamespace(value="charging")
    assert roomberto._json_safe({"state": value, "items": (1, True)}) == {
        "state": "charging",
        "items": [1, True],
    }
