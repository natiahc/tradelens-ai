const state = {
  apiBaseUrl: localStorage.getItem("tradelensApiBaseUrl") || "http://127.0.0.1:8000",
};

const el = {
  apiBaseUrl: document.getElementById("apiBaseUrl"),
  saveApiBaseUrl: document.getElementById("saveApiBaseUrl"),
  refreshHealth: document.getElementById("refreshHealth"),
  refreshBrokers: document.getElementById("refreshBrokers"),
  refreshOrders: document.getElementById("refreshOrders"),
  refreshAudit: document.getElementById("refreshAudit"),
  refreshSummary: document.getElementById("refreshSummary"),
  sendWebhook: document.getElementById("sendWebhook"),
  healthStatus: document.getElementById("healthStatus"),
  healthPayload: document.getElementById("healthPayload"),
  brokerList: document.getElementById("brokerList"),
  orderHistoryBody: document.getElementById("orderHistoryBody"),
  auditBody: document.getElementById("auditBody"),
  auditPayload: document.getElementById("auditPayload"),
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
}

function renderStrategySummary(summary) {
  el.summaryReceived.textContent = String(summary.signals_received ?? 0);
  el.summaryExecuted.textContent = String(summary.executed ?? 0);
  el.summaryBlocked.textContent = String(summary.blocked ?? 0);
  el.summarySkipped.textContent = String(summary.skipped ?? 0);
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

async function initialize() {
  setApiBaseUrl(state.apiBaseUrl);
  await Promise.all([
    refreshHealth(),
    refreshBrokers(),
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
el.refreshOrders.addEventListener("click", refreshOrderHistory);
el.refreshAudit.addEventListener("click", refreshAuditEvents);
el.refreshSummary.addEventListener("click", refreshStrategySummary);
el.sendWebhook.addEventListener("click", sendWebhook);

initialize();
