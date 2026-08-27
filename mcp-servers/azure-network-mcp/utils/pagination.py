"""Azure SDK pagination helper for ItemPaged iterators."""

from __future__ import annotations

import logging
from typing import TypeVar, Callable, Optional

logger = logging.getLogger("azure-network-mcp")

T = TypeVar("T")


def collect_all_pages(paged_iterator, transform: Optional[Callable] = None) -> list:
    """
    Collect all items from an Azure SDK ItemPaged iterator.

    Args:
        paged_iterator: Azure SDK paged result (ItemPaged).
        transform: Optional function to transform each item.

    Returns:
        List of all items (transformed if transform provided).
    """
    results = []
    try:
        for item in paged_iterator:
            if transform:
                results.append(transform(item))
            else:
                results.append(item)
    except StopIteration:
        pass
    except Exception as e:
        logger.error(f"Error during pagination: {e}")
        raise
    return results
