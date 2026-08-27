# Research: Azure Networking MCP Server

**Feature**: 004-azure-network-mcp | **Date**: 2026-03-26

## Research Tasks & Findings

### 1. Azure SDK Client Architecture

**Decision**: Use `azure-identity.DefaultAzureCredential` with `azure-mgmt-network.NetworkManagementClient` and `azure-mgmt-resource.ResourceManagementClient`.

**Rationale**: `DefaultAzureCredential` chains multiple credential sources (environment variables, managed identity, Azure CLI, etc.) and is the Azure-recommended approach. For the NetGeniusClaw use case, the primary path is `ClientSecretCredential` via env vars (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET), but `DefaultAzureCredential` allows flexibility for development (Azure CLI auth) and production (managed identity) without code changes.

**Alternatives considered**:
- `ClientSecretCredential` directly: Too rigid; doesn't support development scenarios.
- `AzureCliCredential` only: Not suitable for headless/CI environments.
- `ChainedTokenCredential` with custom chain: Unnecessary complexity; `DefaultAzureCredential` already provides the right chain.

### 2. Multi-Subscription Support Pattern

**Decision**: Accept an optional `subscription_id` parameter on each tool. Default to `AZURE_SUBSCRIPTION_ID` env var. Create new `NetworkManagementClient` instances per subscription. Cap concurrent subscriptions at 5 using `asyncio.Semaphore`.

**Rationale**: Azure SDK clients are bound to a subscription at construction time. Creating per-subscription clients is the idiomatic approach. A semaphore prevents exceeding the ARM API rate limit of ~1200 reads per 5 minutes per tenant.

**Alternatives considered**:
- Single client with subscription switching: Not supported by Azure SDK; clients are immutable per subscription.
- Pre-create clients for all subscriptions at startup: Requires knowing subscriptions upfront; less flexible.
- No concurrency limit: Risk of ARM API throttling (HTTP 429) causing cascading failures.

### 3. Azure ARM API Version Pinning

**Decision**: Pin API versions as constants in `utils/constants.py`. Use `api_version="2024-05-01"` for `Microsoft.Network` resources (latest stable as of 2026).

**Rationale**: Pinning ensures deterministic behavior across environments. The Azure SDK's default API version resolution can vary by SDK version, leading to inconsistencies. Explicit pinning also makes upgrades intentional and auditable.

**Alternatives considered**:
- Use SDK default versions: Risk of behavior changes on SDK updates.
- Use latest preview versions: Unstable; features may be removed.
- Per-resource-type versions: Unnecessary granularity; the `Microsoft.Network` resource provider uses a single API version for all resource types.

### 4. Rate Limiting and Retry Strategy

**Decision**: Implement exponential backoff with jitter, respecting `Retry-After` headers from Azure ARM. Use the `azure-core` built-in retry policy with custom configuration.

**Rationale**: Azure ARM returns HTTP 429 with a `Retry-After` header when rate-limited. The `azure-core` library already implements retry logic; we configure it with max_retries=3, exponential backoff, and respect for Retry-After headers. This avoids reimplementing retry logic.

**Alternatives considered**:
- Custom retry wrapper: Unnecessary; azure-core handles this.
- No retry (fail fast): Poor user experience for transient throttling.
- Fixed delay retry: Less efficient than exponential backoff with jitter.

### 5. Pagination Handling

**Decision**: Use Azure SDK's built-in `.list()` paging iterators. All list operations return `ItemPaged` objects that handle continuation tokens automatically. Wrap in a utility function that collects all pages.

**Rationale**: Azure SDK `list_*()` methods return `ItemPaged` iterators that transparently handle Azure ARM pagination. No custom pagination logic needed.

**Alternatives considered**:
- Manual continuation token handling: Redundant; SDK does this.
- Limit result counts: Could miss resources; unsafe for audit operations.

### 6. CIS Azure Foundations Benchmark Implementation

**Decision**: Implement CIS Azure Foundations Benchmark v2.1.0 NSG-related rules as Python functions in `compliance/cis_azure.py`. Key rules include:
- Rule 6.1: Restrict RDP (port 3389) from internet (0.0.0.0/0)
- Rule 6.2: Restrict SSH (port 22) from internet
- Rule 6.3: Restrict UDP from internet
- Rule 6.4: Ensure NSG flow logs are enabled and retained >= 90 days

**Rationale**: CIS benchmarks are the industry standard for cloud security baseline assessment. Starting with NSG-related rules aligns with the spec's requirement for compliance auditing as a P2 capability.

**Alternatives considered**:
- Open Policy Agent (OPA/Rego): Adds a heavy dependency for initial implementation; consider for future extensibility.
- Azure Policy integration: Requires additional Azure permissions beyond Reader; not suitable for read-only assessment.
- Custom rule engine: Unnecessary complexity for a well-defined rule set.

### 7. FastMCP Server Pattern

**Decision**: Use FastMCP's `@mcp.tool()` decorator pattern with stdio transport. One tool function per Azure resource type. Each tool accepts optional `subscription_id` parameter and returns structured JSON.

**Rationale**: Consistent with the Python MCP server pattern used throughout NetGeniusClaw (pyATS_MCP, etc.). FastMCP simplifies MCP protocol handling and tool registration.

**Alternatives considered**:
- Node.js MCP SDK: Project standardizes on Python for MCP servers (constitution constraint).
- SSE transport: Stdio is the standard for local MCP servers in NetGeniusClaw; SSE adds unnecessary network complexity.
- Raw JSON-RPC implementation: FastMCP abstracts this; no reason to reimplement.

### 8. GAIT Audit Integration

**Decision**: Import and call `gait_mcp` logging functions from within each tool handler. Log operation type, target resource, subscription ID, and result status.

**Rationale**: GAIT is the existing audit infrastructure (Constitution Principle IV). All existing MCP servers integrate with it. Reusing the same pattern ensures audit consistency.

**Alternatives considered**:
- Separate audit MCP server calls: Adds latency; direct integration is simpler.
- Custom logging: Violates Constitution Principle IV requirement for GAIT.

### 9. Error Handling Strategy

**Decision**: Catch Azure SDK exceptions (`HttpResponseError`, `ClientAuthenticationError`, `ResourceNotFoundError`) and translate to user-friendly MCP error responses with actionable guidance.

**Rationale**: Raw Azure exceptions contain technical details (ARM error codes, request IDs) that are not actionable for users. Translating to clear messages with remediation steps (e.g., "Service principal lacks Reader role on subscription X") improves usability.

**Alternatives considered**:
- Pass through raw exceptions: Poor user experience.
- Generic error messages: Not actionable; users need specific guidance.

### 10. Network Watcher Dependency

**Decision**: Check Network Watcher availability per-region before attempting Network Watcher operations. Return a clear informational message when unavailable.

**Rationale**: Network Watcher is not automatically enabled in all regions for all subscriptions. Attempting operations without it yields confusing errors. Proactive checking aligns with the edge case requirement in the spec.

**Alternatives considered**:
- Assume Network Watcher is always available: Leads to confusing errors.
- Skip Network Watcher entirely: Loses valuable diagnostic capability.
