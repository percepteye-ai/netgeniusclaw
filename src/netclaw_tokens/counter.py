"""Token counting against the model server that actually serves the model.

The authority on how a model tokenizes is the server serving it. vLLM and
SGLang both expose a ``POST /tokenize`` endpoint for exactly this, so counting
goes there and gets an EXACT count for the model in use.

This replaces an earlier implementation that called a hosted vendor's
``count_tokens`` API. That was wrong here in two separate ways, and the second
is the one that mattered: it required a vendor account to count tokens for a
model that vendor does not serve, and when it succeeded it returned a count
from a DIFFERENT tokenizer than the one generating the text. An exact number
from the wrong tokenizer is worse than an honest estimate, because it does not
announce itself as approximate.

Falls back to a ``len(text) / 4`` estimate whenever the server cannot answer,
and says so with ``estimated=True``. Never raises: a counting failure must cost
the count, never the interaction it was measuring.

Standard library only. Counting tokens must not impose a dependency on a
process that is already running an agent.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from . import TokenCount

logger = logging.getLogger("netclaw_tokens.counter")

#: Counting must never stall the interaction it measures. A tokenizer that has
#: not answered in two seconds is not going to make the footer more useful.
_TIMEOUT_S = 2.0

#: Warn once per distinct reason. The fallback is a normal operating mode on a
#: server without /tokenize, and a warning on every call would bury real ones.
_warned: set[str] = set()


def _estimate_tokens(text: str) -> int:
    """Approximate token count using the len/4 heuristic."""
    return max(1, len(text) // 4)


def _tokenize_url() -> Optional[str]:
    """Where the serving model's tokenizer lives, or None if unconfigured.

    ``/tokenize`` sits at the server ROOT, not under the OpenAI-compatible
    ``/v1`` prefix, so the prefix is stripped if present.
    """
    base = (os.environ.get("NETGENIUSCLAW_MODEL_BASE_URL")
            or os.environ.get("OPENAI_BASE_URL") or "").strip()
    if not base:
        return None
    base = base.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base + "/tokenize"


def _count_via_server(payload: dict) -> Optional[int]:
    """Exact token count from the model server, or None if it cannot answer.

    Response shapes differ between servers and versions, so both the documented
    ``count`` field and a returned ``tokens`` array are accepted. Anything else
    is treated as no answer rather than guessed at.
    """
    url = _tokenize_url()
    if not url:
        _warn_once("unconfigured", "no model base URL set (NETGENIUSCLAW_MODEL_BASE_URL "
                                  "or OPENAI_BASE_URL); using local estimation")
        return None
    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
        _warn_once(type(exc).__name__,
                   f"model server tokenizer unavailable ({type(exc).__name__}); "
                   f"using local estimation")
        return None

    if isinstance(body, dict):
        n = body.get("count")
        if isinstance(n, int) and not isinstance(n, bool):
            return n
        toks = body.get("tokens")
        if isinstance(toks, list):
            return len(toks)
    _warn_once("shape", "model server returned an unrecognised /tokenize response; "
                        "using local estimation")
    return None


def _warn_once(key: str, msg: str) -> None:
    if key not in _warned:
        _warned.add(key)
        logger.warning("%s (further occurrences at debug level)", msg)
    else:
        logger.debug("%s", msg)


def _result(tokens: int, model: str, *, estimated: bool) -> TokenCount:
    return TokenCount(
        input_tokens=tokens,
        output_tokens=0,
        model=model,
        timestamp=datetime.now(timezone.utc),
        estimated=estimated,
    )


def count_tokens(text: str, model: str = "") -> TokenCount:
    """Count tokens for a text string.

    Args:
        text: The text to count tokens for.
        model: The model identifier, passed to the server so it selects the
            right tokenizer. Empty means "whatever the server has loaded".

    Returns:
        TokenCount with input_tokens populated. ``estimated=True`` when the
        server could not answer and the len/4 heuristic was used instead.

    Never raises — always returns a result, exact or estimated.
    """
    n = _count_via_server({"model": model, "prompt": text} if model
                          else {"prompt": text})
    if n is not None:
        return _result(n, model, estimated=False)
    return _result(_estimate_tokens(text), model, estimated=True)


def _flatten(messages: list[dict], system: Optional[str]) -> str:
    total = system or ""
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += content
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and "text" in block:
                    total += block["text"]
    return total


def count_message_tokens(
    messages: list[dict],
    model: str = "",
    system: Optional[str] = None,
) -> TokenCount:
    """Count tokens for a full message array (input context).

    The system prompt is prepended as a message rather than passed as a
    separate field: the OpenAI-compatible chat format carries it as
    ``role="system"``, and a server applying its chat template needs it in the
    array to account for the template's own tokens.
    """
    payload_msgs = ([{"role": "system", "content": system}] if system else []) + list(messages)
    payload: dict = {"messages": payload_msgs}
    if model:
        payload["model"] = model

    n = _count_via_server(payload)
    if n is not None:
        return _result(n, model, estimated=False)
    return _result(_estimate_tokens(_flatten(messages, system)), model, estimated=True)
