# Data Model: GitLab MCP Server Integration

**Feature**: 008-gitlab-mcp-server
**Date**: 2026-03-27

## Entities

### GitLabConfig

Runtime configuration for the GitLab MCP server connection, sourced entirely from environment variables.

| Field | Type | Source | Default | Validation |
|-------|------|--------|---------|------------|
| personal_access_token | str | `GITLAB_PERSONAL_ACCESS_TOKEN` | (required) | Non-empty string, valid GitLab PAT |
| api_url | str | `GITLAB_API_URL` | `https://gitlab.com` | Must be valid HTTPS URL |
| read_only_mode | bool | `GITLAB_READ_ONLY_MODE` | `false` | "true"/"false" |

**Validation rules**:
- `personal_access_token` must be a valid GitLab PAT with appropriate scopes
- `api_url` must not have a trailing slash
- Server fails to start if `GITLAB_PERSONAL_ACCESS_TOKEN` is not set

### GitLabProject

A repository with associated issues, merge requests, pipelines, wiki, and settings.

| Field | Type | Description |
|-------|------|-------------|
| id | int | Numeric project ID |
| path_with_namespace | str | Full project path including group nesting (e.g., "org/team/project") |
| name | str | Project display name |
| description | str? | Project description |
| default_branch | str | Default branch name |
| visibility | str | "private", "internal", or "public" |
| web_url | str | GitLab web URL |

### Issue

A work item within a GitLab project.

| Field | Type | Description |
|-------|------|-------------|
| iid | int | Project-scoped issue number |
| title | str | Issue title |
| description | str? | Issue body (markdown) |
| state | str | "opened" or "closed" |
| assignees | list[User] | Assigned users |
| labels | list[str] | Applied labels |
| milestone | Milestone? | Associated milestone |
| created_at | str | ISO 8601 creation timestamp |
| updated_at | str | ISO 8601 last update timestamp |
| web_url | str | GitLab web URL |

### MergeRequest

A code change proposal within a GitLab project.

| Field | Type | Description |
|-------|------|-------------|
| iid | int | Project-scoped MR number |
| title | str | MR title |
| description | str? | MR body (markdown) |
| state | str | "opened", "closed", or "merged" |
| source_branch | str | Source branch name |
| target_branch | str | Target branch name |
| assignees | list[User] | Assigned reviewers |
| labels | list[str] | Applied labels |
| merge_status | str | "can_be_merged", "cannot_be_merged", etc. |
| pipeline | Pipeline? | Head pipeline status |
| web_url | str | GitLab web URL |

### Pipeline

A CI/CD pipeline execution.

| Field | Type | Description |
|-------|------|-------------|
| id | int | Pipeline ID |
| status | str | "running", "pending", "success", "failed", "canceled", "skipped" |
| ref | str | Branch or tag name |
| sha | str | Commit SHA |
| created_at | str | ISO 8601 creation timestamp |
| updated_at | str | ISO 8601 last update timestamp |
| web_url | str | GitLab web URL |

### PipelineJob

A single job within a pipeline stage.

| Field | Type | Description |
|-------|------|-------------|
| id | int | Job ID |
| name | str | Job name |
| stage | str | Pipeline stage name |
| status | str | "running", "pending", "success", "failed", "canceled" |
| duration | float? | Duration in seconds |
| runner | str? | Runner name/description |
| web_url | str | GitLab web URL |

### Commit

A source code change.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Full commit SHA |
| short_id | str | Abbreviated SHA |
| title | str | Commit message first line |
| message | str | Full commit message |
| author_name | str | Author name |
| authored_date | str | ISO 8601 author date |
| web_url | str | GitLab web URL |

### Label

A categorization tag.

| Field | Type | Description |
|-------|------|-------------|
| id | int | Label ID |
| name | str | Label name |
| color | str | Hex color code |
| description | str? | Label description |

### Milestone

A time-bounded project goal.

| Field | Type | Description |
|-------|------|-------------|
| id | int | Milestone ID |
| title | str | Milestone title |
| due_date | str? | Due date (YYYY-MM-DD) |
| state | str | "active" or "closed" |

### Release

A versioned package.

| Field | Type | Description |
|-------|------|-------------|
| tag_name | str | Git tag |
| name | str | Release name |
| description | str? | Release notes (markdown) |
| created_at | str | ISO 8601 creation timestamp |

### WikiPage

A documentation page.

| Field | Type | Description |
|-------|------|-------------|
| slug | str | URL-safe page identifier |
| title | str | Page title |
| content | str | Page body (markdown) |
| format | str | Content format ("markdown", "rdoc", "asciidoc") |

## Relationships

```
GitLabProject --[has many]--> Issue
GitLabProject --[has many]--> MergeRequest
GitLabProject --[has many]--> Pipeline --[has many]--> PipelineJob
GitLabProject --[has many]--> Commit
GitLabProject --[has many]--> Label
GitLabProject --[has many]--> Milestone
GitLabProject --[has many]--> Release
GitLabProject --[has many]--> WikiPage
MergeRequest --[has one]--> Pipeline (head pipeline)
Issue --[has many]--> Label
Issue --[has one?]--> Milestone
MergeRequest --[has many]--> Label
MergeRequest --[has one?]--> Milestone
```

## State Transitions

### Issue Lifecycle
```
opened → closed (→ reopened → closed)
```

### Merge Request Lifecycle
```
opened → merged
opened → closed (→ reopened → merged/closed)
```

### Pipeline Lifecycle
```
created → pending → running → success/failed/canceled
```
