const chatContainer = document.getElementById('chatContainer');
const chatLayout = document.getElementById('chatLayout');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

userInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    sendBtn.disabled = this.value.trim() === '';
});

// Enter to send
userInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    appendUserMessage(text);

    userInput.value = '';
    userInput.style.height = 'auto';
    sendBtn.disabled = true;

    const typingId = showTypingIndicator();

    setTimeout(() => {
        document.getElementById(typingId).remove();

        const aiResponse = `Based on the active model evaluation, here is the requested breakdown:

The current predictive engine has flagged IP \`192.168.1.105\` with an **87% confidence** of being part of a coordinated scan.

**SHAP Feature Contributions:**
<ul>
    <li><code>SYN_Packet_Count</code>: +0.24 (High anomaly detected)</li>
    <li><code>Flow_Duration</code>: -0.12 (Suppresses risk slightly)</li>
    <li><code>Dest_Port_Diversity</code>: +0.31 (Primary risk driver)</li>
</ul>

If you wish to mitigate this early, you can apply the following firewall rule:
<pre><code>iptables -A INPUT -s 192.168.1.105 -j DROP
logger "Automated mitigation applied by Sentinel"</code></pre>

Would you like to review the historical traffic for this specific IP?
Based on the active model evaluation, here is the requested breakdown:

The current predictive engine has flagged IP \`192.168.1.105\` with an **87% confidence** of being part of a coordinated scan.

**SHAP Feature Contributions:**
<ul>
    <li><code>SYN_Packet_Count</code>: +0.24 (High anomaly detected)</li>
    <li><code>Flow_Duration</code>: -0.12 (Suppresses risk slightly)</li>
    <li><code>Dest_Port_Diversity</code>: +0.31 (Primary risk driver)</li>
</ul>

If you wish to mitigate this early, you can apply the following firewall rule:
<pre><code>iptables -A INPUT -s 192.168.1.105 -j DROP
logger "Automated mitigation applied by Sentinel"</code></pre>

Would you like to review the historical traffic for this specific IP?

`;

        appendAIMessage(aiResponse);
    }, 1200);
}

function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'msg-row user';
    row.innerHTML = `<div class="bubble">${escapeHTML(text)}</div>`;
    chatLayout.appendChild(row);
    scrollToBottom();
}

function appendAIMessage(htmlContent) {
    const row = document.createElement('div');
    row.className = 'msg-row ai';
    row.innerHTML = `
                <div class="avatar ai">
               <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-globe-check-icon lucide-globe-check"><path d="m15 6 2 2 4-4"/><path d="M2 12h20A10 10 0 1 1 12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 4-10"/></svg>   
                </div>
                <div class="bubble">${htmlContent}</div>
            `;
    chatLayout.appendChild(row);
    scrollToBottom();
}

function showTypingIndicator() {
    const id = 'typing-' + Date.now();
    const row = document.createElement('div');
    row.className = 'msg-row ai';
    row.id = id;
    row.innerHTML = `
                <div class="avatar ai">
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-text-scan-ai"><path stroke="none" d="M0 0h24v24H0z" fill="none" /><path d="M8 12h4.5" /><path d="M8 8h6" /><path d="M8 16h2" /><path d="M3 7v-2a2 2 0 0 1 2 -2h2" /><path d="M3 17v2a2 2 0 0 0 2 2h2" /><path d="M17 3h2a2 2 0 0 1 2 2v2" /><path d="M14 21v-4a2 2 0 1 1 4 0v4" /><path d="M14 19h4" /><path d="M21 15v6" /></svg>                </div>           
                 <div class="bubble">
                    <div class="typing"><span></span><span></span><span></span></div>
                </div>
            `;
    chatLayout.appendChild(row);
    scrollToBottom();
    return id;
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, tag => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag]));
}

sendBtn.disabled = true;