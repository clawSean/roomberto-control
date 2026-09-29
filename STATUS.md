# Status

Updated: 2026-09-29

Phase: implementation

## Current

- Security review targets upstream `roombapy-prime` `v0.4.0`, immutable commit
  `8fce9139822886ab03aceb5a5787eb851cc0a095`.
- Runtime is isolated with `uv`; upstream optional `tools` extra is excluded.
- Local CLI reads credentials from 1Password at runtime and supports read-only
  robot discovery, state, and map room discovery. It exposes no
  mission-control or settings-write command.
- Local guardrail suite: `7 passed`. Upstream exact-commit suite: `1303 passed,
  1 skipped`. `pip-audit`: no known vulnerabilities. Bandit: no medium/high
  findings; only reviewed low-confidence/low-severity subprocess/assert noise.
- JPop created the `Irobot - Roomberto` Login item in the `Sean` vault. Its
  field metadata was verified without reading or displaying values.
- First live read-only account discovery passed: one Prime-generation robot,
  name `Roomberto`, SKU `Q311020`; BLID was redacted in output. No robot
  connection or device command occurred.

## Next

1. Read current state and resolve map/room IDs through one bounded read-only
   inspection session.
2. Ask separately before adding or running any robot-moving canary.
