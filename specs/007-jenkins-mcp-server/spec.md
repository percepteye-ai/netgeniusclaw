# Feature Specification: Jenkins MCP Server Integration

**Feature Branch**: `007-jenkins-mcp-server`
**Created**: 2026-03-27
**Status**: Draft
**Input**: User description: "Integrate the Jenkins MCP server plugin into netgeniusclaw as a new MCP server integration. The Jenkins MCP server is an official Jenkins plugin that implements the server-side Model Context Protocol, enabling Jenkins to act as an MCP server for CI/CD pipeline management."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Monitor Pipeline and Build Status (Priority: P1)

As a network engineer or DevOps operator, I want to check the status of Jenkins jobs and their latest builds from within my AI assistant, so I can monitor CI/CD pipeline health without switching to the Jenkins web interface.

**Why this priority**: Observing current state is the foundational capability. Before triggering builds or analyzing logs, operators need visibility into what jobs exist and their current status. This aligns with the constitution's "read-before-write" principle (II) and provides immediate value with zero risk.

**Independent Test**: Can be fully tested by asking "show me all Jenkins jobs" or "what is the status of the last build for job deploy-network-config" and verifying that accurate job and build information is returned.

**Acceptance Scenarios**:

1. **Given** Jenkins is running with configured jobs, **When** the operator requests a list of all jobs, **Then** the system returns a paginated list of jobs sorted by name with their current status (enabled/disabled, last build result).

2. **Given** Jenkins has a job with a completed build, **When** the operator requests the latest build for that job, **Then** the system returns the build number, result (success/failure/unstable), duration, timestamp, and display name.

3. **Given** Jenkins has a job with a build currently in the queue, **When** the operator requests the queue status, **Then** the system returns the queued item details including why it is waiting and estimated start time.

4. **Given** Jenkins is unreachable or credentials are invalid, **When** the operator attempts any query, **Then** the system returns a clear error message indicating the connectivity or authentication issue without exposing credentials.

---

### User Story 2 - Trigger and Track Builds (Priority: P2)

As a network engineer, I want to trigger Jenkins builds (including parameterized builds) from my AI assistant and track their progress, so I can kick off network automation pipelines (config deployment, compliance checks, backup jobs) without leaving my workflow.

**Why this priority**: Build triggering is the primary write operation and the most valuable interactive capability. It transforms the integration from passive monitoring to active CI/CD management. This is gated by the constitution's "human-in-the-loop" principle (XIV) — explicit operator approval before triggering.

**Independent Test**: Can be tested by requesting "trigger build for job deploy-network-config with parameter BRANCH=main" and verifying the build is queued, a queue item ID is returned, and the build eventually starts.

**Acceptance Scenarios**:

1. **Given** Jenkins has a parameterized job, **When** the operator requests to trigger a build with specific parameters, **Then** the system submits the build with those parameters and returns the queue item ID for tracking.

2. **Given** a build has been triggered and is running, **When** the operator requests the build status using the queue item or build number, **Then** the system returns the current build status (running, success, failure, aborted) and progress information.

3. **Given** the operator requests to trigger a build with an invalid parameter value (e.g., a choice parameter with a value not in the allowed list), **When** the trigger is attempted, **Then** the system returns a clear validation error listing the allowed values.

4. **Given** the operator requests to trigger a build for a job that does not exist, **When** the trigger is attempted, **Then** the system returns a clear error indicating the job was not found.

---

### User Story 3 - Analyze Build Logs (Priority: P3)

As a network engineer troubleshooting a failed pipeline, I want to retrieve and search through build logs from my AI assistant, so I can quickly find errors and understand what went wrong without navigating the Jenkins UI.

**Why this priority**: Log analysis is the primary troubleshooting tool. When builds fail, operators need to quickly find the relevant error messages. This builds on US1 (knowing which builds failed) and provides the diagnostic detail needed to resolve issues.

**Independent Test**: Can be tested by requesting "show me the last 100 lines of the build log for job deploy-network-config build #42" or "search the build log for 'ERROR'" and verifying the correct log content is returned.

**Acceptance Scenarios**:

1. **Given** Jenkins has a completed build with log output, **When** the operator requests the build log, **Then** the system returns the log content with pagination support (configurable number of lines and start offset).

2. **Given** a build log contains error messages, **When** the operator requests to search the log for a pattern (e.g., "ERROR" or "timeout"), **Then** the system returns matching log lines with their line numbers and surrounding context.

3. **Given** a build log is very large (thousands of lines), **When** the operator requests the full log, **Then** the system returns it in manageable paginated chunks rather than truncating or failing.

---

### User Story 4 - Track Source Code Changes (Priority: P4)

As a network engineer, I want to see which source code changes triggered a build and find which jobs are associated with a specific Git repository, so I can correlate infrastructure changes with pipeline executions.

**Why this priority**: SCM integration provides the change-tracking context that connects "what changed" with "what ran." This is valuable for audit and root-cause analysis but depends on the core job/build capabilities from US1 and US2.

**Independent Test**: Can be tested by requesting "show me the changes in build #42 of job deploy-network-config" or "find all jobs using repository git@github.com:org/network-configs.git" and verifying accurate SCM data is returned.

**Acceptance Scenarios**:

1. **Given** a Jenkins build was triggered by an SCM change, **When** the operator requests the change sets for that build, **Then** the system returns the list of commits, authors, messages, and affected files.

2. **Given** Jenkins has multiple jobs configured with Git repositories, **When** the operator requests to find all jobs using a specific repository URL, **Then** the system returns the matching jobs with their SCM configuration details.

3. **Given** a Jenkins job has SCM configuration, **When** the operator requests the SCM details for that job, **Then** the system returns the repository URL, branch configuration, and polling/webhook settings.

---

### User Story 5 - Verify Jenkins Health and Identity (Priority: P5)

As an operator, I want to check the health status of the Jenkins instance and verify which user the integration is authenticated as, so I can confirm the integration is properly connected and has appropriate permissions.

**Why this priority**: Health checks and identity verification are operational hygiene capabilities. They support initial setup validation and ongoing monitoring but are not part of core CI/CD workflows.

**Independent Test**: Can be tested by requesting "check Jenkins health" or "who am I on Jenkins" and verifying accurate system status and user identity are returned.

**Acceptance Scenarios**:

1. **Given** Jenkins is running and healthy, **When** the operator requests a health check, **Then** the system returns the Jenkins instance health and readiness status.

2. **Given** valid credentials are configured, **When** the operator requests identity information, **Then** the system returns the authenticated user's name, permissions, and any relevant account details.

---

### Edge Cases

- What happens when the Jenkins instance is behind a corporate proxy or firewall that blocks MCP transport connections?
- How does the system handle Jenkins jobs nested in folders (e.g., "folder1/folder2/job-name")?
- What happens when the operator triggers a build but the Jenkins queue is full or the executor is offline?
- How does the system behave when Jenkins requires CRUMB/CSRF tokens in addition to API tokens?
- What happens when a build is in progress and the operator requests the log — does it stream partial output or wait for completion?
- How does the system handle Jenkins instances with thousands of jobs — are job listings performant and paginated?
- What happens when the Jenkins plugin version is older than the minimum required and exposes fewer tools?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST register the Jenkins MCP server in the netgeniusclaw configuration so that AI assistants can discover and connect to it.
- **FR-002**: System MUST support listing and retrieving Jenkins job information including job name, status, and configuration.
- **FR-003**: System MUST support retrieving build details including build number, result, duration, and timestamps.
- **FR-004**: System MUST support triggering Jenkins builds with optional parameters (string, boolean, choice, and text types).
- **FR-005**: System MUST support retrieving build logs with pagination (configurable line count and offset).
- **FR-006**: System MUST support searching build logs by pattern or regular expression.
- **FR-007**: System MUST support retrieving SCM configuration and change sets from jobs and builds.
- **FR-008**: System MUST support discovering jobs by associated Git repository URL.
- **FR-009**: System MUST support health checks and authenticated user identity queries.
- **FR-010**: All connection credentials (Jenkins URL, username, API token) MUST be read from environment variables at runtime — never hardcoded.
- **FR-011**: System MUST log all interactions with Jenkins to the GAIT audit trail.
- **FR-012**: System MUST handle connection failures, authentication errors, and Jenkins API errors gracefully with descriptive messages that do not expose credentials.
- **FR-013**: System MUST support Jenkins jobs organized in folder hierarchies (nested paths).
- **FR-014**: System MUST provide documentation (README) covering setup, available tools, authentication, and usage examples.
- **FR-015**: System MUST not break any existing netgeniusclaw MCP servers or skills when added.

### Key Entities

- **Jenkins Job**: A configured CI/CD pipeline or task in Jenkins, identified by its full path (which may include folder nesting). Has a name, status (enabled/disabled), and configuration including SCM settings and parameters.
- **Build**: A single execution of a Jenkins job. Has a build number, result (success/failure/unstable/aborted), start time, duration, log output, and associated SCM changes.
- **Build Parameter**: A typed input to a parameterized Jenkins job. Includes name, type (string, boolean, choice, text, password, run), default value, and allowed values for choice parameters.
- **Queue Item**: A build request waiting in the Jenkins queue before execution begins. Has a queue ID, reason for waiting, and reference to the associated job.
- **Change Set**: A collection of source code commits associated with a build, including commit hash, author, message, and affected files.
- **SCM Configuration**: The source code management settings for a job, including repository URL, branch specification, and polling configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can list Jenkins jobs and retrieve build status within 5 seconds of requesting.
- **SC-002**: Operators can trigger parameterized builds and receive a queue item confirmation within 5 seconds.
- **SC-003**: Build log retrieval returns results within 5 seconds for logs up to 10,000 lines.
- **SC-004**: Log search returns matching lines within 5 seconds for logs up to 10,000 lines.
- **SC-005**: All 16 Jenkins MCP tools are accessible and documented in the integration.
- **SC-006**: 100% of Jenkins interactions are recorded in the GAIT audit trail.
- **SC-007**: All artifact coherence checklist items are complete (README, install.sh, UI, SOUL.md, SKILL.md, .env.example, TOOLS.md, config/openclaw.json).
- **SC-008**: Existing netgeniusclaw MCP servers and skills remain fully functional after the addition (backwards compatibility verified).
- **SC-009**: Connection and authentication errors are handled gracefully — no credentials are exposed in error messages.

## Assumptions

- Jenkins is already deployed and accessible over the network from the machine running the AI assistant. This integration does not manage Jenkins deployment or plugin installation.
- The Jenkins MCP Server plugin (version 0.158 or later) is installed on the Jenkins instance. The plugin provides the MCP server endpoint; netgeniusclaw registers and connects to it as a client.
- Jenkins is accessible via HTTPS with a valid TLS certificate, or the operator has accepted the risk of HTTP transport.
- The operator has generated a Jenkins API token with appropriate permissions for the jobs they need to access. This integration does not manage Jenkins user accounts or permissions.
- The Jenkins MCP plugin supports three transport options (SSE, Streamable HTTP, Stateless); the integration will be configured for Streamable HTTP by default as the recommended transport for AI agent usage.
- This is primarily a configuration and registration integration — the MCP server runs natively inside Jenkins via the plugin. NetGeniusClaw's role is to register the server, create skills that leverage the tools, and ensure artifact coherence.
- Build triggering follows the constitution's "human-in-the-loop" principle (XIV) — the AI assistant will confirm with the operator before executing trigger actions.
- The Jenkins instance has the CRUMB issuer enabled (default) for CSRF protection; the MCP plugin handles this transparently.
