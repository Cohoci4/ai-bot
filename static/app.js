// =========================================================================
// DevinX — Chat UI Client
// =========================================================================

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const taskListEl = document.getElementById("task-list");
const statusDot = document.querySelector(".status-dot");
const statusText = document.querySelector(".status-text");
const approvalModal = document.getElementById("approval-modal");
const approvalCommand = document.getElementById("approval-command");

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

        case "approval_request":
            showApproval(msg.data.command);
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
    el.innerHTML = `
        <div class="tool-label">🔧 Tool Call: ${escapeHtml(data.name)}</div>
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
        <div class="tool-label">❌ Error</div>
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

// ---- Approval ----
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

// ---- Send Message ----
function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isStreaming) return;

    // Remove welcome message
    const welcome = messagesEl.querySelector(".welcome-message");
    if (welcome) welcome.remove();

    // Add user message
    const messageEl = createMessageEl("user");
    messageEl.querySelector(".message-bubble").innerHTML = renderMarkdown(text);

    // Clear input
    inputEl.value = "";
    inputEl.style.height = "auto";

    // Show typing
    addTypingIndicator();
    isStreaming = true;
    setStatus("thinking", "Thinking...");
    sendBtn.disabled = true;

    // Send via WS
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
    // Simple markdown rendering
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
