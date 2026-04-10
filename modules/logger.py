import sqlite3
import json
import os
from datetime import datetime
from modules.cache import get_cache_size

DB_PATH = "cache/cache.db"
SESSION_ID = datetime.utcnow().isoformat()

MODEL_COSTS = {
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
}

DEFAULT_COST = {"input": 3.0, "output": 15.0}


def _get_connection():
    os.makedirs("cache", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_log():
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON session_log(session_id)")
    conn.commit()
    conn.close()


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
            input_tokens, output_tokens
        ),
        "original_cost": meta.get("original_cost") if meta.get("original_cost") is not None else estimate_cost(
            meta.get("original_model", "unknown"),
            input_tokens, output_tokens
        ),
        "prompt_preview": _get_prompt_preview(body),
    }

    conn = _get_connection()
    conn.execute(
        "INSERT INTO session_log (session_id, timestamp, data) VALUES (?, ?, ?)",
        (SESSION_ID, entry["timestamp"], json.dumps(entry))
    )
    conn.commit()
    conn.close()


def _get_prompt_preview(body: dict) -> str:
    messages = body.get("messages", [])
    if not messages:
        return ""
    last = messages[-1].get("content", "")
    if isinstance(last, str):
        return last[:100]
    return ""


def get_sessions() -> list:
    conn = _get_connection()
    rows = conn.execute("""
        SELECT session_id, COUNT(*) as call_count, MIN(timestamp) as started_at
        FROM session_log
        GROUP BY session_id
        ORDER BY started_at DESC
    """).fetchall()
    conn.close()
    return [
        {
            "session_id": r["session_id"],
            "call_count": r["call_count"],
            "started_at": r["started_at"],
            "is_current": r["session_id"] == SESSION_ID
        }
        for r in rows
    ]


def _build_stats(rows: list, session_id: str | None) -> dict:
    calls = [json.loads(r["data"]) for r in rows]

    total_calls = len(calls)
    cache_hits = sum(1 for e in calls if e["cache_hit"])
    api_calls = total_calls - cache_hits
    total_input_tokens = sum(e["input_tokens"] for e in calls)
    total_output_tokens = sum(e["output_tokens"] for e in calls)
    total_actual_cost = sum(e["actual_cost"] for e in calls)
    total_original_cost = sum(e["original_cost"] for e in calls)
    total_savings = total_original_cost - total_actual_cost
    avg_latency = (
        sum(e["latency_ms"] for e in calls if not e["cache_hit"]) / api_calls
        if api_calls > 0 else 0
    )
    routed_calls = [e for e in calls if not e["cache_hit"] and e.get("router_latency_ms", 0) > 0]
    avg_router_latency = (
        sum(e["router_latency_ms"] for e in routed_calls) / len(routed_calls)
        if routed_calls else 0
    )

    complexity_counts = {"SIMPLE": 0, "MODERATE": 0, "COMPLEX": 0}
    for e in calls:
        if e.get("complexity") in complexity_counts:
            complexity_counts[e["complexity"]] += 1

    routing_counts = {"downgraded": 0, "kept": 0, "skipped": 0}
    for e in calls:
        decision = e.get("routing_decision", "skipped")
        if decision in routing_counts:
            routing_counts[decision] += 1

    return {
        "session_id": session_id or "overall",
        "is_current": session_id == SESSION_ID,
        "cache_size": get_cache_size(),
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
        "calls": list(reversed(calls)),
    }


def get_stats(session_id: str | None = None) -> dict:
    conn = _get_connection()
    if session_id:
        rows = conn.execute(
            "SELECT data FROM session_log WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT data FROM session_log ORDER BY id ASC"
        ).fetchall()
    conn.close()
    return _build_stats(rows, session_id)


init_log()