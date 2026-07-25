const ui = {
    feed: document.getElementById('threatFeed'),
    iocs: document.getElementById('activeIocs'),
    blocked: document.getElementById('blockedIps'),
};

async function fetchThreatData() {
    try {
        const data = await SentinelUI.fetchDashboardData();

        if (ui.iocs) {
            ui.iocs.innerHTML = `${Number(data.total_iocs || 0).toLocaleString()} <span class="trend-up">live</span>`;
        }
        if (ui.blocked) {
            ui.blocked.innerHTML = `${Number(data.total_blocked || 0).toLocaleString()} <span class="trend-up">blocked</span>`;
        }

        renderThreatFeed([
            ...(data.blocked_list || []),
            ...SentinelUI.flowsFrom(data).filter((f) => f.status === 'anomaly'),
        ]);

        SentinelUI.updateMonitoringStatusBadge(
            data.monitoring_mode,
            data.is_fallback_active,
            data.user_api_token
        );
    } catch (error) {
        console.error('Error fetching threat intel:', error);
    }
}

function renderThreatFeed(flows) {
    if (!ui.feed) return;
    ui.feed.innerHTML = '';

    const threats = flows.filter((f) => f.status === 'anomaly' || f.is_attack || f.isAttack);

    if (!threats.length) {
        ui.feed.innerHTML = '<tr><td colspan="5" class="text-center">No active threat indicators detected.</td></tr>';
        return;
    }

    const seen = new Set();
    threats.forEach((row) => {
        const key = `${row.src}-${row.time}-${row.proto}`;
        if (seen.has(key)) return;
        seen.add(key);

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="color: var(--text-secondary);">${row.time || 'N/A'}</td>
            <td>${row.src || ''}</td>
            <td>${row.proto || 'TCP'}</td>
            <td><span class="badge critical">High</span></td>
            <td class="action-blocked">Blocked / Flagged</td>
        `;
        ui.feed.appendChild(tr);
    });
}

setInterval(fetchThreatData, 3000);
fetchThreatData();
