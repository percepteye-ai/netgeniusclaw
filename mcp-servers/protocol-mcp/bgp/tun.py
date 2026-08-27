"""
TUN Device Manager — Cross-platform TUN interface for NetClaw data-plane tunnels.

Linux:  /dev/net/tun with IFF_TUN | IFF_NO_PI
macOS:  utun via PF_SYSTEM socket (SYSPROTO_CONTROL + com.apple.net.utun_control)

Requires root/sudo or CAP_NET_ADMIN.
"""

import fcntl
import logging
import os
import platform
import re
import socket
import struct
import subprocess
from typing import Optional

logger = logging.getLogger("TUN")

# Linux TUN constants
TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

# macOS utun constants
PF_SYSTEM = 32
SYSPROTO_CONTROL = 2
AF_SYS_CONTROL = 2
UTUN_CONTROL_NAME = b"com.apple.net.utun_control"
CTLIOCGINFO = 0xC0644E03  # _IOWR('N', 3, struct ctl_info)


class TUNDevice:
    """
    Cross-platform TUN device for reading/writing raw IP packets.

    Attributes:
        name: Actual interface name (e.g. "nclaw0" on Linux, "utun5" on macOS)
        fd:   File descriptor for reading/writing raw IP packets
    """

    def __init__(self, name: str):
        self.requested_name = name
        self.name: str = ""
        self.fd: int = -1
        self._sock: Optional[socket.socket] = None  # macOS utun socket
        self._system = platform.system()

    def open(self) -> str:
        """Open TUN device. Returns actual interface name. Raises OSError on failure."""
        if self._system == "Linux":
            return self._open_linux()
        elif self._system == "Darwin":
            return self._open_darwin()
        else:
            raise OSError(f"Unsupported platform: {self._system}")

    def _open_linux(self) -> str:
        self.fd = os.open("/dev/net/tun", os.O_RDWR)
        # struct ifreq: 16-byte name + 2-byte flags, padded to 40 bytes
        ifr = struct.pack("16sH", self.requested_name.encode(), IFF_TUN | IFF_NO_PI)
        ifr = ifr.ljust(40, b'\x00')
        result = fcntl.ioctl(self.fd, TUNSETIFF, ifr)
        self.name = result[:16].decode().strip('\x00')
        logger.info("Opened Linux TUN: %s (fd=%d)", self.name, self.fd)
        return self.name

    def _open_darwin(self) -> str:
        import ctypes
        import ctypes.util

        # Snapshot existing utun interfaces before creation
        existing_utuns = set()
        try:
            result = subprocess.run(["ifconfig", "-l"], capture_output=True, text=True, timeout=3)
            existing_utuns = {i for i in result.stdout.strip().split() if i.startswith("utun")}
        except Exception:
            pass

        self._sock = socket.socket(PF_SYSTEM, socket.SOCK_DGRAM, SYSPROTO_CONTROL)

        # Get control ID for utun
        ctl_info = struct.pack("I", 0) + UTUN_CONTROL_NAME.ljust(96, b'\x00')
        ctl_info = fcntl.ioctl(self._sock.fileno(), CTLIOCGINFO, ctl_info)
        ctl_id = struct.unpack("I", ctl_info[:4])[0]

        # Build sockaddr_ctl struct and connect via ctypes (Python socket.connect
        # doesn't accept raw bytes for PF_SYSTEM on macOS)
        # struct sockaddr_ctl { u_char sc_len; u_char sc_family; u_int16_t ss_sysaddr;
        #                       u_int32_t sc_id; u_int32_t sc_unit; u_int32_t[5] sc_reserved; }
        # sc_unit=0 means auto-assign
        sc_addr = struct.pack("=BBHIi5I", 32, AF_SYS_CONTROL, 0, ctl_id, 0,
                              0, 0, 0, 0, 0)

        libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
        ret = libc.connect(self._sock.fileno(), sc_addr, len(sc_addr))
        if ret != 0:
            errno_val = ctypes.get_errno()
            raise OSError(errno_val, f"connect() failed for utun: {os.strerror(errno_val)}")

        self.fd = self._sock.fileno()

        # Determine actual utun interface name by comparing before/after
        self.name = "utun?"
        try:
            result = subprocess.run(["ifconfig", "-l"], capture_output=True, text=True, timeout=3)
            current_utuns = {i for i in result.stdout.strip().split() if i.startswith("utun")}
            new_utuns = current_utuns - existing_utuns
            if new_utuns:
                self.name = sorted(new_utuns, key=lambda x: int(x[4:]))[-1]
            else:
                # Fallback: use the highest-numbered utun
                if current_utuns:
                    self.name = sorted(current_utuns, key=lambda x: int(x[4:]))[-1]
        except Exception:
            pass

        logger.info("Opened macOS TUN: %s (fd=%d)", self.name, self.fd)
        return self.name

    def close(self) -> None:
        """Close TUN device."""
        if self._sock:
            self._sock.close()
            self._sock = None
            self.fd = -1
        elif self.fd >= 0:
            os.close(self.fd)
            self.fd = -1
        if self.name:
            logger.info("Closed TUN: %s", self.name)

    def read_packet(self) -> bytes:
        """Read one raw IP packet (blocking). Returns bytes or empty on error."""
        if self.fd < 0:
            return b''
        try:
            data = os.read(self.fd, 65535)
            if self._system == "Darwin" and len(data) > 4:
                data = data[4:]  # Strip 4-byte AF header on macOS utun
            return data
        except OSError:
            return b''

    def write_packet(self, packet: bytes) -> int:
        """Write raw IP packet to TUN. Returns bytes written."""
        if self.fd < 0 or not packet:
            return 0
        try:
            if self._system == "Darwin":
                # Prepend 4-byte AF header (AF_INET6=30 for IPv6, AF_INET=2 for IPv4)
                ip_version = (packet[0] >> 4) if packet else 0
                af = 30 if ip_version == 6 else 2
                af_header = struct.pack(">I", af)
                return os.write(self.fd, af_header + packet) - 4
            return os.write(self.fd, packet)
        except OSError:
            return 0

    def configure_address(self, address: str, prefix_len: int) -> bool:
        """Assign IPv6 address to TUN interface."""
        try:
            if self._system == "Linux":
                subprocess.run(
                    ["ip", "-6", "addr", "add", f"{address}/{prefix_len}", "dev", self.name],
                    check=True, capture_output=True, timeout=5
                )
            elif self._system == "Darwin":
                subprocess.run(
                    ["ifconfig", self.name, "inet6", f"{address}/{prefix_len}"],
                    check=True, capture_output=True, timeout=5
                )
            logger.info("Configured %s/%d on %s", address, prefix_len, self.name)
            return True
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else ""
            if "exists" in stderr or "already" in stderr:
                return True
            logger.error("Failed to configure address on %s: %s", self.name, stderr)
            return False

    def bring_up(self) -> bool:
        """Bring TUN interface up."""
        try:
            if self._system == "Linux":
                subprocess.run(
                    ["ip", "link", "set", self.name, "up"],
                    check=True, capture_output=True, timeout=5
                )
            elif self._system == "Darwin":
                subprocess.run(
                    ["ifconfig", self.name, "up"],
                    check=True, capture_output=True, timeout=5
                )
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to bring up %s: %s", self.name, e)
            return False

    def set_mtu(self, mtu: int) -> bool:
        """Set MTU on TUN interface."""
        try:
            if self._system == "Linux":
                subprocess.run(
                    ["ip", "link", "set", self.name, "mtu", str(mtu)],
                    check=True, capture_output=True, timeout=5
                )
            elif self._system == "Darwin":
                subprocess.run(
                    ["ifconfig", self.name, "mtu", str(mtu)],
                    check=True, capture_output=True, timeout=5
                )
            return True
        except subprocess.CalledProcessError:
            return False
