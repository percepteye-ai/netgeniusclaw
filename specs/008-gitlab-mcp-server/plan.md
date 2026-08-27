# Implementation Plan: GitLab MCP Server Integration

**Branch**: `008-gitlab-mcp-server` | **Date**: 2026-03-27 | **Spec**: `specs/008-gitlab-mcp-server/spec.md`
**Input**: Feature specification from `/specs/008-gitlab-mcp-server/spec.md`

## Summary

Integrate the community GitLab MCP server (@zereight/mcp-gitlab) into netgeniusclaw by registering it as a locally-spawned MCP server in config/openclaw.json, creating the mcp-servers/gitlab-mcp/ directory with documentation, building a companion skill (workspace/skills/gitlab-devops/) with operational workflows, and completing all artifact coherence items. The community server is a TypeScript/Node.js application that runs locally via stdio transport and communicates with any GitLab instance (gitlab.com or self-hosted) via the GitLab REST API using a Personal Access Token. It exposes 98+ tools covering issues, merge requests, pipelines, repositories, wikis, labels, milestones, and releases.

## Technical Context

**Language/Version**: TypeScript/Node.js (community MCP server). No netclaw-authored server code — configuration and skill documentation only.
**Primary Dependencies**: @zereight/mcp-gitlab (npm package), Node.js 18+
**Storage**: N/A (stateless proxy to GitLab REST API)
**Testing**: Manual verification — confirm tool discovery and invocation against a GitLab instance
**Target Platform**: Linux/macOS with Node.js 18+ installed
**Project Type**: MCP server registration + skill authoring (configuration integration)
**Performance Goals**: Query responses within 5 seconds (per SC-001 through SC-005)
**Constraints**: Requires Node.js 18+ runtime; GitLab instance must be accessible via HTTPS
**Scale/Scope**: 98+ tools exposed across issues, MRs, pipelines, repos, wikis, labels, milestones, releases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | PASS | Read operations are observation-only. Write operations (create issue, create MR, pipeline control) gated by human-in-the-loop (XIV). Read-only mode available via GITLAB_READ_ONLY_MODE env var. |
| II. Read-Before-Write | PASS | Skill workflow requires observing current state before making changes. |
| III. ITSM-Gated Changes | PASS | Issue/MR creation can be coordinated with ServiceNow CRs via existing servicenow-mcp. Not required for read-only operations. |
| IV. Immutable Audit Trail | PASS | All GitLab interactions logged to GAIT via skill-level gait_mcp integration (FR-016). |
| V. MCP-Native Integration | PASS | Community server implements MCP natively via stdio transport. |
| VI. Multi-Vendor Neutrality | PASS | GitLab-specific logic stays in the GitLab MCP server. Skills provide DevOps workflows without vendor lock-in. |
| VII. Skill Modularity | PASS | Single skill (gitlab-devops) with focused DevOps workflows. |
| VIII. Verify After Every Change | PASS | Skill workflow includes post-change verification (verify issue/MR creation, check pipeline status after trigger). |
| IX. Security by Default | PASS | Credentials (GITLAB_PERSONAL_ACCESS_TOKEN) from env vars only. PAT with minimal required scopes. |
| X. Observability as First-Class | PASS | Pipeline monitoring and health checks built into the tool set. Three.js HUD will be updated. |
| XI. Artifact Coherence | PENDING | Will be completed during implementation. |
| XII. Documentation-as-Code | PENDING | MCP server README and SKILL.md will be created during implementation. |
| XIII. Credential Safety | PASS | GITLAB_PERSONAL_ACCESS_TOKEN and GITLAB_API_URL read from env vars. .env.example documents them without values. |
| XIV. Human-in-the-Loop | PASS | Write operations (create issue, create MR, pipeline cancel/retry) require explicit operator confirmation. |
| XV. Backwards Compatibility | PASS | New MCP server in isolated directory. Node.js dependency does not conflict with existing Python servers. |
| XVI. Spec-Driven Development | PASS | Following full SDD workflow. |

## Project Structure

### Documentation (this feature)

```text
specs/008-gitlab-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool reference)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
mcp-servers/gitlab-mcp/
└── README.md                     # MCP server documentation (tools, env vars, setup)

workspace/skills/gitlab-devops/
└── SKILL.md                      # Skill documentation (workflows, tool usage, examples)
```

**Structure Decision**: No server code is authored by netgeniusclaw. The community @zereight/mcp-gitlab package is installed via npm and spawned as a local process. The mcp-servers/gitlab-mcp/ directory contains only README.md documenting the integration. The companion skill provides operational workflows for DevOps pipeline and project management.

## Complexity Tracking

> No constitution violations requiring justification. This is a configuration integration using a community Node.js MCP server. All principles satisfied by design.
