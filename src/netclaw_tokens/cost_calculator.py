"""Model-aware token cost calculator.

A SELF-HOSTED model has no per-token vendor price, so the default is zero and
that is the honest answer rather than a placeholder. The point of this module
is not to invent a number; it is to apply one you declare.

Declare real prices when you are billed per token — a hosted OpenAI-compatible
endpoint, say — through ``NETCLAW_TOKEN_PRICING_OVERRIDE``:

    NETCLAW_TOKEN_PRICING_OVERRIDE='{"qwen/qwen3.5-4b": {"input": 0.1, "output": 0.4}}'

An earlier version shipped a hosted vendor's price list and, for any model not
on it, silently billed at that vendor's flagship rate. Running a 4B model on
your own GPU it reported dollars per million tokens that were not being spent,
and there was nothing in the output to say the number was fictional. A wrong
number that looks authoritative is worse than a zero that is true.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict

from . import CostEstimate, ModelPricing

logger = logging.getLogger("netclaw_tokens.cost_calculator")

# ---------------------------------------------------------------------------
# Default pricing (per 1M tokens, USD)
# ---------------------------------------------------------------------------
#: The name a model gets when nothing has been declared for it. Zero, because
#: a model you serve yourself costs no dollars per token — the GPU is a fixed
#: cost the meter never sees.
SELF_HOSTED = "self-hosted"

DEFAULT_PRICING: Dict[str, ModelPricing] = {
    SELF_HOSTED: ModelPricing(
        model_name=SELF_HOSTED,
        input_price_per_1m=0.0,
        output_price_per_1m=0.0,
        # Prefix caching in vLLM or SGLang saves LATENCY, not money. A billing
        # discount here would be inventing a refund on a bill nobody sends.
        cache_discount_pct=0.0,
    ),
}

#: Provider prefixes stripped before lookup, so a declared price for
#: ``qwen/qwen3.5-4b`` is found whether the caller says that, ``local/qwen/…``
#: or ``lmstudio/qwen/…``. Nothing is aliased to a different model.
PROVIDER_PREFIXES: tuple[str, ...] = ("local/", "vllm/", "lmstudio/", "sglang/", "openai/")

MODEL_ALIASES: Dict[str, str] = {}


def _resolve_model(model: str) -> str:
    """Canonical identifier for a model reference.

    Strips a provider prefix so the same model priced once is found however it
    is referenced. An empty reference resolves to ``self-hosted``.
    """
    m = (model or "").lower().strip()
    if not m:
        return SELF_HOSTED
    for prefix in PROVIDER_PREFIXES:
        if m.startswith(prefix):
            m = m[len(prefix):]
            break
    return MODEL_ALIASES.get(m, m)


def _load_pricing_overrides() -> Dict[str, ModelPricing]:
    """Load pricing overrides from NETCLAW_TOKEN_PRICING_OVERRIDE env var.

    Expected format: JSON string like:
      {"qwen/qwen3.5-4b": {"input": 0.1, "output": 0.4}}
    """
    raw = os.environ.get("NETCLAW_TOKEN_PRICING_OVERRIDE", "")
    if not raw:
        return {}

    try:
        overrides_data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning(
            "NETCLAW_TOKEN_PRICING_OVERRIDE is not valid JSON; ignoring overrides"
        )
        return {}

    overrides: Dict[str, ModelPricing] = {}
    for model_name, prices in overrides_data.items():
        canonical = _resolve_model(model_name)
        base = DEFAULT_PRICING.get(canonical)
        overrides[canonical] = ModelPricing(
            model_name=canonical,
            input_price_per_1m=prices.get("input", base.input_price_per_1m if base else 0.0),
            output_price_per_1m=prices.get("output", base.output_price_per_1m if base else 0.0),
            cache_discount_pct=prices.get("cache_discount", base.cache_discount_pct if base else 0.0),
        )

    return overrides


def get_pricing(model: str = "") -> ModelPricing:
    """Return pricing for the given model, with env var override support.

    An undeclared model costs ZERO, which is the truth for a model you serve
    yourself. It is never billed at some other model's rate.
    """
    canonical = _resolve_model(model)

    # Check overrides first
    overrides = _load_pricing_overrides()
    if canonical in overrides:
        return overrides[canonical]

    # Check defaults
    if canonical in DEFAULT_PRICING:
        return DEFAULT_PRICING[canonical]

    # Nothing declared. Zero is correct for a self-hosted model; if this one is
    # billed per token, declare it rather than have a number invented for it.
    if canonical != SELF_HOSTED:
        logger.debug(
            "No pricing declared for '%s'; reporting zero cost. Set "
            "NETCLAW_TOKEN_PRICING_OVERRIDE if this endpoint bills per token.",
            model,
        )
    return DEFAULT_PRICING[SELF_HOSTED]


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "",
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> CostEstimate:
    """Calculate USD cost for token usage.

    Args:
        input_tokens: Number of input tokens (non-cached).
        output_tokens: Number of output tokens.
        model: Model identifier for pricing lookup.
        cache_creation_tokens: Tokens used to create cache entry.
        cache_read_tokens: Tokens read from cache (discounted).

    Returns:
        CostEstimate with itemized costs.
    """
    pricing = get_pricing(model)

    # Input cost: regular input tokens + cache creation tokens at full price
    regular_input = input_tokens + cache_creation_tokens
    input_cost = (regular_input / 1_000_000) * pricing.input_price_per_1m

    # Output cost
    output_cost = (output_tokens / 1_000_000) * pricing.output_price_per_1m

    # Cache discount: cached read tokens get discount
    discount_rate = pricing.cache_discount_pct / 100.0
    cache_read_cost_full = (cache_read_tokens / 1_000_000) * pricing.input_price_per_1m
    cache_discount = cache_read_cost_full * discount_rate

    # Cached reads still cost something (1 - discount_rate), so add the reduced cost
    # and subtract the discount from what would have been full price
    input_cost += cache_read_cost_full  # Add full cost first
    # Then the discount is applied

    total_cost = input_cost + output_cost - cache_discount

    return CostEstimate(
        input_cost=round(input_cost, 6),
        output_cost=round(output_cost, 6),
        cache_discount=round(cache_discount, 6),
        total_cost=round(total_cost, 6),
        model=_resolve_model(model),
    )
