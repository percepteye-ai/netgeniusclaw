# Data Model: HashiCorp Vault MCP Server Integration

**Feature**: 019-vault-mcp-server | **Date**: 2026-04-04

## Overview

This is a stateless MCP server integration. The Vault MCP server acts as a proxy to the Vault API. No local data storage is required. Secret values are NEVER returned in output.

## External Entities (Vault API)

### Secret (KV v2)

| Field | Type | Description |
|-------|------|-------------|
| path | string | Secret path |
| version | integer | Secret version |
| created_time | datetime | Creation timestamp |
| deletion_time | datetime | Scheduled deletion |
| destroyed | boolean | Permanently destroyed flag |
| custom_metadata | object | User metadata |
| keys | array | Secret key names (values REDACTED) |

### Mount

| Field | Type | Description |
|-------|------|-------------|
| path | string | Mount path |
| type | string | Secret engine type |
| description | string | Mount description |
| config | object | Mount configuration |
| options | object | Mount options |
| accessor | string | Mount accessor ID |

### PKI Issuer

| Field | Type | Description |
|-------|------|-------------|
| issuer_id | string | Issuer identifier |
| issuer_name | string | Issuer name |
| key_id | string | Associated key ID |
| certificate | string | CA certificate (PEM) |
| ca_chain | array | CA certificate chain |
| manual_chain | array | Manual chain override |

### PKI Role

| Field | Type | Description |
|-------|------|-------------|
| name | string | Role name |
| issuer_ref | string | Default issuer |
| ttl | duration | Default TTL |
| max_ttl | duration | Maximum TTL |
| allow_localhost | boolean | Allow localhost CN |
| allowed_domains | array | Permitted domains |
| allow_subdomains | boolean | Allow subdomains |
| allowed_uri_sans | array | Allowed URI SANs |
| key_type | string | Key type (rsa, ec, ed25519) |
| key_bits | integer | Key size |

### Certificate

| Field | Type | Description |
|-------|------|-------------|
| serial_number | string | Certificate serial |
| certificate | string | Certificate (PEM) |
| issuing_ca | string | Issuing CA (PEM) |
| ca_chain | array | Full CA chain |
| private_key | string | Private key (REDACTED in output) |
| private_key_type | string | Key type |
| expiration | integer | Expiration timestamp |

## Output Redaction Rules

### Secret Read Response
```json
{
  "exists": true,
  "path": "secret/network/router-credentials",
  "version": 3,
  "keys": ["username", "password", "enable_secret"],
  "values": "[REDACTED - use inject_to parameter]"
}
```

### Certificate Issue Response
```json
{
  "serial_number": "7a:b5:c3:...",
  "common_name": "router.example.com",
  "expiration": "2026-05-04T00:00:00Z",
  "injected_to": "/tmp/router-cert.pem",
  "private_key": "[REDACTED - saved to injected_to path]"
}
```

## Relationships

```
┌──────────────────┐       ┌─────────────────────┐
│      Mount       │───────│    Secret Engine    │
└──────────────────┘       └─────────────────────┘
         │                          │
         │                          │
         ▼                          ▼
┌──────────────────┐       ┌─────────────────────┐
│     Secret       │       │    PKI Issuer       │
└──────────────────┘       └─────────────────────┘
                                    │
                                    │
                                    ▼
                           ┌─────────────────────┐
                           │     PKI Role        │
                           └─────────────────────┘
                                    │
                                    │
                                    ▼
                           ┌─────────────────────┐
                           │    Certificate      │
                           └─────────────────────┘
```

## No Local Storage

This integration does not persist any data locally. All state is maintained by Vault.
