# Deployment Guide — Groww RAG Chatbot

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐
│   Frontend      │ ──API──▶│    Backend       │
│   (Vercel)      │         │    (Render)      │
│   Next.js 14    │         │    FastAPI       │
└─────────────────┘         └──────────────────┘
        │                           │
        ▼                           ▼
   Vercel CDN               Vector Store (JSON)
                            Groq LLM API
```

- **Backend**: FastAPI on [Render](https://render.com) (Python 3.11)
- **Frontend**: Next.js 14 on [Vercel](https://vercel.com)
- **CI/CD**: GitHub Actions (daily scraping cron + manual dispatch)

---

## Prerequisites

| Requirement | Details |
|---|---|
| GitHub account | Repository: `github.com/hey2308/Groww-RAG-chatbot` |
| Render account | Free tier sufficient (Web Service) |
| Vercel account | Free tier sufficient |
| Groq API key | [console.groq.com](https://console.groq.com) — required for LLM responses |
| OpenAI API key | Optional fallback — [platform.openai.com](https://platform.openai.com) |

---

## Step 1 — Backend Deployment (Render)

### 1.1 Create a New Web Service

1. Go to [render.com](https://render.com) → **New +** → **Web Service**
2. Connect your GitHub repository: `Groww-RAG-chatbot`
3. Configure the service:

| Setting | Value |
|---|---|
| **Name** | `groww-rag-backend` (or any name) |
| **Region** | Choose closest to you (e.g., Singapore, Oregon) |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free |

### 1.2 Environment Variables

Add these in **Settings → Environment Variables**:

| Key | Value | Required |
|---|---|---|
| `GROQ_API_KEY` | Your Groq API key | **Yes** |
| `OPENAI_API_KEY` | Your OpenAI API key | No |
| `PORT` | `8000` (Render sets this automatically) | Auto |
| `ENVIRONMENT` | `production` | No |

### 1.3 Deploy

1. Click **Create Web Service**
2. Wait for the build to complete (~2-3 minutes)
3. Once deployed, note your backend URL: `https://groww-rag-backend.onrender.com`
4. Test the health endpoint:
   ```
   https://groww-rag-backend.onrender.com/api/health
   ```

### 1.4 Populate Vector Store

The vector store is populated by the GitHub Actions daily scraping pipeline. After the first successful pipeline run, the `vector_store/` directory will contain `store.json` with fund data.

To manually trigger a pipeline run:
1. Go to **GitHub → Actions → Daily Data Scraping → Run workflow**
2. Wait for the pipeline to complete
3. Pull the latest data and push:
   ```bash
   git pull origin main
   git add backend/vector_store/
   git commit -m "Update vector store data"
   git push origin main
   ```

> **Note**: The `vector_store/` directory is in `.gitignore` by default. For production, you may want to either:
> - Include `store.json` in the repo (remove from `.gitignore`)
> - Run the rebuild script on Render via a post-deploy hook

---

## Step 2 — Frontend Deployment (Vercel)

### 2.1 Create a New Project

1. Go to [vercel.com](https://vercel.com) → **Add New → Project**
2. Import your GitHub repository: `Groww-RAG-chatbot`
3. Vercel auto-detects Next.js. Configure:

| Setting | Value |
|---|---|
| **Root Directory** | `frontend` |
| **Framework Preset** | Next.js |
| **Build Command** | `next build` |
| **Output Directory** | `.next` |
| **Install Command** | `npm install` |

### 2.2 Environment Variables

Add these in **Settings → Environment Variables** (before deploying):

| Key | Value | Required |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://groww-rag-backend.onrender.com` | **Yes** |

> **Important**: Replace the URL with your actual Render backend URL from Step 1.3.

### 2.3 Deploy

1. Click **Deploy**
2. Wait for the build (~2 minutes)
3. Your frontend will be available at: `https://groww-rag-chatbot.vercel.app`

### 2.4 Verify

1. Open the frontend URL
2. Type a test query like *"What is the expense ratio of HDFC Large Cap Fund?"*
3. Confirm the chatbot responds with factual data and source citations

---

## Step 3 — Connect Frontend to Backend (CORS)

The backend CORS is configured to allow all origins by default (`allow_origins=["*"]`). For production, restrict it to your Vercel domain:

**File**: `backend/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.vercel.app"],  # Replace with your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push — Render will auto-deploy.

---

## Step 4 — GitHub Actions CI/CD

The repository includes a daily scraping pipeline (`.github/workflows/data-scraping.yml`):

| Trigger | Schedule | Description |
|---|---|---|
| Cron | Daily at 2:00 AM UTC | Scrapes Groww.in, cleans, chunks, embeds, and stores fund data |
| Manual | GitHub Actions → Run workflow | On-demand pipeline trigger |

### GitHub Secrets (Optional)

| Secret | Purpose |
|---|---|
| `GROQ_API_KEY` | For pipeline LLM operations |
| `NOTIFICATION_WEBHOOK` | Slack/Discord webhook for pipeline status notifications |

---

## Environment Variables Summary

### Backend (Render)

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxx       # optional
PORT=8000
ENVIRONMENT=production
```

### Frontend (Vercel)

```env
NEXT_PUBLIC_API_URL=https://groww-rag-backend.onrender.com
```

---

## Troubleshooting

### Backend won't start on Render
- Check the build logs for missing dependencies
- Ensure `requirements.txt` is in the `backend/` directory
- Verify `GROQ_API_KEY` is set in environment variables

### Frontend shows "Network Error"
- Verify `NEXT_PUBLIC_API_URL` points to your Render backend URL (not `localhost`)
- Check that the backend health endpoint responds: `curl https://your-backend.onrender.com/api/health`
- Ensure CORS allows your Vercel domain

### Chatbot returns empty or generic responses
- The vector store may be empty — trigger the GitHub Actions pipeline manually
- Verify `GROQ_API_KEY` is valid and has quota remaining

### Render free tier spins down
- Render free instances sleep after 15 minutes of inactivity
- First request after sleep takes ~30-50 seconds (cold start)
- Upgrade to a paid plan for always-on instances

---

## Deployment Checklist

- [ ] Groq API key obtained from console.groq.com
- [ ] Backend deployed on Render with environment variables
- [ ] Backend health endpoint returns 200
- [ ] Vector store populated (GitHub Actions pipeline ran successfully)
- [ ] Frontend deployed on Vercel with `NEXT_PUBLIC_API_URL` set
- [ ] Chatbot responds to test queries
- [ ] CORS configured for production Vercel domain
