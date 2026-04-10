from datetime import datetime

_session_log = []
_session_start = datetime.utcnow().isoformat()

MODEL_COSTS = {
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
}

DEFAULT_COST = {"input": 3.0, "output": 15.0}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    costs = MODEL_COSTS.get(model, DEFAULT_COST)
    return (input_tokens / 1_000_000 * costs["input"]) + (output_tokens / 1_000_000 * costs["output"])


def log_request(body: dict, response: dict, meta: dict):
    usage = response.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "cache_hit": meta.get("cache_hit", False),
        "original_model": meta.get("original_model", "unknown"),
        "routed_model": meta.get("routed_model"),
        "routing_decision": meta.get("routing_decision", "skipped"),
        "complexity": meta.get("complexity"),
        "original_message_count": meta.get("original_message_count", 0),
        "trimmed_message_count": meta.get("trimmed_message_count"),
        "latency_ms": meta.get("latency_ms", 0),
        "router_latency_ms": meta.get("router_latency_ms", 0),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "actual_cost": meta.get("actual_cost") if meta.get("actual_cost") is not None else estimate_cost(
            meta.get("routed_model") or meta.get("original_model", "unknown"),
            input_tokens,
            output_tokens
        ),
        "original_cost": meta.get("original_cost") if meta.get("original_cost") is not None else estimate_cost(
            meta.get("original_model", "unknown"),
            input_tokens,
            output_tokens
        ),
        "prompt_preview": _get_prompt_preview(body),
    }

    _session_log.append(entry)


def _get_prompt_preview(body: dict) -> str:
    messages = body.get("messages", [])
    if not messages:
        return ""
    last = messages[-1].get("content", "")
    if isinstance(last, str):
        return last[:100]
    return ""


from modules.cache import get_cache_size


def get_stats() -> dict:
    total_calls = len(_session_log)
    cache_hits = sum(1 for e in _session_log if e["cache_hit"])
    api_calls = total_calls - cache_hits
    total_input_tokens = sum(e["input_tokens"] for e in _session_log)
    total_output_tokens = sum(e["output_tokens"] for e in _session_log)
    total_actual_cost = sum(e["actual_cost"] for e in _session_log)
    total_original_cost = sum(e["original_cost"] for e in _session_log)
    total_savings = total_original_cost - total_actual_cost
    avg_latency = (
        sum(e["latency_ms"] for e in _session_log if not e["cache_hit"]) / api_calls
        if api_calls > 0 else 0
    )

    complexity_counts = {"SIMPLE": 0, "MODERATE": 0, "COMPLEX": 0}
    for e in _session_log:
        if e["complexity"] in complexity_counts:
            complexity_counts[e["complexity"]] += 1

    routing_counts = {"downgraded": 0, "kept": 0, "skipped": 0}
    for e in _session_log:
        decision = e.get("routing_decision", "skipped")
        if decision in routing_counts:
            routing_counts[decision] += 1

    routed_calls = [e for e in _session_log if not e["cache_hit"] and e.get("router_latency_ms", 0) > 0]
    avg_router_latency = (
        sum(e["router_latency_ms"] for e in routed_calls) / len(routed_calls)
        if routed_calls else 0
    )

    cache_size = get_cache_size()

    return {
        "session_start": _session_start,
        "cache_size": cache_size,
        "summary": {
            "total_calls": total_calls,
            "cache_hits": cache_hits,
            "api_calls": api_calls,
            "cache_hit_rate": round(cache_hits / total_calls * 100, 1) if total_calls > 0 else 0,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_actual_cost": round(total_actual_cost, 6),
            "total_original_cost": round(total_original_cost, 6),
            "total_savings": round(total_savings, 6),
            "avg_latency_ms": round(avg_latency, 1),
            "avg_router_latency_ms": round(avg_router_latency, 1),
        },
        "complexity_counts": complexity_counts,
        "routing_counts": routing_counts,
        "calls": list(reversed(_session_log)),
    }