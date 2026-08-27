# Tasks: Azure Networking MCP Server

**Input**: Design documents from `/specs/004-azure-network-mcp/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and dependency configuration

- [x] T001 Create directory structure for `mcp-servers/azure-network-mcp/` with subdirectories: `tools/`, `clients/`, `models/`, `compliance/`, `utils/` (each with `__init__.py`)
- [x] T002 Create `mcp-servers/azure-network-mcp/requirements.txt` with dependencies: `mcp[cli]`, `azure-identity`, `azure-mgmt-network`, `azure-mgmt-resource`, `azure-mgmt-dns`, `azure-mgmt-frontdoor`
- [x] T003 [P] Create `mcp-servers/azure-network-mcp/utils/constants.py` with pinned Azure ARM API versions (e.g., `NETWORK_API_VERSION = "2024-05-01"`) and Azure error code mappings
- [x] T004 [P] Create `mcp-servers/azure-network-mcp/.env.example` with AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID (descriptions only, no values)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement Azure client factory in `mcp-servers/azure-network-mcp/clients/azure_client.py` with DefaultAzureCredential, per-subscription NetworkManagementClient creation, asyncio.Semaphore(5) for concurrency limiting, and credential validation on startup
- [x] T006 Implement response models in `mcp-servers/azure-network-mcp/models/responses.py` with dataclasses/TypedDicts for all entities from data-model.md: VNet, Subnet, VNetPeering, NetworkSecurityGroup, SecurityRule, ComplianceFinding, ExpressRouteCircuit, ExpressRoutePeering, VPNGateway, VPNConnection, AzureFirewall, FirewallPolicy, RuleCollectionGroup, RuleCollection, LoadBalancer, BackendPool, HealthProbe, RouteTable, Route, PrivateEndpoint, DnsZone, DnsRecordSet
- [x] T007 [P] Implement pagination utility in `mcp-servers/azure-network-mcp/utils/pagination.py` with a `collect_all_pages()` helper that wraps Azure SDK ItemPaged iterators
- [x] T008 [P] Implement error handling utility in `mcp-servers/azure-network-mcp/utils/rate_limiter.py` with retry configuration for azure-core (max_retries=3, exponential backoff, Retry-After header respect) and Azure exception translation to user-friendly error dicts (AuthenticationError, AuthorizationError, SubscriptionNotFoundError, ResourceNotFoundError, ThrottlingError, ValidationError)
- [x] T009 Create FastMCP server entry point in `mcp-servers/azure-network-mcp/azure_network_mcp_server.py` with FastMCP initialization (name="azure-network-mcp", stdio transport), environment variable loading, credential validation, and GAIT audit logging decorator that wraps each tool call with timestamp, operation, target resource, subscription_id, and result status

**Checkpoint**: Foundation ready - Azure client factory, response models, error handling, pagination, and MCP server skeleton are operational. User story implementation can now begin.

---

## Phase 3: User Story 1 - Query VNet Topology and Connectivity (Priority: P1) -- MVP

**Goal**: Network engineers can query Azure VNet topology including VNets, subnets, peerings, and associated NSGs/route tables across one or more subscriptions.

**Independent Test**: Configure Azure credentials for a subscription with VNets, query topology, verify VNet list returns name/address_space/region/provisioning_state; VNet details include subnets with NSG and route table cross-references; peering status shows Connected/Disconnected/Initiated state.

### Implementation for User Story 1

- [x] T010 [US1] Implement `azure_list_vnets` tool in `mcp-servers/azure-network-mcp/tools/vnet.py` using NetworkManagementClient.virtual_networks.list_all(), mapping results to VNet response model with name, id, resource_group, location, address_space, subnet_count, peering_count, provisioning_state, tags. Accept optional subscription_id parameter. Include GAIT audit logging. Handle empty subscription (return empty list with informational message).
- [x] T011 [US1] Implement `azure_get_vnet_details` tool in `mcp-servers/azure-network-mcp/tools/vnet.py` using NetworkManagementClient.virtual_networks.get(), returning full VNet with all subnets (including nsg_name, nsg_id, route_table_name, route_table_id, delegations, service_endpoints, private_endpoints), all peerings (with peering_state, traffic forwarding settings), and DNS settings. Support lookup by name+resource_group or by resource_id.
- [x] T012 [US1] Implement `azure_get_vnet_peerings` tool in `mcp-servers/azure-network-mcp/tools/vnet.py` using NetworkManagementClient.virtual_network_peerings.list(), returning VNetPeering objects with peering_state, allow_vnet_access, allow_forwarded_traffic, allow_gateway_transit, use_remote_gateways. Handle inaccessible remote VNet (report peering config with note that remote VNet details are inaccessible).
- [x] T013 [US1] Register VNet tools (azure_list_vnets, azure_get_vnet_details, azure_get_vnet_peerings) with FastMCP server in `mcp-servers/azure-network-mcp/azure_network_mcp_server.py` by importing from tools/vnet.py and decorating with @mcp.tool()

**Checkpoint**: User Story 1 complete. VNet topology query is fully functional with multi-subscription support, GAIT logging, and error handling.

---

## Phase 4: User Story 2 - Audit NSG Rules and Effective Security (Priority: P2)

**Goal**: Security engineers can audit NSG rules, view effective security rules on NICs, and run CIS Azure Foundations Benchmark compliance checks to identify overly permissive rules.

**Independent Test**: Query NSGs in a subscription, verify rules sorted by priority with full details; query effective security rules for a NIC; run compliance audit and verify it flags rules allowing SSH/RDP from 0.0.0.0/0.

### Implementation for User Story 2

- [x] T014 [P] [US2] Implement `azure_list_nsgs` tool in `mcp-servers/azure-network-mcp/tools/nsg.py` using NetworkManagementClient.network_security_groups.list_all(), returning NSG objects with name, resource_group, location, associated_subnets, associated_nics, is_orphaned flag (true if no subnet or NIC associations). Include GAIT audit logging.
- [x] T015 [P] [US2] Implement `azure_get_nsg_rules` tool in `mcp-servers/azure-network-mcp/tools/nsg.py` using NetworkManagementClient.network_security_groups.get(), returning all inbound and outbound rules (both custom and default) sorted by priority, with full SecurityRule details: name, priority, direction, access, protocol, source/destination address prefixes, source/destination port ranges, description.
- [x] T016 [US2] Implement `azure_get_effective_security_rules` tool in `mcp-servers/azure-network-mcp/tools/nsg.py` using NetworkManagementClient.network_interfaces.list_effective_network_security_groups(), accepting nic_name and resource_group, returning aggregated effective rules from all applicable NSGs.
- [x] T017 [US2] Implement CIS Azure Foundations Benchmark rules in `mcp-servers/azure-network-mcp/compliance/cis_azure.py` with functions for: Rule 6.1 (restrict RDP port 3389 from 0.0.0.0/0), Rule 6.2 (restrict SSH port 22 from 0.0.0.0/0), Rule 6.3 (restrict UDP from internet), Rule 6.4 (NSG flow logs enabled with >= 90 day retention). Each function accepts SecurityRule list and returns ComplianceFinding objects with rule_id, severity, description, remediation.
- [x] T018 [US2] Implement `azure_audit_nsg_compliance` tool in `mcp-servers/azure-network-mcp/tools/nsg.py` that lists all NSGs (or a specific NSG by name/resource_group), evaluates each NSG's rules against CIS benchmark functions from compliance/cis_azure.py, and returns a list of ComplianceFinding objects. Accept optional nsg_name, resource_group, subscription_id filters.
- [x] T019 [US2] Register NSG and compliance tools (azure_list_nsgs, azure_get_nsg_rules, azure_get_effective_security_rules, azure_audit_nsg_compliance) with FastMCP server in `mcp-servers/azure-network-mcp/azure_network_mcp_server.py`

**Checkpoint**: User Story 2 complete. NSG rule auditing, effective security rules, and CIS compliance checks are functional.

---

## Phase 5: User Story 3 - Monitor ExpressRoute and VPN Gateway Health (Priority: P3)

**Goal**: Network engineers can monitor ExpressRoute circuit status, peering configurations, route tables, and VPN Gateway connection health for hybrid connectivity troubleshooting.

**Independent Test**: Query ExpressRoute circuits and verify circuit status, peering details, and route tables match Azure Portal; query VPN Gateways and verify connection status (Connected/Connecting/NotConnected) and BGP settings.

### Implementation for User Story 3

- [x] T020 [P] [US3] Implement `azure_get_expressroute_status` tool in `mcp-servers/azure-network-mcp/tools/expressroute.py` using NetworkManagementClient.express_route_circuits.list_all() (or .get() for specific circuit), returning ExpressRouteCircuit objects with name, sku, peering_location, bandwidth, provisioning_state, circuit_provisioning_state, and nested ExpressRoutePeering list with state, peer addresses, VLAN ID, ASN. Include GAIT logging.
- [x] T021 [P] [US3] Implement `azure_get_expressroute_routes` tool in `mcp-servers/azure-network-mcp/tools/expressroute.py` using NetworkManagementClient.express_route_circuits.list_routes_table(), accepting circuit_name, resource_group, peering_name (AzurePrivatePeering/MicrosoftPeering), returning learned routes with network prefix, next_hop, as_path, origin.
- [x] T022 [P] [US3] Implement `azure_get_vpn_gateway_status` tool in `mcp-servers/azure-network-mcp/tools/vpn_gateway.py` using NetworkManagementClient.virtual_network_gateways.list() and NetworkManagementClient.virtual_network_gateway_connections.list(), returning VPNGateway objects with name, sku, gateway_type, vpn_type, active_active, bgp_settings, and nested VPNConnection list with connection_status, connection_type, egress/ingress bytes. Handle P2S config (client address pool, tunnel type, auth type). Never expose shared keys.
- [x] T023 [US3] Register ExpressRoute and VPN tools (azure_get_expressroute_status, azure_get_expressroute_routes, azure_get_vpn_gateway_status) with FastMCP server in `mcp-servers/azure-network-mcp/azure_network_mcp_server.py`

**Checkpoint**: User Story 3 complete. ExpressRoute and VPN Gateway health monitoring is functional.

---

## Phase 6: User Story 4 - Inspect Azure Firewall Policies and Threat Intelligence (Priority: P4)

**Goal**: Security engineers can inspect Azure Firewall configurations, policies with rule collections, and threat intelligence/IDPS settings without opening the Azure Portal.

**Independent Test**: List firewalls and verify SKU tier and policy association; query a firewall policy and verify rule collection groups, individual rules, and threat intelligence mode; verify Premium SKU returns IDPS status.

### Implementation for User Story 4

- [x] T024 [P] [US4] Implement `azure_list_firewalls` tool in `mcp-servers/azure-network-mcp/tools/firewall.py` using NetworkManagementClient.azure_firewalls.list_all(), returning AzureFirewall objects with name, resource_group, location, sku_tier, provisioning_state, firewall_policy_id, threat_intel_mode, ip_configurations. Handle classic rules (no policy) with informational message. Include GAIT logging.
- [x] T025 [P] [US4] Implement `azure_get_firewall_policy` tool in `mcp-servers/azure-network-mcp/tools/firewall.py` using NetworkManagementClient.firewall_policies.get() and NetworkManagementClient.firewall_policy_rule_collection_groups.list(), returning FirewallPolicy with threat_intelligence_mode, dns_proxy_enabled, intrusion_detection_mode (Premium only), and nested RuleCollectionGroups with priority, RuleCollections with action_type/rule_type, and individual rules with source/destination/protocol/port details.
- [x] T026 [US4] Register Firewall tools (azure_list_firewalls, azure_get_firewall_policy) with FastMCP server in `mcp-servers/azure-network-mcp/azure_network_mcp_server.py`

**Checkpoint**: User Story 4 complete. Azure Firewall policy inspection and threat intelligence reporting are functional.

---

## Phase 7: User Story 5 - Analyze Load Balancer and Application Gateway Health (Priority: P5)

**Goal**: Network engineers can check Load Balancer backend health, Application Gateway WAF config and backend status, and Azure Front Door routing/origin health.

**Independent Test**: List load balancers with SKU/type; query backend health and verify per-member Healthy/Unhealthy/Unknown status; query Application Gateway WAF config and backend health; query Front Door routing rules and origin groups.

### Implementation for User Story 5

- [x] T027 [P] [US5] Implement `azure_list_load_balancers` tool in `mcp-servers/azure-network-mcp/tools/load_balancer.py` using NetworkManagementClient.load_balancers.list_all(), returning LoadBalancer objects with name, sku, type (Public/Internal), resource_group, frontend_ip_configs, backend_pools summary, health_probes summary, provisioning_state. Include GAIT logging.
- [x] T028 [P] [US5] Implement `azure_get_lb_backend_health` tool in `mcp-servers/azure-network-mcp/tools/load_balancer.py` using NetworkManagementClient.load_balancers.list_inbound_nat_rules_by_load_balancer() and backend health APIs, returning BackendPool objects with per-member health status (Healthy/Unhealthy/Unknown) and HealthProbe details (protocol, port, path, interval, threshold).
- [x] T029 [P] [US5] Implement `azure_get_app_gateway_health` tool in `mcp-servers/azure-network-mcp/tools/app_gateway.py` using NetworkManagementClient.application_gateways.list_all() and .backend_health(), returning Application Gateway config with listeners, routing rules, WAF mode/rule set/disabled rules/custom rules, and per-backend-server health status. Also handle Azure Front Door via azure-mgmt-frontdoor client, returning routing rules, origin groups, origins with health, and WAF policy association. Include GAIT logging.
- [x] T030 [US5] Register Load Balancer and Application Gateway tools (azure_list_load_balancers, azure_get_lb_backend_health, azure_get_app_gateway_health) with FastMCP server in `mcp-servers/azure-network-mcp/azure_network_mcp_server.py`

**Checkpoint**: User Story 5 complete. Load Balancer and Application Gateway health reporting is functional.

---

## Phase 8: Supporting Services (Route Tables, Network Watcher, Private Link, DNS)

**Purpose**: Implement remaining MCP tools for Route Tables, Network Watcher, Private Link, and DNS that support cross-cutting use cases across multiple user stories.

- [x] T031 [P] Implement `azure_get_route_tables` tool in `mcp-servers/azure-network-mcp/tools/route_table.py` using NetworkManagementClient.route_tables.list_all() and .get(), returning RouteTable objects with routes (name, address_prefix, next_hop_type, next_hop_ip), associated_subnets, disable_bgp_route_propagation. Support effective routes via NetworkManagementClient.network_interfaces.list_effective_route_table() when nic_name is provided. Include GAIT logging.
- [x] T032 [P] Implement Network Watcher tool in `mcp-servers/azure-network-mcp/tools/network_watcher.py` that checks Network Watcher availability per-region via NetworkManagementClient.network_watchers.list_all(), and exposes connection monitor status, flow log configuration, and network topology retrieval. Return clear informational message when Network Watcher is not enabled in a region. Include GAIT logging.
- [x] T033 [P] Implement `azure_get_private_endpoints` tool in `mcp-servers/azure-network-mcp/tools/private_link.py` using NetworkManagementClient.private_endpoints.list_by_subscription(), returning PrivateEndpoint objects with name, subnet_id, private_ip, service_connection details, and private_dns_zones associations. Include GAIT logging.
- [x] T034 [P] Implement `azure_get_dns_zones` tool in `mcp-servers/azure-network-mcp/tools/dns.py` using DnsManagementClient.zones.list() and .record_sets.list_by_dns_zone(), returning DnsZone objects with zone_type (Public/Private), record_count, name_servers, linked_vnets, and DnsRecordSet list with type/ttl/records. Handle pagination for zones with thousands of records. Include GAIT logging.
- [x] T035 Register supporting tools (azure_get_route_tables, network_watcher, azure_get_private_endpoints, azure_get_dns_zones) with FastMCP server in `mcp-servers/azure-network-mcp/azure_network_mcp_server.py`

**Checkpoint**: All 18 MCP tools are implemented and registered.

---

## Phase 9: Polish & Cross-Cutting Concerns (Artifact Coherence)

**Purpose**: Full artifact coherence per Constitution Principle XI. All documentation, installation, UI, and configuration updates required before the feature is considered complete.

- [x] T036 Create `mcp-servers/azure-network-mcp/README.md` with: server description, tool inventory table (all 18 tools with name, description, parameters), environment variables (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID), transport protocol (stdio), installation instructions, required Azure RBAC permissions (Reader role minimum), and architecture diagram showing tool-to-Azure-service mapping
- [x] T037 [P] Update `scripts/install.sh` to add Azure Network MCP server installation steps: pip install of requirements.txt, .env.example copy prompt, credential validation check
- [x] T038 [P] Update `ui/netclaw-visual/` to add Three.js HUD node for the Azure Network MCP server integration showing connection status and tool count
- [x] T039 [P] Update `SOUL.md` with Azure networking skill definitions, identity references, and capability summary for the azure-network-ops and azure-security-audit skills
- [x] T040 [P] Create `workspace/skills/azure-network-ops/SKILL.md` following the pattern from aws-network-ops/SKILL.md: frontmatter (name, description, version, tags), MCP server command and env vars, tool inventory table (18 tools organized by service area), workflows (VNet Topology Audit, Hybrid Connectivity Check, Security Posture Assessment), important rules (read-only, subscription-scoped, GAIT logging), environment variables section
- [x] T041 [P] Update `workspace/skills/azure-security-audit/SKILL.md` to add Azure NSG compliance audit workflows using azure_audit_nsg_compliance and azure_get_effective_security_rules tools, CIS Azure Foundations Benchmark references, and integration guidance with azure-network-ops
- [x] T042 [P] Update `.env.example` at repository root to add Azure Network MCP environment variables section: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID with descriptive comments
- [x] T043 [P] Update `TOOLS.md` with Azure Network MCP server entry in infrastructure reference: server name, tool count (18), service areas covered, transport protocol, required permissions
- [x] T044 [P] Update `config/openclaw.json` to add azure-network-mcp server registration under mcpServers with command, args, and env mappings per quickstart.md
- [x] T045 Validate quickstart.md end-to-end: verify all commands in `specs/004-azure-network-mcp/quickstart.md` work correctly with the implemented server, fix any discrepancies between documented and actual behavior
- [x] T046 Verify existing skills are unbroken: confirm that no existing MCP servers or skills were affected by the addition; run a smoke check on adjacent capabilities (aws-network-ops, gcp-compute-ops) to ensure no import conflicts or configuration side effects

**Checkpoint**: Full artifact coherence achieved. All documentation, installation, UI, and configuration artifacts are updated.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion
- **User Story 2 (Phase 4)**: Depends on Phase 2 completion (independent of US1)
- **User Story 3 (Phase 5)**: Depends on Phase 2 completion (independent of US1, US2)
- **User Story 4 (Phase 6)**: Depends on Phase 2 completion (independent of US1-US3)
- **User Story 5 (Phase 7)**: Depends on Phase 2 completion (independent of US1-US4)
- **Supporting Services (Phase 8)**: Depends on Phase 2 completion (independent of US1-US5)
- **Polish (Phase 9)**: Depends on Phases 3-8 completion (needs all tools implemented for documentation)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2 - Independent of US1 (NSG tools are self-contained)
- **User Story 3 (P3)**: Can start after Phase 2 - Independent of US1-US2
- **User Story 4 (P4)**: Can start after Phase 2 - Independent of US1-US3
- **User Story 5 (P5)**: Can start after Phase 2 - Independent of US1-US4
- **Supporting Services**: Can start after Phase 2 - Independent of all user stories

### Within Each User Story

- Tool implementations within a story can run in parallel (marked [P]) when they write to different files
- Tool registration task depends on all tool implementations in that story being complete
- GAIT logging is built into each tool (no separate dependency)

### Parallel Opportunities

- Phase 1: T003 and T004 can run in parallel
- Phase 2: T007 and T008 can run in parallel (both are utilities)
- Phase 3-8: ALL user story phases can run in parallel after Phase 2 completes
- Within Phase 4: T014 and T015 can run in parallel (same file but independent functions)
- Within Phase 5: T020, T021, T022 can all run in parallel (different files)
- Within Phase 6: T024 and T025 can run in parallel (same file but independent functions)
- Within Phase 7: T027, T028, T029 can all run in parallel (different files)
- Phase 8: T031, T032, T033, T034 can all run in parallel (different files)
- Phase 9: T037-T044 can all run in parallel (different files)

---

## Parallel Example: User Story 1

```bash
# Launch all VNet tool implementations in parallel (they are in the same file but T010-T012 are sequential within vnet.py):
Task T010: "Implement azure_list_vnets in tools/vnet.py"
Task T011: "Implement azure_get_vnet_details in tools/vnet.py" (after T010)
Task T012: "Implement azure_get_vnet_peerings in tools/vnet.py" (after T011)
Task T013: "Register VNet tools in azure_network_mcp_server.py" (after T012)
```

## Parallel Example: User Stories 3-5 (after Phase 2)

```bash
# All three stories can start simultaneously:
Stream A: T020-T023 (ExpressRoute + VPN Gateway)
Stream B: T024-T026 (Azure Firewall)
Stream C: T027-T030 (Load Balancer + App Gateway)
Stream D: T031-T035 (Route Tables, Network Watcher, Private Link, DNS)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T009)
3. Complete Phase 3: User Story 1 (T010-T013)
4. **STOP and VALIDATE**: Test VNet topology query independently
5. Deploy/demo if ready - engineers can already query Azure VNet topology

### Incremental Delivery

1. Complete Setup + Foundational --> Foundation ready
2. Add User Story 1 (VNet Topology) --> Test independently --> MVP!
3. Add User Story 2 (NSG Audit) --> Test independently --> Security value added
4. Add User Story 3 (ExpressRoute/VPN) --> Test independently --> Hybrid monitoring
5. Add User Story 4 (Firewall) --> Test independently --> Firewall audit
6. Add User Story 5 (Load Balancer) --> Test independently --> Full L4/L7 visibility
7. Add Supporting Services (Phase 8) --> All 18 tools complete
8. Complete Polish (Phase 9) --> Full artifact coherence, ship-ready

### Parallel Team Strategy

With multiple developers after Phase 2 completes:

- Developer A: User Story 1 (VNet) + User Story 2 (NSG/Compliance)
- Developer B: User Story 3 (ExpressRoute/VPN) + User Story 4 (Firewall)
- Developer C: User Story 5 (Load Balancer/App GW) + Supporting Services (Phase 8)
- All converge for Phase 9 (Polish/Coherence)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All 18 MCP tools must be registered before Phase 9 documentation can be finalized
- GAIT audit logging is integrated into each tool implementation (not a separate task)
- Error handling (auth errors, throttling, validation) is built into the foundational phase and inherited by all tools
