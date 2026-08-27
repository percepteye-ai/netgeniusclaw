# Data Model: Atlassian MCP Server Integration

**Feature**: 009-atlassian-mcp-server
**Date**: 2026-03-27

## Entities

### AtlassianConfig

Runtime configuration for the Atlassian MCP server connection, sourced entirely from environment variables.

| Field | Type | Source | Default | Validation |
|-------|------|--------|---------|------------|
| jira_url | str | `JIRA_URL` | (required if using Jira) | Must be valid HTTPS URL |
| jira_username | str | `JIRA_USERNAME` | (required if using Jira) | Email (Cloud) or username (Server/DC) |
| jira_api_token | str | `JIRA_API_TOKEN` | (required if using Jira) | API token (Cloud) or PAT (Server/DC) |
| confluence_url | str | `CONFLUENCE_URL` | (required if using Confluence) | Must be valid HTTPS URL |
| confluence_username | str | `CONFLUENCE_USERNAME` | (required if using Confluence) | Email (Cloud) or username (Server/DC) |
| confluence_api_token | str | `CONFLUENCE_API_TOKEN` | (required if using Confluence) | API token (Cloud) or PAT (Server/DC) |

**Validation rules**:
- At least one product (Jira or Confluence) must be configured
- URLs must not have trailing slashes
- Server fails gracefully if both products are unconfigured

### JiraProject

A collection of issues organized under a project key.

| Field | Type | Description |
|-------|------|-------------|
| key | str | Project key (e.g., "NET", "OPS") |
| name | str | Project display name |
| projectTypeKey | str | "software", "service_desk", "business" |
| lead | User | Project lead |
| issueTypes | list[IssueType] | Available issue types for this project |

### JiraIssue

A work item in a Jira project.

| Field | Type | Description |
|-------|------|-------------|
| key | str | Issue key (e.g., "NET-1234") |
| summary | str | Issue title |
| description | str? | Issue body (markdown or Atlassian Document Format) |
| status | Status | Current workflow status |
| priority | Priority | Issue priority (Highest, High, Medium, Low, Lowest) |
| issuetype | IssueType | Issue type (Bug, Task, Story, Epic, Sub-task, etc.) |
| assignee | User? | Assigned user |
| reporter | User | Issue creator |
| labels | list[str] | Applied labels |
| components | list[Component] | Associated components |
| fixVersions | list[Version] | Fix version(s) |
| created | str | ISO 8601 creation timestamp |
| updated | str | ISO 8601 last update timestamp |
| resolution | str? | Resolution status if closed (Fixed, Won't Fix, Duplicate, etc.) |
| parent | JiraIssue? | Parent issue (for sub-tasks) |
| issuelinks | list[IssueLink] | Linked issues |

### IssueTransition

A workflow state change for a Jira issue.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Transition ID |
| name | str | Transition name (e.g., "Start Progress", "Resolve", "Close") |
| to | Status | Target status after transition |
| hasScreen | bool | Whether the transition requires field input |

### ConfluenceSpace

A named collection of wiki pages.

| Field | Type | Description |
|-------|------|-------------|
| key | str | Space key (e.g., "NET-DOCS") |
| name | str | Space display name |
| type | str | "global" or "personal" |
| status | str | "current" or "archived" |

### ConfluencePage

A wiki document within a Confluence space.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Page ID |
| title | str | Page title |
| spaceKey | str | Containing space key |
| body | str | Page content (storage format or view format) |
| version | int | Current version number |
| status | str | "current" or "draft" |
| ancestors | list[PageRef] | Parent pages (for hierarchy) |
| labels | list[Label] | Applied labels |
| created | str | ISO 8601 creation timestamp |
| updated | str | ISO 8601 last update timestamp |

### Comment

A text entry attached to a Jira issue or Confluence page.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Comment ID |
| body | str | Comment content |
| author | User | Comment author |
| created | str | ISO 8601 creation timestamp |
| updated | str | ISO 8601 last update timestamp |

### IssueLink

A typed relationship between entities.

| Field | Type | Description |
|-------|------|-------------|
| type | str | Link type name (e.g., "Blocks", "Relates", "Clones") |
| inwardIssue | JiraIssue? | Inward linked issue |
| outwardIssue | JiraIssue? | Outward linked issue |

## Relationships

```
JiraProject --[has many]--> JiraIssue
JiraIssue --[has current]--> Status
JiraIssue --[available]--> IssueTransition (depends on current status + workflow)
JiraIssue --[has many]--> Comment
JiraIssue --[has many]--> IssueLink
ConfluenceSpace --[has many]--> ConfluencePage
ConfluencePage --[has parent]--> ConfluencePage (hierarchy)
ConfluencePage --[has many]--> Comment
JiraIssue --[links to]--> ConfluencePage (cross-product via remote links)
```

## State Transitions

### Jira Issue Lifecycle (typical, varies by workflow)

```
Open → In Progress → Resolved → Closed
Open → In Progress → Reopened → In Progress → Resolved → Closed
Open → Won't Fix → Closed
```

Available transitions depend on:
1. The project's configured workflow
2. The issue's current status
3. The user's permissions

### Confluence Page Lifecycle

```
Draft → Current (published)
Current → Updated (new version, current version incremented)
```

## Deployment Type Differences

| Aspect | Cloud | Server/Data Center |
|--------|-------|--------------------|
| Auth | Email + API token | Username + PAT |
| Jira URL | `https://your-domain.atlassian.net` | `https://jira.example.com` |
| Confluence URL | Same domain as Jira | Separate URL possible |
| REST API | v3 (Cloud) + v2 | v2 |
| Custom fields | Consistent format | Instance-specific IDs |
