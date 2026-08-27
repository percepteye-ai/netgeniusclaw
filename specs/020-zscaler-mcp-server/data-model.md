# Data Model: Zscaler MCP Server Integration

**Feature**: 020-zscaler-mcp-server | **Date**: 2026-04-04

## Overview

This is a stateless MCP server integration. The Zscaler MCP server acts as a proxy to Zscaler's OneAPI. No local data storage is required.

## External Entities

### ZPA Application Segment

| Field | Type | Description |
|-------|------|-------------|
| id | string | Segment identifier |
| name | string | Segment name |
| description | string | Segment description |
| enabled | boolean | Active status |
| domain_names | array | Application domains |
| segment_group_id | string | Parent group |
| server_groups | array | Associated server groups |
| tcp_port_ranges | array | TCP ports |
| udp_port_ranges | array | UDP ports |
| double_encrypt | boolean | Double encryption |
| bypass_type | enum | Bypass configuration |

### ZPA Access Policy

| Field | Type | Description |
|-------|------|-------------|
| id | string | Policy identifier |
| name | string | Policy name |
| description | string | Description |
| action | enum | ALLOW, DENY |
| rule_order | integer | Evaluation order |
| conditions | array | Policy conditions |
| app_connector_groups | array | Connector groups |
| app_server_groups | array | Server groups |

### ZIA Firewall Rule

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Rule identifier |
| name | string | Rule name |
| order | integer | Rule order |
| rank | integer | Rule rank |
| state | enum | ENABLED, DISABLED |
| action | enum | ALLOW, BLOCK, CAUTION |
| src_ips | array | Source IPs |
| dest_addresses | array | Destinations |
| dest_ip_categories | array | IP categories |
| dest_countries | array | Countries |
| nw_applications | array | Applications |
| nw_application_groups | array | App groups |
| app_services | array | App services |
| app_service_groups | array | Service groups |
| labels | array | Labels |
| time_windows | array | Time windows |

### ZIA URL Filtering Rule

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Rule identifier |
| name | string | Rule name |
| order | integer | Rule order |
| state | enum | ENABLED, DISABLED |
| action | enum | ALLOW, CAUTION, BLOCK |
| url_categories | array | URL categories |
| protocols | array | Protocols |
| locations | array | Locations |
| groups | array | User groups |
| departments | array | Departments |
| time_windows | array | Time windows |
| block_override | boolean | Allow override |

### ZDX Application

| Field | Type | Description |
|-------|------|-------------|
| id | string | Application identifier |
| name | string | Application name |
| score | integer | ZDX score (0-100) |
| page_fetch_time | integer | Page load time (ms) |
| server_response_time | integer | Server time (ms) |
| dns_time | integer | DNS resolution (ms) |
| availability | float | Availability percentage |
| affected_users | integer | Impacted users |

### ZDX User

| Field | Type | Description |
|-------|------|-------------|
| id | string | User identifier |
| email | string | User email |
| device_id | string | Device ID |
| zscaler_score | integer | Overall score |
| device_score | integer | Device score |
| network_score | integer | Network score |
| app_score | integer | Application score |
| location | string | User location |

## Relationships

```
┌──────────────────────────────────────────────────────────────┐
│                        Zscaler Zero Trust                      │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │     ZPA     │    │     ZIA     │    │     ZDX     │       │
│  │  Private    │    │  Internet   │    │  Experience │       │
│  │  Access     │    │  Access     │    │  Monitoring │       │
│  └─────────────┘    └─────────────┘    └─────────────┘       │
│         │                  │                  │               │
│         ▼                  ▼                  ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │ App Segments│    │  Firewall   │    │Applications │       │
│  │ Policies    │    │  Rules      │    │Users        │       │
│  │ Connectors  │    │  URL Filter │    │Metrics      │       │
│  └─────────────┘    └─────────────┘    └─────────────┘       │
│                                                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │  ZIdentity  │    │  Z-Insights │    │    EASM     │       │
│  │  Users/IdP  │    │  Analytics  │    │  Attack     │       │
│  │             │    │  Threat Int.│    │  Surface    │       │
│  └─────────────┘    └─────────────┘    └─────────────┘       │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

## Policy Hierarchy

### ZPA Access Policy Evaluation
```
Global Policy → Segment Group Policy → Application Policy
                         ↓
               [First Match Wins]
```

### ZIA Rule Evaluation
```
Firewall Rules → URL Rules → DLP Rules → SSL Rules
       ↓              ↓           ↓          ↓
   [Action]      [Action]    [Action]   [Action]
```

## No Local Storage

This integration does not persist any data locally. All state is maintained by Zscaler.
