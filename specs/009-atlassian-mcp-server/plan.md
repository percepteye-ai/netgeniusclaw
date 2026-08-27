# Implementation Plan: Atlassian MCP Server Integration

**Branch**: `009-atlassian-mcp-server` | **Date**: 2026-03-27 | **Spec**: `specs/009-atlassian-mcp-server/spec.md`
**Input**: Feature specification from `/specs/009-atlassian-mcp-server/spec.md`

## Summary

Integrate the community Atlassian MCP server (mcp-atlassian by sooperset) into netgeniusclaw by registering it as a locally-spawned MCP server in config/openclaw.json, creating the mcp-servers/atlassian-mcp/ directory with documentation, building a companion skill (workspace/skills/atlassian-itsm/) with operational workflows for Jira issue tracking and Confluence documentation, and completing all artifact coherence items. The community server is a Python application that runs locally via stdio transport and communicates with Atlassian Cloud or Server/Data Center instances via the REST API. It exposes 72 tools covering Jira issues, Confluence pages, comments, transitions, labels, and cross-product linking.

## Technical Context

**Language/Version**: Python 3.10+ (community MCP server). No netclaw-authored server code — configuration and skill documentation only.
**Primary Dependencies**: mcp-atlassian (pip package), Python 3.10+
**Storage**: N/A (stateless proxy to Atlassian REST APIs)
**Testing**: Manual verification — confirm tool discovery and invocation against Jira and Confluence
**Target Platform**: Linux/macOS with Python 3.10+ installed
**Project Type**: MCP server registration + skill authoring (configuration integration)
**Performance Goals**: Query responses within 5 seconds (per SC-001 through SC-004); bulk operations within 30 seconds (SC-005)
**Constraints**: Requires either Atlassian Cloud API token or Server/DC Personal Access Token
**Scale/Scope**: 72 tools exposed across Jira and Confluence (issues, pages, comments, transitions, labels, links)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | PASS | Read operations are observation-only. Write operations (create issue, create page, transitions) gated by human-in-the-loop (XIV). |
| II. Read-Before-Write | PASS | Skill workflow requires observing current state before making changes. |
| III. ITSM-Gated Changes | PASS | Jira issue creation and transitions directly support ITSM workflows. Can be coordinated with ServiceNow CRs. |
| IV. Immutable Audit Trail | PASS | All Atlassian interactions logged to GAIT via skill-level gait_mcp integration (FR-014). |
| V. MCP-Native Integration | PASS | Community server implements MCP natively via stdio transport. |
| VI. Multi-Vendor Neutrality | PASS | Atlassian-specific logic stays in the Atlassian MCP server. Skills provide ITSM workflows without vendor lock-in. |
| VII. Skill Modularity | PASS | Single skill (atlassian-itsm) with focused issue tracking and documentation workflows. |
| VIII. Verify After Every Change | PASS | Skill workflow includes post-change verification (verify issue creation, confirm page updates). |
| IX. Security by Default | PASS | Credentials from env vars only. API tokens with appropriate permissions. |
| X. Observability as First-Class | PASS | Issue and page status monitoring built into tool set. Three.js HUD will be updated. |
| XI. Artifact Coherence | PENDING | Will be completed during implementation. |
| XII. Documentation-as-Code | PENDING | MCP server README and SKILL.md will be created during implementation. |
| XIII. Credential Safety | PASS | JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN, CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN read from env vars. .env.example documents them without values. |
| XIV. Human-in-the-Loop | PASS | Write operations (create issue, create page, transitions, comments) require explicit operator confirmation. |
| XV. Backwards Compatibility | PASS | New MCP server in isolated directory. Python dependencies isolated via pip. |
| XVI. Spec-Driven Development | PASS | Following full SDD workflow. |

## Project Structure

### Documentation (this feature)

```text
specs/009-atlassian-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool reference)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
mcp-servers/atlassian-mcp/
└── README.md                      # MCP server documentation (tools, env vars, setup)

workspace/skills/atlassian-itsm/
└── SKILL.md                       # Skill documentation (workflows, tool usage, examples)
```

**Structure Decision**: No server code is authored by netgeniusclaw. The community mcp-atlassian package is installed via pip/uvx and spawned as a local process. The mcp-servers/atlassian-mcp/ directory contains only README.md documenting the integration. The companion skill provides operational workflows for ITSM issue tracking and Confluence documentation management.

## Complexity Tracking

> No constitution violations requiring justification. This is a configuration integration using a community Python MCP server consistent with netgeniusclaw's Python stack. All principles satisfied by design.
