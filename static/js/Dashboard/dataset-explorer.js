let fullDataset = [];
let filteredDataset = [];
let currentPage = 1;
const rowsPerPage = 12;

const sidePanel = document.getElementById('sidePanel');
const backdrop = document.getElementById('backdrop');
const btnClosePanel = document.getElementById('btnClosePanel');
const panelTitle = document.getElementById('panelTitle');
const jsonOutput = document.getElementById('jsonOutput');
const toastContainer = document.getElementById('toastContainer');

function isAttackRow(row) {
    return Boolean(row.is_attack ?? row.isAttack);
}

async function loadRealDataset() {
    try {
        const response = await fetch('/api/dataset-explorer-data');
        if (!response.ok) throw new Error('Failed to fetch data');
        fullDataset = await response.json();
        filteredDataset = [...fullDataset];
        updateStats(filteredDataset);
        renderTable();
        showToast('Dataset loaded successfully', 'success');
    } catch (error) {
        console.error('Error loading dataset:', error);
        showToast('Failed to load real-time data.', 'error');
    }
}

function showToast(message, type = 'success') {
    if (!toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function renderTable() {
    const tbody = document.getElementById('tableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const start = (currentPage - 1) * rowsPerPage;
    const paginatedItems = filteredDataset.slice(start, start + rowsPerPage);

    paginatedItems.forEach((row) => {
        const tr = document.createElement('tr');
        tr.onclick = () => openRowDetails(row.id);
        const attack = isAttackRow(row);
        tr.innerHTML = `
            <td class="mono">${row.id}</td>
            <td class="mono">${row.time}</td>
            <td class="mono">${row.src}</td>
            <td class="mono">${row.dest}</td>
            <td>${row.proto}</td>
            <td class="mono">${row.duration}</td>
            <td class="mono">${row.packets}</td>
            <td><span class="badge ${attack ? 'attack' : 'normal'}">${row.label}</span></td>
        `;
        tbody.appendChild(tr);
    });
    updatePagination();
}

function updatePagination() {
    const totalPages = Math.max(1, Math.ceil(filteredDataset.length / rowsPerPage));
    const pageInfo = document.getElementById('pageInfo');
    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');
    if (pageInfo) pageInfo.innerText = `Page ${currentPage} of ${totalPages}`;
    if (btnPrev) btnPrev.disabled = currentPage <= 1;
    if (btnNext) btnNext.disabled = currentPage >= totalPages;
}

function applyFilters() {
    const searchTerm = (document.getElementById('searchInput')?.value || '').toLowerCase();
    const protoFilter = document.getElementById('filterProtocol')?.value || 'All';
    const labelFilter = document.getElementById('filterLabel')?.value || 'All';

    filteredDataset = fullDataset.filter((row) => {
        const matchesSearch =
            String(row.src || '').toLowerCase().includes(searchTerm) ||
            String(row.dest || '').toLowerCase().includes(searchTerm);
        const matchesProto = protoFilter === 'All' || row.proto === protoFilter;
        const attack = isAttackRow(row);
        const matchesLabel =
            labelFilter === 'All' ||
            (labelFilter === 'Normal' ? !attack : attack);
        return matchesSearch && matchesProto && matchesLabel;
    });

    currentPage = 1;
    updateStats(filteredDataset);
    renderTable();
}

function updateStats(data) {
    const total = data.length;
    const attacks = data.filter(isAttackRow).length;
    const statTotal = document.getElementById('statTotal');
    const statAttack = document.getElementById('statAttack');
    const statNormal = document.getElementById('statNormal');
    if (statTotal) statTotal.innerText = total.toLocaleString();
    if (statAttack) statAttack.innerText = attacks.toLocaleString();
    if (statNormal) statNormal.innerText = (total - attacks).toLocaleString();
}

function openRowDetails(flowId) {
    const flowData = fullDataset.find((f) => f.id === flowId);
    if (!flowData) return;
    if (panelTitle) panelTitle.innerText = `Flow Details: ${flowData.id}`;
    if (jsonOutput) jsonOutput.innerHTML = syntaxHighlight(JSON.stringify(flowData, null, 4));
    sidePanel?.classList.add('active');
    backdrop?.classList.add('active');
}

function closePanel() {
    sidePanel?.classList.remove('active');
    backdrop?.classList.remove('active');
}

function syntaxHighlight(json) {
    return json.replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function (match) {
            let cls = 'json-number';
            if (/^"/.test(match)) cls = /:$/.test(match) ? 'json-key' : 'json-string';
            else if (/true|false/.test(match)) cls = 'json-boolean';
            return `<span class="${cls}">${match}</span>`;
        }
    );
}

document.getElementById('searchInput')?.addEventListener('input', applyFilters);
document.getElementById('filterProtocol')?.addEventListener('change', applyFilters);
document.getElementById('filterLabel')?.addEventListener('change', applyFilters);
document.getElementById('btnPrev')?.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage -= 1;
        renderTable();
    }
});
document.getElementById('btnNext')?.addEventListener('click', () => {
    const totalPages = Math.max(1, Math.ceil(filteredDataset.length / rowsPerPage));
    if (currentPage < totalPages) {
        currentPage += 1;
        renderTable();
    }
});
btnClosePanel?.addEventListener('click', closePanel);
backdrop?.addEventListener('click', closePanel);

loadRealDataset();
setInterval(loadRealDataset, 10000);
