# TradeLens — simple AI assistant, search and Dhan connection

The existing Vercel dashboard has **Simple view** by default: Try demo,
Upload price data, Ask TradeLens, and optional Connect Dhan. All simulated
trading features operate without a broker and do not place real orders.

## How the assistant works

- **Guide:** "How do I use this app?" describes the actual dashboard.
- **Apply:** "Set capital to 30000", "Set fast MA to 15", "Use compact
  dashboard layout" immediately apply browser-level paper/UI changes.
- **Credentials:** "Set Dhan API key to ..." fills only the password field,
  redacts the message, and never sends the key to Ollama, OpenAI, or saved chat.
  Review and click Save under Broker Credentials. Never paste PIN/OTP/password.
- **Search:** "Search the web for NSE data provider APIs" runs a server-side
  Brave search when `BRAVE_SEARCH_API_KEY` is configured, returning attributed
  source links. Without one, the app links to external search honestly.
- **Read-only broker:** "Fetch my Dhan holdings", "Fetch my funds",
  "Fetch my orders" retrieves via the protected server and shows information
  only in the account section, not in the AI prompt.
- **App changes:** "Add RSI alerts" can save a proposed development request.
  Changes to repository code, authentication, server secrets, or deployment
  require developer implementation/review and must not be auto-executed by
  an untrusted language-model response.
- **Diagnostics:** "Run diagnostics" invokes the existing sanitized checks.
  Read-only app insight is available. Raw infrastructure logs are retrieved
  separately through the authorized Render/Vercel accounts.

The assistant is grounded with a curated local handbook in
`backend/src/tradelens_ai/services/assistant_knowledge.py`. This is an
inexpensive retrieval-based way to teach a model how the app works; it
does **not** require GPU fine-tuning or training data, and it can be updated
as app features change.

## Optional model: Ollama, no model UI for end users

You do not need to operate Ollama in the browser. The Render backend uses
the model if one is reachable and configured; otherwise guided replies
continue to work.

Optional Render environment variables (set privately in Render):

```
TRADELENS_CHAT_PROVIDER=ollama
OLLAMA_BASE_URL=https://your-secure-model-host.example
OLLAMA_MODEL=llama3.2
OLLAMA_API_KEY=          # optional if your model host uses bearer authentication
```

The host must be reachable from Render. An Ollama service on your laptop
at 127.0.0.1:11434 is **not** reachable from a cloud Render container.
Do not publicly expose an unauthenticated Ollama endpoint.

Alternative: use `OPENAI_API_KEY` on Render with
`TRADELENS_CHAT_PROVIDER=openai`. Do not put model keys in Vercel's
client-side environment or chat.

## Optional real web search

Set `BRAVE_SEARCH_API_KEY` on Render; the assistant queries Brave Search
over HTTPS, returning up to five links. Never assume an LLM alone fetched
current information. Externally sourced descriptions are untrusted content,
not executable instructions.

## Dhan: Connect account securely

For individual Dhan traders, the [official DhanHQ authentication documentation]
(https://dhanhq.co/docs/v2/authentication/) describes an API key/secret
consent flow: (1) generate consent, (2) user signs in on Dhan's website and
completes 2FA, (3) app exchanges a one-time token ID for an access token.

1. Set `TRADELENS_ADMIN_TOKEN` and a stable `TRADELENS_MASTER_KEY` on the
   existing Render backend. Both are required for secure credential storage.
2. In Dhan Web > Profile > Get Trading & Data APIs, create an API key/secret.
   Set the app redirect URL exactly to the frontend's home origin with
   trailing slash (the UI displays the URL).
3. In TradeLens, choose **Connect Dhan → Add API credentials**.
   Enter client ID, API key and API secret into protected **Broker
   Credentials**, then Save. This saves them encrypted server-side; never
   paste credentials into model prompts or exported log files.
4. Choose **Connect with Dhan** (or tell the assistant "Connect Dhan").
   TradeLens creates a one-time consent session and opens
   `https://auth.dhan.co/` for your own browser authentication.
5. After Dhan redirects to the frontend, TradeLens captures and removes the
   `tokenId` from its URL, then exchanges it on Render against the server's
   API secret and stores the short-lived Dhan access token encrypted.
6. Choose **Fetch my holdings**, or ask chat to fetch specific read-only
   categories: funds, holdings, positions, orders, profile.

**Limitations:** Dhan keys must be created by you; Dhan login/OTP cannot be
skipped or performed by Ollama. A pending OAuth flow is valid for 10 minutes
and single-use; Dhan controls token lifetime. An active token and brokerage
permissions are needed for account data. Market data subscriptions may cost
extra. The app is NOT authorized to place live trades via this chat.

## Existing deployment — no new project required

Keep `render.yaml` and `vercel.json` pointed at the existing backend and
frontend. GitHub CI checks Python tests and JavaScript syntax.
Render must configure the private environment keys; the Vercel deployment
needs authorization to verify that code is live. Publishing GitHub code is
not the same as a successful production deployment.

## Security limitations

- This is a single-owner, admin-token access model—not multi-user OAuth,
  registered OAuth provider management, or a production IAM platform.
- The repository may still be publicly visible; GitHub visibility must be
  changed by an admin, and past secrets (if leaked) must be rotated.
- Never enable `TRADELENS_ALLOW_LIVE_ORDERS` on a public installation.
- Sanitize logs; do not show detailed private holdings to a public visitor.
- AI-generated commands are NOT authorized instructions to execute arbitrary
  code, bypass broker login, change credentials, or submit trades.
- Daily profits cannot be promised. Use paper research and include costs,
  slippage, walk-forward validation and maximum drawdown in evaluations.
