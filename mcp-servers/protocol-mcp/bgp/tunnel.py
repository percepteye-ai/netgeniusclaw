"""
NetClaw IP-over-TCP Tunnel Manager

Establishes a data-plane tunnel alongside each BGP session:
- Protocol discrimination via 5-byte magic "NCTUN" + 4-byte AS on port 1179
- Length-prefixed framing: [2-byte big-endian length][raw IP packet]
- Asyncio forwarding: TUN <-> TCP
- Deterministic IPv6 /127 address assignment per peer pair

Lower-AS side initiates the tunnel TCP connection (avoids collision).
"""

import asyncio
import logging
import struct
import subprocess
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .constants import (
    NCTUN_MAGIC, NCTUN_FRAME_HEADER_SIZE, NCTUN_MAX_PACKET_SIZE,
)
from .tun import TUNDevice

logger = logging.getLogger("TunnelManager")

# Global tunnel index counter
_tun_index = 0


def compute_tunnel_addresses(local_as: int, peer_as: int) -> Tuple[str, str]:
    """
    Deterministic overlay address assignment for a peer pair.

    Overlay prefix: fd00:cc::/48
    For pair (AS_low, AS_high): subnet fd00:cc:{low_hex}:{high_hex}::/127
    Lower AS gets ::0, higher AS gets ::1

    Args:
        local_as: Our AS number
        peer_as: Peer AS number

    Returns:
        (local_address, remote_address) as full IPv6 address strings
    """
    as_low = min(local_as, peer_as)
    as_high = max(local_as, peer_as)

    subnet = f"fd00:cc:{as_low:x}:{as_high:x}::"

    if local_as <= peer_as:
        return f"{subnet}0", f"{subnet}1"
    else:
        return f"{subnet}1", f"{subnet}0"


@dataclass
class PeerTunnel:
    """State for a single peer's data-plane tunnel."""
    peer_as: int
    local_as: int
    tun_device: Optional[TUNDevice] = None
    reader: Optional[asyncio.StreamReader] = None
    writer: Optional[asyncio.StreamWriter] = None
    local_address: str = ""
    remote_address: str = ""
    tun_to_tcp_task: Optional[asyncio.Task] = None
    tcp_to_tun_task: Optional[asyncio.Task] = None
    running: bool = False
    stats: Dict = field(default_factory=lambda: {
        "packets_tx": 0, "packets_rx": 0,
        "bytes_tx": 0, "bytes_rx": 0,
        "errors": 0,
    })


class TunnelManager:
    """
    Manages data-plane tunnels for all BGP peers.

    Lifecycle:
    1. BGP session established, both peers advertise CAP_NETCLAW_TUNNEL=201
    2. Lower-AS side initiates TCP connection with NCTUN magic + 4-byte AS
    3. Higher-AS side accepts via protocol discrimination in agent._handle_incoming_connection
    4. Both sides create TUN device, assign overlay addresses, start forwarding
    """

    def __init__(self, local_as: int, kernel_route_manager=None):
        self.local_as = local_as
        self.kernel_route_manager = kernel_route_manager
        self.tunnels: Dict[int, PeerTunnel] = {}  # peer_as -> PeerTunnel
        self.logger = logging.getLogger(f"TunnelManager[AS{local_as}]")
        self._forwarding_enabled = False

    def enable_ip_forwarding(self) -> None:
        """Enable kernel IP forwarding (requires sudo)."""
        if self._forwarding_enabled:
            return
        for cmd in [
            ["sysctl", "-w", "net.ipv4.ip_forward=1"],
            ["sysctl", "-w", "net.ipv6.conf.all.forwarding=1"],
        ]:
            try:
                subprocess.run(cmd, capture_output=True, timeout=5)
            except Exception as e:
                self.logger.warning("Could not run %s: %s", " ".join(cmd), e)
        self._forwarding_enabled = True
        self.logger.info("IP forwarding enabled (v4+v6)")

    async def initiate_tunnel(self, peer_as: int, endpoint: str,
                              retries: int = 3, retry_delay: float = 10.0) -> bool:
        """
        Initiate outbound tunnel connection (called by lower-AS side).

        Args:
            peer_as: Peer AS number
            endpoint: Peer's tunnel endpoint "host:port"
            retries: Number of retry attempts
            retry_delay: Seconds between retries

        Returns:
            True if tunnel established successfully
        """
        if peer_as in self.tunnels and self.tunnels[peer_as].running:
            self.logger.debug("Tunnel to AS%d already active", peer_as)
            return True

        # Parse host:port (handle hostname:port format)
        host, _, port_str = endpoint.rpartition(":")
        port = int(port_str)

        for attempt in range(1, retries + 1):
            if peer_as in self.tunnels and self.tunnels[peer_as].running:
                return True

            self.logger.info("Initiating tunnel to AS%d at %s:%d (attempt %d/%d)",
                             peer_as, host, port, attempt, retries)

            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=30.0,
                )
                # Send magic + our AS number for identification
                writer.write(NCTUN_MAGIC + struct.pack("!I", self.local_as))
                await writer.drain()

                # Brief pause to let remote side process handshake
                await asyncio.sleep(0.5)

                # Check if connection is still alive
                if writer.is_closing():
                    self.logger.warning("Tunnel TCP closed by remote during handshake (attempt %d)", attempt)
                    if attempt < retries:
                        await asyncio.sleep(retry_delay)
                    continue

                tunnel = await self._setup_tunnel(peer_as, reader, writer)
                if tunnel:
                    self.logger.info("Tunnel to AS%d established (initiator)", peer_as)
                    return True

                self.logger.warning("Tunnel setup failed for AS%d (attempt %d)", peer_as, attempt)

            except Exception as e:
                self.logger.error("Failed to initiate tunnel to AS%d (attempt %d): %s",
                                  peer_as, attempt, e)

            if attempt < retries:
                self.logger.info("Retrying tunnel to AS%d in %.0fs...", peer_as, retry_delay)
                await asyncio.sleep(retry_delay)

        self.logger.error("All %d tunnel attempts to AS%d failed", retries, peer_as)
        return False

    async def accept_tunnel(self, peer_as: int,
                            reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter) -> bool:
        """
        Accept inbound tunnel connection (called by higher-AS side).

        The NCTUN magic + 4-byte AS have already been consumed by the agent's
        protocol discrimination logic.

        Args:
            peer_as: Peer AS number (read from tunnel handshake)
            reader: TCP stream reader
            writer: TCP stream writer

        Returns:
            True if tunnel set up successfully
        """
        self.logger.info("Accepting tunnel from AS%d", peer_as)

        tunnel = await self._setup_tunnel(peer_as, reader, writer)
        if tunnel:
            self.logger.info("Tunnel from AS%d established (acceptor)", peer_as)
            return True
        return False

    async def _setup_tunnel(self, peer_as: int,
                            reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter) -> Optional[PeerTunnel]:
        """Common tunnel setup: create TUN, assign addresses, start forwarding."""
        global _tun_index

        # Tear down existing tunnel for this peer if any
        if peer_as in self.tunnels:
            await self.teardown_tunnel(peer_as)

        # Compute overlay addresses
        local_addr, remote_addr = compute_tunnel_addresses(self.local_as, peer_as)

        # Create TUN device
        tun_name = f"nclaw{_tun_index}"
        _tun_index += 1

        tun = TUNDevice(tun_name)
        try:
            actual_name = tun.open()
        except OSError as e:
            self.logger.error("Cannot create TUN %s: %s (need sudo?)", tun_name, e)
            return None

        # Bring up and configure
        tun.bring_up()
        tun.set_mtu(NCTUN_MAX_PACKET_SIZE)
        tun.configure_address(local_addr, 127)

        # Enable IP forwarding
        self.enable_ip_forwarding()

        # Create tunnel state
        tunnel = PeerTunnel(
            peer_as=peer_as,
            local_as=self.local_as,
            tun_device=tun,
            reader=reader,
            writer=writer,
            local_address=local_addr,
            remote_address=remote_addr,
            running=True,
        )
        self.tunnels[peer_as] = tunnel

        # Start forwarding tasks
        tunnel.tun_to_tcp_task = asyncio.create_task(
            self._forward_tun_to_tcp(tunnel)
        )
        tunnel.tcp_to_tun_task = asyncio.create_task(
            self._forward_tcp_to_tun(tunnel)
        )

        self.logger.info(
            "Tunnel AS%d ready: %s <-> %s on %s",
            peer_as, local_addr, remote_addr, actual_name
        )

        # Store endpoint for reconnection
        tunnel._endpoint = endpoint if hasattr(tunnel, '_endpoint') else None

        return tunnel

    async def _forward_tun_to_tcp(self, tunnel: PeerTunnel) -> None:
        """Read IP packets from TUN, length-frame them, send over TCP."""
        loop = asyncio.get_event_loop()
        tun = tunnel.tun_device

        while tunnel.running and tunnel.writer and not tunnel.writer.is_closing():
            try:
                # Read from TUN fd in executor (blocking read)
                packet = await loop.run_in_executor(None, tun.read_packet)
                if not packet:
                    await asyncio.sleep(0.01)
                    continue

                if len(packet) > NCTUN_MAX_PACKET_SIZE:
                    tunnel.stats["errors"] += 1
                    continue

                # Frame: [2-byte big-endian length][raw IP packet]
                frame = struct.pack("!H", len(packet)) + packet
                tunnel.writer.write(frame)
                await tunnel.writer.drain()

                tunnel.stats["packets_tx"] += 1
                tunnel.stats["bytes_tx"] += len(packet)

            except asyncio.CancelledError:
                break
            except (ConnectionError, BrokenPipeError):
                self.logger.warning("Tunnel TCP lost (tun->tcp) AS%d", tunnel.peer_as)
                break
            except Exception as e:
                self.logger.error("tun->tcp error AS%d: %s", tunnel.peer_as, e)
                tunnel.stats["errors"] += 1
                await asyncio.sleep(0.1)

    async def _forward_tcp_to_tun(self, tunnel: PeerTunnel) -> None:
        """Read length-framed IP packets from TCP, write to TUN."""
        tun = tunnel.tun_device
        loop = asyncio.get_event_loop()

        while tunnel.running and tunnel.reader:
            try:
                # Read 2-byte length header
                len_bytes = await tunnel.reader.readexactly(NCTUN_FRAME_HEADER_SIZE)
                pkt_len = struct.unpack("!H", len_bytes)[0]

                if pkt_len == 0 or pkt_len > NCTUN_MAX_PACKET_SIZE:
                    tunnel.stats["errors"] += 1
                    continue

                # Read packet payload
                packet = await tunnel.reader.readexactly(pkt_len)

                # Write to TUN in executor (blocking write)
                await loop.run_in_executor(None, tun.write_packet, packet)

                tunnel.stats["packets_rx"] += 1
                tunnel.stats["bytes_rx"] += pkt_len

            except asyncio.IncompleteReadError:
                self.logger.warning("Tunnel TCP closed (tcp->tun) AS%d", tunnel.peer_as)
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("tcp->tun error AS%d: %s", tunnel.peer_as, e)
                tunnel.stats["errors"] += 1
                await asyncio.sleep(0.1)

    async def teardown_tunnel(self, peer_as: int) -> None:
        """Tear down tunnel for a specific peer."""
        tunnel = self.tunnels.pop(peer_as, None)
        if not tunnel:
            return

        tunnel.running = False

        # Cancel forwarding tasks
        for task in [tunnel.tun_to_tcp_task, tunnel.tcp_to_tun_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close TCP
        if tunnel.writer:
            try:
                tunnel.writer.close()
                await tunnel.writer.wait_closed()
            except Exception:
                pass

        # Close TUN device
        if tunnel.tun_device:
            tunnel.tun_device.close()

        self.logger.info("Tunnel to AS%d torn down", peer_as)

    async def teardown_all(self) -> None:
        """Tear down all tunnels (called on shutdown)."""
        for peer_as in list(self.tunnels.keys()):
            await self.teardown_tunnel(peer_as)

    def get_tunnel_address(self, peer_as: int) -> Optional[str]:
        """Get our local overlay address for a specific peer tunnel."""
        tunnel = self.tunnels.get(peer_as)
        if tunnel and tunnel.running:
            return tunnel.local_address
        return None

    def get_tunnel_stats(self) -> Dict:
        """Get statistics for all tunnels."""
        return {
            f"AS{peer_as}": {
                "local_address": t.local_address,
                "remote_address": t.remote_address,
                "tun_device": t.tun_device.name if t.tun_device else None,
                "running": t.running,
                **t.stats,
            }
            for peer_as, t in self.tunnels.items()
        }
