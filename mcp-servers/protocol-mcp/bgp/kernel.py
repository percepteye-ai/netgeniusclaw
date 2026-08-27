"""
Kernel Route Manager — stub for platforms without netlink support.
Installs/removes routes in the OS FIB when BGP best-path changes.
"""
import logging

logger = logging.getLogger(__name__)


class KernelRouteManager:
    """Manages kernel/FIB route installation. Dry-run by default on macOS."""

    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        if dry_run:
            logger.info("KernelRouteManager running in dry-run mode (no FIB changes)")

    def install_route(self, prefix, next_hop, **kwargs):
        if self.dry_run:
            logger.debug("DRY-RUN: install %s via %s", prefix, next_hop)
            return True
        return False

    def remove_route(self, prefix, **kwargs):
        if self.dry_run:
            logger.debug("DRY-RUN: remove %s", prefix)
            return True
        return False

    def get_installed_routes(self):
        return []
