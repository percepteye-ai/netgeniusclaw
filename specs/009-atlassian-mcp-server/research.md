# Research: Atlassian MCP Server Integration

**Feature**: 009-atlassian-mcp-server
**Date**: 2026-03-27

## R1: Community vs Official Atlassian MCP Server

**Decision**: Use the community mcp-atlassian package (by sooperset) as the primary integration.

**Rationale**: Two options were evaluated:
- **Official Atlassian Rovo MCP Server**: Remote cloud MCP at `mcp.atlassian.com`, OAuth 2.1, Jira + Confluence + Compass. Cloud-only, requires Atlassian Intelligence subscription.
- **Community mcp-atlassian**: 72 tools, Python, stdio/SSE transport, Cloud + Server/Data Center support, API token/PAT auth, 4.7k+ stars, 118 contributors, Apache 2.0 license.

The community server is preferred because: (1) it supports both Cloud and Server/Data Center deployments — critical for enterprise network teams that commonly run self-hosted Atlassian, (2) it uses Python consistent with netgeniusclaw's primary stack, (3) it supports simple API token auth without OAuth app registration, (4) it has comprehensive tool coverage (72 tools), and (5) it is the most actively maintained Atlassian MCP server.

**Alternatives considered**:
- Official Atlassian Rovo MCP: Rejected as primary target — Cloud-only, requires Atlassian Intelligence subscription, limited to OAuth 2.1 which requires app registration. Documented as alternative for Cloud-only teams.
- Building a custom Python MCP server wrapping Atlassian APIs: Rejected — the community server already provides comprehensive, well-tested coverage.

## R2: Transport Protocol

**Decision**: Use stdio transport (default) by spawning the community server as a local Python process via `uvx`.

**Rationale**: Stdio transport is consistent with the majority of netgeniusclaw MCP servers. The community server supports stdio natively via `uvx mcp-atlassian`. This uses uv's package runner to auto-install and execute the package. SSE transport is also available but not needed for single-user deployments.

**Alternatives considered**:
- SSE transport: More complex, suited for shared/multi-user deployments.
- Docker: Available but adds container runtime dependency.
- pip install + direct python: Less portable than uvx which handles virtual environments.

## R3: Authentication — Atlassian Cloud

**Decision**: Use API tokens generated from Atlassian account settings, passed via `JIRA_API_TOKEN` and `CONFLUENCE_API_TOKEN` environment variables alongside the account email as username.

**Rationale**: API tokens are the standard programmatic access method for Atlassian Cloud. The community server reads credentials from env vars. For Cloud, both Jira and Confluence share the same Atlassian account, so typically `JIRA_USERNAME` and `CONFLUENCE_USERNAME` are the same email address, and `JIRA_API_TOKEN` and `CONFLUENCE_API_TOKEN` are the same token.

**Alternatives considered**:
- OAuth 2.0: Supported but requires creating an Atlassian developer app and configuring callback URLs — excessive for single-user CLI usage.
- Basic auth with password: Deprecated by Atlassian for Cloud.

## R4: Authentication — Server/Data Center

**Decision**: Use Personal Access Tokens (PATs) for Jira/Confluence Server and Data Center deployments.

**Rationale**: PATs are the recommended auth method for Jira Server 8.14+ and Confluence Data Center. They are scoped and revocable. The community server supports PATs via the same env vars used for Cloud tokens.

**Alternatives considered**:
- Basic auth with password: Still works on Server/DC but less secure than PATs.
- OAuth 1.0a: Legacy Atlassian auth method — more complex and being deprecated.

## R5: openclaw.json Registration

**Decision**: Register as a stdio MCP server using `uvx` to run the community package.

**Registration format**:
```json
{
  "atlassian-mcp": {
    "command": "uvx",
    "args": ["mcp-atlassian"],
    "env": {
      "JIRA_URL": "${JIRA_URL}",
      "JIRA_USERNAME": "${JIRA_USERNAME}",
      "JIRA_API_TOKEN": "${JIRA_API_TOKEN}",
      "CONFLUENCE_URL": "${CONFLUENCE_URL}",
      "CONFLUENCE_USERNAME": "${CONFLUENCE_USERNAME}",
      "CONFLUENCE_API_TOKEN": "${CONFLUENCE_API_TOKEN}"
    }
  }
}
```

**Rationale**: Using `uvx` (uv package executor) auto-installs the package in an isolated environment, consistent with modern Python MCP server deployment patterns. The env vars support independent Jira and Confluence configurations to handle cases where they are at different URLs (Server/DC) or only one product is available.

**Alternatives considered**:
- pip install + python -m: Requires manual installation step and risks dependency conflicts.
- Docker: Adds container runtime dependency.

## R6: Graceful Degradation (Jira-only or Confluence-only)

**Decision**: If only Jira or only Confluence environment variables are set, the integration degrades gracefully — tools for the unconfigured product are not exposed or return "not configured" messages.

**Rationale**: Per the spec assumption, some Atlassian instances may only have one product available. The community server handles this by checking which credentials are provided at startup.

## R7: Skill Design

**Decision**: Create a single `atlassian-itsm` skill covering both Jira issue tracking and Confluence documentation workflows.

**Rationale**: Jira and Confluence are used together in ITSM workflows — an incident logged in Jira often references a runbook in Confluence, and a postmortem page in Confluence links back to the Jira ticket. Splitting into two skills would fragment this natural workflow. The skill name "atlassian-itsm" reflects its primary use in IT Service Management workflows, aligning with Constitution III (ITSM-Gated Changes).

**Alternatives considered**:
- Two skills (jira-tracking, confluence-docs): Fragments the workflow. An operator creating an incident in Jira and writing a postmortem in Confluence should use one skill.
- Generic name "atlassian-devops": ITSM is more accurate for the network operations focus.

## R8: GAIT Audit Integration

**Decision**: GAIT logging at the skill level via gait_mcp tools, consistent with all other netgeniusclaw MCP integrations.

**Rationale**: The community MCP server cannot be modified to add GAIT calls. Skill-level logging captures all operator-initiated interactions.

## R9: Jira Custom Fields and Workflows

**Decision**: The integration queries available transitions and fields dynamically per project rather than assuming a fixed schema.

**Rationale**: Jira workflows and custom fields vary dramatically between projects and instances. The community server handles this by querying the Jira REST API for available transitions before attempting state changes, and by supporting arbitrary custom field values in create/update operations.
