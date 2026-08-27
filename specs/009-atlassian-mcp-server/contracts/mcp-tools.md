# MCP Tool Reference: Atlassian MCP Server

**Feature**: 009-atlassian-mcp-server
**Date**: 2026-03-27
**Transport**: stdio (local process via `uvx mcp-atlassian`)
**Auth**: API Token (Cloud) or Personal Access Token (Server/DC) via env vars
**Source**: Community mcp-atlassian by sooperset (Python, Apache 2.0, 72 tools)

> These tools are provided by the community mcp-atlassian package. NetGeniusClaw registers and spawns it — it does not implement the tools. Only key tools are documented here; the full set is available in the package documentation.

## Key Tools by Category

### Jira Issues

| Tool | Description | Write? |
|------|-------------|--------|
| jira_search | Search issues using JQL (Jira Query Language) | No |
| jira_get_issue | Get issue details by key (e.g., NET-1234) | No |
| jira_create_issue | Create a new issue with type, title, description, priority | Yes |
| jira_update_issue | Update issue fields (summary, description, labels, assignee, priority) | Yes |
| jira_delete_issue | Delete an issue | Yes |
| jira_get_issue_comments | List comments on an issue | No |
| jira_add_comment | Add a comment to an issue | Yes |
| jira_batch_create_issues | Create multiple issues in one operation | Yes |

### Jira Transitions

| Tool | Description | Write? |
|------|-------------|--------|
| jira_get_transitions | List available transitions for an issue (based on current status + workflow) | No |
| jira_transition_issue | Perform a workflow transition (e.g., Open → In Progress) | Yes |

### Jira Project & Fields

| Tool | Description | Write? |
|------|-------------|--------|
| jira_get_projects | List all accessible projects | No |
| jira_get_project | Get project details by key | No |
| jira_get_fields | List all fields (standard + custom) | No |
| jira_get_issue_types | List available issue types for a project | No |

### Jira Links

| Tool | Description | Write? |
|------|-------------|--------|
| jira_link_issues | Create a link between two issues | Yes |
| jira_get_issue_links | List links for an issue | No |
| jira_get_link_types | List available link types | No |

### Confluence Pages

| Tool | Description | Write? |
|------|-------------|--------|
| confluence_search | Search pages using CQL (Confluence Query Language) | No |
| confluence_get_page | Get page content by ID or title+space | No |
| confluence_create_page | Create a new page in a space with title and body | Yes |
| confluence_update_page | Update page content (creates new version) | Yes |
| confluence_delete_page | Delete a page | Yes |

### Confluence Comments

| Tool | Description | Write? |
|------|-------------|--------|
| confluence_get_page_comments | List comments on a page | No |
| confluence_add_comment | Add a comment to a page | Yes |

### Confluence Spaces

| Tool | Description | Write? |
|------|-------------|--------|
| confluence_get_spaces | List all accessible spaces | No |
| confluence_get_space | Get space details by key | No |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| JIRA_URL | Conditional | Jira instance URL (required if using Jira tools) |
| JIRA_USERNAME | Conditional | Email (Cloud) or username (Server/DC) |
| JIRA_API_TOKEN | Conditional | API token (Cloud) or PAT (Server/DC) |
| CONFLUENCE_URL | Conditional | Confluence instance URL (required if using Confluence tools) |
| CONFLUENCE_USERNAME | Conditional | Email (Cloud) or username (Server/DC) |
| CONFLUENCE_API_TOKEN | Conditional | API token (Cloud) or PAT (Server/DC) |

At least one product (Jira or Confluence) must be configured. If only one is configured, tools for the other product are not available.

## Error Responses

All tools return structured error messages for:
- **Connection failure**: Atlassian instance unreachable at configured URL
- **Authentication failure**: Invalid API token or PAT
- **Not found**: Project, issue, page, or space does not exist
- **Permission denied**: Token lacks required permissions or user lacks project/space access
- **Rate limited**: Too many requests — retry after backoff period
- **Invalid transition**: Requested workflow transition not available from current status
- **Validation error**: Required fields missing or invalid values for issue creation/update
