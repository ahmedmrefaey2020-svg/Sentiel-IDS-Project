const incidentInfo = document.getElementById('incidentInfo');
const shapContainer = document.getElementById('shapContainer');

async function fetchXAIData() {
    try {
        const data = await SentinelUI.fetchDashboardData();
        if (data.xai_explanation) renderXAI(data.xai_explanation);
        SentinelUI.updateMonitoringStatusBadge(
            data.monitoring_mode,
            data.is_fallback_active,
            data.user_api_token
        );
    } catch (error) {
        console.error('Error fetching XAI data:', error);
    }
}

function renderXAI(explanation) {
    if (incidentInfo) {
        incidentInfo.innerHTML = `
            <div class="incident-title">Prediction: ${explanation.title}</div>
            <div class="incident-meta">
                <span>Confidence: <strong>${explanation.confidence}%</strong></span>
                <span>Target: ${explanation.target_ip}</span>
                <span>Model: ${explanation.model_name}</span>
            </div>
        `;
    }

    if (!shapContainer) return;

    let html = '';
    (explanation.features || []).forEach((feat) => {
        const isPositive = feat.value > 0;
        const colorClass = isPositive ? 'shap-red' : 'shap-green';
        const sign = isPositive ? '+' : '';
        html += `
            <div class="shap-row">
                <div class="shap-label">${feat.name}</div>
                <div class="shap-value">${sign}${feat.value}%</div>
                <div class="shap-bar-container">
                    <div class="shap-bar ${colorClass}" style="width: ${Math.abs(feat.value)}%;"></div>
                </div>
            </div>
        `;
    });
    shapContainer.innerHTML = html;
}

setInterval(fetchXAIData, 6000);
fetchXAIData();
