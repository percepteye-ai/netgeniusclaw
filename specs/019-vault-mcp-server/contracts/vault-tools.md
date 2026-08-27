# Vault MCP Tools Contract

**Feature**: 019-vault-mcp-server | **Date**: 2026-04-04

## Overview

This document defines the tool interface contract for the official HashiCorp Vault MCP server integration.

**CRITICAL**: Secret values are NEVER displayed in output. Use `inject_to` parameter to inject secrets directly to files or integrations.

## MCP Server Configuration

```json
{
  "vault-mcp": {
    "command": "vault-mcp-server",
    "args": [],
    "env": {
      "VAULT_ADDR": "${VAULT_ADDR}",
      "VAULT_TOKEN": "${VAULT_TOKEN}",
      "VAULT_NAMESPACE": "${VAULT_NAMESPACE}"
    }
  }
}
```

## Tool Catalog by Skill

### vault-secrets (4 tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `read_secret` | read | path, version?, inject_to? | Metadata (values REDACTED) |
| `write_secret` | write | path, data, cas? | Write confirmation |
| `list_secrets` | read | path | Array of secret paths |
| `delete_secret` | write | path, versions? | Delete confirmation |

### vault-pki (6 tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `enable_pki` | write | path, config? | Mount details |
| `create_pki_issuer` | write | mount, name, certificate, key | Issuer details |
| `list_pki_issuers` | read | mount | Array of issuers |
| `create_pki_role` | write | mount, name, config | Role details |
| `list_pki_roles` | read | mount | Array of roles |
| `issue_pki_certificate` | write | mount, role, common_name, san?, ttl?, inject_to? | Certificate metadata |

### vault-mounts (3 tools)

| Tool | Type | Parameters | Returns |
|------|------|------------|---------|
| `list_mounts` | read | type? | Array of mounts |
| `create_mount` | write | path, type, config? | Mount details |
| `delete_mount` | write | path | Delete confirmation |

## Parameter Details

### read_secret

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| path | string | Yes | - | Secret path (e.g., secret/network/router) |
| version | integer | No | latest | Specific version to read |
| inject_to | string | No | - | File path to inject secret JSON |

### issue_pki_certificate

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| mount | string | Yes | - | PKI mount path |
| role | string | Yes | - | PKI role name |
| common_name | string | Yes | - | Certificate CN |
| alt_names | array | No | - | Subject Alternative Names |
| ip_sans | array | No | - | IP SANs |
| ttl | string | No | role default | Certificate TTL |
| inject_to | string | No | - | Directory to save cert/key |

## Output Redaction

### Secret Read
```json
{
  "exists": true,
  "path": "secret/data/network/router-01",
  "version": 3,
  "keys": ["username", "password", "enable_secret"],
  "message": "Secret values redacted. Use inject_to to save to file."
}
```

### Certificate Issue
```json
{
  "serial_number": "7a:b5:c3:d2:...",
  "common_name": "router.example.com",
  "expiration": "2026-05-04T12:00:00Z",
  "ca_chain_length": 2,
  "files_written": [
    "/tmp/certs/router.example.com.crt",
    "/tmp/certs/router.example.com.key",
    "/tmp/certs/ca-chain.crt"
  ]
}
```

## Error Responses

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad Request | Invalid path format |
| 401 | Unauthorized | Invalid or expired token |
| 403 | Forbidden | Policy denies access |
| 404 | Not Found | Secret/mount doesn't exist |
| 412 | Precondition Failed | CAS check failed |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VAULT_ADDR` | Yes | Vault server address |
| `VAULT_TOKEN` | Yes | Authentication token |
| `VAULT_NAMESPACE` | No | Vault namespace (Enterprise) |
| `VAULT_SKIP_VERIFY` | No | Skip TLS verification |
