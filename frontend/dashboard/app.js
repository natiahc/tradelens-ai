const state = {
  apiBaseUrl: localStorage.getItem("tradelensApiBaseUrl") || "http://127.0.0.1:8000",
};

const DEFAULT_RISK_SETTINGS = {
  allowed_symbols: ["INFY", "TCS", "RELIANCE", "SBIN"],
  allowed_brokers: ["mock"],
  max_quantity: 10,
  max_daily_strategy_executions: 20,
};

const el = {
  apiBaseUrl: document.getElementById("apiBaseUrl"),
  saveApiBaseUrl: document.getElementById("saveApiBaseUrl"),
  refreshHealth: document.getElementById("refreshHealth"),
  refreshBrokers: document.getElementById("refreshBrokers"),
  refreshOrders: document.getElementById("refreshOrders"),
  refreshAudit: document.getElementById("refreshAudit"),
  refreshSummary: document.getElementById("refreshSummary"),
  refreshCharts: document.getElementById("refreshCharts"),
  refreshRiskSettings: document.getElementById("refreshRiskSettings"),
  saveRiskSettings: document.getElementById("saveRiskSettings"),
  resetRiskSettings: document.getElementById("resetRiskSettings"),
  sendWebhook: document.getElementById("sendWebhook"),
  healthStatus: document.getElementById("healthStatus"),
  healthPayload: document.getElementById("healthPayload"),
  brokerList: document.getElementById("brokerList"),
  orderHistoryBody: document.getElementById("orderHistoryBody"),
  auditBody: document.getElementById("auditBody"),
  auditPayload: document.getElementById("auditPayload"),
  outcomeBars: document.getElementById("outcomeBars"),
  recentTimeline: document.getElementById("recentTimeline"),
  webhookResponse: document.getElementById("webhookResponse"),
  webhookSource: document.getElementById("webhookSource"),
  webhookSignalType: document.getElementById("webhookSignalType"),
  webhookBroker: document.getElementById("webhookBroker"),
  webhookSymbol: document.getElementById("webhookSymbol"),
  webhookExchange: document.getElementById("webhookExchange"),
  webhookSide: document.getElementById("webhookSide"),
  webhookQuantity: document.getElementById("webhookQuantity"),
  webhookOrderType: document.getElementById("webhookOrderType"),
  webhookProductType: document.getElementById("webhookProductType"),
  includePaperTradeOrder: document.getElementById("includePaperTradeOrder"),
  riskAllowedSymbols: document.getElementById("riskAllowedSymbols"),
  riskAllowedBrokers: document.getElementById("riskAllowedBrokers"),
  riskMaxQuantity: document.getElementById("riskMaxQuantity"),
  riskMaxDailyExecutions: document.getElementById("riskMaxDailyExecutions"),
  riskSettingsResponse: document.getElementById("riskSettingsResponse"),
  summaryReceived: document.getElementById("summaryReceived"),
  summaryExecuted: document.getElementById("summaryExecuted"),
  summaryBlocked: document.getElementById("summaryBlocked"),
  summarySkipped: document.getElementById("summarySkipped"),
};

function setApiBaseUrl(url) {
  state.apiBaseUrl = url.replace(/\/$/, "");
  localStorage.setItem("tradelensApiBaseUrl", state.apiBaseUrl);
  el.apiBaseUrl.value = state.apiBaseUrl;
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${state.apiBaseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const text = await response.text();
  let body;
  try {
    body = text ? JSON.parse(text) : {};
  } catch {
    body = { raw: text };
  }

  if (!response.ok) {
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }

  return body;
}

function renderHealth(data) {
  el.healthStatus.textContent = data.status || "unknown";
  el.healthStatus.style.background = data.status === "ok" ? "#166534" : "#7c2d12";
  el.healthPayload.textContent = JSON.stringify(data, null, 2);
}

function renderBrokers(data) {
  el.brokerList.innerHTML = "";
  for (const broker of data.brokers || []) {
    const item = document.createElement("li");
    item.textContent = broker;
    el.brokerList.appendChild(item);
  }
}

function renderRiskSettings(data) {
  el.riskAllowedSymbols.value = (data.allowed_symbols || []).join(",");
  el.riskAllowedBrokers.value = (data.allowed_brokers || []).join(",");
  el.riskMaxQuantity.value = String(data.max_quantity ?? 1);
  el.riskMaxDailyExecutions.value = String(data.max_daily_strategy_executions ?? 1);
  el.riskSettingsResponse.textContent = JSON.stringify(data, null, 2);
}

function renderOrderHistory(data) {
  el.orderHistoryBody.innerHTML = "";
  for (const row of data || []) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.record_id}</td>
      <td>${row.broker_name}</td>
      <td>${row.order_id}</td>
      <td>${row.symbol}</td>
      <td>${row.side}</td>
      <td>${row.quantity}</td>
      <td>${row.status}</td>
      <td>${row.created_at}</td>
    `;
    el.orderHistoryBody.appendChild(tr);
  }
}

function renderAuditEvents(data) {
  el.auditBody.innerHTML = "";
  for (const row of data || []) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.event_id}</td>
      <td>${row.event_type}</td>
      <td>${row.broker_name || "-"}</td>
      <td>${row.entity_id || "-"}</td>
      <td>${row.created_at}</td>
    `;
    el.auditBody.appendChild(tr);
  }
  el.auditPayload.textContent = JSON.stringify(data, null, 2);
  renderRecentTimeline(data || []);
}

function renderStrategySummary(summary) {
  el.summaryReceived.textContent = String(summary.signals_received ?? 0);
  el.summaryExecuted.textContent = String(summary.executed ?? 0);
  el.summaryBlocked.textContent = String(summary.blocked ?? 0);
  el.summarySkipped.textContent = String(summary.skipped ?? 0);
  renderOutcomeBars(summary);
}

function renderOutcomeBars(summary) {
  const rows = [
    ["Received", summary.signals_received ?? 0],
    ["Executed", summary.executed ?? 0],
    ["Blocked", summary.blocked ?? 0],
    ["Skipped", summary.skipped ?? 0],
  ];
  const max = Math.max(1, ...rows.map(([, value]) => value));
  el.outcomeBars.innerHTML = "";

  for (const [label, value] of rows) {
    const widthPct = Math.max(6, Math.round((value / max) * 100));
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <div class="bar-label">${label}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${widthPct}%"></div></div>
      <div class="bar-value">${value}</div>
    `;
    el.outcomeBars.appendChild(row);
  }
}

function renderRecentTimeline(events) {
  const filtered = events
    .filter((event) => event.event_type.startsWith("strategy_signal_"))
    .slice(0, 12);

  el.recentTimeline.innerHTML = "";
  if (filtered.length === 0) {
    el.recentTimeline.innerHTML = '<div class="timeline-item"><div class="timeline-time">-</div><div class="timeline-type">No strategy activity yet</div></div>';
    return;
  }

  for (const event of filtered) {
    const item = document.createElement("div");
    item.className = "timeline-item";
    item.innerHTML = `
      <div class="timeline-time">${event.created_at}</div>
      <div class="timeline-type">${event.event_type}</div>
    `;
    el.recentTimeline.appendChild(item);
  }
}

async function refreshHealth() {
  try {
    renderHealth(await apiFetch("/health"));
  } catch (error) {
    el.healthStatus.textContent = "error";
    el.healthStatus.style.background = "#991b1b";
    el.healthPayload.textContent = String(error.message || error);
  }
}

async function refreshBrokers() {
  try {
    renderBrokers(await apiFetch("/brokers"));
  } catch (error) {
    el.brokerList.innerHTML = `<li>${error.message || error}</li>`;
  }
}

async function refreshRiskSettings() {
  try {
    renderRiskSettings(await apiFetch("/risk/settings"));
  } catch (error) {
    el.riskSettingsResponse.textContent = String(error.message || error);
  }
}

function buildRiskSettingsPayload() {
  return {
    allowed_symbols: el.riskAllowedSymbols.value.split(",").map((s) => s.trim()).filter(Boolean),
    allowed_brokers: el.riskAllowedBrokers.value.split(",").map((s) => s.trim()).filter(Boolean),
    max_quantity: Number(el.riskMaxQuantity.value),
    max_daily_strategy_executions: Number(el.riskMaxDailyExecutions.value),
  };
}

async function saveRiskSettings() {
  const payload = buildRiskSettingsPayload();
  el.riskSettingsResponse.textContent = "Saving...";
  try {
    const result = await apiFetch("/risk/settings", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    renderRiskSettings(result);
    await refreshAuditEvents();
  } catch (error) {
    el.riskSettingsResponse.textContent = String(error.message || error);
  }
}

async function resetRiskSettings() {
  renderRiskSettings(DEFAULT_RISK_SETTINGS);
  await saveRiskSettings();
}

async function refreshOrderHistory() {
  try {
    renderOrderHistory(await apiFetch("/orders/history"));
  } catch (error) {
    el.orderHistoryBody.innerHTML = `<tr><td colspan="8">${error.message || error}</td></tr>`;
  }
}

async function refreshAuditEvents() {
  try {
    renderAuditEvents(await apiFetch("/audit/events"));
  } catch (error) {
    el.auditBody.innerHTML = `<tr><td colspan="5">${error.message || error}</td></tr>`;
    el.auditPayload.textContent = String(error.message || error);
    renderRecentTimeline([]);
  }
}

async function refreshStrategySummary() {
  try {
    renderStrategySummary(await apiFetch("/strategy/summary"));
  } catch (error) {
    renderStrategySummary({ signals_received: 0, executed: 0, blocked: 0, skipped: 0 });
  }
}

function buildWebhookPayload() {
  const payload = {
    source: el.webhookSource.value,
    signal_type: el.webhookSignalType.value,
    broker: el.webhookBroker.value,
    payload: {},
  };

  if (el.includePaperTradeOrder.checked) {
    payload.payload.paper_trade_order = {
      symbol: el.webhookSymbol.value,
      exchange: el.webhookExchange.value,
      side: el.webhookSide.value,
      quantity: Number(el.webhookQuantity.value),
      order_type: el.webhookOrderType.value,
      product_type: el.webhookProductType.value,
      client_order_id: `dashboard-${Date.now()}`,
    };
  }

  return payload;
}

async function sendWebhook() {
  const payload = buildWebhookPayload();
  el.webhookResponse.textContent = "Sending...";
  try {
    const result = await apiFetch("/webhooks/strategy", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    el.webhookResponse.textContent = JSON.stringify(result, null, 2);
    await refreshOrderHistory();
    await refreshAuditEvents();
    await refreshStrategySummary();
  } catch (error) {
    el.webhookResponse.textContent = String(error.message || error);
  }
}

async function refreshCharts() {
  await Promise.all([refreshStrategySummary(), refreshAuditEvents()]);
}

async function initialize() {
  setApiBaseUrl(state.apiBaseUrl);
  await Promise.all([
    refreshHealth(),
    refreshBrokers(),
    refreshRiskSettings(),
    refreshOrderHistory(),
    refreshAuditEvents(),
    refreshStrategySummary(),
  ]);
}

el.saveApiBaseUrl.addEventListener("click", async () => {
  setApiBaseUrl(el.apiBaseUrl.value.trim());
  await initialize();
});

el.refreshHealth.addEventListener("click", refreshHealth);
el.refreshBrokers.addEventListener("click", refreshBrokers);
el.refreshRiskSettings.addEventListener("click", refreshRiskSettings);
el.saveRiskSettings.addEventListener("click", saveRiskSettings);
el.resetRiskSettings.addEventListener("click", resetRiskSettings);
el.refreshOrders.addEventListener("click", refreshOrderHistory);
el.refreshAudit.addEventListener("click", refreshAuditEvents);
el.refreshSummary.addEventListener("click", refreshStrategySummary);
el.refreshCharts.addEventListener("click", refreshCharts);
el.sendWebhook.addEventListener("click", sendWebhook);

initialize();
