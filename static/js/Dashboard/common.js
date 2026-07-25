const SentinelUI = (() => {
    const badgeCss = `
.monitoring-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 30px;
    font-size: 0.85rem;
    font-weight: 600;
    transition: all 0.3s ease;
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.monitoring-status-badge .badge-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}
.mode-scapy {
    background-color: rgba(59, 130, 246, 0.1);
    color: #60a5fa;
    border-color: rgba(59, 130, 246, 0.2);
}
.mode-scapy .badge-dot {
    background-color: #3b82f6;
    box-shadow: 0 0 8px #3b82f6;
}
.mode-agent {
    background-color: rgba(16, 185, 129, 0.1);
    color: #34d399;
    border-color: rgba(16, 185, 129, 0.2);
}
.mode-agent .badge-dot {
    background-color: #10b981;
    box-shadow: 0 0 8px #10b981;
}
.mode-fallback {
    background-color: rgba(245, 158, 11, 0.1);
    color: #fbbf24;
    border-color: rgba(245, 158, 11, 0.2);
    animation: alert-pulse 1.5s infinite;
}
.mode-fallback .badge-dot {
    background-color: #f59e0b;
    box-shadow: 0 0 8px #f59e0b;
}
@keyframes alert-pulse {
    0% { opacity: 0.8; }
    50% { opacity: 1; }
    100% { opacity: 0.8; }
}`;

    let cssReady = false;

    function ensureBadgeStyles() {
        if (cssReady) return;
        const style = document.createElement('style');
        style.textContent = badgeCss;
        document.head.appendChild(style);
        cssReady = true;
    }

    function updateMonitoringStatusBadge(mode, isFallback, tokenPreview) {
        ensureBadgeStyles();
        let badge = document.getElementById('monitoring-status-badge');
        if (!badge) {
            badge = document.createElement('div');
            badge.id = 'monitoring-status-badge';
            const header = document.querySelector('header');
            if (header) header.appendChild(badge);
            else return;
        }

        if (mode === 'scapy') {
            badge.className = 'monitoring-status-badge mode-scapy';
            badge.innerHTML = '<span class="badge-dot"></span> Scapy Sniffing Active';
            return;
        }

        if (isFallback) {
            badge.className = 'monitoring-status-badge mode-fallback';
            badge.innerHTML = '<span class="badge-dot"></span> Agent Offline — Waiting for Site Telemetry';
            return;
        }

        const preview = tokenPreview ? `${String(tokenPreview).substring(0, 8)}...` : 'Configured';
        badge.className = 'monitoring-status-badge mode-agent';
        badge.innerHTML = `<span class="badge-dot"></span> Agent Active (${preview})`;
    }

    async function fetchDashboardData() {
        const response = await fetch('/api/dashboard-data');
        if (!response.ok) throw new Error(`Dashboard HTTP ${response.status}`);
        return response.json();
    }

    function connectLiveSocket(onData) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/ws/live-traffic`;
        const socket = new WebSocket(wsUrl);

        socket.onmessage = (event) => {
            try {
                onData(JSON.parse(event.data));
            } catch (_) {}
        };

        socket.onerror = () => socket.close();
        socket.onclose = () => setTimeout(() => connectLiveSocket(onData), 5000);
        return socket;
    }

    function flowsFrom(data) {
        return data.network_flows || data.recent_flows || [];
    }

    return {
        updateMonitoringStatusBadge,
        fetchDashboardData,
        connectLiveSocket,
        flowsFrom,
    };
})();
