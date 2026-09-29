# Log

## 2026-09-29

- Started after direct `roombapy-prime` Combo 105 support was identified.
- Audited stable `v0.4.0`; pinned its verified commit rather than a moving branch.
- Added an isolated, read-only adapter and macOS Keychain credential boundary.
- Replaced the planned Keychain copy with runtime-only reads from JPop's
  `Irobot - Roomberto` item in the Sean 1Password vault.
- Live read-only discovery authenticated successfully and identified one Prime
  robot named Roomberto, SKU `Q311020`, with the BLID redacted.
- JPop requested a live launch: one `start` publish was transport-acknowledged,
  and JPop confirmed Roomberto physically launched. JPop then requested home:
  one `dock` publish was transport-acknowledged. No retry was sent.
