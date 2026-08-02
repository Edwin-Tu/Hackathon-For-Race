"use strict";

const $ = (id) => document.getElementById(id);
const MAX_AUDIO_BYTES = 15 * 1024 * 1024;
const SESSION_STORAGE_KEY = "careAgentSessionId";

const state = {
  mode: "voice",
  mediaRecorder: null,
  mediaStream: null,
  audioChunks: [],
  audioFile: null,
  previewUrl: null,
  pendingConfirmation: null,
  toastTimer: null,
  apiAuthRequired: false,
  lastOutputEventId: 0,
  outputPollTimer: null,
};

const elements = {
  sessionId: $("sessionId"),
  apiToken: $("apiToken"),
  browserSpeechEnabled: $("browserSpeechEnabled"),
  apiStatus: $("apiStatus"),
  modelLabel: $("modelLabel"),
  envLabel: $("envLabel"),
  requestState: $("requestState"),
  startRecordBtn: $("startRecordBtn"),
  stopRecordBtn: $("stopRecordBtn"),
  recordOrb: $("recordOrb"),
  recordingHint: $("recordingHint"),
  audioPreview: $("audioPreview"),
  audioFile: $("audioFile"),
  dropZone: $("dropZone"),
  fileMeta: $("fileMeta"),
  voiceLanguage: $("voiceLanguage"),
  transcribeBtn: $("transcribeBtn"),
  voiceTurnBtn: $("voiceTurnBtn"),
  textMessage: $("textMessage"),
  guardMessage: $("guardMessage"),
  confirmationBox: $("confirmationBox"),
  confirmationSummary: $("confirmationSummary"),
  confirmActionBtn: $("confirmActionBtn"),
  cancelActionBtn: $("cancelActionBtn"),
  rawJson: $("rawJson"),
  toast: $("toast"),
};

function makeSessionId() {
  if (globalThis.crypto?.randomUUID) {
    return `ui-${globalThis.crypto.randomUUID()}`;
  }
  return `ui-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function setRequestState(label, kind = "idle") {
  elements.requestState.textContent = label;
  elements.requestState.className = `request-state ${kind}`;
}

function showToast(message, kind = "success") {
  clearTimeout(state.toastTimer);
  elements.toast.textContent = message;
  elements.toast.className = `toast ${kind}`;
  elements.toast.hidden = false;
  state.toastTimer = setTimeout(() => {
    elements.toast.hidden = true;
  }, 3600);
}

function formatBytes(value) {
  if (!Number.isFinite(value)) return "—";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatNumber(value, digits = 2) {
  return Number.isFinite(value) ? Number(value).toFixed(digits) : "—";
}

function setMetric(id, value, detail, kind = "muted") {
  const valueEl = $(id);
  const detailEl = $(`${id.replace("Status", "Detail").replace("Action", "Detail")}`);
  valueEl.textContent = value;
  valueEl.className = `metric-value ${kind}`;
  if (detailEl) detailEl.textContent = detail;
}

function setBadge(element, text, kind = "neutral") {
  element.textContent = text;
  element.className = `badge ${kind}`;
}

function resetConfirmation() {
  state.pendingConfirmation = null;
  elements.confirmationBox.hidden = true;
  elements.confirmationSummary.textContent = "此操作需要再次確認。";
}

function setPendingConfirmation(agent, originalMessage) {
  if (!agent?.requires_confirmation || !agent.confirmation_token) {
    resetConfirmation();
    return;
  }
  state.pendingConfirmation = {
    token: agent.confirmation_token,
    message: originalMessage || "確認執行待處理操作",
    sessionId: agent.session_id || elements.sessionId.value,
  };
  elements.confirmationSummary.textContent = agent.confirmation_summary || "此操作需要再次確認。";
  elements.confirmationBox.hidden = false;
}

function clearChildren(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function renderTools(toolEvents = []) {
  const tbody = $("toolTableBody");
  clearChildren(tbody);
  $("toolCountBadge").textContent = `${toolEvents.length} tools`;

  if (!toolEvents.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 5;
    td.className = "empty-cell";
    td.textContent = "尚無工具執行紀錄";
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  for (const event of toolEvents) {
    const tr = document.createElement("tr");
    const values = [
      event.tool_name || "—",
      event.status || "—",
      event.record_id || "—",
      event.error_code || "—",
      event.idempotency_replayed ? "是" : "否",
    ];
    for (const value of values) {
      const td = document.createElement("td");
      td.textContent = String(value);
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
}

function renderGuard(guard) {
  if (!guard) {
    setMetric("guardAction", "—", "尚無結果", "muted");
    return;
  }
  const allowed = Boolean(guard.allowed);
  const action = guard.action || (allowed ? "ALLOW" : "BLOCK");
  const score = guard.overall_risk_score ?? 0;
  const category = guard.primary_category || "none";
  setMetric(
    "guardAction",
    action,
    `${guard.overall_risk_level || "unknown"} · score ${score} · ${category}`,
    allowed ? "good" : "bad",
  );
}

function renderTranscription(transcript, trace) {
  const text = transcript || "尚未取得逐字稿";
  $("transcriptText").textContent = text;
  $("transcriptText").className = `large-copy${transcript ? "" : " placeholder"}`;
  const language = trace?.language || "—";
  setBadge($("transcriptLanguage"), language, transcript ? "good" : "neutral");
  $("whisperModel").textContent = trace?.model || "—";
  $("languageProbability").textContent = Number.isFinite(trace?.language_probability)
    ? `${(trace.language_probability * 100).toFixed(1)}%`
    : "—";
  $("audioDuration").textContent = Number.isFinite(trace?.duration_seconds)
    ? `${formatNumber(trace.duration_seconds, 2)} 秒`
    : "—";
}

function renderAgent(agent) {
  if (!agent) {
    setMetric("agentStatus", "—", "尚無結果", "muted");
    setMetric("toolStatus", "—", "尚無結果", "muted");
    setMetric("speechStatus", "—", "尚無結果", "muted");
    $("agentReply").textContent = "尚未取得 Agent 回覆";
    $("agentReply").className = "large-copy placeholder";
    renderTools([]);
    return;
  }

  const actionStatus = agent.action_status || "no_action";
  const operationCompleted = Boolean(agent.operation_completed);
  const denied = actionStatus === "denied" || agent.success === false;
  setMetric(
    "agentStatus",
    actionStatus,
    operationCompleted ? "寫入操作已取得後端成功證據" : (agent.error_type || "未完成寫入操作"),
    operationCompleted ? "good" : denied ? "bad" : "info",
  );

  $("agentReply").textContent = agent.reply || "—";
  $("agentReply").className = "large-copy";
  $("agentModel").textContent = agent.model || "未呼叫模型";
  const usage = agent.usage || {};
  $("tokenUsage").textContent = `${usage.input_tokens || 0} in / ${usage.output_tokens || 0} out / ${usage.total_tokens || 0} total`;
  $("agentError").textContent = agent.error_type
    ? `${agent.error_type}${agent.error_message ? `：${agent.error_message}` : ""}`
    : "無";
  setBadge(
    $("operationBadge"),
    operationCompleted ? "COMPLETED" : actionStatus.toUpperCase(),
    operationCompleted ? "good" : denied ? "bad" : "warn",
  );

  const toolEvents = Array.isArray(agent.tool_events) ? agent.tool_events : [];
  const succeeded = toolEvents.filter((event) => event.success && event.status === "succeeded");
  const failed = toolEvents.filter((event) => !event.success || ["failed", "denied"].includes(event.status));
  setMetric(
    "toolStatus",
    toolEvents.length ? `${succeeded.length}/${toolEvents.length} 成功` : "未執行",
    failed.length ? `${failed.length} 個工具未成功` : (toolEvents[0]?.record_id || "沒有工具證據"),
    failed.length ? "bad" : succeeded.length ? "good" : "muted",
  );
  renderTools(toolEvents);
  renderGuard(agent.input_guard);
}

function renderSpeech(speech) {
  if (!speech) {
    setMetric("speechStatus", "未執行", "此回合沒有本機語音輸出證據", "muted");
    return;
  }
  setMetric(
    "speechStatus",
    speech.ok ? "成功" : "失敗",
    `${speech.backend || "unknown"}${speech.error ? ` · ${speech.error}` : ""}`,
    speech.ok ? "good" : "bad",
  );
}

function browserSpeechAvailable() {
  return Boolean(globalThis.speechSynthesis && globalThis.SpeechSynthesisUtterance);
}

function browserBeep() {
  try {
    const AudioContext = globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!AudioContext) return;
    const context = new AudioContext();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.frequency.value = 880;
    gain.gain.value = 0.06;
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start();
    oscillator.stop(context.currentTime + 0.16);
    oscillator.addEventListener("ended", () => context.close());
  } catch (_) {
    // Browser audio is best effort and never changes backend operation status.
  }
}

function speakInBrowser(text, { beep = false } = {}) {
  if (!elements.browserSpeechEnabled?.checked || !browserSpeechAvailable()) return false;
  const normalized = String(text || "").replace(/\s+/g, " ").trim().slice(0, 1000);
  if (!normalized) return false;
  if (beep) browserBeep();
  globalThis.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(normalized);
  utterance.lang = "zh-TW";
  utterance.rate = 0.92;
  globalThis.speechSynthesis.speak(utterance);
  return true;
}

function renderResponse(payload, originalMessage = "") {
  elements.rawJson.textContent = JSON.stringify(payload, null, 2);

  const isVoice = Object.prototype.hasOwnProperty.call(payload, "agent");
  const isGuardOnly = Object.prototype.hasOwnProperty.call(payload, "input_guard")
    && !isVoice
    && !Object.prototype.hasOwnProperty.call(payload, "tool_events");

  if (isVoice) {
    renderTranscription(payload.transcript, payload.trace);
    renderAgent(payload.agent);
    renderSpeech(payload.speech_delivery);
    setPendingConfirmation(payload.agent, payload.transcript || originalMessage);
    if (payload.agent?.reply && !payload.speech_delivery?.ok) {
      const spoken = speakInBrowser(payload.agent.reply);
      if (spoken) setMetric("speechStatus", "成功", "browser_speech", "good");
    }
    return;
  }

  if (isGuardOnly) {
    renderTranscription("", null);
    renderGuard(payload.input_guard);
    setMetric(
      "agentStatus",
      "未呼叫",
      "Input Guard 獨立檢查不會呼叫 Bedrock",
      "muted",
    );
    setMetric("toolStatus", "未執行", "Input Guard 獨立檢查不會執行工具", "muted");
    setMetric("speechStatus", "未執行", "沒有語音輸出", "muted");
    $("agentReply").textContent = payload.safe_response || "此模式只檢查輸入安全性。";
    $("agentReply").className = "large-copy";
    $("agentModel").textContent = "未呼叫模型";
    $("tokenUsage").textContent = "0 in / 0 out / 0 total";
    $("agentError").textContent = payload.allowed ? "無" : "Input Guard 已阻擋";
    setBadge($("operationBadge"), payload.action || "CHECK", payload.allowed ? "good" : "bad");
    renderTools([]);
    resetConfirmation();
    return;
  }

  renderTranscription("", null);
  renderAgent(payload);
  renderSpeech(null);
  setPendingConfirmation(payload, originalMessage);
  if (payload?.reply) {
    const spoken = speakInBrowser(payload.reply);
    if (spoken) setMetric("speechStatus", "成功", "browser_speech", "good");
  }
}

function normalizeApiError(response, body) {
  if (body && typeof body === "object") {
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((item) => item.msg || JSON.stringify(item)).join("；");
    if (body.error_message) return body.error_message;
  }
  return `HTTP ${response.status} ${response.statusText}`;
}

function authorizedOptions(url, options = {}) {
  const next = { ...options };
  const headers = new Headers(options.headers || {});
  const token = elements.apiToken?.value.trim();
  if (url.startsWith("/api/") && token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  next.headers = headers;
  return next;
}

async function requestJson(url, options = {}) {
  setRequestState("執行中", "running");
  try {
    const response = await fetch(url, authorizedOptions(url, options));
    const contentType = response.headers.get("content-type") || "";
    const body = contentType.includes("application/json")
      ? await response.json()
      : { detail: await response.text() };
    if (!response.ok) throw new Error(normalizeApiError(response, body));
    setRequestState("完成", "success");
    return body;
  } catch (error) {
    setRequestState("失敗", "error");
    throw error;
  }
}

function requireSessionId() {
  const value = elements.sessionId.value.trim();
  if (value) return value;
  const generated = makeSessionId();
  elements.sessionId.value = generated;
  sessionStorage.setItem(SESSION_STORAGE_KEY, generated);
  return generated;
}

function setBusy(busy) {
  const ids = [
    "sendTextBtn", "checkGuardBtn", "confirmActionBtn", "cancelActionBtn", "runSchedulerBtn",
    "refreshEventsBtn", "refreshStatusBtn",
  ];
  for (const id of ids) {
    const button = $(id);
    if (button) button.disabled = Boolean(busy);
  }
  elements.transcribeBtn.disabled = Boolean(busy) || !state.audioFile;
  elements.voiceTurnBtn.disabled = Boolean(busy) || !state.audioFile;
  elements.startRecordBtn.disabled = Boolean(busy) || Boolean(state.mediaRecorder);
  elements.stopRecordBtn.disabled = Boolean(busy) || !state.mediaRecorder;
}

async function runTask(task, successMessage) {
  setBusy(true);
  try {
    const payload = await task();
    if (successMessage) showToast(successMessage, "success");
    return payload;
  } catch (error) {
    showToast(error instanceof Error ? error.message : String(error), "error");
    elements.rawJson.textContent = JSON.stringify({ error: String(error) }, null, 2);
    return null;
  } finally {
    setBusy(false);
  }
}

function selectAudioFile(file) {
  if (!file) return;
  if (file.size > MAX_AUDIO_BYTES) {
    showToast("音訊檔超過 15 MB 上限。", "error");
    return;
  }
  if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
  state.audioFile = file;
  state.previewUrl = URL.createObjectURL(file);
  elements.audioPreview.src = state.previewUrl;
  elements.audioPreview.hidden = false;
  elements.fileMeta.textContent = `${file.name} · ${file.type || "unknown"} · ${formatBytes(file.size)}`;
  elements.transcribeBtn.disabled = false;
  elements.voiceTurnBtn.disabled = false;
}

function supportedRecorderMimeType() {
  if (!globalThis.MediaRecorder) return "";
  const candidates = [
    "audio/mp4;codecs=mp4a.40.2",
    "audio/mp4",
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
  ];
  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) || "";
}

function extensionForMime(mimeType) {
  if (mimeType.includes("mp4")) return "m4a";
  if (mimeType.includes("ogg")) return "ogg";
  if (mimeType.includes("webm")) return "webm";
  return "webm";
}

async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia || !globalThis.MediaRecorder) {
    throw new Error("此瀏覽器不支援麥克風錄音，請改用音訊檔上傳。" );
  }
  state.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mimeType = supportedRecorderMimeType();
  const options = mimeType ? { mimeType } : undefined;
  state.audioChunks = [];
  state.mediaRecorder = new MediaRecorder(state.mediaStream, options);
  state.mediaRecorder.addEventListener("dataavailable", (event) => {
    if (event.data?.size) state.audioChunks.push(event.data);
  });
  state.mediaRecorder.addEventListener("stop", () => {
    const finalMime = state.mediaRecorder?.mimeType || mimeType || "audio/webm";
    const blob = new Blob(state.audioChunks, { type: finalMime });
    const extension = extensionForMime(finalMime);
    selectAudioFile(new File([blob], `recording-${Date.now()}.${extension}`, { type: finalMime }));
    stopMediaTracks();
    state.mediaRecorder = null;
    elements.startRecordBtn.disabled = false;
    elements.stopRecordBtn.disabled = true;
    elements.recordOrb.classList.remove("recording");
    elements.recordingHint.textContent = "錄音完成，可先播放預覽，再執行完整語音回合。";
  });
  state.mediaRecorder.start(250);
  elements.startRecordBtn.disabled = true;
  elements.stopRecordBtn.disabled = false;
  elements.recordOrb.classList.add("recording");
  elements.recordingHint.textContent = "錄音中，完成後按停止錄音。";
}

function stopMediaTracks() {
  if (state.mediaStream) {
    for (const track of state.mediaStream.getTracks()) track.stop();
    state.mediaStream = null;
  }
}

function stopRecording() {
  if (state.mediaRecorder && state.mediaRecorder.state !== "inactive") {
    state.mediaRecorder.stop();
  }
}

async function sendVoice(endpoint) {
  if (!state.audioFile) throw new Error("請先錄音或選擇音訊檔。" );
  const form = new FormData();
  form.append("audio", state.audioFile, state.audioFile.name);
  const language = elements.voiceLanguage.value;
  if (language) form.append("language", language);
  if (endpoint.endsWith("/turn")) form.append("session_id", requireSessionId());
  const payload = await requestJson(endpoint, { method: "POST", body: form });
  renderResponse(payload);
  return payload;
}

async function sendChat(message, confirmationToken = null) {
  const trimmed = message.trim();
  if (!trimmed && !confirmationToken) throw new Error("請輸入訊息。" );
  const body = {
    message: trimmed || "確認執行待處理操作",
    session_id: requireSessionId(),
  };
  if (confirmationToken) body.confirmation_token = confirmationToken;
  const payload = await requestJson("/api/agent/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  renderResponse(payload, trimmed);
  return payload;
}

async function resolveConfirmation(decision) {
  if (!state.pendingConfirmation) throw new Error("目前沒有待確認操作。" );
  const pending = state.pendingConfirmation;
  elements.sessionId.value = pending.sessionId;
  sessionStorage.setItem(SESSION_STORAGE_KEY, pending.sessionId);
  const payload = await requestJson("/api/agent/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: pending.sessionId,
      confirmation_token: pending.token,
      decision,
    }),
  });
  renderResponse(payload, pending.message);
  resetConfirmation();
  return payload;
}

async function checkGuard(message) {
  const trimmed = message.trim();
  if (!trimmed) throw new Error("請輸入要檢查的文字。" );
  const payload = await requestJson("/api/security/input-guard/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: trimmed, session_id: requireSessionId() }),
  });
  renderResponse(payload, trimmed);
  return payload;
}

async function refreshHealth() {
  try {
    const health = await requestJson("/health");
    elements.apiStatus.textContent = "ONLINE";
    elements.apiStatus.className = "status-dot-label ok";
    elements.modelLabel.textContent = health.model_id || "—";
    elements.envLabel.textContent = health.app_env || "—";
    state.apiAuthRequired = Boolean(health.api_auth_required);
    if (state.apiAuthRequired && !elements.apiToken.value.trim()) {
      elements.apiToken.placeholder = "此雲端服務需要 Token";
    }
  } catch (error) {
    elements.apiStatus.textContent = "OFFLINE";
    elements.apiStatus.className = "status-dot-label error";
    elements.modelLabel.textContent = "—";
    elements.envLabel.textContent = "—";
    throw error;
  }
}

async function refreshSchedulerStatus() {
  const status = await requestJson("/api/reminders/status");
  $("schedulerEnabled").textContent = status.enabled ? "是" : "否";
  $("schedulerRunning").textContent = status.running ? "是" : "否";
  $("schedulerPoll").textContent = Number.isFinite(status.poll_seconds) ? `${status.poll_seconds} 秒` : "—";
  $("alarmBackend").textContent = status.local_alarm_backend || "—";
  $("ttsBackend").textContent = status.local_tts_backend || "—";
  return status;
}

async function refreshOutputEvents({ speakNew = true } = {}) {
  const events = await requestJson("/api/output/events?limit=30");
  const newEvents = events.filter((event) => Number(event.event_id || 0) > state.lastOutputEventId);
  const maxId = events.reduce((value, event) => Math.max(value, Number(event.event_id || 0)), state.lastOutputEventId);
  if (speakNew) {
    for (const event of newEvents) {
      if (event.event_type === "reminder.triggered") {
        speakInBrowser(event.speech_text || event.display_text, { beep: true });
      }
    }
  }
  state.lastOutputEventId = maxId;
  const container = $("outputEvents");
  clearChildren(container);
  $("outputEventCount").textContent = String(events.length);
  if (!events.length) {
    const p = document.createElement("p");
    p.className = "placeholder";
    p.textContent = "尚無輸出事件";
    container.appendChild(p);
    return events;
  }
  for (const event of [...events].reverse()) {
    const item = document.createElement("article");
    item.className = "event-item";
    const title = document.createElement("strong");
    title.textContent = event.event_type || "output.event";
    const text = document.createElement("p");
    text.textContent = event.display_text || "—";
    const meta = document.createElement("small");
    meta.textContent = `${event.created_at || "—"}${event.session_id ? ` · ${event.session_id}` : ""}`;
    item.append(title, text, meta);
    container.appendChild(item);
  }
  return events;
}

async function runSchedulerOnce() {
  const payload = await requestJson("/api/reminders/run-once", { method: "POST" });
  showToast(`Scheduler 處理 ${payload.processed || 0} 筆提醒。`, "success");
  await Promise.allSettled([refreshSchedulerStatus(), refreshOutputEvents()]);
  return payload;
}

function clearResults() {
  renderTranscription("", null);
  renderAgent(null);
  renderSpeech(null);
  renderGuard(null);
  elements.rawJson.textContent = "尚無資料";
  resetConfirmation();
  setRequestState("待命", "idle");
}

function switchMode(mode) {
  state.mode = mode;
  for (const tab of document.querySelectorAll(".mode-tab")) {
    const active = tab.dataset.mode === mode;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
  }
  const mapping = { voice: "voiceMode", text: "textMode", guard: "guardMode" };
  for (const [key, id] of Object.entries(mapping)) {
    const panel = $(id);
    const active = key === mode;
    panel.hidden = !active;
    panel.classList.toggle("active", active);
  }
}

function bindEvents() {
  for (const tab of document.querySelectorAll(".mode-tab")) {
    tab.addEventListener("click", () => switchMode(tab.dataset.mode));
  }
  for (const chip of document.querySelectorAll("[data-example]")) {
    chip.addEventListener("click", () => {
      elements.textMessage.value = chip.dataset.example || "";
    });
  }
  for (const chip of document.querySelectorAll("[data-guard-example]")) {
    chip.addEventListener("click", () => {
      elements.guardMessage.value = chip.dataset.guardExample || "";
    });
  }

  elements.apiToken.value = sessionStorage.getItem("careAgentApiToken") || "";
  elements.sessionId.addEventListener("input", () => {
    const value = elements.sessionId.value.trim();
    if (value) sessionStorage.setItem(SESSION_STORAGE_KEY, value);
  });
  elements.apiToken.addEventListener("input", () => {
    sessionStorage.setItem("careAgentApiToken", elements.apiToken.value);
  });

  elements.startRecordBtn.addEventListener("click", () => runTask(startRecording));
  elements.stopRecordBtn.addEventListener("click", stopRecording);
  elements.audioFile.addEventListener("change", () => selectAudioFile(elements.audioFile.files?.[0]));
  elements.dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    elements.dropZone.classList.add("dragging");
  });
  elements.dropZone.addEventListener("dragleave", () => elements.dropZone.classList.remove("dragging"));
  elements.dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    elements.dropZone.classList.remove("dragging");
    selectAudioFile(event.dataTransfer?.files?.[0]);
  });

  elements.transcribeBtn.addEventListener("click", () => runTask(
    () => sendVoice("/api/voice/transcribe"),
    "Whisper 轉錄完成。",
  ));
  elements.voiceTurnBtn.addEventListener("click", () => runTask(
    () => sendVoice("/api/voice/turn"),
    "完整語音回合完成。",
  ));
  $("sendTextBtn").addEventListener("click", () => runTask(
    () => sendChat(elements.textMessage.value),
    "Agent 回合完成。",
  ));
  $("checkGuardBtn").addEventListener("click", () => runTask(
    () => checkGuard(elements.guardMessage.value),
    "Input Guard 檢查完成。",
  ));
  elements.confirmActionBtn.addEventListener("click", () => runTask(
    () => resolveConfirmation("confirm"),
    "待確認操作已執行。",
  ));
  elements.cancelActionBtn.addEventListener("click", () => runTask(
    () => resolveConfirmation("cancel"),
    "待確認操作已取消。",
  ));

  $("clearResultBtn").addEventListener("click", clearResults);
  $("refreshStatusBtn").addEventListener("click", () => runTask(async () => {
    await Promise.all([refreshHealth(), refreshSchedulerStatus(), refreshOutputEvents()]);
  }, "狀態已更新。"));
  $("refreshEventsBtn").addEventListener("click", () => runTask(refreshOutputEvents, "輸出事件已更新。"));
  $("runSchedulerBtn").addEventListener("click", () => runTask(runSchedulerOnce));

  window.addEventListener("beforeunload", () => {
    stopMediaTracks();
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
    if (state.outputPollTimer) clearInterval(state.outputPollTimer);
    globalThis.speechSynthesis?.cancel();
  });
}

async function init() {
  elements.sessionId.value = sessionStorage.getItem(SESSION_STORAGE_KEY) || makeSessionId();
  sessionStorage.setItem(SESSION_STORAGE_KEY, elements.sessionId.value);
  bindEvents();
  clearResults();
  setRequestState("初始化", "running");
  const results = await Promise.allSettled([
    refreshHealth(),
    refreshSchedulerStatus(),
    refreshOutputEvents({ speakNew: false }),
  ]);
  const failed = results.filter((item) => item.status === "rejected");
  setRequestState(failed.length ? "部分服務不可用" : "待命", failed.length ? "error" : "idle");
  if (failed.length) showToast("部分狀態端點無法讀取，仍可嘗試其他功能。", "error");
  state.outputPollTimer = setInterval(() => {
    refreshOutputEvents({ speakNew: true }).catch(() => {});
  }, 2500);
}

init();
