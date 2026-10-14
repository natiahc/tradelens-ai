# TradeLens Assistant — chat-driven app guidance

The TradeLens Assistant is available via the floating **Ask TradeLens** button
on the existing Vercel dashboard. It is an **advisory and safe-configuration
assistant**, not an autonomous coding/deployment or trading agent.

## What the user can ask

- **"How do I use this app?"** → a six-step walkthrough of Small Capital Lab,
  historical CSVs, paper backtests, diagnostics and saved change requests.
- **"Set capital to 30000"** → instantly changes simulated capital in this
  browser (and updates simulated available cash if it matched the old capital).
- **"Set fast MA to 15"**, **"Set slow MA to 60"**, **"Set stop loss to 2%"** →
  changes local research inputs subject to input constraints.
- **"Set symbol to INFY"** → updates the research symbol.
- **"Run diagnostics"**, **"Run backtest"**, **"Calculate paper position"** →
  clicks the corresponding existing dashboard action.
- **"Hide Dhan onboarding"**, **"Show Dhan onboarding"**,
  **"Use compact dashboard layout"**, **"Normal layout"** →
  alters local layout without deploying.
- **"Show supported APIs"** → explains API support and directs the user to
  Audit & Diagnostics.
- **"Add an RSI strategy and performance chart"** → the assistant explains
  the requirements. Selecting **Save request** puts the feature request in
  the admin-protected Render SQLite request queue. If not authenticated,
  it saves a local browser draft instead; **Export requests** downloads it.

A chat request NEVER modifies backend code, creates a PR, deploys to Vercel
or Render, modifies broker credentials, or places a live trade.
Implementation requests remain **proposed** until a developer reviews and
implements them. The assistant is not a replacement for a supervised coding
agent.

## Security and privacy

- Operational chat and shared request storage use existing
  `TRADELENS_ADMIN_TOKEN` header authentication.
- Enter admin token in dashboard **Unlock Tools**. The app stores it in
  `sessionStorage` for the browser tab only, not in persistent localStorage.
- Browser-side guided chat and local research controls work without a token.
- Chat history is held in memory and is cleared when the page reloads.
- Avoid entering private API credentials, broker tokens, account identifiers
  or passwords in chat. Secret-shaped inputs are rejected.
- Saved requests must not contain credentials.
- Optional AI messages go to the configured AI endpoint. If no compatible
  model is reachable, guided mode continues to work.
- API replies are displayed with `textContent` and not rendered as HTML.

## Optional AI model: Ollama (self-hosted/remote)

Ollama can serve a local model, but the **existing Render backend must reach
the Ollama service over the network**. `http://localhost:11434` on your
laptop means your *laptop*, not the Render container. Do not expose an
unauthenticated Ollama port to the public internet.

Configure **on the same existing Render backend service** using protected
environment variables:

```env
TRADELENS_CHAT_PROVIDER=ollama
OLLAMA_BASE_URL=https://your-authenticated-ollama-host.example
OLLAMA_MODEL=llama3.2
OLLAMA_API_KEY=          # optional, if your securely hosted endpoint uses bearer auth
```

The exact `OLLAMA_MODEL` must already be installed and available on that
server. TradeLens sends non-streaming `POST /api/chat` requests with
a time limit and falls back to guided replies on connection failures.
A local Ollama process is **not** provisioned or started by this project.
Running large models on Render Starter is not assumed to be feasible.

For a hosted OpenAI model instead:

```env
TRADELENS_CHAT_PROVIDER=openai
OPENAI_API_KEY=your-server-side-secret
TRADELENS_CHAT_MODEL=gpt-4.1-mini
```

Set `TRADELENS_CHAT_PROVIDER=auto` to try configured Ollama first, then
OpenAI, then guided mode; `guided` disables all external AI calls. Never
place an API key in Vercel frontend JavaScript or GitHub.

The AI response has no repository, deployment, trading or admin tools. It
only explains, troubleshoots and proposes changes; deterministic browser
commands handle the limited safe changes above.

## APIs provided by existing Render backend

- `POST /assistant/chat`: authenticated advisory response, with
  `mode` equal to `guided`, `ollama` or `openai`.
- `POST /assistant/requests`: authenticated save of a proposed request.
- `GET /assistant/requests`: authenticated list of saved proposals.

All other existing APIs, including diagnostics, broker management,
paper position sizing and CSV backtest, remain on the same service.

## Deployment and verification

- Backend: existing `tradelens-ai-backend` Render service.
- Frontend: existing `tradelens-ai` Vercel project and domain.
- Code: `natiahc/tradelens-ai`, branch `main`; normal GitHub
  auto-deploy workflow should update the existing services if enabled.
- GitHub Actions runs Python backend tests, JS syntax checks and presence of
  required assistant HTML elements.

For full AI answers on Render, configure **both** the admin token and
the model provider environment; otherwise the browser offers guided mode.
