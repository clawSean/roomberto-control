# Roomberto Control

Guarded read-only access to a Roomba Combo 105 through iRobot's cloud.

## Security posture

- Upstream is pinned to reviewed commit `8fce9139822886ab03aceb5a5787eb851cc0a095`
  (`v0.4.0`), not a branch.
- The optional upstream `tools` package is not installed because it contains
  robot-moving verification commands.
- Credentials live only in the macOS login Keychain under
  `com.clawsean.roomberto.irobot`; they are never command-line arguments,
  environment variables, config files, or logs.
- Each CLI invocation makes at most one initial login attempt. There is no
  blind retry loop or `auto_refresh` credential closure.
- The CLI exposes only `setup`, `discover`, `status`, and `rooms`. It has no
  cleaning, pause, stop, dock, schedule, settings, or map-edit command.

## Setup

```bash
uv sync --frozen
uv run roomberto.py setup
uv run roomberto.py discover
```

`setup` prompts locally for the iRobot username and password. Nothing secret is
printed. `discover` authenticates once and lists redacted robot identifiers.

For a multi-robot account, pass the full BLID locally:

```bash
uv run roomberto.py status --blid '<full-blid>'
uv run roomberto.py rooms --blid '<full-blid>'
```

The BLID is not persisted by this project.

## Removal

```bash
uv run roomberto.py delete-credentials
```

Then move this directory to Trash. No service, daemon, listener, or OpenClaw
configuration is installed.
