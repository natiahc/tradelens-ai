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

### Render deploy steps
1. Push the repository to GitHub
2. In Render, choose **New +** -> **Blueprint**
3. Select this GitHub repository
4. Render will detect `render.yaml`
5. Add the missing secret value for `TRADELENS_MASTER_KEY`
6. Deploy

After deploy, verify:

- `https://your-render-service.onrender.com/health`

## 2. Deploy frontend on Vercel

The repository includes a root `vercel.json` for the static dashboard.

### Vercel deploy steps
1. Import the GitHub repository into Vercel
2. Vercel will use `vercel.json`
3. Deploy

After deploy, open the dashboard.

## 3. Connect frontend to backend

In the dashboard UI:

1. Open **UI Settings**
2. Set **API Base URL** to your Render backend URL
   - example: `https://your-render-service.onrender.com`
3. Save UI Settings

## 4. Recommended production follow-up

The backend currently allows broad CORS for development convenience.
Before production use, restrict CORS to your Vercel domain.

## 5. Notes

- SQLite is acceptable for initial deployment because Render persistent disk is configured
- for larger scale or multi-instance deployment, move to Postgres later
- broker credentials are stored server-side and encrypted at rest using `TRADELENS_MASTER_KEY`
