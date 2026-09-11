"use strict";

const views = {
  landing: document.getElementById("view-landing"),
  host: document.getElementById("view-host"),
  join: document.getElementById("view-join"),
  settings: document.getElementById("view-settings"),
};

function showView(name) {
  for (const [key, el] of Object.entries(views)) {
    el.hidden = key !== name;
  }
}

document.querySelectorAll("[data-nav]").forEach((el) => {
  el.addEventListener("click", () => showView(el.dataset.nav));
});

function wsUrl(path) {
  const scheme = location.protocol === "https:" ? "wss:" : "ws:";
  return `${scheme}//${location.host}${path}`;
}

function appendLogLine(container, { kind, text, sender }, selfNickname) {
  const wasAtBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 8;
  container.querySelector(".log-empty")?.remove();

  const line = document.createElement("div");
  line.className = `log-line log-line--${kind}`;
  if (sender) {
    line.classList.add("log-line--chat");
    if (sender === selfNickname) line.classList.add("log-line--self");
    const senderEl = document.createElement("span");
    senderEl.className = "sender";
    senderEl.textContent = `${sender}: `;
    line.appendChild(senderEl);
    line.appendChild(document.createTextNode(text));
  } else {
    line.textContent = kind === "system" ? `• ${text}` : text;
  }
  container.appendChild(line);
  if (wasAtBottom) container.scrollTop = container.scrollHeight;
}

function setEmpty(container, message) {
  container.innerHTML = "";
  const p = document.createElement("div");
  p.className = "log-empty";
  p.textContent = message;
  container.appendChild(p);
}

/* ---------------- Host ---------------- */

const hostForm = document.getElementById("host-form");
const hostError = document.getElementById("host-error");
const hostActive = document.getElementById("host-active");
const hostAddress = document.getElementById("host-address");
const hostLog = document.getElementById("host-log");
const hostUsers = document.getElementById("host-users");
const hostCount = document.getElementById("host-count");
let hostSocket = null;

function renderHostUsers(names) {
  hostUsers.innerHTML = "";
  hostCount.textContent = names.length;
  for (const name of names) {
    const li = document.createElement("li");
    li.textContent = name;
    hostUsers.appendChild(li);
  }
}

function connectHostFeed() {
  setEmpty(hostLog, "No activity yet.");
  hostSocket = new WebSocket(wsUrl("/ws/host"));
  hostSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    appendLogLine(hostLog, data);
    if (/joined the chat|left the chat/.test(data.text)) refreshHostStatus();
  };
}

async function refreshHostStatus() {
  const res = await fetch("/api/host/status");
  const data = await res.json();
  if (data.hosting) renderHostUsers(data.connected);
}

async function enterHostedState(data) {
  hostForm.hidden = true;
  hostActive.hidden = false;
  hostAddress.textContent = `${data.host}:${data.port}`;
  renderHostUsers(data.connected || []);
  if (!hostSocket) connectHostFeed();
}

hostForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hostError.hidden = true;
  const fd = new FormData(hostForm);
  const port = fd.get("port");
  const body = {
    host: fd.get("host") || "0.0.0.0",
    port: port ? Number(port) : null,
    password: fd.get("password") || null,
    max_clients: Number(fd.get("max_clients") || 200),
  };
  const submitBtn = hostForm.querySelector("button[type=submit]");
  submitBtn.disabled = true;
  try {
    const res = await fetch("/api/host/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Could not start hosting.");
    await enterHostedState(data);
  } catch (err) {
    hostError.textContent = err.message;
    hostError.hidden = false;
  } finally {
    submitBtn.disabled = false;
  }
});

document.getElementById("host-stop").addEventListener("click", async () => {
  await fetch("/api/host/stop", { method: "POST" });
  hostSocket?.close();
  hostSocket = null;
  hostActive.hidden = true;
  hostForm.hidden = false;
});

document.getElementById("host-copy").addEventListener("click", () => {
  navigator.clipboard?.writeText(hostAddress.textContent);
});

/* ---------------- Join ---------------- */

const joinForm = document.getElementById("join-form");
const joinError = document.getElementById("join-error");
const joinActive = document.getElementById("join-active");
const joinLog = document.getElementById("join-log");
const joinStatusText = document.getElementById("join-status-text");
const joinStatusDot = document.getElementById("join-status-dot");
const sendForm = document.getElementById("send-form");
const sendInput = document.getElementById("send-input");
let joinSocket = null;
let myNickname = null;

function resetJoinView() {
  joinSocket = null;
  myNickname = null;
  joinActive.hidden = true;
  joinForm.hidden = false;
  joinStatusDot.classList.remove("status-dot--live");
}

joinForm.addEventListener("submit", (event) => {
  event.preventDefault();
  joinError.hidden = true;
  const fd = new FormData(joinForm);
  const submitBtn = joinForm.querySelector("button[type=submit]");
  submitBtn.disabled = true;

  const socket = new WebSocket(wsUrl("/ws/join"));
  joinSocket = socket;

  socket.onopen = () => {
    socket.send(
      JSON.stringify({
        host: fd.get("host"),
        port: Number(fd.get("port")),
        nickname: fd.get("nickname"),
        password: fd.get("password") || null,
        use_ssl: fd.get("use_ssl") === "on",
      })
    );
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.kind === "connected") {
      myNickname = data.text;
      joinForm.hidden = true;
      joinActive.hidden = false;
      joinStatusDot.classList.add("status-dot--live");
      joinStatusText.textContent = `Connected as ${myNickname}`;
      setEmpty(joinLog, "No messages yet — say hello.");
      sendInput.focus();
      return;
    }
    if (data.kind === "error" && !myNickname) {
      joinError.textContent = data.text;
      joinError.hidden = false;
      submitBtn.disabled = false;
      return;
    }
    appendLogLine(joinLog, data, myNickname);
  };

  socket.onclose = () => {
    submitBtn.disabled = false;
    if (myNickname) {
      joinStatusDot.classList.remove("status-dot--live");
      joinStatusText.textContent = "Disconnected";
    }
  };
});

sendForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = sendInput.value.trim();
  if (!text || !joinSocket || joinSocket.readyState !== WebSocket.OPEN) return;
  joinSocket.send(JSON.stringify({ type: "send", text }));
  appendLogLine(joinLog, { kind: "chat", text, sender: myNickname }, myNickname);
  sendInput.value = "";
});

document.getElementById("join-list").addEventListener("click", () => {
  joinSocket?.send(JSON.stringify({ type: "list" }));
});

document.getElementById("join-disconnect").addEventListener("click", () => {
  joinSocket?.close();
  resetJoinView();
});

/* ---------------- Settings ---------------- */

const settingsForm = document.getElementById("settings-form");
const settingsError = document.getElementById("settings-error");
const settingsSaved = document.getElementById("settings-saved");
let currentSettings = null;

function applySettingsToForm(data) {
  settingsForm.nickname.value = data.nickname;
  settingsForm.default_interface.value = data.default_interface;
  settingsForm.default_host.value = data.default_host;
  settingsForm.default_port.value = data.default_port ?? "";
  settingsForm.web_open_browser.checked = data.web_open_browser;
  settingsForm.log_level.checked = data.log_level === "debug";
}

function applySettingsToJoinForm(data) {
  const nicknameField = document.getElementById("join-nickname");
  if (nicknameField.dataset.autofilled !== "false") {
    nicknameField.value = data.nickname;
    nicknameField.dataset.autofilled = "true";
  }
  if (data.default_host) document.getElementById("join-host").value = data.default_host;
  if (data.default_port) document.getElementById("join-port").value = data.default_port;
}

// Once the user edits the nickname themselves, stop overwriting it when
// settings are saved elsewhere (e.g. from the Settings page).
document.getElementById("join-nickname").addEventListener("input", (event) => {
  event.target.dataset.autofilled = "false";
});

async function loadSettings() {
  const res = await fetch("/api/settings");
  currentSettings = await res.json();
  applySettingsToForm(currentSettings);
  applySettingsToJoinForm(currentSettings);
}

settingsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  settingsError.hidden = true;
  settingsSaved.hidden = true;
  const fd = new FormData(settingsForm);
  const port = fd.get("default_port");
  const body = {
    nickname: fd.get("nickname"),
    default_interface: fd.get("default_interface"),
    default_host: fd.get("default_host"),
    default_port: port ? Number(port) : null,
    web_open_browser: fd.get("web_open_browser") === "on",
    log_level: fd.get("log_level") === "on" ? "debug" : "normal",
  };
  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Could not save settings.");
    currentSettings = data;
    applySettingsToJoinForm(data);
    settingsSaved.hidden = false;
  } catch (err) {
    settingsError.textContent = err.message;
    settingsError.hidden = false;
  }
});

/* ---------------- Startup ---------------- */

(async function init() {
  await loadSettings();
  const res = await fetch("/api/status");
  const data = await res.json();
  if (data.hosting) {
    showView("host");
    await enterHostedState(data);
  }
})();
