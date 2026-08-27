"""CIS Azure Foundations Benchmark compliance rules for NSG auditing."""

from __future__ import annotations

from typing import Optional
from models.responses import SecurityRule, ComplianceFinding


def _is_any_source(rule: SecurityRule) -> bool:
    """Check if rule allows traffic from any source (0.0.0.0/0 or * or Internet)."""
    any_prefixes = {"*", "0.0.0.0/0", "0.0.0.0", "Internet", "internet"}
    if rule.source_address_prefix and rule.source_address_prefix in any_prefixes:
        return True
    if rule.source_address_prefixes:
        for prefix in rule.source_address_prefixes:
            if prefix in any_prefixes:
                return True
    return False


def _port_in_range(port: int, port_range: Optional[str]) -> bool:
    """Check if a port number falls within a port range string."""
    if not port_range:
        return False
    if port_range == "*":
        return True
    for part in port_range.split(","):
        part = part.strip()
        if "-" in part:
            try:
                low, high = part.split("-", 1)
                if int(low) <= port <= int(high):
                    return True
            except ValueError:
                continue
        else:
            try:
                if int(part) == port:
                    return True
            except ValueError:
                continue
    return False


def check_cis_6_1_restrict_rdp(
    rules: list[SecurityRule],
    nsg_id: str,
    nsg_name: str,
) -> list[ComplianceFinding]:
    """CIS 6.1: Ensure that RDP access (port 3389) is restricted from the internet."""
    findings = []
    for rule in rules:
        if (
            rule.access == "Allow"
            and rule.direction == "Inbound"
            and _is_any_source(rule)
            and _port_in_range(3389, rule.destination_port_range)
            and rule.protocol in ("*", "TCP", "Tcp")
        ):
            findings.append(ComplianceFinding(
                rule_id="6.1",
                rule_name="Restrict RDP from Internet",
                severity="Critical",
                resource_id=nsg_id,
                resource_name=nsg_name,
                description=(
                    f"NSG rule '{rule.name}' allows RDP (port 3389) from the internet "
                    f"({rule.source_address_prefix or 'multiple sources'}). "
                    "This exposes systems to brute-force and credential-stuffing attacks."
                ),
                remediation=(
                    "Restrict RDP access to specific IP ranges or use Azure Bastion / "
                    "Just-In-Time VM access instead of opening port 3389 to 0.0.0.0/0."
                ),
                nsg_rule_name=rule.name,
            ))
    return findings


def check_cis_6_2_restrict_ssh(
    rules: list[SecurityRule],
    nsg_id: str,
    nsg_name: str,
) -> list[ComplianceFinding]:
    """CIS 6.2: Ensure that SSH access (port 22) is restricted from the internet."""
    findings = []
    for rule in rules:
        if (
            rule.access == "Allow"
            and rule.direction == "Inbound"
            and _is_any_source(rule)
            and _port_in_range(22, rule.destination_port_range)
            and rule.protocol in ("*", "TCP", "Tcp")
        ):
            findings.append(ComplianceFinding(
                rule_id="6.2",
                rule_name="Restrict SSH from Internet",
                severity="Critical",
                resource_id=nsg_id,
                resource_name=nsg_name,
                description=(
                    f"NSG rule '{rule.name}' allows SSH (port 22) from the internet "
                    f"({rule.source_address_prefix or 'multiple sources'}). "
                    "This exposes systems to brute-force attacks."
                ),
                remediation=(
                    "Restrict SSH access to specific IP ranges or use Azure Bastion / "
                    "Just-In-Time VM access instead of opening port 22 to 0.0.0.0/0."
                ),
                nsg_rule_name=rule.name,
            ))
    return findings


def check_cis_6_3_restrict_udp(
    rules: list[SecurityRule],
    nsg_id: str,
    nsg_name: str,
) -> list[ComplianceFinding]:
    """CIS 6.3: Ensure no NSG allows unrestricted UDP access from the internet."""
    findings = []
    for rule in rules:
        if (
            rule.access == "Allow"
            and rule.direction == "Inbound"
            and _is_any_source(rule)
            and rule.protocol in ("*", "UDP", "Udp")
            and rule.destination_port_range == "*"
        ):
            findings.append(ComplianceFinding(
                rule_id="6.3",
                rule_name="Restrict UDP from Internet",
                severity="High",
                resource_id=nsg_id,
                resource_name=nsg_name,
                description=(
                    f"NSG rule '{rule.name}' allows unrestricted UDP from the internet. "
                    "This can enable DDoS amplification and DNS reflection attacks."
                ),
                remediation=(
                    "Restrict UDP access to specific ports and source IP ranges. "
                    "Never allow UDP * from 0.0.0.0/0."
                ),
                nsg_rule_name=rule.name,
            ))
    return findings


def check_cis_6_4_nsg_flow_logs(
    nsg_id: str,
    nsg_name: str,
    flow_logs_enabled: bool = False,
    retention_days: int = 0,
) -> list[ComplianceFinding]:
    """CIS 6.4: Ensure NSG flow logs are enabled with >= 90 day retention."""
    findings = []
    if not flow_logs_enabled:
        findings.append(ComplianceFinding(
            rule_id="6.4",
            rule_name="NSG Flow Logs Enabled",
            severity="Medium",
            resource_id=nsg_id,
            resource_name=nsg_name,
            description=(
                f"NSG '{nsg_name}' does not have flow logs enabled. "
                "Flow logs are essential for network traffic analysis and security monitoring."
            ),
            remediation=(
                "Enable NSG flow logs via Network Watcher with a retention period of "
                "at least 90 days. Store logs in a Storage Account or Log Analytics workspace."
            ),
        ))
    elif retention_days < 90:
        findings.append(ComplianceFinding(
            rule_id="6.4",
            rule_name="NSG Flow Log Retention",
            severity="Medium",
            resource_id=nsg_id,
            resource_name=nsg_name,
            description=(
                f"NSG '{nsg_name}' flow log retention is {retention_days} days, "
                "which is below the recommended 90-day minimum."
            ),
            remediation=(
                "Increase NSG flow log retention to at least 90 days for compliance "
                "with CIS Azure Foundations Benchmark."
            ),
        ))
    return findings


def run_all_checks(
    rules: list[SecurityRule],
    nsg_id: str,
    nsg_name: str,
    flow_logs_enabled: bool = False,
    retention_days: int = 0,
) -> list[ComplianceFinding]:
    """Run all CIS Azure Foundations Benchmark checks against an NSG."""
    findings = []
    findings.extend(check_cis_6_1_restrict_rdp(rules, nsg_id, nsg_name))
    findings.extend(check_cis_6_2_restrict_ssh(rules, nsg_id, nsg_name))
    findings.extend(check_cis_6_3_restrict_udp(rules, nsg_id, nsg_name))
    findings.extend(check_cis_6_4_nsg_flow_logs(nsg_id, nsg_name, flow_logs_enabled, retention_days))
    return findings
