// =========================================================================
// DevinX Ultimate — Chat UI Client
// =========================================================================

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const taskListEl = document.getElementById("task-list");
const assumptionsListEl = document.getElementById("assumptions-list");
const statusDot = document.querySelector(".status-dot");
const statusText = document.querySelector(".status-text");
const approvalModal = document.getElementById("approval-modal");
const approvalCommand = document.getElementById("approval-command");
const criticalModal = document.getElementById("critical-modal");
const criticalCommand = document.getElementById("critical-command");
const criticalInput = document.getElementById("critical-input");
const reportModal = document.getElementById("report-modal");
const reportTitle = document.getElementById("report-title");
const reportFrame = document.getElementById("report-frame");

let ws = null;
let currentAssistantBubble = null;
let isStreaming = false;

// ---- WebSocket Connection ----
function connect() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${protocol}//${location.host}/ws`);

    ws.onopen = () => {
        setStatus("connected", "Connected");
    };

    ws.onclose = () => {
        setStatus("disconnected", "Disconnected");
        isStreaming = false;
        currentAssistantBubble = null;
        sendBtn.disabled = false;
        setTimeout(connect, 3000);
    };

    ws.onerror = () => {
        setStatus("disconnected", "Error");
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
    };
}

function setStatus(state, text) {
    statusDot.className = `status-dot ${state}`;
    statusText.textContent = text;
}

// ---- Message Handling ----
function handleMessage(msg) {
    switch (msg.type) {
        case "assistant_chunk":
            handleChunk(msg.data.content);
            break;

        case "assistant_done":
            finishAssistant();
            break;

        case "tool_call":
            addToolCall(msg.data);
            break;

        case "tool_result":
            addToolResult(msg.data);
            break;

        case "task_update":
            updateTasks(msg.data.tasks);
            break;

        case "assumptions_update":
            updateAssumptions(msg.data.assumptions);
            break;

        case "approval_request":
            showApproval(msg.data.command);
            break;

        case "critical_request":
            showCritical(msg.data.command);
            break;

        case "report":
            showReport(msg.data);
            break;

        case "error":
            addError(msg.data.message);
            break;
    }
}

function handleChunk(content) {
    if (!currentAssistantBubble) {
        removeTypingIndicator();
        const messageEl = createMessageEl("assistant");
        currentAssistantBubble = messageEl.querySelector(".message-bubble");
        currentAssistantBubble._rawContent = "";
    }
    currentAssistantBubble._rawContent += content;
    currentAssistantBubble.innerHTML = renderMarkdown(currentAssistantBubble._rawContent);
    scrollToBottom();
}

function finishAssistant() {
    if (currentAssistantBubble) {
        currentAssistantBubble.innerHTML = renderMarkdown(currentAssistantBubble._rawContent || "");
    }
    currentAssistantBubble = null;
    isStreaming = false;
    setStatus("connected", "Connected");
    sendBtn.disabled = false;
}

function addToolCall(data) {
    currentAssistantBubble = null;

    const el = document.createElement("div");
    el.className = "tool-call";

    const safetyBadge = data.arguments && data.arguments.safety_level
        ? ` <span class="safety-badge safety-${data.arguments.safety_level}">${data.arguments.safety_level}</span>`
        : "";

    el.innerHTML = `
        <div class="tool-label">🔧 Tool Call: ${escapeHtml(data.name)}${safetyBadge}</div>
        <div class="tool-body">${escapeHtml(JSON.stringify(data.arguments, null, 2))}</div>
    `;
    messagesEl.appendChild(el);
    scrollToBottom();
}

function addToolResult(data) {
    const el = document.createElement("div");
    el.className = `tool-result ${data.success ? "" : "error"}`;

    const icon = data.success ? "✓" : "✗";
    const output = data.output.length > 500
        ? data.output.substring(0, 500) + "... (truncated)"
        : data.output;

    el.innerHTML = `
        <div class="tool-label">${icon} Result: ${escapeHtml(data.tool_name)}</div>
        <div class="tool-body">${escapeHtml(output)}</div>
    `;
    messagesEl.appendChild(el);
    scrollToBottom();
}

function addError(message) {
    const el = document.createElement("div");
    el.className = "tool-result error";
    el.innerHTML = `
        <div class="tool-label">Error</div>
        <div class="tool-body">${escapeHtml(message)}</div>
    `;
    messagesEl.appendChild(el);
    finishAssistant();
    scrollToBottom();
}

// ---- Tasks ----
function updateTasks(tasks) {
    if (!tasks || tasks.length === 0) {
        taskListEl.innerHTML = '<p class="empty-state">No tasks yet. Start a conversation!</p>';
        return;
    }

    taskListEl.innerHTML = tasks.map((t) => `
        <div class="task-item ${t.status}">
            <span class="task-status-icon"></span>
            <div class="task-content">
                <div class="task-title">${escapeHtml(t.title)}</div>
                ${t.details ? `<div class="task-details">${escapeHtml(t.details)}</div>` : ""}
            </div>
        </div>
    `).join("");
}

// ---- Assumptions ----
function updateAssumptions(assumptions) {
    if (!assumptions || assumptions.length === 0) {
        assumptionsListEl.innerHTML = '<p class="empty-state">No assumptions logged.</p>';
        return;
    }

    assumptionsListEl.innerHTML = assumptions.map((a, i) => `
        <div class="assumption-item">
            <span class="assumption-number">${i + 1}.</span>
            <div class="assumption-content">
                <div class="assumption-text">${escapeHtml(a.assumption)}</div>
                ${a.context ? `<div class="assumption-context">${escapeHtml(a.context)}</div>` : ""}
            </div>
        </div>
    `).join("");
}

// ---- Approval (requires_approval) ----
function showApproval(command) {
    approvalCommand.textContent = command;
    approvalModal.classList.remove("hidden");
}

function respondApproval(approved) {
    approvalModal.classList.add("hidden");
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: "approval_response",
            approved: approved,
        }));
    }
}

// ---- Critical Approval ----
function showCritical(command) {
    criticalCommand.textContent = command;
    criticalInput.value = "";
    criticalModal.classList.remove("hidden");
    criticalInput.focus();
}

function respondCritical(confirmed) {
    if (confirmed) {
        const inputVal = criticalInput.value.trim().toUpperCase();
        if (inputVal !== "CONFIRM CRITICAL") {
            criticalInput.classList.add("shake");
            setTimeout(() => criticalInput.classList.remove("shake"), 500);
            return;
        }
    }
    criticalModal.classList.add("hidden");
    criticalInput.value = "";
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: "critical_response",
            confirmed: confirmed,
        }));
    }
}

// Critical modal: Enter key to confirm
criticalInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        respondCritical(true);
    }
});

// ---- Report Modal ----
function showReport(data) {
    reportTitle.textContent = data.title || "Report";
    const blob = new Blob([data.html], { type: "text/html" });
    reportFrame.src = URL.createObjectURL(blob);
    reportModal.classList.remove("hidden");
}

function closeReport() {
    reportModal.classList.add("hidden");
    reportFrame.src = "";
}

// ---- Send Message ----
function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isStreaming) return;

    const welcome = messagesEl.querySelector(".welcome-message");
    if (welcome) welcome.remove();

    const messageEl = createMessageEl("user");
    messageEl.querySelector(".message-bubble").innerHTML = renderMarkdown(text);

    inputEl.value = "";
    inputEl.style.height = "auto";

    addTypingIndicator();
    isStreaming = true;
    setStatus("thinking", "Thinking...");
    sendBtn.disabled = true;

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ message: text }));
    }

    scrollToBottom();
}

// ---- Helpers ----
function createMessageEl(role) {
    const el = document.createElement("div");
    el.className = `message ${role}`;
    el.innerHTML = `<div class="message-bubble"></div>`;
    messagesEl.appendChild(el);
    return el;
}

function addTypingIndicator() {
    removeTypingIndicator();
    const el = document.createElement("div");
    el.className = "typing-indicator";
    el.id = "typing";
    el.innerHTML = "<span></span><span></span><span></span>";
    messagesEl.appendChild(el);
    scrollToBottom();
}

function removeTypingIndicator() {
    const el = document.getElementById("typing");
    if (el) el.remove();
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function renderMarkdown(text) {
    let html = escapeHtml(text);

    // Code blocks
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
        return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

    // Italic
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

    // Line breaks
    html = html.replace(/\n/g, "<br>");

    return html;
}

// ---- Input Handling ----
inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

inputEl.addEventListener("input", () => {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 150) + "px";
});

// ---- Initialize ----
connect();
