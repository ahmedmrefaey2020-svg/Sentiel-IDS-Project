const ui = {
    progress: document.getElementById('timeProgress'),
    banner: document.getElementById('forecastBanner'),
    title: document.getElementById('forecastTitle'),
    desc: document.getElementById('forecastDesc'),
    mainProb: document.getElementById('mainProbability'),
    log: document.getElementById('eventLog'),
};

function getLogTime() {
    return new Date().toLocaleTimeString('en-US', { hour12: false });
}

function addLogEntry(message, level) {
    if (!ui.log) return;
    const li = document.createElement('li');
    li.className = `log-item ${level}`;
    li.innerHTML = `<span class="log-time">[${getLogTime()}]</span><span class="log-message">${message}</span>`;
    ui.log.prepend(li);
    if (ui.log.children.length > 5) ui.log.removeChild(ui.log.lastChild);
}

function updateTimelineUI(riskScore, message) {
    const score = Number(riskScore) || 0;
    const level = score > 80 ? 'critical' : score > 50 ? 'warning' : 'normal';
    const title =
        score > 80
            ? 'HIGH PROBABILITY OF ATTACK'
            : score > 50
              ? 'Elevated Risk Horizon'
              : 'Monitoring Normal Traffic';

    if (ui.progress) ui.progress.style.width = `${score}%`;
    if (ui.mainProb) ui.mainProb.innerText = `${score}%`;
    if (ui.title) ui.title.innerText = title;
    if (ui.desc) ui.desc.innerText = message || '';
    if (ui.banner) ui.banner.classList.toggle('alert', score > 80);
    if (score > 50) addLogEntry(message || title, level);
}

async function fetchPredictionTimeline() {
    try {
        const data = await SentinelUI.fetchDashboardData();
        updateTimelineUI(data.risk_score, data.risk_message);
        SentinelUI.updateMonitoringStatusBadge(
            data.monitoring_mode,
            data.is_fallback_active,
            data.user_api_token
        );
    } catch (error) {
        console.error('Error fetching timeline data:', error);
    }
}

setInterval(fetchPredictionTimeline, 3000);
fetchPredictionTimeline();
