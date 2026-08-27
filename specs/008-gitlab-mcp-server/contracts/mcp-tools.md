# MCP Tool Reference: GitLab MCP Server

**Feature**: 008-gitlab-mcp-server
**Date**: 2026-03-27
**Transport**: stdio (local process via `npx @zereight/mcp-gitlab`)
**Auth**: GitLab Personal Access Token via `GITLAB_PERSONAL_ACCESS_TOKEN` env var
**Source**: Community @zereight/mcp-gitlab (TypeScript/Node.js, MIT license, 98+ tools)

> These tools are provided by the community @zereight/mcp-gitlab package. NetGeniusClaw registers and spawns it — it does not implement the tools. Only key tools are documented here; the full set is available in the package documentation.

## Key Tools by Category

### Issues

| Tool | Description | Write? |
|------|-------------|--------|
| list_issues | List issues with filters (state, labels, assignee, milestone) | No |
| get_issue | Get issue details by project and issue IID | No |
| create_issue | Create a new issue with title, description, labels, assignee | Yes |
| update_issue | Update issue fields (title, description, state, labels, assignee) | Yes |
| add_issue_comment | Add a comment (note) to an issue | Yes |
| list_issue_comments | List comments on an issue | No |

### Merge Requests

| Tool | Description | Write? |
|------|-------------|--------|
| list_merge_requests | List MRs with filters (state, labels, source/target branch) | No |
| get_merge_request | Get MR details including diff stats and approval status | No |
| create_merge_request | Create a new MR with title, source/target branches | Yes |
| update_merge_request | Update MR fields (title, description, labels, assignee) | Yes |
| merge_merge_request | Merge an MR (with optional squash, remove source branch) | Yes |
| add_merge_request_comment | Add a comment to an MR | Yes |

### Pipelines

| Tool | Description | Write? |
|------|-------------|--------|
| list_pipelines | List pipelines with filters (status, ref, source) | No |
| get_pipeline | Get pipeline details | No |
| get_pipeline_jobs | List jobs in a pipeline | No |
| get_pipeline_job_log | Get job console output | No |
| create_pipeline | Trigger a new pipeline on a branch | Yes |
| retry_pipeline | Retry a failed pipeline | Yes |
| cancel_pipeline | Cancel a running pipeline | Yes |

### Repository

| Tool | Description | Write? |
|------|-------------|--------|
| list_repository_tree | List files and directories in a repository | No |
| get_file_content | Get raw content of a file at a specific ref | No |
| list_commits | List commits with filters (branch, path, date range) | No |
| get_commit | Get commit details including diff | No |
| compare_branches | Compare two branches (diff summary) | No |

### Projects

| Tool | Description | Write? |
|------|-------------|--------|
| list_projects | List accessible projects with filters | No |
| get_project | Get project details by ID or path | No |
| search_projects | Search projects by name or keyword | No |

### Labels, Milestones, Releases, Wiki

| Tool | Description | Write? |
|------|-------------|--------|
| list_labels / create_label / update_label / delete_label | Label CRUD | Mixed |
| list_milestones / create_milestone / update_milestone | Milestone management | Mixed |
| list_releases / get_release / create_release | Release management | Mixed |
| list_wiki_pages / get_wiki_page / create_wiki_page / update_wiki_page / delete_wiki_page | Wiki CRUD | Mixed |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| GITLAB_PERSONAL_ACCESS_TOKEN | Yes | GitLab PAT with `api` or `read_api` scope |
| GITLAB_API_URL | No | GitLab API URL (default: https://gitlab.com) |
| GITLAB_READ_ONLY_MODE | No | Restrict to read-only operations (default: false) |

## Error Responses

All tools return structured error messages for:
- **Connection failure**: GitLab API unreachable at configured URL
- **Authentication failure**: Invalid or expired personal access token
- **Not found**: Project, issue, MR, or pipeline does not exist
- **Permission denied**: Token lacks required scope or user lacks project access
- **Rate limited**: Too many requests — retry after backoff period
- **Conflict**: Merge request has conflicts and cannot be merged
