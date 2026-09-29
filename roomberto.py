#!/usr/bin/env python3
"""Read-only Roomberto adapter.

This module intentionally exposes no robot-moving or settings-writing methods.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
# This is used only for the fixed 1Password CLI and never through a shell.
import subprocess  # nosec B404
import sys
from typing import Any

import aiohttp
from roombapy_prime import CloudAccount
from roombapy_prime.models.robot_info import parse_active_map_versions

OP_ITEM = "Irobot - Roomberto"
COUNTRY_DEFAULT = "US"


class CredentialError(RuntimeError):
    pass


def _op_read(field: str) -> str:
    executable = shutil.which("op")
    if executable is None:
        raise CredentialError("1Password CLI is unavailable")
    result = subprocess.run(  # nosec B603
        [executable, "read", f"op://Sean/{OP_ITEM}/{field}"],
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    if result.returncode != 0:
        raise CredentialError(
            "Roomberto credentials are unavailable from the Sean 1Password vault"
        )
    return result.stdout.rstrip("\n")


def _credentials() -> tuple[str, str, str]:
    return (
        _op_read("username"),
        _op_read("password"),
        COUNTRY_DEFAULT,
    )


def _redact_id(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
    return f"sha256:{digest}"


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "value"):
        return _json_safe(value.value)
    return str(value)


def _reported(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    state = payload.get("state")
    if not isinstance(state, dict):
        return {}
    reported = state.get("reported")
    return reported if isinstance(reported, dict) else {}


def _state_summary(payload: Any) -> dict[str, Any]:
    reported = _reported(payload)
    mission = reported.get("cleanMissionStatus")
    if not isinstance(mission, dict):
        mission = {}
    return {
        "phase": mission.get("phase"),
        "battery_percent": reported.get("batPct"),
        "error": mission.get("error"),
    }


def _select_blid(account: CloudAccount, requested: str | None) -> str:
    if requested:
        if requested not in account.robots:
            raise ValueError("Requested BLID is not present on this iRobot account")
        return requested
    if len(account.robots) != 1:
        raise ValueError("Account has multiple robots; pass --blid explicitly")
    return next(iter(account.robots))


async def _login() -> tuple[aiohttp.ClientSession, CloudAccount]:
    username, password, country = _credentials()
    session = aiohttp.ClientSession()
    try:
        # Exactly one initial login attempt. No retries and no auto-refresh.
        account = await CloudAccount.login(
            session, username, password, country, request_timeout=20.0
        )
    except BaseException:
        await session.close()
        raise
    return session, account


async def discover() -> dict[str, Any]:
    session, account = await _login()
    try:
        robots = []
        for blid, entry in account.robots.items():
            robots.append(
                {
                    "blid": _redact_id(blid),
                    "generation": account.generation(blid),
                    "sku": getattr(entry, "sku", None),
                    "name": getattr(entry, "name", None),
                }
            )
        return {"ok": True, "read_only": True, "robots": robots}
    finally:
        await session.close()


async def status(blid: str | None) -> dict[str, Any]:
    session, account = await _login()
    robot = None
    try:
        selected = _select_blid(account, blid)
        robot = await account.prime_robot(selected, auto_refresh=False)
        await robot.connect(timeout=10.0)
        state = await robot.get_state(timeout=8.0)
        return {
            "ok": True,
            "read_only": True,
            "robot": _redact_id(selected),
            "state": _json_safe(state.payload),
        }
    finally:
        if robot is not None:
            await robot.disconnect()
        await session.close()


async def rooms(blid: str | None) -> dict[str, Any]:
    session, account = await _login()
    robot = None
    try:
        selected = _select_blid(account, blid)
        robot = await account.prime_robot(selected, auto_refresh=False)
        await robot.connect(timeout=10.0)
        versions = parse_active_map_versions(await robot.get_active_map_versions())
        maps: list[dict[str, Any]] = []
        for entry in versions:
            metadata = await robot.get_map_metadata(entry.p2map_id)
            version = metadata.current_map_version
            names = (
                await robot.get_map_region_names(metadata.p2map_id, version)
                if version is not None
                else {}
            )
            maps.append(
                {
                    "map_id": metadata.p2map_id,
                    "map_name": metadata.name,
                    "version": version,
                    "rooms": [
                        {"region_id": region_id, "name": name}
                        for region_id, name in sorted(names.items())
                    ],
                }
            )
        return {
            "ok": True,
            "read_only": True,
            "robot": _redact_id(selected),
            "maps": maps,
        }
    finally:
        if robot is not None:
            await robot.disconnect()
        await session.close()


async def _simple_action(blid: str | None, command: str) -> dict[str, Any]:
    """Send exactly one confirmed basic command without retrying."""
    session, account = await _login()
    robot = None
    try:
        selected = _select_blid(account, blid)
        robot = await account.prime_robot(selected, auto_refresh=False)
        await robot.connect(timeout=10.0)
        before = _state_summary((await robot.get_state(timeout=8.0)).payload)
        if command == "start" and before["phase"] == "run":
            return {
                "ok": True,
                "command_sent": False,
                "reason": "already_running",
                "before": before,
                "after": before,
            }
        acknowledged = await robot.send_simple_command(command)
        await asyncio.sleep(5)
        after = _state_summary((await robot.get_state(timeout=8.0)).payload)
        return {
            # Prime 105's unnamed shadow may omit live mission fields. A broker
            # acknowledgment proves delivery, not physical effect.
            "ok": bool(acknowledged),
            "command": command,
            "command_sent": True,
            "transport_acknowledged": acknowledged,
            "before": before,
            "after": after,
        }
    finally:
        if robot is not None:
            await robot.disconnect()
        await session.close()


async def launch(blid: str | None) -> dict[str, Any]:
    return await _simple_action(blid, "start")


async def home(blid: str | None) -> dict[str, Any]:
    return await _simple_action(blid, "dock")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("discover", help="List account robots without connecting to one")
    for name, help_text in (
        ("status", "Read the selected robot's current state"),
        ("rooms", "Read map and room identifiers"),
        ("launch", "Start one whole-home cleaning mission"),
        ("home", "Send Roomberto back to the dock"),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--blid", help="Exact robot BLID; not persisted")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "discover":
            output = asyncio.run(discover())
        elif args.command == "status":
            output = asyncio.run(status(args.blid))
        elif args.command == "rooms":
            output = asyncio.run(rooms(args.blid))
        elif args.command == "launch":
            output = asyncio.run(launch(args.blid))
        elif args.command == "home":
            output = asyncio.run(home(args.blid))
        else:  # pragma: no cover
            raise AssertionError("unreachable")
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except (CredentialError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2
    except Exception as exc:
        # Do not print repr(), raw upstream responses, or tracebacks: authentication
        # failures can carry vendor response objects we do not want in chat/logs.
        print(
            json.dumps({"ok": False, "error": type(exc).__name__}),
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
