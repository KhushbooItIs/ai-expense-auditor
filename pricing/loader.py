"""
Loads pricing data from DB into a plain dict that the engine can consume
without any Django imports. Cache TTL = 5 min so admin edits propagate quickly.
"""
from django.core.cache import cache

_CACHE_KEY = "pricing_data_v1"
_CACHE_TTL = 300  # 5 minutes


def get_pricing_data() -> dict:
    data = cache.get(_CACHE_KEY)
    if data is None:
        data = _load_from_db()
        cache.set(_CACHE_KEY, data, timeout=_CACHE_TTL)
    return data


def bust_cache():
    """Call from admin save_model override if you want instant propagation."""
    cache.delete(_CACHE_KEY)


def _load_from_db() -> dict:
    from pricing.models import VendorPlan, ToolFitScore

    plans = {}
    for p in VendorPlan.objects.all():
        plans[(p.vendor_key, p.plan_key)] = {
            "vendor_name": p.vendor_name,
            "plan_name": p.plan_name,
            "price_monthly": float(p.price_monthly) if p.price_monthly is not None else None,
            "price_per_seat": float(p.price_per_seat) if p.price_per_seat is not None else None,
            "min_seats": p.min_seats,
            "max_seats": p.max_seats,
            "features": p.features,
            "credex_eligible": p.credex_eligible,
            "source_url": p.source_url,
        }

    fit_scores = {}
    for s in ToolFitScore.objects.all():
        fit_scores[(s.vendor_key, s.plan_key, s.use_case)] = {
            "score": s.score,
            "reasoning": s.reasoning,
        }

    return {"plans": plans, "fit_scores": fit_scores}
