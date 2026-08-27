# Feature Specification: Atlassian MCP Server Integration

**Feature Branch**: `009-atlassian-mcp-server`
**Created**: 2026-03-27
**Status**: Draft
**Input**: User description: "Integrate Atlassian MCP server into netgeniusclaw for Jira issue tracking and Confluence wiki management via Model Context Protocol. Two options available: official Atlassian Rovo MCP Server (remote cloud, OAuth 2.1, Jira + Confluence + Compass) and community mcp-atlassian (72 tools, Python, Cloud + Server/Data Center support)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Search and View Jira Issues (Priority: P1)

As a network engineer or operations team member, I want to search, filter, and inspect Jira issues from my AI assistant, so I can track network change requests, outage tickets, and maintenance tasks without switching to the Jira web interface.

**Why this priority**: Jira issue visibility is the foundational read-only capability. Network teams use Jira to manage change requests, incident tickets, and maintenance windows. Being able to query issue status, assignees, and details is the minimum viable integration. This aligns with the constitution's "read-before-write" principle (II) and provides immediate value with zero risk.

**Independent Test**: Can be fully tested by asking "show me open issues in project NET assigned to me" or "search for Jira issues with label 'outage'" and verifying that accurate issue data is returned with correct titles, states, assignees, and priorities.

**Acceptance Scenarios**:

1. **Given** a Jira project has issues, **When** the operator searches using a query (e.g., project = NET AND status = Open), **Then** the system returns matching issues with their key, title, status, assignee, priority, and creation date.

2. **Given** a specific Jira issue exists, **When** the operator requests its details by issue key (e.g., NET-1234), **Then** the system returns the full issue including title, description, status, assignee, labels, priority, comments, and linked issues.

3. **Given** the operator wants to find issues assigned to them, **When** they request their current assignments, **Then** the system returns all issues assigned to the authenticated user across accessible projects.

4. **Given** Jira is unreachable or credentials are invalid, **When** the operator attempts any query, **Then** the system returns a clear error message indicating the connectivity or authentication issue without exposing tokens or credentials.

---

### User Story 2 - Search and Read Confluence Pages (Priority: P2)

As a network engineer, I want to search and read Confluence pages from my AI assistant, so I can find network documentation, runbooks, and architecture diagrams without leaving my workflow.

**Why this priority**: Confluence holds institutional knowledge — network runbooks, topology diagrams, change procedures, and vendor documentation. Providing read access to this knowledge base enables the AI assistant to reference authoritative documentation when helping with network operations. This is independently valuable even without Jira integration.

**Independent Test**: Can be tested by requesting "search Confluence for 'BGP runbook'" or "show me the page 'Network Architecture Overview' in space NET-DOCS" and verifying accurate page content is returned.

**Acceptance Scenarios**:

1. **Given** a Confluence space has pages, **When** the operator searches using a query, **Then** the system returns matching pages with their title, space, last modified date, and excerpt.

2. **Given** a specific Confluence page exists, **When** the operator requests its content, **Then** the system returns the page title, body content, labels, and version information.

3. **Given** a Confluence space exists, **When** the operator requests to list its pages, **Then** the system returns pages in the space with titles, hierarchy, and modification dates.

4. **Given** a Confluence page has comments, **When** the operator requests page details, **Then** the system includes the comment thread with authors and timestamps.

---

### User Story 3 - Create and Update Jira Issues (Priority: P3)

As a network engineer, I want to create new Jira issues and update existing ones from my AI assistant, so I can log incidents, create change requests, and update ticket status as part of my network operations workflow without context-switching.

**Why this priority**: Write operations on Jira complete the incident management loop. Operators can create a ticket for a detected issue, update status after resolution, and add comments with findings — all from the assistant. This is gated by the constitution's "human-in-the-loop" principle (XIV) — explicit operator approval before write actions. It also supports the "ITSM-gated changes" principle (III) by enabling Jira-based change tracking.

**Independent Test**: Can be tested by requesting "create a Jira issue in project NET titled 'Router-01 BGP peer down' with priority Critical" and verifying the issue is created with the correct fields and returns the issue key and URL.

**Acceptance Scenarios**:

1. **Given** a Jira project, **When** the operator requests to create a new issue with title, description, type, and priority, **Then** the system creates the issue and returns the issue key and URL.

2. **Given** an existing Jira issue, **When** the operator requests to update its status (e.g., transition from Open to In Progress), **Then** the system transitions the issue and confirms the new status.

3. **Given** an existing Jira issue, **When** the operator requests to add a comment, **Then** the system posts the comment and confirms.

4. **Given** an existing Jira issue, **When** the operator requests to update fields (labels, assignee, priority), **Then** the system updates the fields and confirms the changes.

---

### User Story 4 - Create and Update Confluence Pages (Priority: P4)

As a network engineer, I want to create new Confluence pages and update existing ones from my AI assistant, so I can document network changes, create incident postmortems, and maintain runbooks as part of my operational workflow.

**Why this priority**: Write operations on Confluence enable documentation-as-code workflows. After resolving a network incident, the operator can create a postmortem page directly from the assistant. This supports the constitution's "documentation-as-code" principle (XII). Write operations are lower priority than read because most operators spend more time consuming documentation than creating it.

**Independent Test**: Can be tested by requesting "create a Confluence page in space NET-DOCS titled 'Incident Postmortem: Router-01 Outage'" and verifying the page is created with the correct title and content.

**Acceptance Scenarios**:

1. **Given** a Confluence space, **When** the operator requests to create a new page with title and body content, **Then** the system creates the page and returns the page URL.

2. **Given** an existing Confluence page, **When** the operator requests to update its content, **Then** the system updates the page and confirms the new version.

3. **Given** an existing Confluence page, **When** the operator requests to add a comment, **Then** the system posts the comment with the operator's identity.

---

### User Story 5 - Cross-Product Linking and Bulk Operations (Priority: P5)

As a project lead, I want to perform bulk operations (create multiple Jira issues at once) and leverage cross-product linking between Jira and Confluence from my AI assistant, so I can efficiently manage large-scale network projects and maintain traceability between work items and documentation.

**Why this priority**: Bulk operations and cross-product linking are power-user features that save time on large projects but are not part of day-to-day network operations. They enhance productivity for project leads managing network transformation initiatives.

**Independent Test**: Can be tested by requesting "create 5 Jira issues in project NET for each of the following tasks: [list]" and verifying all issues are created with correct titles and linked appropriately.

**Acceptance Scenarios**:

1. **Given** a Jira project, **When** the operator requests to create multiple issues from a structured list, **Then** the system creates all issues and returns their keys and URLs.

2. **Given** a Jira issue and a Confluence page, **When** the operator requests to link them, **Then** the system creates the cross-product link.

3. **Given** a Jira issue with linked Confluence pages, **When** the operator requests issue details, **Then** the linked Confluence pages are included in the response.

---

### Edge Cases

- What happens when the operator queries a Jira project or Confluence space they do not have permission to access?
- How does the system handle Atlassian Cloud instances with rate limiting — are requests throttled gracefully?
- What happens when the operator attempts to transition a Jira issue to a status not allowed by the workflow?
- How does the system handle Confluence pages with complex formatting (tables, macros, embedded media)?
- What happens when the API token or OAuth session expires mid-operation?
- How does the system handle Jira custom fields that vary between projects?
- What happens when a Confluence page has restrictions that prevent the authenticated user from viewing it?
- How does the system behave when the Jira or Confluence instance is a Server/Data Center deployment with different API endpoints than Cloud?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST register the Atlassian MCP server in the netgeniusclaw configuration so that AI assistants can discover and connect to it.
- **FR-002**: System MUST support searching Jira issues using query language with filters for project, status, assignee, labels, and priority.
- **FR-003**: System MUST support retrieving detailed Jira issue information including title, description, status, assignee, priority, labels, comments, and linked issues.
- **FR-004**: System MUST support creating new Jira issues with configurable type, title, description, priority, labels, and assignee.
- **FR-005**: System MUST support updating Jira issues including field modifications and workflow transitions.
- **FR-006**: System MUST support adding comments to Jira issues.
- **FR-007**: System MUST support searching Confluence pages using query language with filters for space, title, and content.
- **FR-008**: System MUST support retrieving Confluence page content including title, body, labels, and version history.
- **FR-009**: System MUST support creating new Confluence pages with title, body content, and space assignment.
- **FR-010**: System MUST support updating existing Confluence page content.
- **FR-011**: System MUST support adding comments to Confluence pages.
- **FR-012**: System MUST support listing Jira issue links and Confluence page relationships.
- **FR-013**: All connection credentials (Jira URL, Confluence URL, username, API tokens) MUST be read from environment variables at runtime — never hardcoded.
- **FR-014**: System MUST log all interactions with Atlassian products to the GAIT audit trail.
- **FR-015**: System MUST handle connection failures, authentication errors, rate limiting, and Atlassian API errors gracefully with descriptive messages that do not expose tokens or credentials.
- **FR-016**: System MUST support both Atlassian Cloud and Server/Data Center deployments by accepting configurable URLs and authentication methods.
- **FR-017**: System MUST provide documentation (README) covering setup, available tools, authentication for both Cloud and Server/Data Center, and usage examples.
- **FR-018**: System MUST not break any existing netgeniusclaw MCP servers or skills when added.
- **FR-019**: System MUST support bulk issue creation from structured input.
- **FR-020**: System MUST respect Atlassian permission models — operations fail gracefully when the user lacks permission rather than exposing unauthorized data.

### Key Entities

- **Jira Project**: A collection of issues organized under a project key (e.g., NET). Has configured issue types, workflows, custom fields, and permission schemes.
- **Jira Issue**: A work item with a unique key (e.g., NET-1234), title (summary), description, type (Bug, Task, Story, etc.), status, priority, assignee, reporter, labels, and comments.
- **Issue Transition**: A workflow state change for a Jira issue (e.g., Open → In Progress → Resolved). Available transitions depend on the project's workflow configuration.
- **Confluence Space**: A named collection of wiki pages organized by team or topic. Has a key identifier and configurable permissions.
- **Confluence Page**: A wiki document with title, body content, parent page (for hierarchy), labels, version history, and comments. Lives within a Confluence space.
- **Comment**: A text entry attached to a Jira issue or Confluence page, with author, timestamp, and content.
- **Issue Link**: A typed relationship between two Jira issues (e.g., "blocks", "is blocked by", "relates to") or between a Jira issue and a Confluence page.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can search Jira issues and receive results within 5 seconds of requesting.
- **SC-002**: Operators can search and retrieve Confluence pages within 5 seconds of requesting.
- **SC-003**: Jira issue creation and update operations complete within 5 seconds.
- **SC-004**: Confluence page creation and update operations complete within 5 seconds.
- **SC-005**: Bulk issue creation (up to 10 issues) completes within 30 seconds.
- **SC-006**: 100% of Atlassian interactions are recorded in the GAIT audit trail.
- **SC-007**: All artifact coherence checklist items are complete (README, install.sh, UI, SOUL.md, SKILL.md, .env.example, TOOLS.md, config/openclaw.json).
- **SC-008**: Existing netgeniusclaw MCP servers and skills remain fully functional after the addition (backwards compatibility verified).
- **SC-009**: Connection, authentication, and permission errors are handled gracefully — no tokens or credentials are exposed in error messages.
- **SC-010**: The integration works with both Atlassian Cloud and Server/Data Center deployments when configured with the appropriate URLs and authentication.

## Assumptions

- An Atlassian instance (Cloud or Server/Data Center) is already deployed and accessible over the network from the machine running the AI assistant. This integration does not manage Atlassian deployment.
- For Cloud deployments, the operator has generated an API token from their Atlassian account. For Server/Data Center deployments, the operator has generated a Personal Access Token with appropriate permissions.
- The community MCP server (mcp-atlassian by sooperset) is the primary integration target due to its comprehensive tool coverage (72 tools), Python implementation (consistent with netgeniusclaw's stack), support for both Cloud and Server/Data Center, and active maintenance (4.7k+ stars, 118 contributors). The official Atlassian Rovo MCP Server is noted as an alternative for teams using Atlassian Cloud exclusively.
- Jira and Confluence are both available on the target Atlassian instance. If only one product is available, the integration degrades gracefully — tools for the unavailable product return clear "not configured" messages.
- The integration will use stdio transport by default (running the MCP server as a local process) with SSE and Streamable HTTP available as alternatives for shared deployments.
- Write operations (issue creation, page creation, transitions) follow the constitution's "human-in-the-loop" principle (XIV) — the AI assistant will confirm with the operator before executing mutating actions.
- Jira workflows and custom fields vary between projects and instances. The integration handles this variability by querying available transitions and fields dynamically rather than assuming a fixed schema.
- The Atlassian instance version supports the REST API endpoints used by the MCP server. For Server/Data Center, Jira v8.14+ and Confluence v6.0+ are required.
