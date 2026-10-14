/* Beginner-first homepage. Existing components stay mounted for legacy JS. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  if (!$("welcomeHome")) return;
  const modeKey = "tradelensDashboardModeV1";
  const simple = $("tlSimpleMode"), advanced = $("tlAdvancedMode");
  const scope = document.querySelector(".layout");

  function setMode(mode) {
    const isAdvanced = mode === "advanced";
    document.body.classList.toggle("tl-advanced-mode", isAdvanced);
    simple.setAttribute("aria-pressed", String(!isAdvanced));
    advanced.setAttribute("aria-pressed", String(isAdvanced));
    simple.classList.toggle("is-selected", !isAdvanced);
    advanced.classList.toggle("is-selected", isAdvanced);
    try {localStorage.setItem(modeKey, isAdvanced ? "advanced" : "simple");} catch (_) {}
  }
  function goToLab() {
    $("smallCapitalResearch").scrollIntoView({behavior: "smooth", block: "start"});
  }
  simple.addEventListener("click", () => setMode("simple"));
  advanced.addEventListener("click", () => setMode("advanced"));

  $("tlTryDemo").addEventListener("click", () => {
    $("scDemoData").click();
    goToLab();
    $("scBacktestButton").focus();
  });
  $("tlUploadData").addEventListener("click", () => {
    goToLab();
    $("scCsvFile").focus();
    // Avoid forcing file dialogs from unexpected or automated clicks.
  });
  $("tlOpenAssistant").addEventListener("click", () => $("tlChatLauncher").click());

  function navigateToHiddenTools() {
    setMode("advanced");
    $("diagnosticsCenter").scrollIntoView({behavior: "smooth", block: "start"});
  }
  // Existing assistant "Run diagnostics" opens a section otherwise hidden in simple mode.
  $("diagRun")?.addEventListener("click", () => {
    if (!document.body.classList.contains("tl-advanced-mode")) navigateToHiddenTools();
  });

  async function probe() {
    const status = $("tlQuickStatus");
    const base = ($("apiBaseUrl")?.value.trim() ||
      localStorage.getItem("tradelensApiBaseUrl") ||
      "https://tradelens-ai-t8za.onrender.com").replace(/\/+$/, "");
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 7500);
      try {
        const res = await fetch(base + "/health", {signal: controller.signal, cache: "no-store"});
        if (!res.ok) throw new Error("Server error");
        status.textContent = "Practice server online";
        status.parentElement.classList.remove("tl-health-warning");
      } finally {clearTimeout(timer);}
    } catch (_) {
      status.textContent = "Server offline — check Advanced tools";
      status.parentElement.classList.add("tl-health-warning");
    }
  }
  $("saveApiBaseUrl")?.addEventListener("click", () => setTimeout(probe, 1000));
  setMode(localStorage.getItem(modeKey) === "advanced" ? "advanced" : "simple");
  probe();
})();
