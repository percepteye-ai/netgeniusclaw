# Changes from the upstream work

Required by Apache License 2.0 §4(b): this is a modified redistribution and
these are the modifications.

**Upstream:** NetClaw — https://github.com/automateyournetwork/netclaw
**Imported from commit:** `0b4886e04ecddcca27a775727460ae36887f3542`
**Imported on:** 2026-08-27

## 1. Renamed to NetGeniusClaw

The product name was changed in prose and documentation only — 3,351
occurrences across 723 `.md` / `.html` files.

**Functional identifiers were deliberately NOT renamed**, because renaming them
changes behaviour rather than branding, and nothing in the licence requires it:

| Kept as-is | Why |
|---|---|
| `netclaw_tokens` | a Python package name; renaming breaks every import |
| `netclaw-mobile` | the iOS/Flutter project identifier |
| `netclaw-core`, `netclaw-edge1`, `netclaw-edge2` | container names the FRR lab and its scripts address |
| `scripts/netclaw` | the launcher path, and the `~/.local/bin` symlink |
| `#netclaw-*` | Slack channel names an operator configured |
| `netclaw.jpg` | an asset path |
| `automateyournetwork/netclaw` | the upstream URL — attribution, must not change |

The rename matched `netclaw` only where it stands alone as a product name,
never where it is part of a compound identifier.

## 2. Removed a GPLv3 component

`mcp-servers/zabbix-mcp/vendor/zabbix-mcp-server/` (18 files) was **GNU GPL
v3** inside an otherwise Apache-2.0 tree. GPLv3 and Apache 2.0 are one-way
compatible — Apache code may be taken into a GPL project, never the reverse —
so redistributing it under a blanket Apache 2.0 statement would have misstated
its licence.

Nothing functional was lost: the registered server runs
`zabbix_mcp_server.server` out of `mcp-servers/zabbix-mcp/.venv`, so the
vendored copy was never on the execution path. The venv installs it from
upstream, under its own licence, as before.

## 3. Completed the three.js attribution

`workspace/skills/threejs-network-viz/vendor/three/` (three.js r147) shipped
without the MIT **permission notice**, and two of its three files carried no
copyright notice at all. MIT requires both to travel with the code.

- Added `vendor/three/LICENSE` (MIT, © 2010-2022 three.js authors).
- Added the standard `@license` / SPDX header to `OrbitControls.js` and
  `GLTFLoader.js`. `core/three.js` already carried one.

Both files were syntax-checked after the edit.

## 4. History was not carried

This is a single import commit from the upstream working tree, not a history
fork. That is deliberate: a scan of all 747 upstream commits found a live-looking
lab credential (`CML_PASSWORD` for a private host, with its username) that had
been **removed from the working tree but remained in history**. Carrying the
history would have republished it.

No credential-shaped strings — OpenAI, Anthropic, GitHub, Slack, AWS, Google,
GitLab, npm, SendGrid keys, or PEM private keys — were found anywhere in the
747 commits. The only other literal was `YourPassword123`, a placeholder in a
spec document.

## What is NOT in this fork

The Percepteye agent-flywheel integration — the MCP outcome shim, the config
projection, the decision-rule grader — is **not** here. It is a separate body of
work that modifies no NetGeniusClaw source, and mixing an unrelated feature into
a licensing-and-rebrand import would make both harder to review.

The README still describes the agent as running on Anthropic Claude, which is
what upstream ships. Moving it to an open-weights model is a configuration
change made outside this tree.
