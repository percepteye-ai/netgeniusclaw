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

No credential-shaped strings — OpenAI, the model provider, GitHub, Slack, AWS, Google,
GitLab, npm, SendGrid keys, or PEM private keys — were found anywhere in the
747 commits. The only other literal was `YourPassword123`, a placeholder in a
spec document.

## 5. Open weights, and no hosted-vendor dependency anywhere

Upstream ran on a hosted vendor's flagship model by default, and several
components called that vendor's API directly. This fork runs on a **local,
OpenAI-compatible model server** and has no hosted-vendor dependency left in it.

### Configuration

`config/openclaw.json`: added `models.providers.local`
(`api: "openai-completions"`, vLLM's default base URL); `primary` →
`local/qwen/qwen3.5-4b`; added the matching `agents.defaults.models` allow-list
entry, without which the agent rejects the model and refuses every turn
(`scripts/in2n-member-home.py`); **removed the vendor fallback**, which was a
silent escape hatch back to a hosted provider the moment the local endpoint
hiccups.

### Code that actually called a vendor API

| Where | Was | Now |
|---|---|---|
| `src/netclaw_tokens/counter.py` | the vendor SDK's `count_tokens` | the **serving model's own** `/tokenize` (vLLM/SGLang), stdlib only |
| `src/netclaw_tokens/cost_calculator.py` | a hosted price list; unknown models billed at the flagship rate | **zero by default** — the truth for a model you host — with `NETCLAW_TOKEN_PRICING_OVERRIDE` for endpoints that bill |
| `mcp-servers/twilio-voice-mcp/webhook_server.py` | vendor `/v1/messages`, incl. a tool-use loop | OpenAI chat-completions, tool loop converted to `tool_calls` / `role:"tool"` |
| `mcp-servers/twitter-mcp/server.py` | vendor `/v1/messages` | OpenAI chat-completions |
| `scripts/in2n-member-home.py` | registered a direct vendor provider per member claw | registers the local OpenAI-compatible provider |
| `scripts/probe-mist-mcp.py` | vendor `count_tokens` endpoint | the model server's `/tokenize` |
| `tests/{fortinet,bgp-intel}/test_manifest_size.py` | vendor SDK for the budget ceiling | the shared counter, **keeping** the deliberately pessimistic `len/3.4` fallback so a budget check never guesses low |
| `src/netclaw_tokens/requirements.txt` | `anthropic>=0.40.0` | **dependency removed**, nothing added |

The counter change is a correctness fix, not only a branding one. Calling one
vendor's tokenizer to count tokens for a model that vendor does not serve
returned an exact number from the **wrong tokenizer** — worse than an estimate,
because it does not announce itself as approximate. Seven tests cover the new
path (`tests/test_token_counter.py`); the 44 existing token-library tests still
pass.

### Egress and installer

The DefenseClaw sandbox allowlist and `netclaw-secure-start.sh` no longer punch
a hole to a vendor domain — a loopback model server needs no outbound rule at
all. `scripts/setup.sh` prompts for a model base URL instead of a vendor key,
and `.env.example` documents `NETGENIUSCLAW_MODEL_BASE_URL` /
`_API_KEY` / `NETGENIUSCLAW_MODEL`.

### Also fixed in passing

`mcp-servers/twitter-mcp/server.py` hardcoded the **upstream author's personal
Twitter handle** into the agent's system prompt, so the agent introduced itself
to strangers as a specific real person unconnected to this deployment. It now
reads `TWITTER_HANDLE` and omits the handle when unset.

### `CLAUDE.md` → `DEVELOPMENT.md`

Renamed after checking what OpenClaw actually does with it, rather than
assuming. Two facts settled it:

- `loadContextFileFromDir` tries `AGENTS.md`, `AGENTS.MD`, `CLAUDE.md`,
  `CLAUDE.MD` and takes the **first that exists**. This repo has `AGENTS.md` at
  its root, so `CLAUDE.md` was **already shadowed and never loaded as agent
  context**. Removing it changes nothing at runtime.
- The file was never agent context anyway. It is Spec Kit's generated
  *development* guidelines — Active Technologies, Project Structure, Commands,
  Code Style, Recent Changes — written for someone working ON the repo. Folding
  it into `AGENTS.md` would have been the wrong move twice over: wrong audience,
  and 236 lines of build metadata taxing every conversation, since `AGENTS.md`
  is the bootstrap file re-injected after every compaction
  (`AGENTS_BOOTSTRAP_FILENAME`).

`.specify/scripts/bash/update-agent-context.sh` now writes `DEVELOPMENT.md`
under a `dev` target, and 28 files referencing the old name were updated.

### What was deliberately NOT renamed

**Third-party names that must resolve.** `@anthropic-ai/microsoft-graph-mcp`
— and `scripts/check-package-references.py` exists precisely to record that this
package **404s**, so renaming it destroys the finding — plus `anthropics/skills`
and `opsmill/claude-marketplace`. A renamed dependency points at nothing.

**`docs/ietf/`.** `draft-capobianco-ncfed-00` is a submitted IETF
Internet-Draft. Editing a published standards document to say something it does
not say is not a rename. A bulk pass garbled it and it was restored verbatim.

**`.gitignore`'s `.claude` entry**, which stops a contributor's local tooling
directory being committed. Removing it causes the thing it prevents.

## 6. The agent flywheel, integrated

`percepteye/` adds continual learning: tool outcomes are observed at the MCP
transport as `ok` / `failed` / **`unknown`**, the agent's decisions are graded
against this repo's own `AGENTS.md` safety rules, and a trained policy can be
applied back to `config/openclaw.json`.

It **modifies no existing source**. The projection opens `config/openclaw.json`
read-only and writes a derived copy into the rollout's own directory; the
customer's config is never touched. Everything new lives under `percepteye/`.

One piece is knowingly out of place: `percepteye/mcp_shim.py` belongs in the SDK
as `percepteye_agent_flywheel.mcp_shim` and is written to move there unchanged.
It is vendored here so this repo has a working integration in the meantime, and
its docstring says so — it already *depends* on the SDK for `record_tool_call`,
so this duplicates a file, not a contract.

Two defects were found by the tests written alongside it, and both are recorded
in the suite: the shim deadlocked on stdin EOF, hanging every rollout to its full
deadline; and the decision rules scored an agent that did **nothing** at 1.00,
because two "absence of bad behaviour" rules passed with no opportunity to
misbehave. 37 tests, both modules mutation-tested.

## Note on the order these landed

§1-§4 were the licensing-and-rebrand import and went in first, on their own.
§5 (open weights) and §6 (the flywheel) followed as separate commits, so each is
reviewable without the others. The flywheel was deliberately held back from the
import for exactly that reason; it is in now, under `percepteye/`, and adds no
change to any file that existed before it.
