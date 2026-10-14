/* TradeLens diagnostics: fail-safe, never logs credentials or submits trades. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const KEY = "tradelensDiagnosticHistory";
  const DEFAULT_API = "https://tradelens-ai-t8za.onrender.com";
  const MAX_LOGS = 50;
  const cleanApi = () => {
    const chosen = ($("apiBaseUrl")?.value || "").trim()
      || localStorage.getItem("tradelensApiBaseUrl") || DEFAULT_API;
    return chosen.replace(/\/+$/, "");
  };
  const token = () => sessionStorage.getItem("tradelensAdminToken") || "";
  const safeText = (s) => String(s == null ? "" : s).slice(0, 280);
  const iso = () => new Date().toISOString();
  let active = false;

  const readLogs = () => {
    try {
      const value = JSON.parse(localStorage.getItem(KEY) || "[]");
      return Array.isArray(value) ? value.slice(-MAX_LOGS) : [];
    } catch (_) { return []; }
  };
  const saveEvent = (check, status, message) => {
    const logs = readLogs();
    logs.push({
      at: iso(), check: safeText(check),
      status: safeText(status), message: safeText(message),
      api: cleanApi().split("?")[0], // no query strings or auth data
    });
    localStorage.setItem(KEY, JSON.stringify(logs.slice(-MAX_LOGS)));
    $("diagLog").textContent = JSON.stringify(readLogs().slice(-15), null, 2);
  };
  async function call(path, method = "GET", admin = false) {
    const headers = { Accept: "application/json" };
    if (admin) {
      if (!token()) throw new Error("Enter your admin token and select Unlock Tools.");
      headers["X-TradeLens-Admin-Token"] = token();
    }
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), 12000);
    try {
      const result = await fetch(cleanApi() + path, {
        method, headers, signal: abort.signal,
      });
      let data;
      try { data = await result.json(); }
      catch (_) { throw new Error("Non-JSON API response (HTTP " + result.status + ")"); }
      if (!result.ok) {
        throw new Error("HTTP " + result.status + ": " + safeText(data.detail || "Request failed"));
      }
      return data;
    } finally { clearTimeout(timer); }
  }
  const render = (report) => {
    const table = $("diagChecks");
    table.replaceChildren();
    const findings = Array.isArray(report.findings) ? report.findings : [];
    const add = (name, status, message) => {
      const row = document.createElement("tr");
      for (const content of [name, status, message]) {
        const cell = document.createElement("td");
        cell.textContent = safeText(content);
        row.appendChild(cell);
      }
      table.appendChild(row);
    };
    for (const finding of findings) add(finding.id, finding.status, finding.message);
    const failed = findings.filter((f) => f.status === "fail" || f.status === "blocked");
    $("diagSummary").textContent = failed.length
      ? failed.length + " configuration/availability issue(s). Follow the guidance below."
      : "Backend responded. Review manual checks before using real capital.";
    const caps = (report.capabilities || []).map((item) =>
      item.method + " " + item.path + " (" + (item.admin ? "admin token" : "public research") + ")"
    );
    $("diagCapabilities").textContent = "Supported APIs:\n" + caps.join("\n") +
      "\n\nImportant limitations:\n" + (report.limitations || []).join("\n");
    saveEvent("capability_check", failed.length ? "attention" : "pass",
      failed.length ? failed.map((i) => i.id).join(", ") : "Backend diagnostics available");
  };

  async function run(checkSave = false) {
    if (active) return;
    active = true;
    $("diagRun").disabled = true;
    $("diagSave").disabled = true;
    $("diagSummary").textContent = "Checking the existing Render backend…";
    try {
      const response = await call("/health");
      if (response.status !== "ok") throw new Error("Unexpected /health response");
      const report = await call(checkSave ? "/diagnostics/run" : "/diagnostics/status",
        checkSave ? "POST" : "GET", checkSave);
      render(report);
      if (checkSave) saveEvent("backend_audit_saved", "pass", "Sanitized audit persisted on Render");
    } catch (error) {
      // Don't serialize request data, credential values, or exception stacks.
      const message = safeText(error.message || "Unknown diagnostic problem");
      $("diagSummary").textContent = "Diagnostics not completed: " + message +
        ". Confirm the backend URL and that Render is deployed. Review admin token configuration.";
      saveEvent("backend_diagnostic", "failed", message);
    } finally {
      active = false;
      $("diagRun").disabled = false;
      $("diagSave").disabled = false;
    }
  }

  async function loadBackendLogs() {
    try {
      const logs = await call("/diagnostics/logs?limit=50", "GET", true);
      saveEvent("backend_log_fetch", "pass", "Retrieved " + logs.length + " saved audits");
      return logs;
    } catch (error) {
      saveEvent("backend_log_fetch", "attention", safeText(error.message));
      return [];
    }
  }

  async function exportLogs() {
    const reports = await loadBackendLogs();
    const documentData = {
      created_at: iso(),
      application: "TradeLens AI",
      notice: "Sanitized diagnostics only. No secrets or raw server logs.",
      browser_events: readLogs(),
      backend_saved_audits: reports,
    };
    const blob = new Blob([JSON.stringify(documentData, null, 2)], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "tradelens-audit-" + iso().slice(0, 10) + ".json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  // Never save the admin secret to localStorage; limit it to this browser tab session.
  const adminInput = $("adminAccessToken");
  adminInput.value = token();
  $("saveAdminAccessToken").addEventListener("click", () => {
    const submitted = adminInput.value.trim();
    if (submitted) {
      sessionStorage.setItem("tradelensAdminToken", submitted);
      adminInput.value = "";
      $("diagSummary").textContent = "Admin token available for this browser tab. Run diagnostics to validate it.";
    } else {
      sessionStorage.removeItem("tradelensAdminToken");
      $("diagSummary").textContent = "Admin token cleared. Public paper research remains available.";
    }
  });
  $("diagRun").addEventListener("click", () => run(false));
  $("diagSave").addEventListener("click", () => run(true));
  $("diagExport").addEventListener("click", exportLogs);
  $("diagLog").textContent = JSON.stringify(readLogs().slice(-15), null, 2);
  run(false);

  // While the dashboard is open, check connectivity at most every 15 minutes.
  setInterval(() => { if (document.visibilityState === "visible") run(false); }, 900000);
})();
