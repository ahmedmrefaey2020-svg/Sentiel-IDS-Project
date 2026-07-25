const canvas = document.getElementById('metricsChart');
const ctx = canvas.getContext('2d');

const MAX_POINTS = 60;
let dataPoints = [];

for (let i = 0; i < MAX_POINTS; i++) {
    dataPoints.push({ val: 10, ci: 2 });
}

function resizeCanvas() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    drawChart();
}
window.addEventListener('resize', resizeCanvas);

function drawChart() {
    const rect = canvas.parentElement.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    ctx.clearRect(0, 0, width, height);

    ctx.strokeStyle = '#f3f4f6';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i <= 4; i++) {
        const y = (height / 4) * i;
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
    }
    ctx.stroke();

    const stepX = width / (MAX_POINTS - 1);
    const getY = (val) => height - (val / 100) * height;

    ctx.beginPath();
    dataPoints.forEach((p, i) => {
        const x = i * stepX;
        const y = getY(Math.min(100, p.val + p.ci));
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    for (let i = MAX_POINTS - 1; i >= 0; i--) {
        const p = dataPoints[i];
        ctx.lineTo(i * stepX, getY(Math.max(0, p.val - p.ci)));
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(99, 102, 241, 0.15)';
    ctx.fill();

    ctx.beginPath();
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2.5;
    dataPoints.forEach((p, i) => {
        const x = i * stepX;
        const y = getY(p.val);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
}

async function fetchChartData() {
    try {
        const data = await SentinelUI.fetchDashboardData();
        dataPoints.shift();
        dataPoints.push({
            val: Number(data.risk_score) || 0,
            ci: 3,
        });
        drawChart();
        SentinelUI.updateMonitoringStatusBadge(
            data.monitoring_mode,
            data.is_fallback_active,
            data.user_api_token
        );
    } catch (error) {
        console.error('Error fetching chart data:', error);
    }
}

resizeCanvas();
setInterval(fetchChartData, 2000);
fetchChartData();
