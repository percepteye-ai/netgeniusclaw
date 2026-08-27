#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# scripts/cloudflared-transport.sh — Feature 108: durable Cloudflare Tunnel service
# Generates and manages a systemd --user unit for cloudflared tunnel transport.
# Mirrors spec 057's in2n-services.py pattern (durable, not hand-run).
#
# Why this exists:
#   ngrok-style address-rot (research.md R0) means a process restart produces a
#   NEW host:port with no mechanism to announce it. A Cloudflare Tunnel binds the
#   eN2N listener to a FIXED DNS name — restarts reconnect the same hostname
#   automatically. This script makes that binding durable (FR-002).
#
# TCP/private-network mode ONLY (FR-009):
#   The tunnel relays opaque bytes — NCFED's own TLS (spec 060) is the sole
#   decryption layer. NEVER use HTTP(S) ingress for eN2N traffic. The config.yml
#   MUST use `service: tcp://127.0.0.1:<port>`, not `service: http://...` or
#   `service: https://...`. Using HTTP mode would let Cloudflare's edge terminate
#   or inspect the TLS session, violating the confidentiality invariant (R1).
#
# Prerequisites (must be completed ONCE by the operator before running this):
#   1. cloudflared installed
#      https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
#   2. Tunnel created: cloudflared tunnel create <tunnel-name>
#   3. DNS route bound: cloudflared tunnel route dns <tunnel-name> <hostname>
#   4. config.yml written at ~/.cloudflared/config.yml with TCP ingress:
#        tunnel: <tunnel-uuid>
#        credentials-file: ~/.cloudflared/<tunnel-uuid>.json
#        ingress:
#          - hostname: <your-en2n-hostname>
#            service: tcp://127.0.0.1:7179
#          - service: http_status:404
#      See mcp-servers/protocol-mcp/README.md for the full reference.
#
# Usage:
#   ./scripts/cloudflared-transport.sh generate <tunnel-name> [--port PORT]
#   ./scripts/cloudflared-transport.sh enable  <tunnel-name>
#   ./scripts/cloudflared-transport.sh status  <tunnel-name>
#   ./scripts/cloudflared-transport.sh disable <tunnel-name>
#   ./scripts/cloudflared-transport.sh --help
#
# Idempotent: safe to re-run. generate overwrites the unit file with the same
# content; enable is a no-op if already enabled; status is read-only.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Constants ────────────────────────────────────────────────────────────────
readonly DEFAULT_PORT=7179
readonly UNIT_DIR="${HOME}/.config/systemd/user"
readonly SCRIPT_NAME="$(basename "$0")"
readonly VERSION="108.1.0"

# ── Helpers ──────────────────────────────────────────────────────────────────

die() { echo "ERROR: $*" >&2; exit 1; }
warn() { echo "WARNING: $*" >&2; }
info() { echo "[108] $*"; }

usage() {
    cat <<EOF
${SCRIPT_NAME} v${VERSION} — Durable systemd user service for Cloudflare Tunnel eN2N transport

Usage:
  ${SCRIPT_NAME} generate <tunnel-name> [--port PORT]
  ${SCRIPT_NAME} enable  <tunnel-name>
  ${SCRIPT_NAME} status  <tunnel-name>
  ${SCRIPT_NAME} disable <tunnel-name>
  ${SCRIPT_NAME} --help | -h

Subcommands:
  generate  Write the systemd user unit file (does NOT start the service)
  enable    Enable and start the unit (daemon-reload + enable --now)
  status    Show current unit status (active/inactive/failed)
  disable   Stop and disable the unit (does NOT delete the unit file)

Options:
  --port PORT   Local eN2N listener port (default: ${DEFAULT_PORT})
  --help, -h    Show this help

Examples:
  # One-time setup for a tunnel named "netclaw-byrnbaker":
  ${SCRIPT_NAME} generate netclaw-byrnbaker
  ${SCRIPT_NAME} enable netclaw-byrnbaker

  # Check health:
  ${SCRIPT_NAME} status netclaw-byrnbaker

  # Custom port (if eN2N listens on a non-default port):
  ${SCRIPT_NAME} generate netclaw-byrnbaker --port 8179

Prerequisites (run these once before using this script):
  cloudflared tunnel create <tunnel-name>
  cloudflared tunnel route dns <tunnel-name> <hostname>
  # Then write ~/.cloudflared/config.yml with TCP ingress (FR-009)
EOF
    exit "${1:-0}"
}

# ── Validation helpers ───────────────────────────────────────────────────────

validate_tunnel_name() {
    local name="$1"
    # cloudflared tunnel names: alphanumeric, hyphens, underscores
    if [[ ! "${name}" =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]*$ ]]; then
        die "Invalid tunnel name '${name}'. Must start with alphanumeric, contain only [a-zA-Z0-9_-]."
    fi
}

validate_port() {
    local port="$1"
    if ! [[ "${port}" =~ ^[0-9]+$ ]] || [[ "${port}" -lt 1 ]] || [[ "${port}" -gt 65535 ]]; then
        die "Invalid port '${port}'. Must be 1-65535."
    fi
}

# Locate cloudflared binary (or die trying)
find_cloudflared() {
    local path
    path=$(command -v cloudflared 2>/dev/null || true)
    if [[ -z "${path}" ]]; then
        die "'cloudflared' not found in PATH. Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    fi
    echo "${path}"
}

# Check that systemctl --user is functional
require_systemctl_user() {
    command -v systemctl >/dev/null 2>&1 || die "systemctl not found. This script requires systemd."
    systemctl --user show-environment >/dev/null 2>&1 || die "systemctl --user is not functional. Ensure XDG_RUNTIME_DIR is set and a user session is active (loginctl enable-linger \$USER)."
}

# Derive the unit name from tunnel name
unit_name() {
    echo "cloudflared-${1}.service"
}

# ── Subcommands ──────────────────────────────────────────────────────────────

cmd_generate() {
    local tunnel_name="$1"
    local local_port="$2"

    validate_tunnel_name "${tunnel_name}"
    validate_port "${local_port}"

    local cloudflared_path
    cloudflared_path=$(find_cloudflared)
    local cloudflared_dir
    cloudflared_dir=$(dirname "${cloudflared_path}")

    # Safety: check that credentials exist (from `cloudflared tunnel create`)
    local cred_dir="${HOME}/.cloudflared"
    if [[ ! -d "${cred_dir}" ]]; then
        die "${cred_dir} does not exist. Run 'cloudflared tunnel create ${tunnel_name}' first."
    fi

    local cred_files
    cred_files=$(find "${cred_dir}" -maxdepth 1 -name '*.json' -type f 2>/dev/null | head -1)
    if [[ -z "${cred_files}" ]]; then
        die "No tunnel credentials found in ${cred_dir}/. Run 'cloudflared tunnel create ${tunnel_name}' first."
    fi

    # Warn (don't fail) if config.yml is missing — operator may place it later
    local config_file="${cred_dir}/config.yml"
    if [[ ! -f "${config_file}" ]]; then
        warn "${config_file} not found. The service will fail to start without it."
        warn "See mcp-servers/protocol-mcp/README.md for the required TCP-mode config."
        echo ""
    fi

    # Build a PATH that includes cloudflared's actual install location
    local service_path="${cloudflared_dir}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

    # Create the unit directory (idempotent)
    mkdir -p "${UNIT_DIR}"

    local unit
    unit=$(unit_name "${tunnel_name}")
    local unit_path="${UNIT_DIR}/${unit}"

    # Write the unit file (overwrites if already present — idempotent)
    cat > "${unit_path}" <<UNIT
[Unit]
Description=Cloudflare Tunnel eN2N transport: ${tunnel_name} (feature 108)
Documentation=https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment=HOME=${HOME}
Environment=PATH=${service_path}

# Feature 108 FR-009: TCP/private-network mode ONLY.
# The tunnel relays opaque bytes — NCFED's own TLS (spec 060) is the sole
# decryption layer. NEVER use HTTP(S) ingress for eN2N traffic.
# config.yml MUST contain:  service: tcp://127.0.0.1:${local_port}
#
# cloudflared reads ~/.cloudflared/config.yml by default.
ExecStart=${cloudflared_path} tunnel run ${tunnel_name}

Restart=always
RestartSec=5

# Startup: cloudflared needs time to register with the edge
TimeoutStartSec=30

# Shutdown: graceful SIGTERM handling
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=10

[Install]
WantedBy=default.target
UNIT

    info "Generated: ${unit_path}"
    info "Unit name: ${unit}"
    info "Tunnel:    ${tunnel_name}"
    info "eN2N port: ${local_port} (TCP/private-network mode — FR-009)"
    echo ""
    echo "Next steps:"
    echo "  ${SCRIPT_NAME} enable ${tunnel_name}"
    echo ""
    echo "Or manually:"
    echo "  systemctl --user daemon-reload"
    echo "  systemctl --user enable --now ${unit}"
}

cmd_enable() {
    local tunnel_name="$1"
    validate_tunnel_name "${tunnel_name}"
    require_systemctl_user

    local unit
    unit=$(unit_name "${tunnel_name}")
    local unit_path="${UNIT_DIR}/${unit}"

    if [[ ! -f "${unit_path}" ]]; then
        die "Unit file not found: ${unit_path}. Run '${SCRIPT_NAME} generate ${tunnel_name}' first."
    fi

    info "Enabling and starting ${unit}..."
    systemctl --user daemon-reload
    systemctl --user enable --now "${unit}"

    # Brief status check to confirm it came up
    echo ""
    systemctl --user status "${unit}" --no-pager --lines=5 2>/dev/null || true
    echo ""
    info "Logs: journalctl --user -u ${unit} -f"
}

cmd_status() {
    local tunnel_name="$1"
    validate_tunnel_name "${tunnel_name}"
    require_systemctl_user

    local unit
    unit=$(unit_name "${tunnel_name}")

    local state
    state=$(systemctl --user is-active "${unit}" 2>/dev/null) || true
    state="${state:-unknown}"

    echo "${unit}: ${state}"

    if [[ "${state}" == "active" ]]; then
        # Show brief runtime info
        systemctl --user show "${unit}" --property=MainPID,ActiveEnterTimestamp --no-pager 2>/dev/null | sed 's/^/  /'
    elif [[ "${state}" == "failed" ]]; then
        echo ""
        echo "Recent logs:"
        journalctl --user -u "${unit}" --no-pager --lines=10 2>/dev/null || true
    elif [[ "${state}" == "inactive" || "${state}" == "unknown" ]]; then
        local unit_path="${UNIT_DIR}/${unit}"
        if [[ ! -f "${unit_path}" ]]; then
            echo "  (unit file does not exist — run '${SCRIPT_NAME} generate ${tunnel_name}' first)"
        else
            echo "  (unit exists but is not running — run '${SCRIPT_NAME} enable ${tunnel_name}')"
        fi
    fi

    # Return exit code reflecting health (useful in scripts/monitoring)
    [[ "${state}" == "active" ]]
}

cmd_disable() {
    local tunnel_name="$1"
    validate_tunnel_name "${tunnel_name}"
    require_systemctl_user

    local unit
    unit=$(unit_name "${tunnel_name}")

    info "Stopping and disabling ${unit}..."
    systemctl --user disable --now "${unit}" 2>/dev/null || true
    systemctl --user daemon-reload

    info "Disabled. Unit file preserved at: ${UNIT_DIR}/${unit}"
    info "To re-enable: ${SCRIPT_NAME} enable ${tunnel_name}"
    info "To remove the unit file entirely: rm ${UNIT_DIR}/${unit}"
}

# ── Argument parsing ─────────────────────────────────────────────────────────

main() {
    # Handle --help / -h / no args
    if [[ $# -eq 0 ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
        usage 0
    fi

    local cmd="$1"
    shift

    case "${cmd}" in
        generate|enable|status|disable)
            ;;
        --version|-V)
            echo "${SCRIPT_NAME} v${VERSION}"
            exit 0
            ;;
        *)
            die "Unknown subcommand '${cmd}'. Use '${SCRIPT_NAME} --help' for usage."
            ;;
    esac

    # All subcommands require a tunnel name as the first positional arg
    if [[ $# -eq 0 ]]; then
        die "Missing <tunnel-name>. Usage: ${SCRIPT_NAME} ${cmd} <tunnel-name>"
    fi

    local tunnel_name="$1"
    shift

    # Parse optional flags (only --port is supported, only for generate)
    local local_port="${DEFAULT_PORT}"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --port)
                if [[ $# -lt 2 ]]; then
                    die "--port requires a value"
                fi
                local_port="$2"
                shift 2
                ;;
            *)
                die "Unknown option '$1'. Use '${SCRIPT_NAME} --help' for usage."
                ;;
        esac
    done

    # Dispatch
    case "${cmd}" in
        generate) cmd_generate "${tunnel_name}" "${local_port}" ;;
        enable)   cmd_enable "${tunnel_name}" ;;
        status)   cmd_status "${tunnel_name}" ;;
        disable)  cmd_disable "${tunnel_name}" ;;
    esac
}

main "$@"
