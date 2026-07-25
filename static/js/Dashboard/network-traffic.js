const ui = {
    inbound: document.getElementById('inboundVal'),
    outbound: document.getElementById('outboundVal'),
    latency: document.getElementById('latencyVal'),
    dropped: document.getElementById('droppedVal'),
    graph: document.getElementById('graphContainer'),
    log: document.getElementById('trafficLog'),
};

const config = {
    maxGraphBars: 40,
    maxLogRows: 12,
};

let graphData = Array(config.maxGraphBars).fill(10);

function initGraph() {
    if (!ui.graph) return;
    ui.graph.innerHTML = '';
    for (let i = 0; i < config.maxGraphBars; i++) {
        const bar = document.createElement('div');
        bar.className = 'graph-bar';
        bar.style.height = '5%';
        ui.graph.appendChild(bar);
    }
}

function updateGraph(newValue) {
    if (!ui.graph) return;
    graphData.push(Math.max(1, Math.min(100, Number(newValue) || 0)));
    if (graphData.length > config.maxGraphBars) graphData.shift();

    const bars = ui.graph.children;
    for (let i = 0; i < bars.length; i++) {
        bars[i].style.height = `${graphData[i]}%`;
        if (graphData[i] > 85) bars[i].style.backgroundColor = 'var(--danger-color)';
        else if (graphData[i] > 65) bars[i].style.backgroundColor = '#f59e0b';
        else bars[i].style.backgroundColor = 'var(--brand-color)';
    }
}

function renderLog(rows) {
    if (!ui.log) return;
    ui.log.innerHTML = '';
    rows.slice(0, config.maxLogRows).forEach((row) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="color: var(--text-secondary);">${row.time || ''}</td>
            <td>${row.src || ''}</td>
            <td>${row.port ?? ''}</td>
            <td><span class="protocol-tag">${row.proto || ''}</span></td>
            <td>${row.status === 'anomaly' ? 'Anomaly' : 'Normal'}</td>
        `;
        ui.log.appendChild(tr);
    });
}

async function fetchNetworkData() {
    try {
        const data = await SentinelUI.fetchDashboardData();
        if (ui.inbound) ui.inbound.innerHTML = `${data.packet_rate || 0} <span class="metric-unit">pps</span>`;
        if (ui.outbound) ui.outbound.innerHTML = `${data.active_connections || 0} <span class="metric-unit">flows</span>`;
        if (ui.latency) ui.latency.innerHTML = `${data.risk_score || 0} <span class="metric-unit">% Risk</span>`;
        if (ui.dropped) ui.dropped.innerHTML = `${data.total_blocked || 0} <span class="metric-unit">blocked</span>`;

        updateGraph(data.risk_score);
        renderLog(SentinelUI.flowsFrom(data));
        SentinelUI.updateMonitoringStatusBadge(
            data.monitoring_mode,
            data.is_fallback_active,
            data.user_api_token
        );
    } catch (error) {
        console.error('Error fetching network data:', error);
    }
}

initGraph();
setInterval(fetchNetworkData, 2000);
fetchNetworkData();
