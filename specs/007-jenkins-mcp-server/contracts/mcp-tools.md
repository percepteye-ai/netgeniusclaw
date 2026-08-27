# MCP Tool Reference: Jenkins MCP Server

**Feature**: 007-jenkins-mcp-server
**Date**: 2026-03-27
**Transport**: Streamable HTTP (`{JENKINS_URL}/mcp-server/mcp`)
**Auth**: HTTP Basic (`Authorization: Basic {base64(username:api_token)}`)
**Source**: Jenkins MCP Server Plugin v0.158+ (official Jenkins plugin)

> These tools are provided by the Jenkins MCP Server plugin running inside Jenkins. NetGeniusClaw registers and connects to them — it does not implement them.

## Tool 1: getJob

**Description**: Get details of a specific Jenkins job by its full name (including folder path).

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Full job name including folder path (e.g., "folder/job-name") |

**Returns**: Job details including name, URL, buildability status, color (build status indicator), last build info, and parameter definitions.

---

## Tool 2: getJobs

**Description**: List all Jenkins jobs with optional pagination.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| includeRegex | string | No | Regex pattern to filter job names |
| start | integer | No | Pagination start index |
| limit | integer | No | Maximum number of jobs to return |

**Returns**: Array of job summaries with name, URL, color, and buildable status.

---

## Tool 3: triggerBuild

**Description**: Trigger a new build for a Jenkins job, optionally with parameters.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Full job name |
| parameters | object | No | Key-value pairs of build parameters |

**Returns**: Queue item ID for tracking the build request.

**Safety**: This is a WRITE operation. The skill must confirm with the operator before invoking (Constitution XIV).

---

## Tool 4: getQueueItem

**Description**: Get details of a build request in the Jenkins queue.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | Yes | Queue item ID (returned by triggerBuild) |

**Returns**: Queue item details including wait reason, blocked/buildable status, and executable reference once the build starts.

---

## Tool 5: getBuild

**Description**: Get details of a specific build by job name and build number.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Full job name |
| number | integer | Yes | Build number |

**Returns**: Build details including result, duration, timestamp, building status, and change sets.

---

## Tool 6: updateBuild

**Description**: Update build metadata (display name or keep forever flag).

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Full job name |
| number | integer | Yes | Build number |
| displayName | string | No | New display name for the build |
| keepLog | boolean | No | Whether to keep the build log permanently |

**Returns**: Updated build details.

**Safety**: This is a WRITE operation. The skill must confirm with the operator before invoking (Constitution XIV).

---

## Tool 7: getBuildLog

**Description**: Retrieve build console output with pagination support.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Full job name |
| number | integer | Yes | Build number |
| start | integer | No | Start byte offset in the log |

**Returns**: Build log text content with pagination metadata.

---

## Tool 8: searchBuildLog

**Description**: Search build console output using a regex pattern.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Full job name |
| number | integer | Yes | Build number |
| pattern | string | Yes | Regex pattern to search for |

**Returns**: Matching log lines with context.

---

## Tool 9: getJobScm

**Description**: Get SCM (source code management) configuration for a job.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Full job name |

**Returns**: SCM type, repository URL, branch specifications, and credentials reference.

---

## Tool 10: getBuildScm

**Description**: Get SCM details for a specific build.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Full job name |
| number | integer | Yes | Build number |

**Returns**: SCM revision information for the build.

---

## Tool 11: getBuildChangeSets

**Description**: Get the change sets (commits) that were included in a specific build.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Full job name |
| number | integer | Yes | Build number |

**Returns**: Array of change sets, each containing commit ID, author, message, timestamp, and affected file paths.

---

## Tool 12: findJobsWithScmUrl

**Description**: Find all Jenkins jobs that are configured to use a specific SCM repository URL.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| url | string | Yes | Repository URL to search for |

**Returns**: Array of matching jobs with their SCM configuration.

---

## Tool 13: whoAmI

**Description**: Get details about the currently authenticated user.

**Parameters**: None

**Returns**: Authenticated user's name, full name, and authorities (permissions).

---

## Tool 14: getStatus

**Description**: Get the health status of the Jenkins instance.

**Parameters**: None

**Returns**: Jenkins instance mode, quieting down status, and version information.

---

## Tool 15: getPipelineRuns

**Description**: Get pipeline execution history for a Pipeline job.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Full Pipeline job name |
| start | integer | No | Pagination start index |
| limit | integer | No | Maximum number of runs to return |

**Returns**: Array of pipeline runs with status, duration, and stage information.

---

## Tool 16: getPipelineRunLog

**Description**: Get the log output for a specific pipeline run.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Full Pipeline job name |
| runId | string | Yes | Pipeline run ID |

**Returns**: Pipeline run log content.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| JENKINS_URL | Yes | Jenkins instance URL (e.g., https://jenkins.example.com:8443) |
| JENKINS_USERNAME | Yes | Jenkins username for API access |
| JENKINS_API_TOKEN | Yes | Jenkins API token for authentication |
| JENKINS_AUTH_BASE64 | Yes | Base64-encoded `username:api_token` string |

## Error Responses

All tools return structured error messages for:
- **Connection failure**: Jenkins unreachable at configured URL
- **Authentication failure**: Invalid username or API token
- **Not found**: Job or build does not exist
- **Permission denied**: User lacks required Jenkins permissions
- **Invalid parameters**: Missing required fields or invalid parameter values for parameterized builds
