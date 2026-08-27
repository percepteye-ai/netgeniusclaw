# Third-party software

Components with source included in this repository, and the licences that apply
to them. This repository as a whole is Apache License 2.0; the entries below are
**not**, and their own terms govern.

| Path | Component | Licence |
|---|---|---|
| `workspace/skills/threejs-network-viz/vendor/three/` | three.js r147 | MIT — © 2010-2022 three.js authors. Full text in that directory's `LICENSE`. |
| `ui/netclaw-visual/src/canvas-chat/` | canvas-chat | MIT — © 2026 Tech Built Right. Full text in that directory's `LICENSE`. |

## Removed

| Path | Component | Why |
|---|---|---|
| `mcp-servers/zabbix-mcp/vendor/zabbix-mcp-server/` | zabbix-mcp-server | **GPLv3**, incompatible with redistribution under Apache 2.0. Installed from upstream into a venv at runtime instead. See `CHANGES.md` §2. |

## Not included as source

The ~100 MCP integrations are invoked as separate processes — `npx`, `uvx`,
`docker`, or a per-server venv — and their code is not redistributed here. Each
is obtained from its own publisher under its own licence at install time.

## Known gap

There are no `SPDX-License-Identifier` headers on this project's own files,
inherited from upstream. Every licence audit is therefore a manual one.
