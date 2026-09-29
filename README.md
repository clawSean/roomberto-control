# Roomberto Control

Guarded read-only access to a Roomba Combo 105 through iRobot's cloud.

## Security posture

- Upstream is pinned to reviewed commit `8fce9139822886ab03aceb5a5787eb851cc0a095`
  (`v0.4.0`), not a branch.
- The optional upstream `tools` package is not installed because it contains
  robot-moving verification commands.
- 1Password is the credential source of truth. The adapter reads only the
  `username` and `password` fields from `op://Sean/Irobot - Roomberto` at
  runtime; values are never command-line arguments, config files, or logs.
- Each CLI invocation makes at most one initial login attempt. There is no
  blind retry loop or `auto_refresh` credential closure.
- The CLI exposes read-only `discover`, `status`, and `rooms`, plus one guarded
  `launch` and `home` actions that send exactly one whole-home `start` or
  `dock`. It has no room targeting, pause, stop, schedule, settings, or map-edit
  command.

## Setup

```bash
uv sync --frozen
uv run roomberto.py discover
```

Create a Login item titled `Irobot - Roomberto` in the `Sean` 1Password vault.
`discover` reads it at runtime, authenticates once, and lists redacted robot
identifiers.

For a multi-robot account, pass the full BLID locally:

```bash
uv run roomberto.py status --blid '<full-blid>'
uv run roomberto.py rooms --blid '<full-blid>'
uv run roomberto.py launch --blid '<full-blid>'
uv run roomberto.py home --blid '<full-blid>'
```

The BLID is not persisted by this project.

No service, daemon, listener, Keychain entry, or OpenClaw configuration is
installed.
