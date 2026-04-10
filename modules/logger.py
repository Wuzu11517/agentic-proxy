from datetime import datetime

_session_log = []

MODEL_COSTS = {
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
}

DEFAULT_COST = {"input": 3.0, "output": 15.0}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    costs = MODEL_COSTS.get(model, DEFAULT_COST)
    return (input_tokens / 1_000_000 * costs["input"]) + (output_tokens / 1_000_000 * costs["output"])


def log_request(body: dict, response: dict, meta: dict):
    model = meta.get("routed_model") or meta.get("original_model", "unknown")
    usage = response.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cost = _estimate_cost(model, input_tokens, output_tokens)

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "cache_hit": meta.get("cache_hit", False),
        "original_model": meta.get("original_model", "unknown"),
        "routed_model": meta.get("routed_model"),
        "complexity": meta.get("complexity"),
        "original_message_count": meta.get("original_message_count", 0),
        "trimmed_message_count": meta.get("trimmed_message_count"),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": cost,
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


def get_stats() -> dict:
    total_calls = len(_session_log)
    cache_hits = sum(1 for e in _session_log if e["cache_hit"])
    api_calls = total_calls - cache_hits
    total_input_tokens = sum(e["input_tokens"] for e in _session_log)
    total_output_tokens = sum(e["output_tokens"] for e in _session_log)
    total_cost = sum(e["estimated_cost"] for e in _session_log)

    return {
        "summary": {
            "total_calls": total_calls,
            "cache_hits": cache_hits,
            "api_calls": api_calls,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_cost": round(total_cost, 6),
        },
        "calls": list(reversed(_session_log)),
    }