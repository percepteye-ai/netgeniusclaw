# Implementation Plan: Jenkins MCP Server Integration

**Branch**: `007-jenkins-mcp-server` | **Date**: 2026-03-27 | **Spec**: `specs/007-jenkins-mcp-server/spec.md`
**Input**: Feature specification from `/specs/007-jenkins-mcp-server/spec.md`

## Summary

Integrate the Jenkins MCP Server plugin into netgeniusclaw by registering the external Jenkins-hosted MCP endpoint in config/openclaw.json, creating the mcp-servers/jenkins-mcp/ directory with documentation, building a companion skill (workspace/skills/jenkins-cicd/) with operational workflows, and completing all artifact coherence items. Unlike most netgeniusclaw MCP servers that run locally via stdio, the Jenkins MCP server runs natively inside Jenkins via the official plugin, and netgeniusclaw connects to it over Streamable HTTP transport with Basic Auth. This is primarily a configuration, documentation, and skill-authoring integration — no server.py or Python code is written for the MCP server itself.

## Technical Context

**Language/Version**: N/A (no server code — Jenkins plugin is Java-based and runs inside Jenkins). Skill documentation and configuration files only.
**Primary Dependencies**: Jenkins 2.533+ with MCP Server plugin (v0.158+), MCP Java SDK 0.17.2
**Storage**: N/A (stateless — Jenkins maintains all job/build state)
**Testing**: Manual verification — confirm tool discovery and invocation against a running Jenkins instance
**Target Platform**: Jenkins instance accessible over HTTPS from the AI assistant host
**Project Type**: MCP server registration + skill authoring (configuration integration)
**Performance Goals**: Query responses within 5 seconds (per SC-001 through SC-004)
**Constraints**: Jenkins plugin must be pre-installed; netgeniusclaw has no control over the MCP server implementation
**Scale/Scope**: 16 tools exposed by Jenkins plugin across 4 tool categories (jobs, builds, SCM, system)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First Operations | PASS | Read operations (getJob, getBuild, getBuildLog, etc.) are observation-only. triggerBuild and updateBuild are write operations gated by human-in-the-loop (XIV). |
| II. Read-Before-Write | PASS | Skill workflow requires observing job/build state before triggering builds. |
| III. ITSM-Gated Changes | PASS | Build triggering can be coordinated with ServiceNow CRs via existing servicenow-mcp. Not required for read-only monitoring. |
| IV. Immutable Audit Trail | PASS | All Jenkins interactions logged to GAIT via skill-level gait_mcp integration (FR-011). |
| V. MCP-Native Integration | PASS | Jenkins plugin implements MCP server natively. NetGeniusClaw registers it as a remote MCP server via Streamable HTTP transport. |
| VI. Multi-Vendor Neutrality | PASS | Jenkins-specific logic stays in the Jenkins MCP server. Skills provide CI/CD workflows without vendor lock-in. |
| VII. Skill Modularity | PASS | Single skill (jenkins-cicd) with focused CI/CD operational workflows. |
| VIII. Verify After Every Change | PASS | Skill workflow includes post-trigger verification (check build status after triggering). |
| IX. Security by Default | PASS | Credentials (JENKINS_URL, JENKINS_USERNAME, JENKINS_API_TOKEN) from env vars only. Basic Auth over HTTPS. |
| X. Observability as First-Class | PASS | Health check (getStatus) and identity verification (whoAmI) tools available. Three.js HUD will be updated. |
| XI. Artifact Coherence | PENDING | Will be completed during implementation (README, install.sh, UI, SOUL.md, SKILL.md, .env.example, TOOLS.md, openclaw.json). |
| XII. Documentation-as-Code | PENDING | MCP server README and SKILL.md will be created during implementation. |
| XIII. Credential Safety | PASS | JENKINS_URL, JENKINS_USERNAME, JENKINS_API_TOKEN read from env vars. .env.example documents them without values. |
| XIV. Human-in-the-Loop | PASS | triggerBuild and updateBuild require explicit operator confirmation before execution. |
| XV. Backwards Compatibility | PASS | New MCP server in isolated directory. No changes to existing servers or skills. |
| XVI. Spec-Driven Development | PASS | Following full SDD workflow: specify -> clarify -> plan -> task -> implement. |

## Project Structure

### Documentation (this feature)

```text
specs/007-jenkins-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool reference)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
mcp-servers/jenkins-mcp/
└── README.md                    # MCP server documentation (tools, env vars, setup)

workspace/skills/jenkins-cicd/
└── SKILL.md                     # Skill documentation (workflows, tool usage, examples)
```

**Structure Decision**: No server.py is needed because the Jenkins MCP Server plugin runs natively inside Jenkins. The mcp-servers/jenkins-mcp/ directory contains only README.md documenting the integration. The companion skill in workspace/skills/jenkins-cicd/ provides operational workflows for CI/CD pipeline management.

## Complexity Tracking

> No constitution violations requiring justification. This is a lightweight configuration integration — no server code, no new Python dependencies, no data persistence. All principles satisfied by design.
