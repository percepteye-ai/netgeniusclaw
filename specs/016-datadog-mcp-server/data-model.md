# Data Model: Datadog MCP Server Integration

**Feature**: 016-datadog-mcp-server | **Date**: 2026-04-04

## Overview

This is a stateless remote MCP server integration. The Datadog MCP server acts as a managed proxy to Datadog's APIs. No local data storage is required.

## External Entities (Datadog API)

### Log

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique log identifier |
| timestamp | datetime | Log timestamp |
| message | string | Log message content |
| status | enum | info, warn, error, debug |
| service | string | Service name |
| host | string | Hostname |
| tags | array | Associated tags |
| attributes | object | Custom attributes |

### Metric

| Field | Type | Description |
|-------|------|-------------|
| metric | string | Metric name |
| points | array | Time series data points |
| type | enum | gauge, count, rate |
| unit | string | Measurement unit |
| tags | array | Metric tags |

### Trace

| Field | Type | Description |
|-------|------|-------------|
| trace_id | string | Unique trace identifier |
| spans | array | Trace spans |
| service | string | Root service name |
| resource | string | Resource name |
| duration | integer | Total duration (ns) |
| error | boolean | Has errors |

### Span

| Field | Type | Description |
|-------|------|-------------|
| span_id | string | Unique span identifier |
| name | string | Operation name |
| service | string | Service name |
| resource | string | Resource name |
| type | string | Span type |
| start | integer | Start time (ns) |
| duration | integer | Duration (ns) |
| error | integer | Error flag |
| meta | object | Span metadata |
| metrics | object | Span metrics |

### Incident

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique incident identifier |
| title | string | Incident title |
| status | enum | active, stable, resolved |
| severity | enum | SEV-1, SEV-2, SEV-3, SEV-4, SEV-5 |
| created | datetime | Creation timestamp |
| modified | datetime | Last modification |
| commander | object | Incident commander |
| customer_impact | object | Customer impact details |
| fields | object | Custom fields |
| timeline | array | Timeline events |

### Monitor

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Monitor identifier |
| name | string | Monitor name |
| type | string | Monitor type |
| query | string | Monitor query |
| message | string | Alert message |
| tags | array | Associated tags |
| options | object | Monitor options |
| overall_state | enum | OK, Alert, Warn, No Data |

### Dashboard

| Field | Type | Description |
|-------|------|-------------|
| id | string | Dashboard identifier |
| title | string | Dashboard title |
| description | string | Description |
| widgets | array | Dashboard widgets |
| layout_type | enum | ordered, free |
| author_handle | string | Author email |

## Relationships

```
┌──────────────────┐       ┌─────────────────────┐
│      Service     │───────│       Monitor       │
└──────────────────┘       └─────────────────────┘
         │                          │
         │                          │
         ▼                          ▼
┌──────────────────┐       ┌─────────────────────┐
│       Log        │       │       Metric        │
└──────────────────┘       └─────────────────────┘
         │
         │
         ▼
┌──────────────────┐       ┌─────────────────────┐
│      Trace       │───────│      Incident       │
└──────────────────┘       └─────────────────────┘
         │
         │
         ▼
┌──────────────────┐
│       Span       │
└──────────────────┘
```

## Query Language

Datadog uses a specific query syntax for logs and metrics:

### Log Query Syntax
```
service:network-core status:error @host:router-01
```

### Metric Query Syntax
```
avg:system.cpu.user{host:router-*} by {host}
```

## No Local Storage

This integration does not persist any data locally. All state is maintained by Datadog's managed services.
