def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>agentic-proxy</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #faf9f7;
            --surface: #ffffff;
            --border: #e5e7eb;
            --border2: #f0ede8;
            --text: #111827;
            --muted: #6b7280;
            --muted2: #9ca3af;
            --green: #16a34a;
            --green-bg: #f0fdf4;
            --yellow: #b45309;
            --yellow-bg: #fffbeb;
            --red: #dc2626;
            --red-bg: #fef2f2;
            --blue: #2563eb;
            --blue-bg: #eff6ff;
            --mono: 'JetBrains Mono', monospace;
            --sans: 'Inter', sans-serif;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: var(--sans);
            background: var(--bg);
            background-image: none;
            color: var(--text);
            font-size: 14px;
            line-height: 1.5;
        }

        /* TOPBAR */
        .topbar {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 0 2rem;
            height: 52px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .topbar-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .topbar h1 {
            font-family: var(--mono);
            font-size: 0.95rem;
            font-weight: 500;
            color: var(--text);
        }

        .divider-v {
            width: 1px;
            height: 16px;
            background: var(--border);
        }

        .session-label {
            font-size: 0.78rem;
            color: var(--muted);
            font-family: var(--mono);
        }

        .live-badge {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.72rem;
            color: var(--green);
            font-weight: 500;
        }

        .live-dot {
            width: 6px;
            height: 6px;
            background: var(--green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        /* MAIN LAYOUT */
        .main {
            padding: 1.5rem 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        /* SECTION LABEL */
        .section-label {
            font-size: 0.7rem;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.75rem;
        }

        /* STAT ROW */
        .stat-row {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 1px;
            background: var(--border);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 1.5rem;
        }

        .stat-cell {
            background: var(--surface);
            padding: 1rem 1.25rem;
        }

        .stat-cell .label {
            font-size: 0.7rem;
            color: var(--muted);
            margin-bottom: 0.35rem;
        }

        .stat-cell .value {
            font-size: 1.4rem;
            font-weight: 600;
            color: var(--text);
            font-family: var(--mono);
        }

        .stat-cell .value.green { color: var(--green); }
        .stat-cell .value.blue { color: var(--blue); }

        .stat-cell .sub {
            font-size: 0.7rem;
            color: var(--muted2);
            margin-top: 0.2rem;
            font-family: var(--mono);
        }

        /* CHARTS GRID */
        .charts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .chart-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
        }

        .chart-card .chart-title {
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 1.25rem;
        }

        .donut-wrap {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .donut-center {
            position: relative;
            flex-shrink: 0;
        }

        .donut-center svg { display: block; }

        .donut-legend { flex: 1; min-width: 0; }

        .legend-row {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.45rem;
            font-size: 0.72rem;
        }

        .legend-color {
            width: 8px;
            height: 8px;
            border-radius: 2px;
            flex-shrink: 0;
        }

        .legend-name { color: var(--text); flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .legend-count { color: var(--muted); font-family: var(--mono); font-size: 0.7rem; }

        /* TABLE */
        .table-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }

        .table-top {
            padding: 0.85rem 1.25rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .table-top span {
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .table-top .count {
            font-family: var(--mono);
            font-size: 0.72rem;
            color: var(--muted2);
        }

        .table-scroll { overflow-x: auto; }

        table { width: 100%; border-collapse: collapse; }

        th {
            padding: 0.6rem 1rem;
            text-align: left;
            font-size: 0.68rem;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            background: var(--bg);
            background-image: none;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }

        td {
            padding: 0.6rem 1rem;
            border-bottom: 1px solid var(--border2);
            font-size: 0.78rem;
            white-space: nowrap;
            font-family: var(--mono);
        }

        tr:last-child td { border-bottom: none; }
        tr:hover td { background: var(--bg);
            background-image: none; }

        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            font-size: 0.68rem;
            font-weight: 500;
            font-family: var(--sans);
        }

        .badge.hit { background: var(--green-bg); color: var(--green); }
        .badge.miss { background: #f9fafb; color: var(--muted); border: 1px solid var(--border); }
        .badge.simple { background: var(--green-bg); color: var(--green); }
        .badge.moderate { background: var(--yellow-bg); color: var(--yellow); }
        .badge.complex { background: var(--red-bg); color: var(--red); }
        .badge.downgraded { background: var(--blue-bg); color: var(--blue); }
        .badge.kept { background: var(--bg);
            background-image: none; color: var(--muted); border: 1px solid var(--border); }
        .badge.skipped { background: var(--bg);
            background-image: none; color: var(--muted2); }

        .saved-positive { color: var(--green); }
        .saved-zero { color: var(--muted2); }

        .empty-state {
            text-align: center;
            padding: 3rem;
            color: var(--muted2);
            font-family: var(--sans);
            font-size: 0.85rem;
        }
    </style>
</head>
<body>

<div class="topbar">
    <div class="topbar-left">
        <h1>agentic-proxy</h1>
        <div class="divider-v"></div>
        <span class="session-label" id="session-label">—</span>
    </div>
    <div style="display:flex;align-items:center;gap:0.75rem">
        <button onclick="clearCache()" id="clear-btn" style="font-family:var(--sans);font-size:0.72rem;font-weight:500;color:#6b7280;background:#faf9f7;border:1px solid #e5e7eb;padding:0.35rem 0.75rem;border-radius:5px;cursor:pointer;">Clear Cache</button>
        <div class="live-badge">
            <div class="live-dot"></div>
            Live
        </div>
    </div>
</div>

<div class="main">

    <!-- STAT ROW -->
    <div class="stat-row">
        <div class="stat-cell">
            <div class="label">Total Calls</div>
            <div class="value" id="total-calls">0</div>
        </div>
        <div class="stat-cell">
            <div class="label">Cache Hit Rate</div>
            <div class="value blue" id="hit-rate">0%</div>
            <div class="sub" id="hit-sub">0 hits / 0 calls</div>
        </div>
        <div class="stat-cell">
            <div class="label">Total Saved</div>
            <div class="value green" id="total-savings">$0.000000</div>
            <div class="sub" id="savings-sub">vs $0.000000 without proxy</div>
        </div>
        <div class="stat-cell">
            <div class="label">Cache Savings</div>
            <div class="value green" id="cache-savings">$0.000000</div>
            <div class="sub">from avoided API calls</div>
        </div>
        <div class="stat-cell">
            <div class="label">Routing Savings</div>
            <div class="value green" id="routing-savings">$0.000000</div>
            <div class="sub">from model downgrade</div>
        </div>
        <div class="stat-cell">
            <div class="label">Avg API Latency</div>
            <div class="value" id="avg-latency">0ms</div>
            <div class="sub" id="avg-router-latency">router: 0ms avg</div>
        </div>
        <div class="stat-cell">
            <div class="label">Cache Size</div>
            <div class="value" id="cache-size">0</div>
            <div class="sub" id="cache-size-sub">of 0 max entries</div>
        </div>
    </div>

    <!-- CHARTS -->
    <div class="charts-grid">
        <div class="chart-card">
            <div class="chart-title">Cache Distribution</div>
            <div class="donut-wrap">
                <div class="donut-center">
                    <svg width="80" height="80" viewBox="0 0 80 80" id="cache-svg">
                        <circle cx="40" cy="40" r="30" fill="none" stroke="#e5e7eb" stroke-width="10"/>
                    </svg>
                </div>
                <div class="donut-legend" id="cache-legend"></div>
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-title">Savings Breakdown</div>
            <div class="donut-wrap">
                <div class="donut-center">
                    <svg width="80" height="80" viewBox="0 0 80 80" id="savings-svg">
                        <circle cx="40" cy="40" r="30" fill="none" stroke="#e5e7eb" stroke-width="10"/>
                    </svg>
                </div>
                <div class="donut-legend" id="savings-legend"></div>
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-title">Complexity Distribution</div>
            <div class="donut-wrap">
                <div class="donut-center">
                    <svg width="80" height="80" viewBox="0 0 80 80" id="complexity-svg">
                        <circle cx="40" cy="40" r="30" fill="none" stroke="#e5e7eb" stroke-width="10"/>
                    </svg>
                </div>
                <div class="donut-legend" id="complexity-legend"></div>
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-title">Routing Decisions</div>
            <div class="donut-wrap">
                <div class="donut-center">
                    <svg width="80" height="80" viewBox="0 0 80 80" id="routing-svg">
                        <circle cx="40" cy="40" r="30" fill="none" stroke="#e5e7eb" stroke-width="10"/>
                    </svg>
                </div>
                <div class="donut-legend" id="routing-legend"></div>
            </div>
        </div>
    </div>

    <!-- TABLE -->
    <div class="table-card">
        <div class="table-top">
            <span>Call Log</span>
            <span class="count" id="call-count">0 calls</span>
        </div>
        <div class="table-scroll">
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Time</th>
                        <th>Cache</th>
                        <th>Complexity</th>
                        <th>Routing</th>
                        <th>Original Model</th>
                        <th>Routed To</th>
                        <th>API Latency</th>
                        <th>Router Latency</th>
                        <th>Input</th>
                        <th>Output</th>
                        <th>Actual Cost</th>
                        <th>Without Proxy</th>
                        <th>Saved</th>
                        <th>Prompt</th>
                    </tr>
                </thead>
                <tbody id="calls-body">
                    <tr><td colspan="14" class="empty-state">No calls yet — run your agent to see data</td></tr>
                </tbody>
            </table>
        </div>
    </div>

</div>

<script>
    const CIRC = 2 * Math.PI * 30;

    function drawDonut(svgId, segments) {
        const svg = document.getElementById(svgId);
        if (!svg) return;
        svg.querySelectorAll('.seg').forEach(e => e.remove());
        const total = segments.reduce((s, x) => s + x.value, 0);
        if (total === 0) return;
        let offset = 0;
        segments.forEach(seg => {
            const fill = (seg.value / total) * CIRC;
            const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            c.setAttribute('class', 'seg');
            c.setAttribute('cx', '40');
            c.setAttribute('cy', '40');
            c.setAttribute('r', '30');
            c.setAttribute('fill', 'none');
            c.setAttribute('stroke', seg.color);
            c.setAttribute('stroke-width', '10');
            c.setAttribute('stroke-dasharray', `${fill} ${CIRC - fill}`);
            c.setAttribute('stroke-dashoffset', -offset);
            c.setAttribute('transform', 'rotate(-90 40 40)');
            c.style.transition = 'stroke-dasharray 0.5s ease';
            svg.appendChild(c);
            offset += fill;
        });
    }

    function legendHtml(items) {
        return items.map(i => `
            <div class="legend-row">
                <div class="legend-color" style="background:${i.color}"></div>
                <span class="legend-name">${i.label}</span>
                <span class="legend-count">${i.value}</span>
            </div>
        `).join('');
    }

    function badge(cls, text) {
        return `<span class="badge ${cls}">${text}</span>`;
    }

    function fmt(n) { return '$' + (n || 0).toFixed(6); }

    async function refresh() {
        let data;
        try {
            const res = await fetch('/stats');
            data = await res.json();
        } catch(e) { return; }

        const s = data.summary;

        // Topbar
        if (data.session_start) {
            document.getElementById('session-label').textContent =
                data.session_start.replace('T', ' ').split('.')[0] + ' UTC';
        }

        // Stat row
        document.getElementById('total-calls').textContent = s.total_calls;
        document.getElementById('hit-rate').textContent = s.cache_hit_rate + '%';
        document.getElementById('hit-sub').textContent = `${s.cache_hits} hits / ${s.total_calls} calls`;
        document.getElementById('total-savings').textContent = fmt(s.total_savings);
        document.getElementById('savings-sub').textContent = `vs ${fmt(s.total_original_cost)} without proxy`;
        document.getElementById('avg-latency').textContent = s.avg_latency_ms + 'ms';
        document.getElementById('avg-router-latency').textContent = `router: ${s.avg_router_latency_ms}ms avg`;

        if (data.cache_size) {
            document.getElementById('cache-size').textContent = data.cache_size.entries;
            document.getElementById('cache-size-sub').textContent = `of ${data.cache_size.max_entries} max entries`;
        }

        // Calculate cache savings vs routing savings from call log
        let cacheSavings = 0;
        let routingSavings = 0;
        data.calls.forEach(c => {
            if (c.cache_hit) {
                cacheSavings += (c.original_cost || 0);
            } else {
                routingSavings += Math.max(0, (c.original_cost || 0) - (c.actual_cost || 0));
            }
        });

        document.getElementById('cache-savings').textContent = fmt(cacheSavings);
        document.getElementById('routing-savings').textContent = fmt(routingSavings);

        // Cache donut
        drawDonut('cache-svg', [
            { value: s.cache_hits, color: '#16a34a', label: 'Hits' },
            { value: s.api_calls, color: '#d1d5db', label: 'API Calls' },
        ]);
        document.getElementById('cache-legend').innerHTML = legendHtml([
            { label: 'Cache Hits', value: s.cache_hits, color: '#16a34a' },
            { label: 'API Calls', value: s.api_calls, color: '#d1d5db' },
        ]);

        // Savings donut
        const cacheSavingsRounded = parseFloat(cacheSavings.toFixed(6));
        const routingSavingsRounded = parseFloat(routingSavings.toFixed(6));
        drawDonut('savings-svg', [
            { value: cacheSavings, color: '#16a34a', label: 'Cache' },
            { value: routingSavings, color: '#2563eb', label: 'Routing' },
        ]);
        document.getElementById('savings-legend').innerHTML = legendHtml([
            { label: 'Cache', value: fmt(cacheSavingsRounded), color: '#16a34a' },
            { label: 'Routing', value: fmt(routingSavingsRounded), color: '#2563eb' },
        ]);

        // Complexity donut
        const cc = data.complexity_counts;
        drawDonut('complexity-svg', [
            { value: cc.SIMPLE, color: '#16a34a', label: 'Simple' },
            { value: cc.MODERATE, color: '#b45309', label: 'Moderate' },
            { value: cc.COMPLEX, color: '#dc2626', label: 'Complex' },
        ]);
        document.getElementById('complexity-legend').innerHTML = legendHtml([
            { label: 'Simple', value: cc.SIMPLE, color: '#16a34a' },
            { label: 'Moderate', value: cc.MODERATE, color: '#b45309' },
            { label: 'Complex', value: cc.COMPLEX, color: '#dc2626' },
        ]);

        // Routing donut
        const rc = data.routing_counts;
        drawDonut('routing-svg', [
            { value: rc.downgraded, color: '#2563eb', label: 'Downgraded' },
            { value: rc.kept, color: '#6b7280', label: 'Kept' },
            { value: rc.skipped, color: '#e5e7eb', label: 'Skipped' },
        ]);
        document.getElementById('routing-legend').innerHTML = legendHtml([
            { label: 'Downgraded', value: rc.downgraded, color: '#2563eb' },
            { label: 'Kept', value: rc.kept, color: '#6b7280' },
            { label: 'Skipped', value: rc.skipped, color: '#e5e7eb' },
        ]);

        // Table
        if (data.calls.length === 0) return;
        document.getElementById('call-count').textContent = data.calls.length + ' calls';
        document.getElementById('calls-body').innerHTML = data.calls.map((c, i) => {
            const saved = Math.max(0, (c.original_cost || 0) - (c.actual_cost || 0));
            const routingCls = c.routing_decision === 'downgraded' ? 'downgraded'
                : c.routing_decision === 'kept' ? 'kept' : 'skipped';
            const complexityCls = c.complexity ? c.complexity.toLowerCase() : '';
            return `<tr>
                <td>${data.calls.length - i}</td>
                <td>${c.timestamp.replace('T',' ').split('.')[0]}</td>
                <td>${badge(c.cache_hit ? 'hit' : 'miss', c.cache_hit ? 'HIT' : 'MISS')}</td>
                <td>${c.complexity ? badge(complexityCls, c.complexity) : '—'}</td>
                <td>${badge(routingCls, c.routing_decision || 'skipped')}</td>
                <td>${c.original_model}</td>
                <td>${c.routed_model || '—'}</td>
                <td>${c.latency_ms}ms</td>
                <td>${c.router_latency_ms ? c.router_latency_ms + 'ms' : '—'}</td>
                <td>${c.input_tokens.toLocaleString()}</td>
                <td>${c.output_tokens.toLocaleString()}</td>
                <td>${fmt(c.actual_cost)}</td>
                <td>${fmt(c.original_cost)}</td>
                <td class="${saved > 0 ? 'saved-positive' : 'saved-zero'}">${fmt(saved)}</td>
                <td style="color:#9ca3af;max-width:180px;overflow:hidden;text-overflow:ellipsis">${c.prompt_preview}...</td>
            </tr>`;
        }).join('');
    }

    refresh();
    setInterval(refresh, 2000);

    async function clearCache() {
        const btn = document.getElementById('clear-btn');
        btn.textContent = 'Clearing...';
        btn.disabled = true;
        await fetch('/cache/clear', { method: 'POST' });
        btn.textContent = 'Cleared';
        setTimeout(() => {
            btn.textContent = 'Clear Cache';
            btn.disabled = false;
        }, 2000);
    }
</script>
</body>
</html>"""