/* TradeLens Small Capital Lab — research only; never sends broker orders. */
(() => {
  "use strict";

  const DEFAULT_RENDER_API = "https://tradelens-ai-t8za.onrender.com";
  const $ = (id) => document.getElementById(id);
  const state = { bars: [], source: "" };
  const rupees = (n) => Number.isFinite(Number(n))
    ? new Intl.NumberFormat("en-IN", {
        style: "currency", currency: "INR", maximumFractionDigits: 2
      }).format(Number(n))
    : "—";
  const percentage = (n) => Number.isFinite(Number(n)) ? Number(n).toFixed(2) + "%" : "—";
  const value = (id) => Number($(id).value);
  const apiUrl = () => {
    const selected = $("apiBaseUrl").value.trim()
      || localStorage.getItem("tradelensApiBaseUrl")
      || DEFAULT_RENDER_API;
    return selected.replace(/\/+$/, "");
  };

  async function request(path, payload) {
    const response = await fetch(apiUrl() + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    let data;
    try {
      data = await response.json();
    } catch (_) {
      throw new Error("Backend response was not JSON (HTTP " + response.status + ").");
    }
    if (!response.ok) {
      throw new Error("HTTP " + response.status + ": " + JSON.stringify(data.detail || data));
    }
    return data;
  }

  const setText = (id, message) => { $(id).textContent = String(message); };

  async function plan() {
    const button = $("scPlanButton");
    button.disabled = true;
    setText("scPlanStatus", "Calculating paper-only position…");
    try {
      const payload = {
        symbol: $("scSymbol").value.trim().toUpperCase(),
        entry_price: value("scEntry"),
        stop_price: value("scStop"),
        capital_rupees: value("scCapital"),
        available_cash_rupees: value("scCash"),
        daily_realized_pnl_rupees: value("scDailyPnl"),
      };
      if (!payload.symbol || payload.capital_rupees <= 0 ||
          payload.entry_price <= 0 || payload.stop_price <= 0) {
        throw new Error("Enter a symbol, capital, entry price and stop price.");
      }
      const result = await request("/strategy/small-capital/plan", payload);
      setText("scQuantity", result.quantity + " shares");
      setText("scCashRequired", rupees(result.entry_cash_needed_rupees));
      setText("scEstimatedLoss", rupees(result.estimated_stop_loss_rupees));
      setText("scRemainingRisk", rupees(result.remaining_daily_risk_rupees));
      setText("scPlanStatus", (result.approved ? "Plan: " : "Blocked: ") +
        result.reason + ". Paper only. Indicative input prices; actual losses can exceed estimates.");
    } catch (error) {
      setText("scPlanStatus", "Unable to calculate: " + error.message);
    } finally {
      button.disabled = false;
    }
  }

  function parseCsvLine(line) {
    const result = [];
    let field = "";
    let quoted = false;
    for (let i = 0; i < line.length; i += 1) {
      const ch = line[i];
      if (ch === '"') {
        if (quoted && line[i + 1] === '"') { field += '"'; i += 1; }
        else { quoted = !quoted; }
      } else if (ch === "," && !quoted) {
        result.push(field.trim()); field = "";
      } else { field += ch; }
    }
    if (quoted) throw new Error("Unterminated quoted CSV column.");
    result.push(field.trim());
    return result;
  }

  function validateBars(rows) {
    if (rows.length < 5) throw new Error("Upload at least five daily price bars.");
    if (rows.length > 2000) throw new Error("Maximum 2,000 daily price bars.");
    let previousDate = "";
    for (const row of rows) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(row.date) ||
          !Number.isFinite(Date.parse(row.date)) || row.date <= previousDate) {
        throw new Error("Dates must be valid, increasing YYYY-MM-DD with no duplicates.");
      }
      previousDate = row.date;
      const nums = [row.open, row.high, row.low, row.close];
      if (nums.some((p) => !Number.isFinite(p) || p <= 0) ||
          row.high < Math.max(row.open, row.close) ||
          row.low > Math.min(row.open, row.close)) {
        throw new Error("OHLC values must be positive and their high/low consistent.");
      }
    }
    return rows;
  }

  function parseCsv(csvText) {
    const lines = csvText.replace(/^\uFEFF/, "").split(/\r?\n/).filter((line) => line.trim());
    if (lines.length < 2) throw new Error("CSV is empty.");
    const headings = parseCsvLine(lines.shift()).map((header) => header.toLowerCase());
    const indices = ["date", "open", "high", "low", "close"].map((key) => headings.indexOf(key));
    if (indices.some((index) => index < 0)) {
      throw new Error("CSV columns must include Date,Open,High,Low,Close.");
    }
    return validateBars(lines.map((line) => {
      const parts = parseCsvLine(line);
      const entry = {};
      ["date", "open", "high", "low", "close"].forEach((key, index) => {
        entry[key] = index === 0 ? parts[indices[index]] : Number(parts[indices[index]]);
      });
      return entry;
    }));
  }

  function demoBars() {
    const bars = [];
    const cursor = new Date("2025-01-01T00:00:00Z");
    let previousClose = 100;
    while (bars.length < 160) {
      if (cursor.getUTCDay() !== 0 && cursor.getUTCDay() !== 6) {
        const i = bars.length;
        // Deterministic synthetic price path; these are NOT actual stock prices.
        const close = Math.max(25, 100 + i * 0.12
          + 12 * Math.sin(i / 17) + 2.5 * Math.sin(i / 3));
        bars.push({
          date: cursor.toISOString().slice(0, 10),
          open: Number(previousClose.toFixed(3)),
          high: Number((Math.max(previousClose, close) * 1.004).toFixed(3)),
          low: Number((Math.min(previousClose, close) * 0.996).toFixed(3)),
          close: Number(close.toFixed(3)),
        });
        previousClose = close;
      }
      cursor.setUTCDate(cursor.getUTCDate() + 1);
    }
    return bars;
  }

  function plotEquity(equity) {
    const svg = $("scCurve");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    if (!Array.isArray(equity) || equity.length < 2) return;
    const min = Math.min(...equity), max = Math.max(...equity);
    const span = Math.max(max - min, 1);
    const coordinates = equity.map((point, index) => {
      const x = 8 + (index / (equity.length - 1)) * 624;
      const y = 150 - (Number(point) - min) / span * 140;
      return x.toFixed(2) + "," + y.toFixed(2);
    });
    const path = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    path.setAttribute("points", coordinates.join(" "));
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", "#147d64");
    path.setAttribute("stroke-width", "2.5");
    path.setAttribute("vector-effect", "non-scaling-stroke");
    svg.appendChild(path);
    svg.setAttribute("aria-label", "Simulated equity curve ranging from " +
      rupees(min) + " to " + rupees(max));
  }

  async function backtest() {
    const button = $("scBacktestButton");
    button.disabled = true;
    setText("scBacktestStatus", "Running historical paper backtest…");
    try {
      if (!state.bars.length) throw new Error("Upload CSV data or load the synthetic demo.");
      const fast = value("scFast"), slow = value("scSlow");
      if (fast >= slow || state.bars.length <= slow) {
        throw new Error("Require fast < slow, and more price bars than the slow average.");
      }
      const result = await request("/strategy/small-capital/backtest", {
        symbol: $("scSymbol").value.trim().toUpperCase(),
        capital_rupees: value("scCapital"),
        fast_days: fast,
        slow_days: slow,
        stop_pct: value("scStopPct") / 100,
        bars: state.bars,
      });
      setText("scReturn", percentage(result.total_return_pct));
      setText("scDrawdown", percentage(result.max_drawdown_pct));
      setText("scTrades", result.closed_trades);
      setText("scFinalEquity", rupees(result.final_equity_rupees));
      plotEquity(result.equity_curve);
      setText("scBacktestStatus",
        (state.source === "demo" ? "SYNTHETIC DEMO ONLY — NOT REAL MARKET DATA.\n" : "USER-SUPPLIED HISTORICAL DATA.\n") +
        "Simulated " + result.symbol + ", " + result.first_date + " to " + result.last_date +
        ". Winning closed trades: " + result.winning_closed_trades +
        ". Open shares: " + result.open_position_shares + ".\n" +
        result.assumptions.join("\n"));
    } catch (error) {
      setText("scBacktestStatus", "Backtest not completed: " + error.message);
    } finally {
      button.disabled = false;
    }
  }

  $("scPlanButton").addEventListener("click", plan);
  $("scDemoData").addEventListener("click", () => {
    state.bars = demoBars();
    state.source = "demo";
    $("scCsvFile").value = "";
    setText("scDataStatus", "Loaded " + state.bars.length +
      " SYNTHETIC demo bars. Not market data — for UI testing only.");
  });
  $("scCsvFile").addEventListener("change", async (event) => {
    const file = event.target.files && event.target.files[0];
    state.bars = [];
    state.source = "";
    if (!file) return;
    try {
      if (file.size > 1024 * 1024) throw new Error("CSV must be under 1 MB.");
      state.bars = parseCsv(await file.text());
      state.source = "uploaded";
      setText("scDataStatus", "Loaded " + state.bars.length +
        " rows from " + file.name + ". Check data quality and adjusted-price consistency.");
    } catch (error) {
      setText("scDataStatus", "CSV rejected: " + error.message);
    }
  });
  $("scBacktestButton").addEventListener("click", backtest);
})();
