from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

import roomberto


def test_cli_has_only_read_only_device_operations() -> None:
    commands = set(roomberto.parser()._subparsers._group_actions[0].choices)
    assert commands == {"discover", "status", "rooms", "launch", "home"}


def test_source_does_not_expose_robot_write_methods() -> None:
    source = inspect.getsource(roomberto)
    forbidden = (
        "clean_regions",
        "pause_mission",
        "resume_mission",
        "end_mission",
        "update_settings",
        "edit_map",
    )
    assert not any(name in source for name in forbidden)


def test_state_summary_extracts_only_operational_fields() -> None:
    payload = {
        "state": {
            "reported": {
                "batPct": 88,
                "cleanMissionStatus": {"phase": "charge", "error": 0},
                "private": "not returned",
            }
        }
    }
    assert roomberto._state_summary(payload) == {
        "phase": "charge",
        "battery_percent": 88,
        "error": 0,
    }


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


def test_1password_read_uses_reference_not_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = {}

    monkeypatch.setattr(roomberto.shutil, "which", lambda _: "/safe/op")

    def fake_run(args, **kwargs):
        seen["args"] = args
        return SimpleNamespace(returncode=0, stdout="very-secret\n")

    monkeypatch.setattr(roomberto.subprocess, "run", fake_run)
    assert roomberto._op_read("password") == "very-secret"
    assert seen["args"] == [
        "/safe/op", "read", "op://Sean/Irobot - Roomberto/password"
    ]


def test_json_safe_handles_enums_and_nested_values() -> None:
    value = SimpleNamespace(value="charging")
    assert roomberto._json_safe({"state": value, "items": (1, True)}) == {
        "state": "charging",
        "items": [1, True],
    }
