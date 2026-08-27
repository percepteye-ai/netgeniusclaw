# Feature Specification: GitLab MCP Server Integration

**Feature Branch**: `008-gitlab-mcp-server`
**Created**: 2026-03-27
**Status**: Draft
**Input**: User description: "Integrate GitLab MCP server into netgeniusclaw for repository, pipeline, issue, and merge request management via Model Context Protocol. Two options available: official GitLab MCP server (beta, OAuth 2.0, Premium/Ultimate) and community @zereight/mcp-gitlab (98+ tools, TypeScript, PAT/OAuth)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Issues and Merge Requests (Priority: P1)

As a network engineer or DevOps operator, I want to search, list, and inspect GitLab issues and merge requests from my AI assistant, so I can track work items, review change proposals, and understand project status without switching to the GitLab web interface.

**Why this priority**: Issue and merge request visibility is the foundational read-only capability. Network teams use GitLab issues to track configuration changes, outages, and feature requests. Merge requests represent pending infrastructure-as-code changes. This aligns with the constitution's "read-before-write" principle (II) and provides immediate value with zero risk.

**Independent Test**: Can be fully tested by asking "show me open issues in project network-automation" or "list merge requests awaiting review" and verifying that accurate issue and MR data is returned with correct titles, states, assignees, and labels.

**Acceptance Scenarios**:

1. **Given** a GitLab project has open issues, **When** the operator requests a list of issues, **Then** the system returns issues with their title, state, assignee, labels, and creation date.

2. **Given** a GitLab project has open merge requests, **When** the operator requests merge request details for a specific MR, **Then** the system returns the MR title, description, source/target branches, approval status, and diff summary.

3. **Given** the operator wants to find issues assigned to them across projects, **When** they request "my issues", **Then** the system returns all issues assigned to the authenticated user across accessible projects.

4. **Given** GitLab is unreachable or credentials are invalid, **When** the operator attempts any query, **Then** the system returns a clear error message indicating the connectivity or authentication issue without exposing tokens.

---

### User Story 2 - Monitor CI/CD Pipelines (Priority: P2)

As a network engineer, I want to view pipeline status, inspect job logs, and track pipeline executions from my AI assistant, so I can monitor network automation pipelines (config validation, compliance checks, deployment) and troubleshoot failures quickly.

**Why this priority**: Pipeline monitoring is the CI/CD observability layer. Network teams rely on GitLab CI/CD to validate and deploy infrastructure changes. Quick access to pipeline status and job logs is critical for troubleshooting failed deployments without navigating the GitLab UI.

**Independent Test**: Can be tested by requesting "show pipelines for project network-configs" or "get the log for job deploy in pipeline #123" and verifying accurate pipeline and job data is returned.

**Acceptance Scenarios**:

1. **Given** a GitLab project has pipeline executions, **When** the operator requests a list of pipelines, **Then** the system returns pipelines with their status (running, success, failed, canceled), branch, commit, and trigger information.

2. **Given** a pipeline has jobs, **When** the operator requests job details for a specific pipeline, **Then** the system returns each job's name, stage, status, duration, and runner information.

3. **Given** a pipeline job has completed, **When** the operator requests the job output log, **Then** the system returns the log content with pagination support.

4. **Given** a pipeline is running, **When** the operator requests to cancel or retry the pipeline, **Then** the system executes the action and confirms the updated pipeline status.

---

### User Story 3 - Browse Repositories and Files (Priority: P3)

As a network engineer, I want to browse repository structure, read file contents, and view commit history from my AI assistant, so I can review network configuration files, understand recent changes, and inspect infrastructure-as-code without cloning repositories locally.

**Why this priority**: Repository browsing provides the code context needed to understand what network configurations exist and what has changed. This supports root-cause analysis and change review but depends on knowing which projects to look at (from US1 issue/MR context).

**Independent Test**: Can be tested by requesting "show the directory structure of project network-configs" or "show me the contents of ansible/site.yml" and verifying accurate file content and tree structure are returned.

**Acceptance Scenarios**:

1. **Given** a GitLab project has files, **When** the operator requests the repository tree, **Then** the system returns the directory structure with file and folder names, types, and sizes.

2. **Given** a file exists in a repository, **When** the operator requests the file contents, **Then** the system returns the file content with correct encoding.

3. **Given** a repository has commits, **When** the operator requests the commit history, **Then** the system returns commits with hash, author, message, and timestamp.

4. **Given** two branches exist, **When** the operator requests a diff between them, **Then** the system returns the file-level changes between the branches.

---

### User Story 4 - Manage Issues and Merge Requests (Priority: P4)

As a network engineer, I want to create issues, update issue status, create merge requests, and add comments from my AI assistant, so I can manage network change workflows end-to-end without context-switching.

**Why this priority**: Write operations on issues and merge requests complete the workflow loop. Operators can create a ticket for a network issue, then create an MR with the fix, all from the assistant. This is gated by the constitution's "human-in-the-loop" principle (XIV) — explicit operator approval before write actions.

**Independent Test**: Can be tested by requesting "create an issue in project network-automation titled 'BGP peer flapping on router-01'" and verifying the issue is created with the correct title and returns the issue URL.

**Acceptance Scenarios**:

1. **Given** a GitLab project, **When** the operator requests to create a new issue with a title and description, **Then** the system creates the issue and returns the issue number and URL.

2. **Given** an existing issue, **When** the operator requests to update its labels or assignee, **Then** the system updates the issue and confirms the changes.

3. **Given** a source and target branch exist, **When** the operator requests to create a merge request, **Then** the system creates the MR with the specified title, description, and branch configuration.

4. **Given** an existing merge request, **When** the operator requests to add a comment or approve the MR, **Then** the system posts the comment or records the approval.

---

### User Story 5 - Manage Labels, Milestones, and Releases (Priority: P5)

As a project lead, I want to manage labels, milestones, and releases from my AI assistant, so I can organize and track project progress for network infrastructure initiatives.

**Why this priority**: Project management entities (labels, milestones, releases) support organizational workflows but are not core to day-to-day network operations. They enhance the integration for teams using GitLab for full project lifecycle management.

**Independent Test**: Can be tested by requesting "list milestones for project network-automation" or "create a label called 'critical-infrastructure'" and verifying accurate data is returned or the entity is created.

**Acceptance Scenarios**:

1. **Given** a GitLab project, **When** the operator requests a list of milestones, **Then** the system returns milestones with their title, due date, progress, and status.

2. **Given** a project, **When** the operator requests to create a label with a name and color, **Then** the system creates the label and confirms.

3. **Given** a project with releases, **When** the operator requests release details, **Then** the system returns the release name, tag, description, and associated assets.

---

### Edge Cases

- What happens when the operator queries a project they do not have permission to access?
- How does the system handle GitLab instances with rate limiting enabled — are requests throttled gracefully?
- What happens when a merge request has conflicts and the operator attempts to merge it?
- How does the system handle very large repositories with thousands of files in the tree listing?
- What happens when the GitLab instance is self-hosted with a self-signed TLS certificate?
- How does the system handle projects in deeply nested groups (e.g., "org/team/sub-team/project")?
- What happens when the personal access token expires or is revoked mid-session?
- How does the system handle GitLab wiki pages with embedded images or attachments?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST register the GitLab MCP server in the netgeniusclaw configuration so that AI assistants can discover and connect to it.
- **FR-002**: System MUST support listing, searching, and retrieving issue details including title, state, assignee, labels, and description.
- **FR-003**: System MUST support listing, searching, and retrieving merge request details including title, state, source/target branches, approvals, and diffs.
- **FR-004**: System MUST support listing pipelines and their jobs with status, duration, and stage information.
- **FR-005**: System MUST support retrieving pipeline job logs with pagination.
- **FR-006**: System MUST support pipeline control operations (create, retry, cancel) for both pipelines and individual jobs.
- **FR-007**: System MUST support browsing repository file trees and retrieving file contents.
- **FR-008**: System MUST support viewing commit history and commit diffs.
- **FR-009**: System MUST support creating and updating issues including title, description, labels, and assignees.
- **FR-010**: System MUST support creating merge requests with source/target branch specification.
- **FR-011**: System MUST support merge request operations including commenting, approving, and merging.
- **FR-012**: System MUST support searching for projects/repositories by name or keyword.
- **FR-013**: System MUST support label, milestone, and release management (list, create, update, delete).
- **FR-014**: System MUST support wiki page operations (list, read, create, update, delete).
- **FR-015**: All connection credentials (GitLab URL, personal access token) MUST be read from environment variables at runtime — never hardcoded.
- **FR-016**: System MUST log all interactions with GitLab to the GAIT audit trail.
- **FR-017**: System MUST handle connection failures, authentication errors, rate limiting, and GitLab API errors gracefully with descriptive messages that do not expose tokens.
- **FR-018**: System MUST support both gitlab.com (SaaS) and self-hosted GitLab instances by accepting a configurable API URL.
- **FR-019**: System MUST provide documentation (README) covering setup, available tools, authentication, and usage examples.
- **FR-020**: System MUST not break any existing netgeniusclaw MCP servers or skills when added.
- **FR-021**: System MUST support a read-only mode to restrict the integration to observation-only operations when configured.

### Key Entities

- **GitLab Project**: A repository with associated issues, merge requests, pipelines, wiki, and settings. Identified by numeric ID or path (which may include group nesting).
- **Issue**: A work item in a project with title, description, state (open/closed), assignees, labels, milestone, and discussion thread.
- **Merge Request**: A code change proposal with source/target branches, description, approval status, pipeline status, diffs, and discussion thread.
- **Pipeline**: A CI/CD execution triggered by a commit or manual action. Contains ordered stages, each with one or more jobs.
- **Pipeline Job**: A single unit of work within a pipeline stage. Has a status, duration, log output, and runner assignment.
- **Commit**: A source code change with hash, author, message, timestamp, and file diffs.
- **Label**: A categorization tag applied to issues and merge requests for filtering and organization.
- **Milestone**: A time-bounded collection of issues and merge requests representing a project goal or release target.
- **Release**: A versioned package associated with a Git tag, containing release notes and downloadable assets.
- **Wiki Page**: A documentation page within a project's wiki, with title, content, and revision history.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can search issues and merge requests and receive results within 5 seconds of requesting.
- **SC-002**: Operators can view pipeline status and job details within 5 seconds of requesting.
- **SC-003**: Pipeline job log retrieval returns results within 5 seconds for logs up to 10,000 lines.
- **SC-004**: Repository file browsing and content retrieval completes within 5 seconds per request.
- **SC-005**: Issue and merge request creation/update operations complete within 5 seconds.
- **SC-006**: 100% of GitLab interactions are recorded in the GAIT audit trail.
- **SC-007**: All artifact coherence checklist items are complete (README, install.sh, UI, SOUL.md, SKILL.md, .env.example, TOOLS.md, config/openclaw.json).
- **SC-008**: Existing netgeniusclaw MCP servers and skills remain fully functional after the addition (backwards compatibility verified).
- **SC-009**: Connection, authentication, and rate-limiting errors are handled gracefully — no tokens are exposed in error messages.
- **SC-010**: The integration works with both gitlab.com and self-hosted GitLab instances when configured with the appropriate URL and credentials.

## Assumptions

- A GitLab instance (gitlab.com or self-hosted) is already deployed and accessible over the network from the machine running the AI assistant. This integration does not manage GitLab deployment.
- The operator has generated a GitLab Personal Access Token with appropriate scopes (api, read_api, read_repository, etc.) for the operations they need. This integration does not manage GitLab user accounts or permissions.
- The community MCP server (@zereight/mcp-gitlab) is the primary integration target due to its comprehensive tool coverage (98+ tools), support for both PAT and OAuth authentication, and active maintenance (1.3k+ stars, 81 contributors). The official GitLab MCP server (beta, Premium/Ultimate only) is noted as an alternative for teams with GitLab Premium/Ultimate subscriptions.
- GitLab is accessible via HTTPS with a valid TLS certificate, or the operator has configured the integration to accept self-signed certificates.
- The integration will use stdio transport by default (running the MCP server as a local process) with Streamable HTTP available as an alternative for shared/multi-user deployments.
- Write operations (issue creation, MR creation, pipeline control) follow the constitution's "human-in-the-loop" principle (XIV) — the AI assistant will confirm with the operator before executing mutating actions.
- Rate limiting behavior varies between gitlab.com and self-hosted instances. The integration handles rate-limit responses gracefully with appropriate backoff.
- The GitLab instance version supports the REST API endpoints used by the MCP server. Older self-hosted instances may not support all features.
