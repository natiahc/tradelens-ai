# Deployment Guide

This project is set up to use:

- **Vercel** for the static dashboard frontend
- **Render** for the FastAPI backend

## 1. Deploy backend on Render

The repository includes a `render.yaml` blueprint.

### What Render will do
- build from `backend/`
- install the backend package
- run FastAPI with Uvicorn
- attach a persistent disk for SQLite

### Required environment variable
You must set a valid Fernet key for encrypted broker credential storage.

Generate one locally:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Then set it in Render as:

- `TRADELENS_MASTER_KEY`

### Important backend settings
Configured in `render.yaml`:

- `TRADELENS_DATABASE_PATH=/var/data/tradelens_ai.db`
- persistent disk mounted at `/var/data`

### Recommended production CORS setting
Set your Vercel frontend URL in Render using:

- `TRADELENS_CORS_ORIGINS=https://your-vercel-app.vercel.app`

If you have multiple frontend origins, use a comma-separated list:

- `TRADELENS_CORS_ORIGINS=https://your-vercel-app.vercel.app,https://preview-domain.vercel.app`

For local development, you can leave it unset and the backend will allow all origins.

### Render deploy steps
1. Push the repository to GitHub
2. In Render, choose **New +** -> **Blueprint**
3. Select this GitHub repository
4. Render will detect `render.yaml`
5. Add the missing secret value for `TRADELENS_MASTER_KEY`
6. Add `TRADELENS_CORS_ORIGINS` with your Vercel domain
7. Deploy

After deploy, verify:

- `https://your-render-service.onrender.com/health`

## 2. Deploy frontend on Vercel

The repository includes a root `vercel.json` for the static dashboard.

### Vercel import settings
When importing into Vercel:

- **Framework Preset**: Other
- **Root Directory**: repository root
- **Build Command**: leave empty
- **Install Command**: leave empty
- **Output Directory**: handled by `vercel.json`

### Vercel deploy steps
1. Import the GitHub repository into Vercel
2. Keep the project root at the repository root
3. Let Vercel use the existing `vercel.json`
4. Deploy

After deploy, open the dashboard URL.

## 3. Connect frontend to backend

In the dashboard UI:

1. Open **UI Settings**
2. Set **API Base URL** to your Render backend URL
   - example: `https://your-render-service.onrender.com`
3. Save UI Settings

## 4. Notes

- SQLite is acceptable for initial deployment because Render persistent disk is configured
- for larger scale or multi-instance deployment, move to Postgres later
- broker credentials are stored server-side and encrypted at rest using `TRADELENS_MASTER_KEY`
- production CORS is now configurable through `TRADELENS_CORS_ORIGINS`
- `vercel.json` already points Vercel at `frontend/dashboard`
