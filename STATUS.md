# Status

Updated: 2026-09-29

Phase: implementation

## Current

- Security review targets upstream `roombapy-prime` `v0.4.0`, immutable commit
  `8fce9139822886ab03aceb5a5787eb851cc0a095`.
- Runtime is isolated with `uv`; upstream optional `tools` extra is excluded.
- Local CLI supports Keychain setup, read-only robot discovery, state, and map
  room discovery. It exposes no mission-control or settings-write command.
- Local guardrail suite: `7 passed`. Upstream exact-commit suite: `1303 passed,
  1 skipped`. `pip-audit`: no known vulnerabilities. Bandit: no medium/high
  findings; only reviewed low-confidence/low-severity subprocess/assert noise.
- A nonsecret macOS Keychain write/read/delete canary passed.
- No iRobot credentials have been stored and no live account login has run.

## Next

1. Have JPop enter the iRobot account credentials locally into Keychain.
2. Run one read-only `discover` probe.
3. Resolve Roomberto's exact BLID and map/room IDs.
4. Ask separately before adding or running any robot-moving canary.
