/* TradeLens Assistant. Deterministic safe actions + authenticated guidance.
   Deliberately cannot place real orders, modify code, or deploy services. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const panel = $("tlChatPanel");
  if (!panel) return;
  const localRequestsKey = "tradelensProposedChangesV2";
  const preferenceKey = "tradelensResearchPrefsV2";
  const uiKey = "tradelensUiPreferencesV1";
  const adminToken = () => sessionStorage.getItem("tradelensAdminToken") || "";
  const defaultApi = "https://tradelens-ai-t8za.onrender.com";
  const root = () => ($("apiBaseUrl")?.value.trim() ||
    localStorage.getItem("tradelensApiBaseUrl") || defaultApi).replace(/\/+$/, "");
  const secret = /(?:sk-[A-Za-z0-9_-]{15,}|(?:api[_ -]?key|access[_ -]?token|password|refresh[_ -]?token|client[_ -]?secret)\s*[:=]\s*\S{8,})/i;
  const history = []; // conversations deliberately in-memory, not saved to localStorage
  let draft = "";
  let working = false;
  const fmt = (v) => new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 0
  }).format(v);
  const readRequests = () => {
    try {
      const rows = JSON.parse(localStorage.getItem(localRequestsKey) || "[]");
      return Array.isArray(rows) ? rows.slice(-50) : [];
    } catch (_) { return []; }
  };
  const announce = (text) => { $("tlChatStatus").textContent = text; };
  function bubble(role, message) {
    const row = document.createElement("div");
    row.className = "tl-chat-bubble tl-chat-" + (role === "user" ? "user" : "assistant");
    const p = document.createElement("p");
    p.textContent = String(message).slice(0, 3500);
    row.appendChild(p);
    $("tlChatMessages").appendChild(row);
    $("tlChatMessages").scrollTop = $("tlChatMessages").scrollHeight;
    history.push({ role, content: p.textContent });
    if (history.length > 16) history.splice(0, history.length - 16);
  }
  function setField(id, value, low, high) {
    const field = $(id);
    if (!field || !Number.isFinite(value) || value < low || value > high) return false;
    field.value = String(value);
    field.dispatchEvent(new Event("change", { bubbles: true }));
    const paper = {};
    for (const target of ["scSymbol", "scCapital", "scCash", "scFast", "scSlow", "scStopPct"]) {
      if ($(target)) paper[target] = $(target).value;
    }
    try { localStorage.setItem(preferenceKey, JSON.stringify(paper)); } catch (_) {}
    return true;
  }
  function restorePreferences() {
    try {
      const saved = JSON.parse(localStorage.getItem(preferenceKey) || "{}");
      for (const id of ["scSymbol", "scCapital", "scCash", "scFast", "scSlow", "scStopPct"]) {
        if (!$(id) || typeof saved[id] !== "string") continue;
        if (id === "scSymbol" && /^[A-Z][A-Z0-9&.-]{0,24}$/.test(saved[id])) $(id).value = saved[id];
        if (id !== "scSymbol") {
          const n = Number(saved[id]);
          if (Number.isFinite(n) && n > 0 && n <= 100000000) $(id).value = saved[id];
        }
      }
    } catch (_) {}
  }
  function restoreLayout() {
    try {
      const prefs = JSON.parse(localStorage.getItem(uiKey) || "{}");
      const onboarding = document.querySelector(".onboarding-card");
      if (onboarding) onboarding.classList.toggle("tl-hidden-by-user", Boolean(prefs.hideOnboarding));
      document.body.classList.toggle("tl-compact-view", Boolean(prefs.compactView));
    } catch (_) { /* Invalid preferences do not block assistant. */ }
  }
  function updateLayout(option, selected) {
    const prefs = (() => {
      try { return JSON.parse(localStorage.getItem(uiKey) || "{}"); }
      catch (_) { return {}; }
    })();
    prefs[option] = selected;
    localStorage.setItem(uiKey, JSON.stringify(prefs));
    restoreLayout();
  }

  function parseMoney(raw) {
    const m = raw.replace(/,/g, "").toLowerCase().replace(/\s+/g, "")
      .match(/^(\d+(?:\.\d+)?)(k|lakh|lakhs)?$/);
    return m ? Number(m[1]) * (m[2] === "k" ? 1000 : m[2] ? 100000 : 1) : NaN;
  }
  function action(message) {
    const text = message.trim();
    if (/\b(?:hide|remove|collapse)\b[\s\S]{0,55}\b(?:dhan|onboarding|getting started|setup instructions)\b/i.test(text)) {
      updateLayout("hideOnboarding", true);
      return "Hidden the Dhan onboarding section in this browser. Say 'show Dhan onboarding' to restore it.";
    }
    if (/\b(?:show|restore|unhide)\b[\s\S]{0,55}\b(?:dhan|onboarding|getting started|setup instructions)\b/i.test(text)) {
      updateLayout("hideOnboarding", false);
      return "Dhan onboarding section restored in the dashboard.";
    }
    if (/\b(?:compact|smaller|reduce spacing|less space)\b/i.test(text) && /\b(?:layout|view|dashboard|make|use|switch)\b/i.test(text)) {
      updateLayout("compactView", true);
      return "Compact layout enabled for this browser. Say 'normal layout' to restore spacing.";
    }
    if (/\b(?:normal|default|restore)\s+(?:dashboard\s+)?(?:layout|view|spacing)\b/i.test(text)) {
      updateLayout("compactView", false);
      return "Default dashboard spacing restored.";
    }
    if (/\b(?:set|change|update|make|use)\b/i.test(text)) {
      const capital = text.match(/\b(?:capital|paper budget|simulated capital)\s*(?:to|at|as|of|=)?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?\s*(?:k|lakh|lakhs)?)/i);
      if (capital) {
        const before = Number($("scCapital").value);
        const value = parseMoney(capital[1]);
        if (!setField("scCapital", value, 1000, 100000000))
          return "Simulated capital must be between ₹1,000 and ₹10 crore.";
        if (Number($("scCash").value) === before) setField("scCash", value, 0, 100000000);
        return "Changed paper-trading capital to " + fmt(value) +
          ". This changes only browser research inputs; no money has been deposited.";
      }
      for (const [name, id, min, max] of [
        ["fast", "scFast", 2, 250], ["slow", "scSlow", 3, 500]
      ]) {
        const re = new RegExp("\\b" + name + "\\s*(?:MA|SMA|moving average)\\s*(?:to|at|=)?\\s*(\\d+)", "i");
        const match = text.match(re);
        if (!match) continue;
        const n = Number(match[1]);
        if (name === "fast" && n >= Number($("scSlow").value))
          return "Fast moving average must remain below the slow moving average.";
        if (name === "slow" && n <= Number($("scFast").value))
          return "Slow moving average must remain above the fast moving average.";
        return setField(id, n, min, max)
          ? "Updated " + name + " SMA to " + n + " sessions. Run a paper backtest to evaluate it."
          : "Invalid " + name + " SMA period.";
      }
      const stop = text.match(/\bstop[\s-]?(?:loss|pct|percentage)\s*(?:to|at|=)?\s*(\d+(?:\.\d+)?)\s*%/i);
      if (stop) {
        const n = Number(stop[1]);
        return setField("scStopPct", n, 0.1, 99)
          ? "Changed historical stop estimate to " + n + "%. No live order was changed."
          : "Stop percent must be 0.1%–99%.";
      }
      const symbol = text.match(/\b(?:set|change|use|update)\s+(?:(?:the|paper)\s+)?symbol\s+(?:to|as|=)\s*([A-Za-z][A-Za-z0-9&.-]{0,24})\b/i);
      if (symbol) {
        const value = symbol[1].toUpperCase();
        $("scSymbol").value = value;
        $("scSymbol").dispatchEvent(new Event("change", { bubbles: true }));
        return "Research symbol changed to " + value +
          ". Upload historical prices for that symbol before testing.";
      }
    }
    if (/\b(?:run|check|start)\s+(?:the\s+)?(?:diagnostics|audit|health)\b/i.test(text)) {
      $("diagRun")?.click();
      return "Started Audit & Diagnostics. Review the results in the dashboard.";
    }
    if (/\b(?:run|start)\s+(?:a\s+|the\s+)?(?:paper\s+)?backtest\b/i.test(text)) {
      $("scBacktestButton")?.click();
      return "Started the historical paper backtest. Results appear in Small Capital Lab.";
    }
    if (/\b(?:calculate|plan)\s+(?:a\s+|the\s+)?(?:paper\s+)?(?:position|trade)\b/i.test(text)) {
      $("scPlanButton")?.click();
      return "Started a simulated position calculation in Small Capital Lab.";
    }
    if (/\b(?:show|list|what(?:'s| is| are))\s+(?:the\s+)?(?:supported\s+)?api/i.test(text)) {
      $("diagnosticsCenter")?.scrollIntoView({ behavior: "smooth", block: "start" });
      return "TradeLens supports GET /health, GET /diagnostics/status, " +
        "POST /strategy/small-capital/plan, POST /strategy/small-capital/backtest, " +
        "and admin-authenticated diagnostics, assistant and broker-management endpoints. " +
        "The Diagnostics section lists details and limitations.";
    }
    if (/\b(?:how (?:do|can|to)|guide|tutorial|getting started|help me)\b/i.test(text) &&
      /\b(?:use|start|navigate|app|dashboard|tradelens)\b/i.test(text)) {
      return "Start here:\n1. Open Small Capital Lab. Set simulated capital (try ₹25,000).\n" +
        "2. Click Calculate Paper Position with an example entry price and stop.\n" +
        "3. Upload a historical daily OHLC CSV (Date,Open,High,Low,Close) or use clearly labelled synthetic demo data.\n" +
        "4. Click Run Paper Backtest, then inspect return, max drawdown and estimated costs.\n" +
        "5. Use Audit & Diagnostics to check API health.\n" +
        "6. Use this chat to adjust capital/SMA or request a new app feature.\n" +
        "No live broker orders are enabled, and profits are not guaranteed.";
    }
    return null;
  }
  function offlineReply(message) {
    if (/\b(?:how|explain|what|why|guide|teach|tutorial)\b/i.test(message) &&
      /\b(?:risk|drawdown|trade|profit|loss)\b/i.test(message))
      return "For paper trading, start with a simulated budget and limit exposure. " +
        "Small Capital Lab estimates position size and stop loss; the backtest estimates strategy return and drawdown. " +
        "These estimates exclude some trading costs and cannot guarantee daily income.";
    if (/\b(?:error|debug|not working|fail|logs)\b/i.test(message))
      return "Select Run Diagnostics to check the Render backend. " +
        "If you're an admin, Unlock Tools and Save Backend Audit. " +
        "You can export sanitized logs without revealing keys.";
    if (/\b(?:ollama|ai|model)\b/i.test(message))
      return "This assistant works in guided mode without a model. " +
        "For flexible AI replies, the Render backend can be configured with " +
        "an OpenAI key or an accessible Ollama endpoint. Model settings must be server-side.";
    return "I can guide this app and make safe paper-input changes immediately. " +
      "Try 'How do I use this app?', 'Set capital to 30000', 'Set fast MA to 15', " +
      "'Run diagnostics' or 'Show supported APIs'. To change the app's code, " +
      "describe the feature and press Save request. Requests do not automatically deploy.";
  }
  async function post(path, payload) {
    const controller = new AbortController();
    const deadline = setTimeout(() => controller.abort(), 20000);
    try {
      const res = await fetch(root() + path, {
        method: "POST", signal: controller.signal,
        headers: { "Content-Type": "application/json",
          "X-TradeLens-Admin-Token": adminToken() },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error("HTTP " + res.status);
      return data;
    } finally { clearTimeout(deadline); }
  }
  async function send(message) {
    if (working) return;
    const value = message.trim();
    if (!value) return;
    if (secret.test(value)) {
      announce("Do not paste passwords, broker tokens or API keys into chat.");
      return;
    }
    working = true;
    $("tlChatSend").disabled = true;
    draft = value;
    bubble("user", value);
    $("tlChatInput").value = "";
    announce("Preparing a response…");
    try {
      const localAction = action(value);
      if (localAction) {
        bubble("assistant", localAction);
        announce("Browser research settings updated, or requested check started.");
      } else if (adminToken()) {
        try {
          const context = history.slice(0, -1).slice(-8).map(({ role, content }) => ({ role, content }));
          const result = await post("/assistant/chat", { message: value, history: context });
          bubble("assistant", result.reply || "No reply returned.");
          announce(result.mode === "ai" ? "AI guidance. No code or trades were executed." :
            "Guided reply. No code or trades were executed.");
        } catch (_) {
          bubble("assistant", offlineReply(value));
          announce("Server assistant unavailable; browser guidance provided instead.");
        }
      } else {
        bubble("assistant", offlineReply(value));
        announce("Guided mode. Unlock Tools with your admin token for server-side AI.");
      }
    } finally { working = false; $("tlChatSend").disabled = false; }
  }
  function saveLocalRequest(text) {
    const changes = readRequests();
    const entry = { created_at: new Date().toISOString(), description: text, status: "local_draft" };
    changes.push(entry);
    localStorage.setItem(localRequestsKey, JSON.stringify(changes.slice(-50)));
    return entry;
  }
  async function saveRequest() {
    const description = ($("tlChatInput").value || draft).trim();
    if (description.length < 5 || description.length > 2000 || secret.test(description)) {
      announce("Describe the requested change in 5–2000 characters, without credentials.");
      return;
    }
    // Persist to backend only with authenticated owner/admin session.
    if (adminToken()) {
      try {
        const response = await post("/assistant/requests", { description });
        bubble("assistant", "Saved change request #" + response.request_id +
          " on Render for development review. It has NOT automatically updated the deployed app.");
        announce("Saved on backend.");
        return;
      } catch (_) { /* explicit local fallback below */ }
    }
    try {
      saveLocalRequest(description);
      bubble("assistant", "Saved a LOCAL browser draft. Export requests to share it " +
        "for implementation, or enter your admin token to save it to Render.");
      announce("Saved locally, not on the server.");
    } catch (_) {
      announce("Browser storage unavailable. Copy your request text manually.");
    }
  }
  function exportRequests() {
    const contents = JSON.stringify({
      exported_at: new Date().toISOString(), application: "TradeLens AI",
      status: "Unimplemented feature proposals, not deployed code",
      requests: readRequests()
    }, null, 2);
    const url = URL.createObjectURL(new Blob([contents], { type: "application/json" }));
    const a = document.createElement("a");
    a.href = url; a.download = "tradelens-feature-requests.json";
    a.click(); URL.revokeObjectURL(url);
    announce("Local feature requests exported.");
  }
  function visible(open) {
    panel.hidden = !open;
    $("tlChatLauncher").setAttribute("aria-expanded", String(open));
    if (open) $("tlChatInput").focus();
  }
  $("tlChatLauncher").addEventListener("click", () => visible(panel.hidden));
  $("tlChatClose").addEventListener("click", () => visible(false));
  $("tlChatForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    await send($("tlChatInput").value);
  });
  $("tlChatInput").addEventListener("keydown", async (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      await send($("tlChatInput").value);
    }
  });
  for (const button of document.querySelectorAll("[data-tl-prompt]")) {
    button.addEventListener("click", () => send(button.getAttribute("data-tl-prompt") || ""));
  }
  $("tlChatSave").addEventListener("click", saveRequest);
  $("tlChatExport").addEventListener("click", exportRequests);
  $("tlChatClear").addEventListener("click", () => {
    history.length = 0;
    draft = "";
    $("tlChatMessages").replaceChildren();
    bubble("assistant", "Chat cleared. Ask how to use any feature or tell me what to adjust.");
  });
  restorePreferences();
  restoreLayout();
  bubble("assistant", "Welcome! Ask 'How do I use this app?' for a walkthrough. " +
    "I can change safe paper-trading inputs, guide troubleshooting and save development requests.");
})();
