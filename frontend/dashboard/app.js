const DEFAULT_UI_SETTINGS = {
  api_base_url: "http://127.0.0.1:8000",
  webhook_source: "dashboard",
  webhook_signal_type: "entry_long",
  webhook_broker: "mock",
  webhook_symbol: "INFY",
  webhook_exchange: "NSE",
  webhook_side: "buy",
  webhook_quantity: 2,
  webhook_order_type: "market",
  webhook_product_type: "cnc",
};

const DEFAULT_BROKER_SETUP = {
  broker_name: "mock",
  account_label: "Primary Paper Account",
  execution_mode: "paper",
  default_exchange: "NSE",
  default_product_type: "cnc",
  is_live_enabled: false,
};

const DEFAULT_BROKER_CREDENTIALS = {
  broker_name: "mock",
  client_id_hint: "",
  api_key_hint: "",
  has_access_token: false,
  has_api_secret: false,
  updated_at: "",
};

const state = {
  apiBaseUrl: localStorage.getItem("tradelensApiBaseUrl") || DEFAULT_UI_SETTINGS.api_base_url,
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
  loadUiSettings: document.getElementById("loadUiSettings"),
  saveUiSettings: document.getElementById("saveUiSettings"),
  resetUiSettings: document.getElementById("resetUiSettings"),
  loadBrokerSetup: document.getElementById("loadBrokerSetup"),
  saveBrokerSetup: document.getElementById("saveBrokerSetup"),
  resetBrokerSetup: document.getElementById("resetBrokerSetup"),
  loadBrokerCredentials: document.getElementById("loadBrokerCredentials"),
  saveBrokerCredentials: document.getElementById("saveBrokerCredentials"),
  resetBrokerCredentials: document.getElementById("resetBrokerCredentials"),
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
  settingsApiBaseUrl: document.getElementById("settingsApiBaseUrl"),
  settingsWebhookSource: document.getElementById("settingsWebhookSource"),
  settingsWebhookSignalType: document.getElementById("settingsWebhookSignalType"),
  settingsWebhookBroker: document.getElementById("settingsWebhookBroker"),
  settingsWebhookSymbol: document.getElementById("settingsWebhookSymbol"),
  settingsWebhookExchange: document.getElementById("settingsWebhookExchange"),
  settingsWebhookSide: document.getElementById("settingsWebhookSide"),
  settingsWebhookQuantity: document.getElementById("settingsWebhookQuantity"),
  settingsWebhookOrderType: document.getElementById("settingsWebhookOrderType"),
  settingsWebhookProductType: document.getElementById("settingsWebhookProductType"),
  uiSettingsResponse: document.getElementById("uiSettingsResponse"),
  brokerSetupName: document.getElementById("brokerSetupName"),
  brokerSetupAccountLabel: document.getElementById("brokerSetupAccountLabel"),
  brokerSetupExecutionMode: document.getElementById("brokerSetupExecutionMode"),
  brokerSetupExchange: document.getElementById("brokerSetupExchange"),
  brokerSetupProductType: document.getElementById("brokerSetupProductType"),
  brokerSetupLiveEnabled: document.getElementById("brokerSetupLiveEnabled"),
  brokerSetupResponse: document.getElementById("brokerSetupResponse"),
  brokerCredentialsName: document.getElementById("brokerCredentialsName"),
  brokerCredentialsClientId: document.getElementById("brokerCredentialsClientId"),
  brokerCredentialsApiKey: document.getElementById("brokerCredentialsApiKey"),
  brokerCredentialsAccessToken: document.getElementById("brokerCredentialsAccessToken"),
  brokerCredentialsApiSecret: document.getElementById("brokerCredentialsApiSecret"),
  brokerCredentialsClientIdHint: document.getElementById("brokerCredentialsClientIdHint"),
  brokerCredentialsApiKeyHint: document.getElementById("brokerCredentialsApiKeyHint"),
  brokerCredentialsHasAccessToken: document.getElementById("brokerCredentialsHasAccessToken"),
  brokerCredentialsHasApiSecret: document.getElementById("brokerCredentialsHasApiSecret"),
  brokerCredentialsResponse: document.getElementById("brokerCredentialsResponse"),
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

function loadStoredUiSettings() {
  try {
    const raw = localStorage.getItem("tradelensUiSettings");
    if (!raw) return { ...DEFAULT_UI_SETTINGS };
    return { ...DEFAULT_UI_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULT_UI_SETTINGS };
  }
}

function loadStoredBrokerSetup() {
  try {
    const raw = localStorage.getItem("tradelensBrokerSetup");
    if (!raw) return { ...DEFAULT_BROKER_SETUP };
    return { ...DEFAULT_BROKER_SETUP, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULT_BROKER_SETUP };
  }
}

function loadStoredBrokerCredentials() {
  try {
    const raw = localStorage.getItem("tradelensBrokerCredentials");
    if (!raw) return { ...DEFAULT_BROKER_CREDENTIALS };
    return { ...DEFAULT_BROKER_CREDENTIALS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULT_BROKER_CREDENTIALS };
  }
}

function renderUiSettings(settings) {
  el.settingsApiBaseUrl.value = settings.api_base_url;
  el.settingsWebhookSource.value = settings.webhook_source;
  el.settingsWebhookSignalType.value = settings.webhook_signal_type;
  el.settingsWebhookBroker.value = settings.webhook_broker;
  el.settingsWebhookSymbol.value = settings.webhook_symbol;
  el.settingsWebhookExchange.value = settings.webhook_exchange;
  el.settingsWebhookSide.value = settings.webhook_side;
  el.settingsWebhookQuantity.value = String(settings.webhook_quantity);
  el.settingsWebhookOrderType.value = settings.webhook_order_type;
  el.settingsWebhookProductType.value = settings.webhook_product_type;
  el.uiSettingsResponse.textContent = JSON.stringify(settings, null, 2);
  applyUiSettingsToDashboard(settings);
}

function renderBrokerSetup(setup) {
  el.brokerSetupName.value = setup.broker_name;
  el.brokerSetupAccountLabel.value = setup.account_label;
  el.brokerSetupExecutionMode.value = setup.execution_mode;
  el.brokerSetupExchange.value = setup.default_exchange;
  el.brokerSetupProductType.value = setup.default_product_type;
  el.brokerSetupLiveEnabled.checked = Boolean(setup.is_live_enabled);
  el.brokerSetupResponse.textContent = JSON.stringify(setup, null, 2);
  applyBrokerSetupToDashboard(setup);
}

function renderBrokerCredentials(profile) {
  el.brokerCredentialsName.value = profile.broker_name || DEFAULT_BROKER_CREDENTIALS.broker_name;
  el.brokerCredentialsClientId.value = "";
  el.brokerCredentialsApiKey.value = "";
  el.brokerCredentialsAccessToken.value = "";
  el.brokerCredentialsApiSecret.value = "";
  el.brokerCredentialsClientIdHint.textContent = profile.client_id_hint || "-";
  el.brokerCredentialsApiKeyHint.textContent = profile.api_key_hint || "-";
  el.brokerCredentialsHasAccessToken.textContent = String(Boolean(profile.has_access_token));
  el.brokerCredentialsHasApiSecret.textContent = String(Boolean(profile.has_api_secret));
  el.brokerCredentialsResponse.textContent = JSON.stringify(profile, null, 2);
}

function applyUiSettingsToDashboard(settings) {
  setApiBaseUrl(settings.api_base_url);
  el.webhookSource.value = settings.webhook_source;
  el.webhookSignalType.value = settings.webhook_signal_type;
  el.webhookBroker.value = settings.webhook_broker;
  el.webhookSymbol.value = settings.webhook_symbol;
  el.webhookExchange.value = settings.webhook_exchange;
  el.webhookSide.value = settings.webhook_side;
  el.webhookQuantity.value = String(settings.webhook_quantity);
  el.webhookOrderType.value = settings.webhook_order_type;
  el.webhookProductType.value = settings.webhook_product_type;
}

function applyBrokerSetupToDashboard(setup) {
  el.webhookBroker.value = setup.broker_name;
  el.webhookExchange.value = setup.default_exchange;
  el.webhookProductType.value = setup.default_product_type;
}

function buildUiSettingsPayload() {
  return {
    api_base_url: el.settingsApiBaseUrl.value.trim() || DEFAULT_UI_SETTINGS.api_base_url,
    webhook_source: el.settingsWebhookSource.value.trim() || DEFAULT_UI_SETTINGS.webhook_source,
    webhook_signal_type: el.settingsWebhookSignalType.value.trim() || DEFAULT_UI_SETTINGS.webhook_signal_type,
    webhook_broker: el.settingsWebhookBroker.value.trim() || DEFAULT_UI_SETTINGS.webhook_broker,
    webhook_symbol: el.settingsWebhookSymbol.value.trim() || DEFAULT_UI_SETTINGS.webhook_symbol,
    webhook_exchange: el.settingsWebhookExchange.value.trim() || DEFAULT_UI_SETTINGS.webhook_exchange,
    webhook_side: el.settingsWebhookSide.value,
    webhook_quantity: Number(el.settingsWebhookQuantity.value) || DEFAULT_UI_SETTINGS.webhook_quantity,
    webhook_order_type: el.settingsWebhookOrderType.value,
    webhook_product_type: el.settingsWebhookProductType.value,
  };
}

function buildBrokerSetupPayload() {
  return {
    broker_name: el.brokerSetupName.value.trim() || DEFAULT_BROKER_SETUP.broker_name,
    account_label: el.brokerSetupAccountLabel.value.trim() || DEFAULT_BROKER_SETUP.account_label,
    execution_mode: el.brokerSetupExecutionMode.value,
    default_exchange: el.brokerSetupExchange.value.trim() || DEFAULT_BROKER_SETUP.default_exchange,
    default_product_type: el.brokerSetupProductType.value,
    is_live_enabled: Boolean(el.brokerSetupLiveEnabled.checked),
  };
}

function buildBrokerCredentialsPayload() {
  return {
    broker_name: el.brokerCredentialsName.value.trim() || DEFAULT_BROKER_CREDENTIALS.broker_name,
    client_id: el.brokerCredentialsClientId.value.trim() || null,
    api_key: el.brokerCredentialsApiKey.value.trim() || null,
    access_token: el.brokerCredentialsAccessToken.value.trim() || null,
    api_secret: el.brokerCredentialsApiSecret.value.trim() || null,
  };
}

function saveUiSettings() {
  const payload = buildUiSettingsPayload();
  localStorage.setItem("tradelensUiSettings", JSON.stringify(payload));
  renderUiSettings(payload);
}

function resetUiSettings() {
  localStorage.setItem("tradelensUiSettings", JSON.stringify(DEFAULT_UI_SETTINGS));
  renderUiSettings(DEFAULT_UI_SETTINGS);
}

async function loadBrokerSetup() {
  try {
    const result = await apiFetch("/broker-profile");
    localStorage.setItem("tradelensBrokerSetup", JSON.stringify(result));
    renderBrokerSetup(result);
  } catch (error) {
    const fallback = loadStoredBrokerSetup();
    renderBrokerSetup(fallback);
    el.brokerSetupResponse.textContent = `Backend unavailable, showing local profile\n${JSON.stringify(fallback, null, 2)}`;
  }
}

async function saveBrokerSetup() {
  const payload = buildBrokerSetupPayload();
  el.brokerSetupResponse.textContent = "Saving...";
  try {
    const result = await apiFetch("/broker-profile", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    localStorage.setItem("tradelensBrokerSetup", JSON.stringify(result));
    renderBrokerSetup(result);
    await refreshAuditEvents();
  } catch (error) {
    localStorage.setItem("tradelensBrokerSetup", JSON.stringify(payload));
    renderBrokerSetup(payload);
    el.brokerSetupResponse.textContent = `Saved locally because backend profile API failed\n${String(error.message || error)}`;
  }
}

async function resetBrokerSetup() {
  renderBrokerSetup(DEFAULT_BROKER_SETUP);
  await saveBrokerSetup();
}

async function loadBrokerCredentials() {
  try {
    const result = await apiFetch("/broker-credentials");
    localStorage.setItem("tradelensBrokerCredentials", JSON.stringify(result));
    renderBrokerCredentials(result);
  } catch (error) {
    const fallback = loadStoredBrokerCredentials();
    renderBrokerCredentials(fallback);
    el.brokerCredentialsResponse.textContent = `Backend unavailable, showing local placeholder profile\n${JSON.stringify(fallback, null, 2)}`;
  }
}

async function saveBrokerCredentials() {
  const payload = buildBrokerCredentialsPayload();
  el.brokerCredentialsResponse.textContent = "Saving...";
  try {
    const result = await apiFetch("/broker-credentials", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    localStorage.setItem("tradelensBrokerCredentials", JSON.stringify(result));
    renderBrokerCredentials(result);
    await refreshAuditEvents();
  } catch (error) {
    const fallback = {
      broker_name: payload.broker_name,
      client_id_hint: payload.client_id ? "saved-locally" : "",
      api_key_hint: payload.api_key ? "saved-locally" : "",
      has_access_token: Boolean(payload.access_token),
      has_api_secret: Boolean(payload.api_secret),
      updated_at: new Date().toISOString(),
    };
    localStorage.setItem("tradelensBrokerCredentials", JSON.stringify(fallback));
    renderBrokerCredentials(fallback);
    el.brokerCredentialsResponse.textContent = `Saved local placeholder because backend credential API failed\n${String(error.message || error)}`;
  }
}

async function resetBrokerCredentials() {
  renderBrokerCredentials(DEFAULT_BROKER_CREDENTIALS);
  localStorage.setItem("tradelensBrokerCredentials", JSON.stringify(DEFAULT_BROKER_CREDENTIALS));
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
  const uiSettings = loadStoredUiSettings();
  renderUiSettings(uiSettings);
  await loadBrokerSetup();
  await loadBrokerCredentials();
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

el.loadUiSettings.addEventListener("click", () => renderUiSettings(loadStoredUiSettings()));
el.saveUiSettings.addEventListener("click", saveUiSettings);
el.resetUiSettings.addEventListener("click", resetUiSettings);
el.loadBrokerSetup.addEventListener("click", loadBrokerSetup);
el.saveBrokerSetup.addEventListener("click", saveBrokerSetup);
el.resetBrokerSetup.addEventListener("click", resetBrokerSetup);
el.loadBrokerCredentials.addEventListener("click", loadBrokerCredentials);
el.saveBrokerCredentials.addEventListener("click", saveBrokerCredentials);
el.resetBrokerCredentials.addEventListener("click", resetBrokerCredentials);
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
