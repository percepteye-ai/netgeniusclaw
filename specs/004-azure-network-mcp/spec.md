# Feature Specification: Azure Networking MCP Server

**Feature Branch**: `004-azure-network-mcp`
**Created**: 2026-03-26
**Status**: Draft
**Input**: User description: "Azure Networking MCP Server - Build a new MCP server for Microsoft Azure networking services. Completes NetGeniusClaw multi-cloud story alongside existing AWS and GCP MCP servers."

## Clarifications

### Session 2026-03-26

- Q: Which Azure SDK library should be used for implementation? → A: Python Azure SDK (`azure-mgmt-network` + `azure-identity`), consistent with the Python-based MCP server pattern used throughout the NetGeniusClaw project.
- Q: What MCP tool granularity should be used (fine-grained per operation, resource-grouped, or coarse user-story-level)? → A: Resource-grouped (~15-20 tools, one per resource type), e.g., `azure_list_vnets`, `azure_get_nsg_rules`, `azure_get_expressroute_status`.
- Q: What is the maximum number of concurrent subscription queries? → A: Maximum 5 concurrent subscriptions, balancing Azure ARM API rate limits (~1200 reads/5min per tenant) with practical multi-subscription topology views.
- Q: Should Azure API versions be pinned or use latest dynamically? → A: Pin to specific stable API versions per resource type for deterministic behavior; update versions in controlled maintenance windows.
- Q: What compliance rule set should NSG auditing use for violation detection? → A: CIS Azure Foundations Benchmark rules as the baseline rule set; additional frameworks (PCI-DSS, NIST) deferred to future iterations.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query VNet Topology and Connectivity (Priority: P1)

As a network engineer, I need to query Azure Virtual Network topology so I can understand VNet layout, subnet segmentation, peering relationships, and associated Network Security Groups across one or more Azure subscriptions. This is the foundational capability that all other Azure networking operations depend on.

**Why this priority**: VNet topology is the bedrock of Azure networking. Without visibility into VNets, subnets, and peerings, no other Azure network troubleshooting or auditing is possible. This mirrors the VPC listing and details capability that is the most-used feature of the existing AWS MCP server.

**Independent Test**: Can be fully tested by configuring Azure credentials for a subscription containing VNets with subnets and peerings, then querying topology and verifying accurate results. Delivers immediate value for any engineer managing Azure networks.

**Acceptance Scenarios**:

1. **Given** valid Azure credentials (tenant ID, client ID, client secret, subscription ID) are configured via environment variables, **When** a user requests a list of all VNets, **Then** the system returns all VNets in the subscription with their name, address space, region, resource group, and provisioning state.
2. **Given** a subscription with multiple VNets across different regions, **When** a user requests VNet details for a specific VNet by name or resource ID, **Then** the system returns the full VNet configuration including all subnets, their address prefixes, delegations, service endpoints, and associated NSGs.
3. **Given** two VNets connected via VNet peering, **When** a user queries peering status, **Then** the system returns peering name, remote VNet ID, peering state (Connected/Disconnected/Initiated), traffic forwarding settings, and gateway transit configuration for each direction.
4. **Given** a user has access to multiple Azure subscriptions, **When** they specify a target subscription ID, **Then** the system queries that subscription and returns its VNet topology without requiring reconfiguration of credentials.
5. **Given** valid Azure credentials, **When** a user queries a subscription that contains zero VNets, **Then** the system returns an empty result set with a clear informational message rather than an error.
6. **Given** a VNet with subnets that have associated route tables and NSGs, **When** a user requests subnet details, **Then** each subnet entry includes its associated NSG name/ID and route table name/ID for quick cross-reference.

---

### User Story 2 - Audit NSG Rules and Effective Security (Priority: P2)

As a security-focused network engineer, I need to audit Network Security Group rules and view effective security rules on specific resources so I can verify compliance, troubleshoot access issues, and identify overly permissive rules.

**Why this priority**: Security auditing is the second most common task after topology discovery. NSG misconfiguration is the leading cause of Azure connectivity issues and a primary compliance concern. This capability enables immediate security value on top of VNet topology.

**Independent Test**: Can be fully tested by querying NSG rules for a resource with known security group configurations and verifying the rules match expectations. Delivers value for compliance auditing independent of other capabilities.

**Acceptance Scenarios**:

1. **Given** valid Azure credentials, **When** a user requests all NSGs in a subscription, **Then** the system returns each NSG with its name, resource group, region, associated subnets, and associated network interfaces.
2. **Given** an NSG with both default and custom rules, **When** a user requests the rules for that NSG, **Then** the system returns all inbound and outbound rules sorted by priority, including rule name, priority, direction, access (Allow/Deny), protocol, source/destination address prefixes, and source/destination port ranges.
3. **Given** a virtual machine NIC with multiple NSGs applied (subnet-level and NIC-level), **When** a user requests effective security rules for that NIC, **Then** the system returns the aggregated effective rules showing the combined result of all applicable NSGs.
4. **Given** an NSG with a rule that allows inbound traffic from 0.0.0.0/0 (any source) on port 22 or 3389, **When** a user requests a compliance audit, **Then** the system flags this rule as a finding with severity and a description of the risk.
5. **Given** an NSG that is not associated with any subnet or NIC, **When** a user lists NSGs, **Then** the system identifies it as an orphaned NSG so the engineer can evaluate whether it should be cleaned up.

---

### User Story 3 - Monitor ExpressRoute and VPN Gateway Health (Priority: P3)

As a network engineer responsible for hybrid connectivity, I need to monitor ExpressRoute circuit status and VPN Gateway health so I can proactively detect outages, verify peering configurations, and ensure redundant connectivity paths are operational.

**Why this priority**: Hybrid connectivity (ExpressRoute and VPN) is critical for enterprises running workloads across on-premises and Azure. Monitoring these connections is essential for maintaining SLA compliance and rapid incident response. This is the third priority because it requires hybrid infrastructure to be in place, which is less universal than VNet and NSG operations.

**Independent Test**: Can be fully tested with an Azure subscription that has at least one ExpressRoute circuit or VPN Gateway, verifying that circuit status and tunnel health are reported accurately.

**Acceptance Scenarios**:

1. **Given** an Azure subscription with one or more ExpressRoute circuits, **When** a user queries ExpressRoute status, **Then** the system returns each circuit with its name, SKU, peering location, bandwidth, provisioning state, and circuit provisioning state (Enabled/Disabled).
2. **Given** an ExpressRoute circuit with Azure Private Peering and Microsoft Peering configured, **When** a user requests peering details, **Then** the system returns each peering type with its state, primary/secondary peer addresses, VLAN ID, and ASN.
3. **Given** an ExpressRoute circuit with route tables, **When** a user requests the route table for a specific peering, **Then** the system returns the learned routes including network prefix, next hop, AS path, and route origin.
4. **Given** a VPN Gateway with site-to-site connections, **When** a user queries VPN Gateway status, **Then** the system returns gateway name, SKU, active-active status, BGP settings, and each connection with its name, connection type, and connection status (Connected/Connecting/NotConnected).
5. **Given** a VPN Gateway with point-to-site configuration, **When** a user queries P2S status, **Then** the system returns the VPN client address pool, tunnel type, authentication type, and connected client count.
6. **Given** a VPN tunnel that has transitioned from Connected to NotConnected, **When** a user queries the connection, **Then** the system reports the current state and includes the last connection established time for troubleshooting.

---

### User Story 4 - Inspect Azure Firewall Policies and Threat Intelligence (Priority: P4)

As a network security engineer, I need to inspect Azure Firewall policies, rule collections, and threat intelligence configuration so I can verify that firewall rules align with security policy and threat protection is active.

**Why this priority**: Azure Firewall is the centralized network security control for many Azure environments. Inspecting policies is important for security posture validation, but it is prioritized below connectivity monitoring because not all Azure deployments use Azure Firewall.

**Independent Test**: Can be fully tested with an Azure subscription that has Azure Firewall deployed with at least one firewall policy, verifying that policies and rule collections are returned accurately.

**Acceptance Scenarios**:

1. **Given** an Azure subscription with one or more Azure Firewalls, **When** a user lists firewalls, **Then** the system returns each firewall with its name, resource group, region, SKU tier (Standard/Premium), provisioning state, and associated firewall policy.
2. **Given** an Azure Firewall with an associated policy, **When** a user requests policy details, **Then** the system returns the policy name, threat intelligence mode (Off/Alert/Deny), DNS proxy status, intrusion detection mode (if Premium), and all rule collection groups.
3. **Given** a firewall policy with network, application, and NAT rule collections, **When** a user requests rule collection details for a specific collection group, **Then** the system returns each rule collection with its priority, action type, and individual rules with source, destination, protocol, and port details.
4. **Given** an Azure Firewall Premium with IDPS enabled, **When** a user queries threat intelligence status, **Then** the system returns the IDPS mode (Alert/Deny), signature override count, and threat intelligence mode with any custom allowlist/blocklist entries.
5. **Given** an Azure Firewall with no associated policy (classic rules), **When** a user queries the firewall, **Then** the system reports that classic rule configuration is detected and returns the legacy rule collections.

---

### User Story 5 - Analyze Load Balancer and Application Gateway Health (Priority: P5)

As a network engineer, I need to check Azure Load Balancer and Application Gateway health including frontend/backend pool status, health probe results, and WAF rules so I can troubleshoot application delivery issues and verify high-availability configurations.

**Why this priority**: Load balancing and application delivery are critical for production workloads, but issues in this area are typically application-layer rather than network-layer. This is prioritized last because it builds on the foundational connectivity visibility provided by the higher-priority stories.

**Independent Test**: Can be fully tested with an Azure subscription containing a Load Balancer or Application Gateway with backend pools and health probes, verifying accurate reporting of backend health.

**Acceptance Scenarios**:

1. **Given** an Azure subscription with load balancers, **When** a user lists load balancers, **Then** the system returns each load balancer with its name, SKU, type (Public/Internal), resource group, frontend IP configurations, and provisioning state.
2. **Given** a load balancer with backend pools, **When** a user requests backend pool details, **Then** the system returns each pool with its member VMs/NICs and their health probe status (Healthy/Unhealthy/Unknown).
3. **Given** a load balancer with health probes, **When** a user requests health probe details, **Then** the system returns each probe with its protocol, port, path (for HTTP/HTTPS), interval, and unhealthy threshold.
4. **Given** an Application Gateway with WAF enabled, **When** a user queries WAF configuration, **Then** the system returns the WAF mode (Detection/Prevention), rule set type and version, disabled rule groups, and any custom rules.
5. **Given** an Application Gateway with backend pools, **When** a user requests backend health, **Then** the system returns the health status of each backend server in each pool including the HTTP status and reason for any unhealthy servers.
6. **Given** an Azure Front Door profile, **When** a user queries its configuration, **Then** the system returns routing rules, origin groups, origins with health status, and WAF policy association.

---

### Edge Cases

- What happens when Azure credentials are expired or the service principal lacks Reader permissions on the target subscription? The system MUST return a clear authentication/authorization error with guidance on required permissions.
- What happens when an Azure API call is throttled (HTTP 429)? The system MUST respect retry-after headers and retry gracefully rather than failing immediately.
- What happens when a resource is in a transitional provisioning state (Creating/Updating/Deleting)? The system MUST report the current state accurately rather than treating it as an error.
- What happens when a VNet peering exists but the remote VNet is in a different subscription the credentials cannot access? The system MUST report the peering configuration it can see and indicate that the remote VNet details are inaccessible.
- What happens when querying a subscription in a region where a service (e.g., Azure Firewall Premium) is not available? The system MUST handle the API response gracefully and report that the service is not deployed in that region.
- What happens when Azure DNS zones contain thousands of records? The system MUST handle pagination and return complete results or provide a filtering mechanism.
- What happens when a Network Watcher is not enabled in a region? The system MUST report that Network Watcher is unavailable in that region and indicate which capabilities are affected.
- What happens when the user provides an invalid subscription ID or resource ID? The system MUST return a clear validation error with the expected format.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST authenticate to Azure using service principal credentials (tenant ID, client ID, client secret) provided via environment variables, using the `azure-identity` Python library (`ClientSecretCredential`).
- **FR-002**: System MUST support targeting specific Azure subscriptions by subscription ID, and MUST support querying up to 5 subscriptions concurrently within a single session to respect Azure ARM API rate limits (~1200 reads/5min per tenant).
- **FR-003**: System MUST list, inspect, and return detailed configuration for Virtual Networks including address spaces, subnets, peerings, and associated resources.
- **FR-004**: System MUST list Network Security Groups and return all inbound/outbound rules with full rule details (priority, direction, access, protocol, source, destination, ports).
- **FR-005**: System MUST retrieve effective security rules for a given network interface to show the aggregated impact of all applicable NSGs.
- **FR-006**: System MUST retrieve ExpressRoute circuit status, peering configuration, and route tables.
- **FR-007**: System MUST retrieve VPN Gateway configuration, connection status, and tunnel health for both site-to-site and point-to-site VPN.
- **FR-008**: System MUST list Azure Firewalls and retrieve associated firewall policy details including rule collection groups, rule collections, and individual rules.
- **FR-009**: System MUST retrieve Azure Firewall threat intelligence configuration and IDPS status for Premium SKU firewalls.
- **FR-010**: System MUST retrieve Load Balancer configuration including frontend IPs, backend pools, health probes, load balancing rules, and NAT rules.
- **FR-011**: System MUST retrieve Application Gateway configuration including backend pool health, listener configuration, routing rules, and WAF policy details.
- **FR-012**: System MUST retrieve Azure Front Door configuration including routing rules, origin groups, and WAF policy association.
- **FR-013**: System MUST operate in read-only mode by default. Any write operation (NSG rule modification, route table updates) MUST be gated behind ITSM approval workflow.
- **FR-014**: System MUST log all operations to the GAIT audit trail including timestamp, user identity, operation performed, target resource, and result status.
- **FR-015**: System MUST retrieve Route Table and User Defined Route (UDR) configuration, and MUST support querying effective routes on a specific network interface.
- **FR-016**: System MUST support Network Watcher capabilities including connection monitor status, flow log configuration, and network topology retrieval.
- **FR-017**: System MUST retrieve Private Link and Private Endpoint configurations including service connections and private DNS zone associations.
- **FR-018**: System MUST retrieve Azure DNS zone configuration and record sets.
- **FR-019**: System MUST ship with full artifact coherence: README, install.sh, UI integration, SOUL.md, SKILL.md, .env.example, and TOOLS.md, consistent with existing MCP server patterns.
- **FR-020**: System MUST be implemented in Python using `azure-mgmt-network` and `azure-identity` SDK libraries, consistent with the Python-based MCP server pattern used throughout the NetGeniusClaw project.
- **FR-021**: System MUST expose MCP tools at a resource-grouped granularity (~15-20 tools), with one tool per major Azure networking resource type (e.g., `azure_list_vnets`, `azure_get_nsg_rules`, `azure_get_expressroute_status`).
- **FR-022**: System MUST pin Azure ARM API versions to specific stable releases per resource type. API versions MUST be defined as constants and updated only during controlled maintenance windows.
- **FR-023**: NSG compliance auditing (FR-004, User Story 2 scenario 4) MUST evaluate rules against the CIS Azure Foundations Benchmark as the baseline rule set. Additional compliance frameworks (PCI-DSS, NIST) are deferred to future iterations.

### Key Entities

- **Virtual Network (VNet)**: Azure's fundamental network isolation boundary. Contains address spaces, subnets, peerings, and DNS settings. The primary organizational unit for Azure networking.
- **Network Security Group (NSG)**: Stateful firewall rules applied at the subnet or NIC level. Contains prioritized allow/deny rules for inbound and outbound traffic.
- **ExpressRoute Circuit**: Dedicated private connection between on-premises infrastructure and Azure, provisioned through a connectivity provider. Contains peering configurations and route tables.
- **VPN Gateway**: Managed gateway for encrypted cross-premises connectivity. Supports site-to-site, point-to-site, and VNet-to-VNet connections.
- **Azure Firewall**: Managed cloud-native network security service. Contains firewall policies with network rules, application rules, NAT rules, and threat intelligence configuration.
- **Load Balancer**: Layer-4 load distribution service. Contains frontend IPs, backend pools, health probes, and load balancing/NAT rules.
- **Application Gateway**: Layer-7 application delivery controller. Contains listeners, routing rules, backend pools, health probes, and optional WAF policy.
- **Network Watcher**: Regional diagnostic service for monitoring, diagnosing, and gaining insights into Azure network performance and health.
- **Private Endpoint**: Network interface that connects privately to a service powered by Azure Private Link, using a private IP from the VNet.
- **Route Table**: Collection of user-defined routes (UDRs) that control traffic routing within Azure subnets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A network engineer can retrieve complete VNet topology (VNets, subnets, peerings, NSGs) for an Azure subscription in a single conversational exchange, equivalent to what the AWS MCP server provides for VPC topology.
- **SC-002**: The system correctly returns all NSG rules sorted by priority and identifies compliance violations (e.g., open management ports from any source) with zero false negatives for the CIS Azure Foundations Benchmark rule set.
- **SC-003**: ExpressRoute circuit health and VPN Gateway tunnel status are reported accurately, matching the values shown in the Azure Portal, with latency under 30 seconds for a single subscription query.
- **SC-004**: Azure Firewall policy rule collections are returned with complete rule details, enabling an engineer to audit firewall posture without opening the Azure Portal.
- **SC-005**: Load Balancer and Application Gateway backend health probe status matches Azure Portal reporting with zero discrepancies.
- **SC-006**: All operations produce GAIT audit log entries that include timestamp, operation, target resource, and result, with 100% coverage of executed operations.
- **SC-007**: The MCP server ships with full artifact coherence (README, install.sh, SKILL.md, SOUL.md, .env.example, TOOLS.md, UI integration), matching the pattern established by the existing AWS and GCP MCP servers.
- **SC-008**: No write operations are possible without ITSM gate approval. Attempting a write operation without approval MUST be rejected with a clear denial message.
- **SC-009**: The system handles Azure API errors (authentication failures, authorization errors, throttling, invalid resource IDs) gracefully, returning actionable error messages rather than raw exceptions.

## Assumptions

- Azure service principal credentials will be provided via environment variables (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID) following the same pattern as AWS credential configuration in the existing AWS MCP server.
- The service principal will be granted at minimum the Reader role on target subscriptions. Additional roles (e.g., Network Contributor for write operations) are only required if ITSM-gated write capabilities are enabled.
- The MCP server will follow the same stdio transport pattern used by the existing AWS and GCP MCP servers, consistent with the NetGeniusClaw skill architecture.
- Azure Government and Azure China sovereign clouds are out of scope for the initial release. The server will target Azure Commercial (public cloud) only.
- Rate limiting and pagination of Azure Resource Manager APIs will be handled transparently by the MCP server; the user should not need to manage pagination manually.
- The existing GAIT audit logging infrastructure is available and will be reused for Azure operation logging without requiring new audit infrastructure.
- Network Watcher packet capture and flow log analysis capabilities depend on Network Watcher being enabled in the target region; the system will report clearly when it is not available rather than failing silently.
- Azure ARM API versions will be pinned per resource provider (e.g., `Microsoft.Network` API version `2024-01-01`) and stored as constants in the codebase.
- Maximum concurrent subscription query limit is 5 to stay within Azure ARM tenant-level throttling thresholds.
