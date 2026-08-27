# Research: GitLab MCP Server Integration

**Feature**: 008-gitlab-mcp-server
**Date**: 2026-03-27

## R1: Community vs Official GitLab MCP Server

**Decision**: Use the community @zereight/mcp-gitlab package as the primary integration.

**Rationale**: Two options were evaluated:
- **Official GitLab MCP** (beta): OAuth 2.0 auth, HTTP transport at `/api/v4/mcp`, requires Premium/Ultimate tier. Limited to GitLab-hosted instances with subscription.
- **Community @zereight/mcp-gitlab**: 98+ tools, TypeScript/Node.js, stdio/SSE/HTTP transport, PAT or OAuth auth, 1.3k+ stars, 81 contributors, MIT license.

The community server is preferred because: (1) it works with any GitLab tier including free/self-hosted, (2) it supports PAT auth which is simpler and more widely available, (3) it has far more comprehensive tool coverage (98+ vs limited beta set), (4) it uses stdio transport consistent with most netgeniusclaw MCP servers, and (5) it is actively maintained with frequent releases.

**Alternatives considered**:
- Official GitLab MCP server: Rejected as primary target due to Premium/Ultimate tier requirement, beta status, and HTTP-only transport. Documented as alternative in README for teams with GitLab Premium.
- Building a custom Python MCP server wrapping GitLab API: Rejected — the community server already provides comprehensive coverage. Writing from scratch would duplicate effort.

## R2: Transport Protocol

**Decision**: Use stdio transport (default) by spawning the community server as a local Node.js process via `npx`.

**Rationale**: Stdio transport is consistent with the majority of netgeniusclaw MCP servers (suzieq-mcp, batfish-mcp, gnmi-mcp, etc.) and is the simplest configuration. The community server supports stdio natively via `npx @zereight/mcp-gitlab`. SSE and HTTP transports are available but not needed for single-user deployments.

**Alternatives considered**:
- SSE transport: More complex setup, suited for shared/multi-user deployments. Not needed for standard netgeniusclaw usage.
- HTTP Streamable: Available but adds network layer complexity vs local stdio.

## R3: Authentication

**Decision**: Use GitLab Personal Access Token (PAT) via the `GITLAB_PERSONAL_ACCESS_TOKEN` environment variable.

**Rationale**: PATs are the most widely available authentication method across all GitLab tiers (Free, Premium, Ultimate) and deployment types (gitlab.com, self-hosted). The community server reads the token from the `GITLAB_PERSONAL_ACCESS_TOKEN` env var. Required PAT scopes depend on operations: `read_api` for read-only, `api` for full access including write operations.

**Alternatives considered**:
- OAuth 2.0: Supported by the community server but requires app registration in GitLab and is more complex to configure. Better for multi-user deployments.
- Deploy token: Read-only, limited scope — insufficient for write operations (US4).

## R4: openclaw.json Registration

**Decision**: Register as a stdio MCP server using `npx` to run the community package.

**Registration format**:
```json
{
  "gitlab-mcp": {
    "command": "npx",
    "args": ["-y", "@zereight/mcp-gitlab"],
    "env": {
      "GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_PERSONAL_ACCESS_TOKEN}",
      "GITLAB_API_URL": "${GITLAB_API_URL:-https://gitlab.com}"
    }
  }
}
```

**Rationale**: Using `npx -y` ensures the package is auto-installed if not present, similar to how other Node.js MCP servers are registered. The `GITLAB_API_URL` defaults to gitlab.com for SaaS users but can be overridden for self-hosted instances.

**Alternatives considered**:
- Global npm install + direct node invocation: More fragile, requires separate install step.
- Docker container: Adds container runtime dependency.

## R5: Read-Only Mode

**Decision**: Support a `GITLAB_READ_ONLY_MODE` environment variable to restrict the integration to observation-only operations.

**Rationale**: FR-021 requires a read-only mode. The community server does not natively support this, but the skill documentation can enforce it by instructing the AI to skip write tools when this mode is enabled. The env var is checked at the skill level.

**Alternatives considered**:
- PAT scope restriction: Using `read_api` scope on the PAT effectively prevents writes, but error messages from denied writes may be confusing.
- Server-side filtering: Would require forking the community server.

## R6: Tool Categories

**Decision**: Organize the 98+ tools into the following categories for documentation and skill workflows:

| Category | Key Tools | Spec Story |
|----------|-----------|-----------|
| Issues | list_issues, get_issue, create_issue, update_issue, add_issue_comment | US1, US4 |
| Merge Requests | list_merge_requests, get_merge_request, create_merge_request, update_merge_request, merge_merge_request | US1, US4 |
| Pipelines | list_pipelines, get_pipeline, get_pipeline_jobs, get_pipeline_job_log, create_pipeline, retry_pipeline, cancel_pipeline | US2 |
| Repository | list_repository_tree, get_file_content, get_commit, list_commits, compare_branches | US3 |
| Projects | list_projects, get_project, search_projects | All |
| Labels | list_labels, create_label, update_label, delete_label | US5 |
| Milestones | list_milestones, create_milestone, update_milestone | US5 |
| Releases | list_releases, get_release, create_release | US5 |
| Wiki | list_wiki_pages, get_wiki_page, create_wiki_page, update_wiki_page | FR-014 |

**Rationale**: This grouping aligns with the spec's user stories and makes the skill workflows easy to navigate.

## R7: GAIT Audit Integration

**Decision**: GAIT logging at the skill level via gait_mcp tools, consistent with all other netgeniusclaw MCP integrations.

**Rationale**: The community MCP server cannot be modified to add GAIT calls. Skill-level logging captures all operator-initiated interactions.

## R8: Self-Hosted GitLab Support

**Decision**: Support self-hosted GitLab instances via the `GITLAB_API_URL` environment variable, defaulting to `https://gitlab.com`.

**Rationale**: FR-018 requires support for both SaaS and self-hosted. The community server accepts a configurable API URL. For self-hosted instances with self-signed TLS certificates, the `NODE_TLS_REJECT_UNAUTHORIZED=0` environment variable can be set (documented with security warning).

**Alternatives considered**:
- Only supporting gitlab.com: Would exclude enterprise self-hosted deployments common in network engineering teams.
