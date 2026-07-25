const slider = document.getElementById('confidenceSlider');
const sliderValue = document.getElementById('thresholdValue');
const btnSave = document.getElementById('btnSave');
const btnCancel = document.getElementById('btnCancel');
const toast = document.getElementById('toastBox');
const tokenInput = document.getElementById('apiToken');
const monitoringModeSelect = document.getElementById('monitoringMode');
const downloadBtn = document.getElementById('downloadAgentBtn');

let currentSettings = {};

function syncModeFromToken() {
    if (!tokenInput || !monitoringModeSelect) return;
    const hasToken = Boolean(tokenInput.value.trim());
    monitoringModeSelect.value = hasToken ? 'api_agent' : 'scapy';
    updateDownloadButton(tokenInput.value.trim());
}

function updateDownloadButton(token) {
    if (!downloadBtn) return;
    if (token) {
        downloadBtn.href = `/api/download-agent?token=${encodeURIComponent(token)}`;
        downloadBtn.style.display = 'inline-flex';
        downloadBtn.removeAttribute('aria-disabled');
    } else {
        downloadBtn.href = '#';
        downloadBtn.style.display = 'none';
    }
}

function collectPayload() {
    return {
        orgName: document.getElementById('orgName')?.value || 'My Network',
        adminEmail: document.getElementById('adminEmail')?.value || 'admin@network.local',
        timezone: document.getElementById('timezone')?.value || 'UTC',
        pushNotifications: Boolean(document.getElementById('pushToggle')?.checked),
        emailAlerts: Boolean(document.getElementById('emailToggle')?.checked),
        autoBlock: Boolean(document.getElementById('autoBlockToggle')?.checked),
        activeModel: document.getElementById('activeModel')?.value || 'lstm',
        confidence: parseInt(slider?.value || '85', 10),
        token: tokenInput?.value.trim() || '',
        monitoringMode: monitoringModeSelect?.value || 'scapy',
    };
}

function applySettingsToForm(data) {
    const orgNameInput = document.getElementById('orgName');
    const adminEmailInput = document.getElementById('adminEmail');
    const timezoneInput = document.getElementById('timezone');
    const activeModelSelect = document.getElementById('activeModel');
    const pushToggle = document.getElementById('pushToggle');
    const emailToggle = document.getElementById('emailToggle');
    const autoBlockToggle = document.getElementById('autoBlockToggle');

    if (orgNameInput) orgNameInput.value = data.orgName || 'My Network';
    if (adminEmailInput) adminEmailInput.value = data.adminEmail || 'admin@network.local';
    if (timezoneInput) timezoneInput.value = data.timezone || 'UTC';
    if (activeModelSelect) activeModelSelect.value = data.activeModel || 'lstm';
    if (slider) slider.value = data.confidence || 85;
    if (sliderValue) sliderValue.innerText = `${data.confidence || 85}%`;
    if (tokenInput) tokenInput.value = data.token || '';
    if (monitoringModeSelect) monitoringModeSelect.value = data.token ? 'api_agent' : 'scapy';
    if (pushToggle) pushToggle.checked = data.pushNotifications !== false;
    if (emailToggle) emailToggle.checked = data.emailAlerts !== false;
    if (autoBlockToggle) autoBlockToggle.checked = Boolean(data.autoBlock);
    updateDownloadButton(data.token || '');
}

function showToast(ok = true) {
    if (!toast) return;
    toast.querySelector('span').textContent = ok
        ? 'Settings successfully updated.'
        : 'Failed to update settings.';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

if (slider && sliderValue) {
    slider.addEventListener('input', function () {
        sliderValue.innerText = `${this.value}%`;
        if (this.value < 70) {
            sliderValue.style.color = 'var(--warning-color)';
            if (this.value < 60) sliderValue.style.color = 'var(--danger-color)';
        } else {
            sliderValue.style.color = 'var(--brand-color)';
        }
    });
}

if (tokenInput) {
    tokenInput.addEventListener('input', syncModeFromToken);
}

if (monitoringModeSelect) {
    monitoringModeSelect.addEventListener('change', function () {
        if (this.value === 'api_agent' && tokenInput && !tokenInput.value.trim()) {
            tokenInput.focus();
        }
        if (this.value === 'scapy' && tokenInput) {
            tokenInput.value = '';
            updateDownloadButton('');
        }
    });
}

if (btnSave) {
    btnSave.addEventListener('click', async function () {
        syncModeFromToken();
        const payload = collectPayload();
        try {
            const response = await fetch('/api/update-settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const result = await response.json();
            payload.monitoringMode = result.monitoringMode || payload.monitoringMode;
            currentSettings = payload;
            applySettingsToForm(payload);
            showToast(true);
        } catch (error) {
            console.error('Failed to save settings:', error);
            showToast(false);
        }
    });
}

if (btnCancel) {
    btnCancel.addEventListener('click', function () {
        applySettingsToForm(currentSettings);
    });
}

async function loadSettings() {
    try {
        const response = await fetch('/api/get-settings');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        applySettingsToForm(data);
        currentSettings = collectPayload();
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

document.addEventListener('DOMContentLoaded', loadSettings);
