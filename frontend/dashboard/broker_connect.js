/* Owner-only Dhan OAuth and data retrieval. The AI never receives any secret. */
(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  if (!$("tlDhanOAuthStart")) return;
  const apiUrl = () => ($("apiBaseUrl")?.value.trim() ||
    localStorage.getItem("tradelensApiBaseUrl") ||
    "https://tradelens-ai-t8za.onrender.com").replace(/\/+$/, "");
  const token = () => sessionStorage.getItem("tradelensAdminToken") || "";
  const setStatus = msg => { $("tlDhanStatus").textContent = msg; };
  const pendingKey = "tradelensDhanPendingOauthState";
  let busy = false;

  async function req(path, method = "GET", body = null) {
    if (!token()) throw new Error("Open Advanced tools and unlock with your TradeLens admin token first.");
    const controller = new AbortController();
    const deadline = setTimeout(() => controller.abort(), 18000);
    try {
      const response = await fetch(apiUrl() + path, {
        method,
        signal: controller.signal,
        headers: {
          "X-TradeLens-Admin-Token": token(),
          "Content-Type": "application/json",
        },
        ...(body ? {body: JSON.stringify(body)} : {}),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(typeof result.detail === "string" ? result.detail.slice(0, 170) :
          "Backend request rejected (HTTP " + response.status + ")");
      }
      return result;
    } finally {clearTimeout(deadline);}
  }

  function openSetup(focusId = "brokerCredentialsClientId") {
    $("tlAdvancedMode")?.click();
    $("brokerCredentialsName").value = "dhan";
    $("brokerCredentialsName").dispatchEvent(new Event("change", {bubbles: true}));
    $("brokerCredentialsName").closest("section")?.scrollIntoView({
      behavior: "smooth", block: "start"
    });
    $(focusId)?.focus();
    setStatus("Enter Dhan client ID, API key and API secret here, then Save. Configure the Dhan redirect URL to this site's root URL. Never enter the keys in AI chat.");
  }

  async function start() {
    if (busy) return;
    busy = true;
    $("tlDhanOAuthStart").disabled = true;
    setStatus("Creating a secure Dhan consent session…");
    try {
      const result = await req("/broker/dhan/oauth/start", "POST");
      const destination = new URL(result.login_url);
      if (destination.origin !== "https://auth.dhan.co" ||
          destination.pathname !== "/login/consentApp-login") {
        throw new Error("The broker returned an unexpected login destination.");
      }
      sessionStorage.setItem(pendingKey, result.flow_state);
      setStatus("Opening official Dhan sign-in. Complete login and 2FA there.");
      window.location.assign(destination.href);
    } catch (error) {
      setStatus("Unable to connect: " + error.message);
      $("tlAdvancedMode")?.click();
      busy = false;
      $("tlDhanOAuthStart").disabled = false;
    }
  }

  async function completeOnReturn() {
    const current = new URL(window.location.href);
    const grant = current.searchParams.get("tokenId");
    if (!grant) return;
    // Remove the one-time callback token immediately from the browser URL,
    // history, screenshots and navigations. Never send it to Ollama.
    current.searchParams.delete("tokenId");
    window.history.replaceState({}, "", current.pathname + current.search + current.hash);
    const flowState = sessionStorage.getItem(pendingKey) || "";
    sessionStorage.removeItem(pendingKey);
    if (!flowState) {
      setStatus("Dhan returned but the original login session wasn't found. Start again from this browser tab.");
      return;
    }
    setStatus("Finalizing Dhan connection…");
    try {
      const result = await req("/broker/dhan/oauth/complete", "POST", {
        flow_state: flowState, token_id: grant,
      });
      setStatus(result.message + " Token expires: " + result.expires_at);
    } catch (error) {
      setStatus("Dhan connection could not be completed: " + error.message);
    }
  }

  async function fetchCategory(category = "holdings") {
    if (busy) return "Another broker request is already running.";
    if (!["funds", "holdings", "positions", "orders", "profile"].includes(category)) {
      return "Only read-only account categories are supported.";
    }
    busy = true;
    setStatus("Fetching Dhan " + category + " (read only)…");
    try {
      const response = await req("/broker/dhan/overview/" + category);
      const rows = response.data;
      const count = Array.isArray(rows) ? rows.length : null;
      const output = $("tlDhanOverview");
      output.hidden = false;
      output.textContent = JSON.stringify({
        broker: response.broker, category, read_only: response.read_only,
        data: rows, notice: response.notice,
      }, null, 2);
      setStatus("Fetched Dhan " + category + ". This is private account data—not an AI reply or a trade.");
      output.scrollIntoView({behavior: "smooth", block: "nearest"});
      return count == null ? "Fetched Dhan " + category + ". Private details are shown in the Connect Dhan area."
        : "Fetched " + count + " Dhan " + category + " record(s), shown in the Connect Dhan section.";
    } catch (error) {
      setStatus("Dhan " + category + " fetch failed: " + error.message);
      return "Unable to fetch " + category + ": " + error.message;
    } finally {busy = false;}
  }

  $("tlDhanSetup").addEventListener("click", () => openSetup());
  $("tlDhanOAuthStart").addEventListener("click", start);
  $("tlDhanHoldings").addEventListener("click", () => {fetchCategory("holdings");});

  // Safe functions may be called by explicit user intent from assistant.js.
  window.tradeLensBroker = {
    openSetup, start, fetchCategory,
    fillSecretField: (kind, value) => {
      const names = {
        "client id": "brokerCredentialsClientId",
        "api key": "brokerCredentialsApiKey",
        "api secret": "brokerCredentialsApiSecret",
        "access token": "brokerCredentialsAccessToken",
      };
      const target = names[kind];
      if (!target || !value || value.length > 4000) return false;
      openSetup(target);
      $(target).value = value;
      return true;
    },
  };

  // Return from Dhan's configured redirect URL on the same Vercel site.
  completeOnReturn();
})();
