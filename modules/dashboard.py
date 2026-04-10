def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>agentic-proxy dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }
        h1 { color: #f8fafc; margin-bottom: 0.25rem; }
        .subtitle { color: #94a3b8; margin-bottom: 2rem; font-size: 0.9rem; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .stat { background: #1e293b; border-radius: 8px; padding: 1rem; }
        .stat-label { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
        .stat-value { font-size: 1.5rem; font-weight: 700; color: #f8fafc; margin-top: 0.25rem; }
        table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; }
        th { background: #334155; color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; padding: 0.75rem 1rem; text-align: left; }
        td { padding: 0.75rem 1rem; border-top: 1px solid #334155; font-size: 0.85rem; }
        tr:hover td { background: #263548; }
        .hit { color: #22c55e; font-weight: 600; }
        .miss { color: #f97316; font-weight: 600; }
        .simple { color: #22c55e; font-weight: 600; }
        .moderate { color: #f59e0b; font-weight: 600; }
        .complex { color: #ef4444; font-weight: 600; }
        .pulse { animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .live { display: inline-block; width: 8px; height: 8px; background: #22c55e; border-radius: 50%; margin-right: 6px; }
    </style>
</head>
<body>
    <h1>agentic-proxy</h1>
    <p class="subtitle"><span class="live pulse"></span>Live dashboard — updates every 2 seconds</p>

    <div class="stats" id="stats"></div>

    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Timestamp</th>
                <th>Cache</th>
                <th>Complexity</th>
                <th>Original Model</th>
                <th>Routed To</th>
                <th>Messages</th>
                <th>Input Tokens</th>
                <th>Output Tokens</th>
                <th>Cost</th>
                <th>Prompt Preview</th>
            </tr>
        </thead>
        <tbody id="calls"></tbody>
    </table>

    <script>
        function complexityClass(c) {
            if (!c) return "";
            return c.toLowerCase();
        }

        async function refresh() {
            const res = await fetch("/stats");
            const data = await res.json();
            const s = data.summary;

            document.getElementById("stats").innerHTML = `
                <div class="stat"><div class="stat-label">Total Calls</div><div class="stat-value">${s.total_calls}</div></div>
                <div class="stat"><div class="stat-label">Cache Hits</div><div class="stat-value">${s.cache_hits}</div></div>
                <div class="stat"><div class="stat-label">API Calls</div><div class="stat-value">${s.api_calls}</div></div>
                <div class="stat"><div class="stat-label">Input Tokens</div><div class="stat-value">${s.total_input_tokens.toLocaleString()}</div></div>
                <div class="stat"><div class="stat-label">Output Tokens</div><div class="stat-value">${s.total_output_tokens.toLocaleString()}</div></div>
                <div class="stat"><div class="stat-label">Est. Cost</div><div class="stat-value">$${s.total_cost.toFixed(4)}</div></div>
            `;

            document.getElementById("calls").innerHTML = data.calls.map((c, i) => `
                <tr>
                    <td>${data.calls.length - i}</td>
                    <td>${c.timestamp.replace("T", " ").split(".")[0]}</td>
                    <td class="${c.cache_hit ? "hit" : "miss"}">${c.cache_hit ? "HIT" : "MISS"}</td>
                    <td class="${complexityClass(c.complexity)}">${c.complexity || "-"}</td>
                    <td>${c.original_model}</td>
                    <td>${c.routed_model || "-"}</td>
                    <td>${c.original_message_count} → ${c.trimmed_message_count ?? "-"}</td>
                    <td>${c.input_tokens.toLocaleString()}</td>
                    <td>${c.output_tokens.toLocaleString()}</td>
                    <td>$${c.estimated_cost.toFixed(6)}</td>
                    <td>${c.prompt_preview}...</td>
                </tr>
            `).join("");
        }

        refresh();
        setInterval(refresh, 2000);
    </script>
</body>
</html>"""