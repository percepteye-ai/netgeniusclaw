# Feature Specification: HashiCorp Vault MCP Server Integration

**Feature ID**: 019-vault-mcp-server
**Status**: Draft
**Created**: 2026-04-04

## Overview

Integrate the official HashiCorp Vault MCP server to provide secrets management capabilities within NetGeniusClaw. This enables secure credential rotation for device provisioning and certificate management for network infrastructure.

## Source

- **Repository**: https://github.com/hashicorp/vault-mcp-server
- **Type**: Official (HashiCorp-maintained)
- **License**: MPL-2.0
- **Transport**: stdio or StreamableHTTP

## Tools Available (15+ total)

### Mount Management

| Tool | Description |
|------|-------------|
| `list_mounts` | List all secret engine mounts |
| `create_mount` | Create new secret engine (KV, PKI) |
| `delete_mount` | Remove a secret engine mount |

### Key-Value Operations

| Tool | Description |
|------|-------------|
| `read_secret` | Read secret from KV mount |
| `write_secret` | Write secret to KV mount |
| `list_secrets` | List secrets in a path |
| `delete_secret` | Delete secret or specific keys |

### PKI Certificate Management

| Tool | Description |
|------|-------------|
| `enable_pki` | Enable and configure PKI secrets engine |
| `create_pki_issuer` | Add certificate issuer with PEM credentials |
| `list_pki_issuers` | List all issuers in PKI mount |
| `read_pki_issuer` | Get issuer details |
| `create_pki_role` | Create role for issuing certificates |
| `list_pki_roles` | List available PKI roles |
| `read_pki_role` | Get role configuration |
| `delete_pki_role` | Remove PKI role |
| `issue_pki_certificate` | Issue new certificate using role |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VAULT_ADDR` | Yes | Vault server address (default: http://127.0.0.1:8200) |
| `VAULT_TOKEN` | Yes | Authentication token |
| `VAULT_NAMESPACE` | No | Vault namespace (Enterprise) |

## User Stories

### US1: Secret Retrieval (Priority: P1) MVP
**As a** network engineer
**I want to** retrieve device credentials from Vault
**So that** I can access network devices securely without hardcoding credentials

**Acceptance Criteria:**
- Can read secrets from KV mounts
- Secrets not logged or displayed in plain text
- Can list available secret paths

### US2: Certificate Issuance (Priority: P1) MVP
**As a** network engineer managing TLS infrastructure
**I want to** issue certificates for network devices
**So that** I can enable secure communications

**Acceptance Criteria:**
- Can issue certificates using PKI roles
- Can specify common name, SANs, and TTL
- Certificate and key returned securely

### US3: Credential Rotation (Priority: P2)
**As a** network security engineer
**I want to** rotate device credentials through Vault
**So that** credentials are regularly refreshed

**Acceptance Criteria:**
- Can write new credentials to Vault
- Can trigger credential rotation workflows
- Rotation audited in Vault audit log

### US4: Mount Discovery (Priority: P2)
**As a** network engineer
**I want to** discover available secret mounts
**So that** I know where network credentials are stored

**Acceptance Criteria:**
- Can list all mounts with types
- Can identify network-related mounts
- Shows mount configuration metadata

## Proposed Skills

| Skill | Tools | Description |
|-------|-------|-------------|
| `vault-secrets` | 4 | KV secret read/write operations |
| `vault-pki` | 6 | PKI certificate management |
| `vault-mounts` | 3 | Mount discovery and management |

## Integration Points

- **Terraform**: Inject Vault secrets into Terraform providers
- **pyATS**: Retrieve device credentials for testbed
- **gNMI**: TLS certificates for secure gNMI connections
- **ServiceNow**: Audit credential access with change tickets

## Clarifications

### Session 2026-04-04
- Q: Secret value display policy? → A: Never display values, only confirm secret exists

## Security Considerations

- Vault token scoped to minimum required policies
- Secret values NEVER displayed in output (only existence/metadata confirmed)
- Write operations require explicit approval
- PKI certificates have reasonable TTL limits
- Secrets injected directly to integrations (pyATS, gNMI) without display

## Success Criteria

1. Can query "get network device credentials from Vault" and retrieve securely
2. Can query "issue certificate for router.example.com" and get cert/key
3. Integration appears in NetGeniusClaw UI with correct tool count
4. All 3 skills documented with SKILL.md files
