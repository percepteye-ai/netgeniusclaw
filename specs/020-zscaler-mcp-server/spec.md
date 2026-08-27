# Feature Specification: Zscaler MCP Server Integration

**Feature ID**: 020-zscaler-mcp-server
**Status**: Draft
**Created**: 2026-04-04

## Overview

Integrate the official Zscaler MCP server to provide comprehensive Zero Trust security management within NetGeniusClaw. This is the largest single integration with 300+ tools across ZIA, ZPA, ZDX, ZCC, and other Zscaler services.

## Source

- **Repository**: https://github.com/zscaler/zscaler-mcp-server
- **Type**: Official (Zscaler-maintained)
- **License**: MIT
- **Transport**: stdio, SSE, or StreamableHTTP

## Tools Available (300+ total)

### By Service

| Service | Tools | Description |
|---------|-------|-------------|
| **ZIA** | 106 | Internet Access security policies, firewall rules, URL filtering |
| **ZPA** | 88 | Private Access application segments, connectors, policies |
| **ZDX** | 31 | Digital Experience monitoring, user experience metrics |
| **ZMS** | 20 | Microsegmentation agents and resources |
| **ZTW** | 19 | Workload Segmentation policies |
| **Z-Insights** | 16 | Analytics and threat intelligence |
| **ZIdentity** | 10 | Identity and access management |
| **EASM** | 7 | External Attack Surface Management |
| **ZCC** | 4 | Client Connector device management |

### Tool Naming Convention

- **Read-only**: `list_*`, `get_*` (always available)
- **Write**: `create_*`, `update_*` (requires --enable-write-tools)
- **Delete**: `delete_*` (requires cryptographic confirmation)

## Environment Variables

### OneAPI Authentication (Recommended)

| Variable | Required | Description |
|----------|----------|-------------|
| `ZSCALER_CLIENT_ID` | Yes | OAuth client ID |
| `ZSCALER_CLIENT_SECRET` | Yes | OAuth client secret |
| `ZSCALER_CUSTOMER_ID` | Yes | Customer ID |
| `ZSCALER_VANITY_DOMAIN` | Yes | Organization vanity domain |
| `ZSCALER_CLOUD` | No | Cloud environment (e.g., 'beta') |

### MCP Server Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `ZSCALER_MCP_TRANSPORT` | No | Transport type (stdio/sse/streamable-http) |
| `ZSCALER_MCP_SERVICES` | No | Comma-separated service list |
| `ZSCALER_MCP_WRITE_ENABLED` | No | Enable write operations |
| `ZSCALER_MCP_WRITE_TOOLS` | No | Allowlist pattern for write tools |

## User Stories

### US1: ZPA Application Visibility (Priority: P1) MVP
**As a** network security engineer
**I want to** view ZPA application segments and access policies
**So that** I can understand private application access controls

**Acceptance Criteria:**
- Can list application segments with details
- Can view segment groups and policies
- Can identify connector assignments

### US2: ZIA Policy Inspection (Priority: P1) MVP
**As a** network security engineer
**I want to** inspect ZIA firewall and URL filtering rules
**So that** I can audit internet access policies

**Acceptance Criteria:**
- Can list firewall rules with priorities
- Can view URL filtering policies
- Can identify rule categories and actions

### US3: ZDX Experience Monitoring (Priority: P2)
**As a** network operations engineer
**I want to** view ZDX digital experience metrics
**So that** I can identify user experience issues

**Acceptance Criteria:**
- Can view application performance scores
- Can identify degraded paths
- Can correlate with network metrics

### US4: Security Policy Management (Priority: P3)
**As a** network security engineer
**I want to** create and update security policies
**So that** I can respond to security requirements

**Acceptance Criteria:**
- Can create application segments (with approval)
- Can update firewall rules (with approval)
- All changes require ServiceNow CR

## Proposed Skills

| Skill | Tools | Description |
|-------|-------|-------------|
| `zscaler-zpa` | 20 | Private Access application and policy management |
| `zscaler-zia` | 20 | Internet Access firewall and filtering |
| `zscaler-zdx` | 10 | Digital Experience monitoring |
| `zscaler-identity` | 8 | Identity and connector management |
| `zscaler-insights` | 6 | Analytics and threat intelligence |

## Integration Points

- **ServiceNow**: CR approval for write operations
- **PagerDuty**: Alert on ZDX experience degradation
- **Splunk**: Forward Zscaler logs for analysis
- **Grafana**: Visualize ZDX metrics

## Clarifications

### Session 2026-04-04
- Q: Zscaler services to enable? → A: Enable ALL 9 services (ZIA, ZPA, ZDX, ZMS, ZTW, Z-Insights, ZIdentity, EASM, ZCC)

## Security Considerations

- All 9 Zscaler services enabled (300+ tools total)
- Read-only mode by default (110+ read-only tools always available)
- Write operations require explicit flag and allowlist
- Delete operations require cryptographic confirmation token
- HTTPS required for non-localhost deployments

## Success Criteria

1. Can query "list my ZPA application segments" and get results
2. Can query "show ZIA firewall rules" and see policy details
3. Integration appears in NetGeniusClaw UI with correct tool count
4. All 5 skills documented with SKILL.md files
