# GitLab MCP Server

Community GitLab MCP server integration for netgeniusclaw, providing 98+ tools for GitLab project management, CI/CD pipeline monitoring, repository browsing, and issue/merge request workflows.

## Server Details

| Property | Value |
|----------|-------|
| Package | [@zereight/mcp-gitlab](https://github.com/zereight/mcp-gitlab) |
| Language | TypeScript / Node.js |
| License | MIT |
| Transport | stdio (spawned via `npx -y @zereight/mcp-gitlab`) |
| Tools | 98+ across 9 categories |
| Auth | GitLab Personal Access Token (PAT) |
| Platforms | gitlab.com (SaaS), self-hosted GitLab (any tier) |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITLAB_PERSONAL_ACCESS_TOKEN` | Yes | GitLab PAT with `api` (full access) or `read_api` (read-only) scope |
| `GITLAB_API_URL` | No | GitLab API URL. Default: `https://gitlab.com`. Override for self-hosted instances (e.g., `https://gitlab.example.com`) |
| `GITLAB_READ_ONLY_MODE` | No | Set to `true` to restrict the skill to read-only operations. Default: `false` |

## Authentication

### GitLab.com (SaaS)

1. Go to **Settings > Access Tokens** (or **User Settings > Access Tokens** for personal tokens)
2. Create a token with the required scopes:
   - `read_api` — Read-only access (issues, MRs, pipelines, repositories)
   - `api` — Full access including write operations (create issues, merge MRs, trigger pipelines)
3. Set `GITLAB_PERSONAL_ACCESS_TOKEN` in your environment

### Self-Hosted GitLab

1. Navigate to your GitLab instance: `https://gitlab.example.com/-/user_settings/personal_access_tokens`
2. Create a token with the required scopes
3. Set environment variables:
   ```bash
   export GITLAB_PERSONAL_ACCESS_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
   export GITLAB_API_URL="https://gitlab.example.com"
   ```

### Self-Signed TLS Certificates

For self-hosted instances with self-signed certificates, set:
```bash
export NODE_TLS_REJECT_UNAUTHORIZED=0
```

**Security warning**: This disables TLS certificate verification for all Node.js connections. Use only in trusted network environments. The recommended approach is to add your CA certificate to the system trust store instead.

## Registration (openclaw.json)

```json
{
  "gitlab-mcp": {
    "command": "npx",
    "args": ["-y", "@zereight/mcp-gitlab"],
    "env": {
      "GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_PERSONAL_ACCESS_TOKEN}",
      "GITLAB_API_URL": "${GITLAB_API_URL:-https://gitlab.com}"
    }
  }
}
```

## Tool Categories (98+ tools)

### Issues
- `list_issues` — List issues with filters (state, labels, assignee, milestone)
- `get_issue` — Get issue details by project and issue IID
- `create_issue` — Create a new issue with title, description, labels, assignee
- `update_issue` — Update issue fields (title, description, state, labels, assignee)
- `add_issue_comment` — Add a comment (note) to an issue
- `list_issue_comments` — List comments on an issue

### Merge Requests
- `list_merge_requests` — List MRs with filters (state, labels, source/target branch)
- `get_merge_request` — Get MR details including diff stats and approval status
- `create_merge_request` — Create a new MR with title, source/target branches
- `update_merge_request` — Update MR fields (title, description, labels, assignee)
- `merge_merge_request` — Merge an MR (with optional squash, remove source branch)
- `add_merge_request_comment` — Add a comment to an MR

### Pipelines
- `list_pipelines` — List pipelines with filters (status, ref, source)
- `get_pipeline` — Get pipeline details
- `get_pipeline_jobs` — List jobs in a pipeline
- `get_pipeline_job_log` — Get job console output
- `create_pipeline` — Trigger a new pipeline on a branch
- `retry_pipeline` — Retry a failed pipeline
- `cancel_pipeline` — Cancel a running pipeline

### Repository
- `list_repository_tree` — List files and directories in a repository
- `get_file_content` — Get raw content of a file at a specific ref
- `list_commits` — List commits with filters (branch, path, date range)
- `get_commit` — Get commit details including diff
- `compare_branches` — Compare two branches (diff summary)

### Projects
- `list_projects` — List accessible projects with filters
- `get_project` — Get project details by ID or path
- `search_projects` — Search projects by name or keyword

### Labels
- `list_labels` / `create_label` / `update_label` / `delete_label`

### Milestones
- `list_milestones` / `create_milestone` / `update_milestone`

### Releases
- `list_releases` / `get_release` / `create_release`

### Wiki
- `list_wiki_pages` / `get_wiki_page` / `create_wiki_page` / `update_wiki_page` / `delete_wiki_page`

## Read-Only Mode

Set `GITLAB_READ_ONLY_MODE=true` to restrict the integration to observation-only operations. In this mode, the skill will only use read tools (`list_*`, `get_*`, `search_*`) and skip all write tools (`create_*`, `update_*`, `delete_*`, `merge_*`).

This is useful for:
- Monitoring-only deployments where write access is not desired
- Using a PAT with `read_api` scope only
- Compliance environments that require read-only integrations

## Usage Examples

Once registered with an MCP client (OpenClaw, the agent Desktop, etc.):

- "Show me open issues in project network-automation"
- "List merge requests awaiting review in project infra-configs"
- "Show pipelines for project network-configs on the main branch"
- "Get the job log for the deploy stage in pipeline #456"
- "Show the directory structure of project network-configs"
- "Show me the contents of ansible/site.yml on the develop branch"
- "Create an issue in project network-automation titled 'BGP peer flapping on router-01'"
- "Find all projects matching 'network'"

## Error Handling

All tools return structured error messages for:
- **Connection failure**: GitLab API unreachable at configured URL
- **Authentication failure**: Invalid or expired personal access token
- **Not found**: Project, issue, MR, or pipeline does not exist
- **Permission denied**: Token lacks required scope or user lacks project access
- **Rate limited**: Too many requests — retry after backoff period
- **Conflict**: Merge request has conflicts and cannot be merged

## Alternative: Official GitLab MCP Server

For teams with GitLab Premium or Ultimate subscriptions, the [official GitLab MCP server](https://docs.gitlab.com/ee/user/gitlab_duo/mcp/) (beta) is available. It uses OAuth 2.0 authentication and HTTP transport at `/api/v4/mcp`. The community server (@zereight/mcp-gitlab) is recommended for broader compatibility across all GitLab tiers.

## Prerequisites

- Node.js 18+ (for `npx`)
- Network connectivity from the AI assistant host to the GitLab instance
- GitLab Personal Access Token with appropriate scopes
