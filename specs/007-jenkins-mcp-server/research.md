# Research: Jenkins MCP Server Integration

**Feature**: 007-jenkins-mcp-server
**Date**: 2026-03-27

## R1: Jenkins MCP Plugin Architecture

**Decision**: Register the Jenkins MCP Server plugin as a remote MCP server in netgeniusclaw's config/openclaw.json. No local server.py is needed.

**Rationale**: The Jenkins MCP Server plugin (v0.158+) runs natively inside the Jenkins JVM as a Jenkins extension. It implements the MCP server protocol using the MCP Java SDK 0.17.2 (spec version 2025-06-18). The plugin exposes MCP endpoints directly on the Jenkins HTTP(S) server, so netgeniusclaw connects to it as a remote client rather than spawning a local process. This is architecturally different from most netgeniusclaw MCP servers (which run locally via stdio), but the MCP standard explicitly supports HTTP-based transports.

**Alternatives considered**:
- Writing a Python proxy MCP server that wraps Jenkins REST API: Rejected because the official plugin already implements MCP natively with richer semantics (e.g., parameterized build handling, folder-aware job resolution). A proxy would duplicate effort and lag behind the plugin's feature set.
- Using the Jenkins REST API directly without MCP: Violates Constitution V (MCP-Native Integration).

## R2: Transport Protocol Selection

**Decision**: Use Streamable HTTP transport at the endpoint `{JENKINS_URL}/mcp-server/mcp`.

**Rationale**: The Jenkins MCP plugin supports three transports:
1. **SSE** at `/mcp-server/sse` — Server-Sent Events, older MCP pattern
2. **Streamable HTTP** at `/mcp-server/mcp` — Current recommended MCP transport for AI agent usage
3. **Stateless** at `/mcp-server/stateless` — Single request/response, no session

Streamable HTTP is the recommended transport for MCP as of the 2025-06-18 spec revision. It supports bidirectional streaming within HTTP requests and is the most widely adopted transport across MCP clients.

**Alternatives considered**:
- SSE: Older pattern, being phased out in newer MCP spec versions. Works but not forward-looking.
- Stateless: Too limited — does not support streaming build logs or long-running tool calls.

## R3: Authentication Method

**Decision**: Use HTTP Basic Authentication with Jenkins API tokens. The credentials are Base64-encoded as `username:api_token` and sent in the `Authorization: Basic {base64}` header.

**Rationale**: This is the only authentication method supported by the Jenkins MCP plugin. Jenkins API tokens are the standard credential type for programmatic access — they are scoped to a user's permissions and can be revoked independently of the user's password. The credentials are read from environment variables `JENKINS_USERNAME` and `JENKINS_API_TOKEN` per Constitution XIII.

**Alternatives considered**:
- OAuth2: Not supported by the Jenkins MCP plugin.
- Session cookies: Not supported for MCP transport.

## R4: openclaw.json Registration Pattern

**Decision**: Register as a remote HTTP MCP server using the `url` field instead of the `command`/`args` pattern used by stdio servers.

**Rationale**: The existing MCP servers in openclaw.json all use the `command`/`args` pattern to spawn local processes. Jenkins is different — it's an already-running remote service. The openclaw.json format supports remote MCP servers via a `url` field pointing to the Streamable HTTP endpoint. The environment variables are interpolated at runtime.

**Registration format**:
```json
{
  "jenkins-mcp": {
    "url": "${JENKINS_URL}/mcp-server/mcp",
    "headers": {
      "Authorization": "Basic ${JENKINS_AUTH_BASE64}"
    },
    "env": {
      "JENKINS_URL": "${JENKINS_URL}",
      "JENKINS_AUTH_BASE64": "${JENKINS_AUTH_BASE64}"
    }
  }
}
```

Note: `JENKINS_AUTH_BASE64` is a convenience variable containing the Base64-encoded `username:token` string. The operator generates this from their Jenkins username and API token.

**Alternatives considered**:
- Spawning a local proxy process: Unnecessary complexity when direct HTTP connection works.
- Embedding username:token in URL: Would expose credentials in logs.

## R5: Jenkins Plugin Tool Inventory

**Decision**: Document all 16 tools provided by the Jenkins MCP plugin as-is. Do not subset or wrap them.

**Rationale**: The Jenkins MCP plugin provides a complete, well-designed tool set. Subsetting would reduce functionality without benefit. The tools are:

| Category | Tool | Description |
|----------|------|-------------|
| Job Management | getJob | Get details of a specific job by full name |
| Job Management | getJobs | List all jobs with pagination support |
| Job Management | triggerBuild | Trigger a build with optional parameters |
| Job Management | getQueueItem | Get details of a queued build request |
| Build Operations | getBuild | Get details of a specific build |
| Build Operations | updateBuild | Update build metadata (display name, keep flag) |
| Build Operations | getBuildLog | Retrieve build console output with pagination |
| Build Operations | searchBuildLog | Search build log by regex pattern |
| SCM Integration | getJobScm | Get SCM configuration for a job |
| SCM Integration | getBuildScm | Get SCM details for a specific build |
| SCM Integration | getBuildChangeSets | Get change sets (commits) for a build |
| SCM Integration | findJobsWithScmUrl | Find jobs using a specific SCM repository URL |
| System | whoAmI | Get authenticated user details |
| System | getStatus | Get Jenkins instance health status |
| Pipeline | getPipelineRuns | Get pipeline run history |
| Pipeline | getPipelineRunLog | Get pipeline run log output |

**Alternatives considered**:
- Creating custom wrapper tools: Would add maintenance burden and delay updates when the plugin adds new tools.
- Exposing only read-only tools: Would eliminate triggerBuild/updateBuild which are core to US2 (the #2 priority user story).

## R6: Skill Design

**Decision**: Create a single `jenkins-cicd` skill with workflows covering monitoring, build triggering, log analysis, and SCM tracking.

**Rationale**: Following Constitution VII (Skill Modularity), one focused skill handles all Jenkins CI/CD workflows. The skill documents:
1. Pre-flight checks (whoAmI, getStatus) for setup validation
2. Pipeline monitoring workflows (getJobs → getBuild)
3. Build triggering with human-in-the-loop confirmation
4. Build log troubleshooting (getBuildLog, searchBuildLog)
5. SCM change tracking (getBuildChangeSets, findJobsWithScmUrl)

**Alternatives considered**:
- Multiple skills (jenkins-monitor, jenkins-trigger, jenkins-logs): Fragments what is a cohesive CI/CD workflow. Constitution VII says single well-defined function — CI/CD pipeline management is that function.
- No skill (just register the MCP server): Would miss the operational workflow guidance that makes the tools useful in practice.

## R7: GAIT Audit Integration

**Decision**: GAIT logging handled at the skill level by invoking gait_mcp tools before and after Jenkins operations, following the same pattern as suzieq-observability.

**Rationale**: The MCP server runs remotely inside Jenkins and cannot be modified to add GAIT calls. Logging at the skill level ensures all operator-initiated Jenkins interactions are captured without requiring changes to the Jenkins plugin.

**Alternatives considered**:
- Embedding GAIT in a proxy: Would require a local proxy server, adding unnecessary complexity.
- Relying on Jenkins audit logs only: Would not integrate with netgeniusclaw's GAIT system.
