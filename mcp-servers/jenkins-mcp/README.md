# Jenkins MCP Server

**Server**: Jenkins MCP Server Plugin (official)
**Version**: v0.158+
**Language**: Java (runs inside Jenkins JVM)
**License**: MIT
**Transport**: Streamable HTTP at `/mcp-server/mcp`
**Tools**: 16 tools across 5 categories

## Overview

The Jenkins MCP Server is an official Jenkins plugin that implements the Model Context Protocol (MCP) server-side specification, enabling Jenkins to act as an MCP server. The plugin runs natively inside the Jenkins JVM — netgeniusclaw connects to it as a remote HTTP client rather than spawning a local process. This is architecturally different from most netgeniusclaw MCP servers (which use local stdio transport).

The plugin is built on the MCP Java SDK 0.17.2 (spec version 2025-06-18) and exposes Jenkins CI/CD functionality through 16 well-defined tools.

**Plugin URL**: https://plugins.jenkins.io/mcp-server/

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JENKINS_URL` | Yes | Base URL of the Jenkins instance (e.g., `https://jenkins.example.com`) |
| `JENKINS_USERNAME` | Yes | Jenkins username for authentication |
| `JENKINS_API_TOKEN` | Yes | Jenkins API token (generated from User → Configure → API Token) |
| `JENKINS_AUTH_BASE64` | Yes | Base64-encoded `username:api_token` string for HTTP Basic Auth |

### Generating JENKINS_AUTH_BASE64

The `JENKINS_AUTH_BASE64` variable contains the Base64-encoded credentials used for HTTP Basic Authentication:

```bash
# Generate from username and API token
export JENKINS_AUTH_BASE64=$(echo -n "${JENKINS_USERNAME}:${JENKINS_API_TOKEN}" | base64)

# Or set directly
export JENKINS_AUTH_BASE64="dXNlcm5hbWU6YXBpLXRva2Vu"  # base64 of "username:api-token"
```

## Authentication

The Jenkins MCP plugin uses HTTP Basic Authentication. All requests must include an `Authorization` header with Base64-encoded `username:api_token` credentials.

1. Log in to Jenkins as the user account you want to use for MCP access.
2. Navigate to **User → Configure → API Token**.
3. Click **Add new Token**, give it a descriptive name (e.g., `netclaw-mcp`), and click **Generate**.
4. Copy the token immediately — it will not be shown again.
5. Set environment variables:
   ```bash
   export JENKINS_URL="https://jenkins.example.com"
   export JENKINS_USERNAME="your-username"
   export JENKINS_API_TOKEN="your-api-token"
   export JENKINS_AUTH_BASE64=$(echo -n "${JENKINS_USERNAME}:${JENKINS_API_TOKEN}" | base64)
   ```

**Important**: The API token inherits the permissions of the Jenkins user. Ensure the user has appropriate permissions for the operations you intend to perform (e.g., Job/Build for triggerBuild, Job/Read for getJobs).

## Prerequisites

- **Jenkins**: Version 2.533 or later
- **Plugin**: Jenkins MCP Server plugin v0.158+ installed and enabled
- **Network**: netgeniusclaw host must have HTTP(S) access to the Jenkins instance on port 80/443 (or custom port)

### Plugin Installation

1. Navigate to **Manage Jenkins → Plugins → Available plugins**.
2. Search for "MCP Server".
3. Install the plugin and restart Jenkins if prompted.
4. The MCP endpoints are available immediately at:
   - Streamable HTTP: `{JENKINS_URL}/mcp-server/mcp` (recommended)
   - SSE: `{JENKINS_URL}/mcp-server/sse`
   - Stateless: `{JENKINS_URL}/mcp-server/stateless`

## Registration in openclaw.json

The Jenkins MCP server uses the **remote HTTP** registration pattern (url + headers) instead of the stdio pattern (command + args) used by most netgeniusclaw MCP servers:

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

## Transport Protocols

The plugin supports three transport modes:

| Transport | Endpoint | Use Case |
|-----------|----------|----------|
| **Streamable HTTP** | `/mcp-server/mcp` | Recommended — full bidirectional streaming, session support |
| **SSE** | `/mcp-server/sse` | Legacy — Server-Sent Events, older MCP pattern |
| **Stateless** | `/mcp-server/stateless` | Single request/response, no session state |

NetGeniusClaw uses **Streamable HTTP** as it is the current recommended MCP transport (spec version 2025-06-18) and supports streaming build logs and long-running tool calls.

## Tool Inventory

### Job Management (4 tools)

| Tool | Description |
|------|-------------|
| `getJob` | Get details of a specific job by full name (supports folder paths like `folder1/folder2/job-name`) |
| `getJobs` | List all jobs with pagination support (offset, limit) and optional regex name filter |
| `triggerBuild` | Trigger a build with optional parameters (String, Boolean, Choice, Text, Password, Run types) |
| `getQueueItem` | Get details of a queued build request (waiting reason, position, estimated build number) |

### Build Operations (4 tools)

| Tool | Description |
|------|-------------|
| `getBuild` | Get details of a specific build (result, duration, timestamp, parameters, causes) |
| `updateBuild` | Update build metadata — display name and keep-forever flag (write operation) |
| `getBuildLog` | Retrieve build console output with pagination (start offset for large logs) |
| `searchBuildLog` | Search build log by regex pattern — returns matching lines for error diagnosis |

### SCM Integration (4 tools)

| Tool | Description |
|------|-------------|
| `getJobScm` | Get SCM configuration for a job (repository URL, branches, polling config) |
| `getBuildScm` | Get SCM details for a specific build (revision, branch at build time) |
| `getBuildChangeSets` | Get change sets (commits) for a build — author, message, affected files |
| `findJobsWithScmUrl` | Find all jobs configured to use a specific SCM repository URL |

### System (2 tools)

| Tool | Description |
|------|-------------|
| `whoAmI` | Get authenticated user details — name, authorities/permissions |
| `getStatus` | Get Jenkins instance health — mode (NORMAL/SHUTDOWN), version, quietingDown status |

### Pipeline (2 tools)

| Tool | Description |
|------|-------------|
| `getPipelineRuns` | Get pipeline run history with status, duration, and branch info |
| `getPipelineRunLog` | Get pipeline run log output for specific pipeline executions |

## Example Usage

### Check Connection
```
"Verify my Jenkins connection and show my permissions"
→ Invokes whoAmI to validate authentication and display user authorities
```

### Monitor Jobs
```
"Show me all Jenkins jobs"
→ Invokes getJobs with default pagination

"What is the status of the last build for job deploy-network-config?"
→ Invokes getJob to find the job, then getBuild for the latest build number
```

### Trigger Build
```
"Trigger a build for job deploy-network-config with BRANCH=main and DRY_RUN=true"
→ Invokes getJob first (read-before-write), confirms parameters with operator, then triggerBuild
```

### Analyze Logs
```
"Show me the build log for job deploy-network-config build #42"
→ Invokes getBuildLog with job name and build number

"Search the build log for 'ERROR' in job deploy-network-config build #42"
→ Invokes searchBuildLog with regex pattern
```

### Track Changes
```
"Show me the commits in build #42 of job deploy-network-config"
→ Invokes getBuildChangeSets to list change sets with author/message/files

"Find all jobs using the repository https://github.com/org/network-configs"
→ Invokes findJobsWithScmUrl to locate jobs by SCM URL
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| 401 Unauthorized | Invalid or expired API token | Regenerate API token in Jenkins and update JENKINS_AUTH_BASE64 |
| 403 Forbidden | User lacks required permissions | Grant appropriate Jenkins permissions to the user |
| 404 Not Found | MCP plugin not installed or wrong URL | Install MCP Server plugin; verify JENKINS_URL is correct |
| Connection refused | Jenkins unreachable from netgeniusclaw host | Check network connectivity, firewall rules, and Jenkins URL |
| 503 Service Unavailable | Jenkins is starting up or shutting down | Wait for Jenkins to complete startup; check getStatus |

## Write Operations & Safety

The following tools perform write operations and require human-in-the-loop confirmation (Constitution XIV):

- **triggerBuild**: Starts a new build — confirm parameters before execution
- **updateBuild**: Modifies build metadata (display name, keep flag)

All other tools are read-only and safe for automated use.

## Extensibility

The Jenkins MCP plugin supports custom tool extensions via the `McpServerExtension` interface. If your Jenkins instance has custom extensions installed, additional tools beyond the 16 documented here may be available. Use the MCP `tools/list` call to discover all available tools at runtime.
