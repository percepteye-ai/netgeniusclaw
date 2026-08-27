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

## 5. Open weights by default

Upstream defaults to `anthropic/claude-opus-4-6` with a Claude fallback, and its
README describes the agent as running on Anthropic Claude. This fork defaults to
a **local, OpenAI-compatible model server** instead.

`config/openclaw.json`:

- added `models.providers.local` — `api: "openai-completions"`,
  `baseUrl: http://127.0.0.1:8000/v1` (vLLM's default);
- `agents.defaults.model.primary` → `local/qwen/qwen3.5-4b`;
- added the matching `agents.defaults.models` allow-list entry, without which
  the agent rejects the model and refuses every turn
  (`scripts/in2n-member-home.py:74-76`);
- **removed the Anthropic fallback.** A fallback is a silent escape hatch back
  to a hosted provider the moment the local endpoint hiccups.

Documentation was changed to match, not ahead of, the config: the hero line, the
onboarding step, the "What It Does" sentence, the requirements list, and a new
**Model runtime** section covering vLLM / LM Studio / SGLang.

Two upstream statements were deliberately **left alone because they are true**:

- The token tracker really does call Anthropic's `count_tokens()`
  (`src/netclaw_tokens/counter.py`, with `anthropic>=0.40.0` a hard dependency
  of that library). Rather than delete the claim, the consequence is now stated:
  on an open-weights model it falls back to local estimation against a
  Claude-shaped tokenizer, so counts are approximate.
- Everything under `specs/` still refers to Claude. Those are historical design
  records of work as it was actually done; rewriting them would falsify the
  project's own history.

Two traps are documented in the new section because both produce a config that
looks correct and does not work: **Ollama's `/v1` breaks tool calling** (OpenClaw
drives Ollama over native `/api/chat`), and **`${VAR:-default}` has no meaning
here** — OpenClaw substitutes with `replace(/\$\{([^}]+)\}/g, ...)`, so the
entire contents become the variable name.

## What is NOT in this fork

The Percepteye agent-flywheel integration — the MCP outcome shim, the config
projection, the decision-rule grader — is **not** here. It is a separate body of
work that modifies no NetGeniusClaw source, and mixing an unrelated feature into
a licensing-and-rebrand import would make both harder to review.

The README still describes the agent as running on Anthropic Claude, which is
what upstream ships. Moving it to an open-weights model is a configuration
change made outside this tree.
