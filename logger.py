import json
import os
from datetime import datetime
import config

_session_log = []

# Approximate cost per million tokens (as of 2025)
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


def generate_report():
    if not _session_log:
        return

    os.makedirs(os.path.dirname(config.LOG_OUTPUT_PATH), exist_ok=True)

    total_calls = len(_session_log)
    cache_hits = sum(1 for e in _session_log if e["cache_hit"])
    api_calls = total_calls - cache_hits
    total_input_tokens = sum(e["input_tokens"] for e in _session_log)
    total_output_tokens = sum(e["output_tokens"] for e in _session_log)
    total_cost = sum(e["estimated_cost"] for e in _session_log)

    rows = ""
    for i, e in enumerate(_session_log):
        cache_badge = (
            '<span style="color:#22c55e;font-weight:600">HIT</span>'
            if e["cache_hit"]
            else '<span style="color:#f97316;font-weight:600">MISS</span>'
        )
        routed = e["routed_model"] or "-"
        trimmed = e["trimmed_message_count"] if e["trimmed_message_count"] is not None else "-"
        rows += f"""
        <tr>
            <td>{i + 1}</td>
            <td>{e["timestamp"]}</td>
            <td>{cache_badge}</td>
            <td>{e["original_model"]}</td>
            <td>{routed}</td>
            <td>{e["original_message_count"]} → {trimmed}</td>
            <td>{e["input_tokens"]}</td>
            <td>{e["output_tokens"]}</td>
            <td>${e["estimated_cost"]:.6f}</td>
            <td>{e["prompt_preview"]}...</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>agentic-proxy session report</title>
    <style>
        body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }}
        h1 {{ color: #f8fafc; margin-bottom: 0.25rem; }}
        .subtitle {{ color: #94a3b8; margin-bottom: 2rem; font-size: 0.9rem; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .stat {{ background: #1e293b; border-radius: 8px; padding: 1rem; }}
        .stat-label {{ font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
        .stat-value {{ font-size: 1.5rem; font-weight: 700; color: #f8fafc; margin-top: 0.25rem; }}
        table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; }}
        th {{ background: #334155; color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; padding: 0.75rem 1rem; text-align: left; }}
        td {{ padding: 0.75rem 1rem; border-top: 1px solid #334155; font-size: 0.85rem; }}
        tr:hover td {{ background: #263548; }}
    </style>
</head>
<body>
    <h1>agentic-proxy</h1>
    <p class="subtitle">Session report — {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC</p>

    <div class="stats">
        <div class="stat">
            <div class="stat-label">Total Calls</div>
            <div class="stat-value">{total_calls}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Cache Hits</div>
            <div class="stat-value">{cache_hits}</div>
        </div>
        <div class="stat">
            <div class="stat-label">API Calls</div>
            <div class="stat-value">{api_calls}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Input Tokens</div>
            <div class="stat-value">{total_input_tokens:,}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Output Tokens</div>
            <div class="stat-value">{total_output_tokens:,}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Est. Cost</div>
            <div class="stat-value">${total_cost:.4f}</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Timestamp</th>
                <th>Cache</th>
                <th>Model</th>
                <th>Routed To</th>
                <th>Messages</th>
                <th>Input Tokens</th>
                <th>Output Tokens</th>
                <th>Cost</th>
                <th>Prompt Preview</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</body>
</html>"""

    with open(config.LOG_OUTPUT_PATH, "w") as f:
        f.write(html)

    print(f"\n[agentic-proxy] Session report saved to {config.LOG_OUTPUT_PATH}")
    print(f"[agentic-proxy] {total_calls} calls | {cache_hits} cache hits | {api_calls} API calls | ${total_cost:.4f} estimated cost")