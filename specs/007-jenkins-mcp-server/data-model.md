# Data Model: Jenkins MCP Server Integration

**Feature**: 007-jenkins-mcp-server
**Date**: 2026-03-27

## Entities

### JenkinsConfig

Runtime configuration for the Jenkins MCP server connection, sourced entirely from environment variables.

| Field | Type | Source | Default | Validation |
|-------|------|--------|---------|------------|
| jenkins_url | str | `JENKINS_URL` | (required) | Must be valid HTTP/HTTPS URL |
| auth_base64 | str | `JENKINS_AUTH_BASE64` | (required) | Non-empty Base64 string of `username:api_token` |

**Validation rules**:
- `jenkins_url` must not have a trailing slash
- `jenkins_url` must be a reachable Jenkins instance with the MCP Server plugin installed
- `auth_base64` must decode to a valid `username:token` format
- Connection fails gracefully if Jenkins is unreachable or credentials are invalid

### JenkinsJob

Represents a CI/CD job configured in Jenkins.

| Field | Type | Description |
|-------|------|-------------|
| fullName | str | Full path of the job including folders (e.g., "folder1/folder2/job-name") |
| name | str | Short name of the job |
| url | str | Jenkins web URL for the job |
| color | str | Status color indicator (blue=success, red=failure, yellow=unstable, disabled, notbuilt) |
| buildable | bool | Whether the job can accept new builds |
| inQueue | bool | Whether a build is currently queued |
| lastBuild | Build? | Reference to the most recent build |
| parameters | list[BuildParameter] | Defined parameters for parameterized jobs |

### Build

Represents a single execution of a Jenkins job.

| Field | Type | Description |
|-------|------|-------------|
| number | int | Build number (monotonically increasing per job) |
| result | str? | Build outcome: SUCCESS, FAILURE, UNSTABLE, ABORTED, or null (in progress) |
| displayName | str | Build display name (customizable via updateBuild) |
| timestamp | int | Build start time (Unix epoch milliseconds) |
| duration | int | Build duration in milliseconds |
| building | bool | Whether the build is still running |
| url | str | Jenkins web URL for the build |
| changeSets | list[ChangeSet] | SCM changes that triggered this build |

### BuildParameter

Represents a typed input parameter for parameterized builds.

| Field | Type | Description |
|-------|------|-------------|
| name | str | Parameter name |
| type | str | Parameter type: StringParameterDefinition, BooleanParameterDefinition, ChoiceParameterDefinition, TextParameterDefinition, PasswordParameterDefinition, RunParameterDefinition |
| defaultValue | str? | Default value for the parameter |
| choices | list[str]? | Allowed values for choice parameters |
| description | str? | Human-readable description |

### QueueItem

Represents a build request waiting in the Jenkins queue.

| Field | Type | Description |
|-------|------|-------------|
| id | int | Queue item ID |
| why | str | Reason the build is waiting (e.g., "Waiting for executor", "Quiet period") |
| task | JenkinsJob | Reference to the queued job |
| executable | Build? | Reference to the build once it starts (null while queued) |
| blocked | bool | Whether the queue item is blocked |
| buildable | bool | Whether the item is ready to build |
| stuck | bool | Whether the item appears stuck |

### ChangeSet

Represents a collection of SCM commits associated with a build.

| Field | Type | Description |
|-------|------|-------------|
| kind | str | SCM type (e.g., "git", "svn") |
| items | list[ChangeSetItem] | Individual commits/changes |

### ChangeSetItem

Represents a single SCM commit.

| Field | Type | Description |
|-------|------|-------------|
| commitId | str | Commit hash or revision ID |
| author | str | Author name |
| msg | str | Commit message |
| timestamp | int | Commit timestamp |
| affectedPaths | list[str] | Files changed in this commit |

### SCMConfig

Represents the source code management configuration of a job.

| Field | Type | Description |
|-------|------|-------------|
| type | str | SCM type (e.g., "GitSCM") |
| url | str | Repository URL |
| branches | list[str] | Branch specifications |
| credentialsId | str? | Jenkins credentials ID used for SCM access |

## Relationships

```
JenkinsConfig --[connects to]--> Jenkins MCP Server
JenkinsJob --[has many]--> Build
JenkinsJob --[has many]--> BuildParameter
JenkinsJob --[has one]--> SCMConfig
Build --[has many]--> ChangeSet --[has many]--> ChangeSetItem
Build --[queued as]--> QueueItem
```

## State Transitions

### Build Lifecycle

```
Not Started → Queued → Building → Completed (SUCCESS | FAILURE | UNSTABLE | ABORTED)
```

### Job Status Colors

```
blue         = last build succeeded
red          = last build failed
yellow       = last build unstable
blue_anime   = building (last was success)
red_anime    = building (last was failure)
yellow_anime = building (last was unstable)
disabled     = job is disabled
notbuilt     = job has never been built
```

## Tool Categories

The 16 tools map to these entities as follows:

| Tool | Primary Entity | Operation |
|------|---------------|-----------|
| getJob | JenkinsJob | Read single |
| getJobs | JenkinsJob | Read list |
| triggerBuild | Build/QueueItem | Create |
| getQueueItem | QueueItem | Read single |
| getBuild | Build | Read single |
| updateBuild | Build | Update |
| getBuildLog | Build (log) | Read |
| searchBuildLog | Build (log) | Search |
| getJobScm | SCMConfig | Read |
| getBuildScm | SCMConfig | Read |
| getBuildChangeSets | ChangeSet | Read |
| findJobsWithScmUrl | JenkinsJob | Search |
| whoAmI | (system) | Read |
| getStatus | (system) | Read |
| getPipelineRuns | Build | Read list |
| getPipelineRunLog | Build (log) | Read |
