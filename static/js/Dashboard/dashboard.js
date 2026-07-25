const uiElements = {
    riskScore: document.getElementById('riskScore'),
    activeConn: document.getElementById('activeConn'),
    packetRate: document.getElementById('packetRate'),
    activityTable: document.getElementById('activityTable'),
    predictionAlert: document.getElementById('predictionAlert'),
};

let currentFlows = [];

function processDashboardData(data) {
    if (!data) return;

    if (uiElements.activeConn) {
        const activeConn = data.active_connections ?? data.connections ?? 0;
        uiElements.activeConn.innerText = Number(activeConn).toLocaleString();
    }
    if (uiElements.packetRate) {
        uiElements.packetRate.innerText = Number(data.packet_rate || 0).toLocaleString();
    }

    if (uiElements.riskScore) {
        const riskScore = data.risk_score ?? data.score ?? 0;
        const riskMessage = data.risk_message ?? data.message ?? '';
        
        uiElements.riskScore.innerHTML = `${riskScore}<span>%</span>`;
        uiElements.riskScore.className = `card-value ${riskScore > 70 ? 'risk-high' : 'risk-low'}`;
        if (uiElements.riskScore.nextElementSibling) {
            uiElements.riskScore.nextElementSibling.innerText = riskMessage;
        }
    }

    if (uiElements.predictionAlert) {
        uiElements.predictionAlert.classList.toggle('active', Boolean(data.is_anomaly));
    }

    currentFlows = SentinelUI.flowsFrom(data);
    renderTable(currentFlows);
    SentinelUI.updateMonitoringStatusBadge(
        data.monitoring_mode,
        data.is_fallback_active,
        data.user_api_token
    );
}

function renderTable(flows) {
    if (!uiElements.activityTable) return;
    uiElements.activityTable.innerHTML = '';

    if (!flows || flows.length === 0) {
        uiElements.activityTable.innerHTML = '<tr><td colspan="5" class="text-center">No active traffic</td></tr>';
        return;
    }

    flows.slice(0, 25).forEach((flow) => {
        const tr = document.createElement('tr');
        const badgeClass = flow.status === 'normal' ? 'normal' : 'anomaly';
        const badgeText = flow.status === 'normal' ? 'Normal' : 'Anomaly';
        tr.innerHTML = `
            <td>${flow.time || ''}</td>
            <td>${flow.src || ''}</td>
            <td>${flow.port ?? ''}</td>
            <td>${flow.proto || ''}</td>
            <td><span class="badge ${badgeClass}">${badgeText}</span></td>
        `;
        uiElements.activityTable.appendChild(tr);
    });
}

async function fetchDashboardData() {
    try {
        const data = await SentinelUI.fetchDashboardData();
        processDashboardData(data);
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}

const btnAction = document.querySelector('.btn-action');
if (btnAction) {
    btnAction.addEventListener('click', async function () {
        if (!currentFlows.length) {
            alert('No traffic to block!');
            return;
        }

        const targetIp = currentFlows.find((f) => f.status === 'anomaly')?.src || currentFlows[0].src;

        try {
            const response = await fetch('/api/block-ip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip: targetIp }),
            });
            const result = await response.json();
            alert(result.message || 'Done');
            uiElements.predictionAlert?.classList.remove('active');
            fetchDashboardData();
        } catch (error) {
            console.error('Error blocking IP:', error);
            alert('Failed to block IP.');
        }
    });
}

setInterval(fetchDashboardData, 5000);
fetchDashboardData();
SentinelUI.connectLiveSocket(processDashboardData);