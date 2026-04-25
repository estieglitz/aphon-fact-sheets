# APHON Medication Fact Sheet Generator — Deployment Guide

A web app for generating custom PDF packets of APHON Hematology/Oncology
Medication Fact Sheets (5th Edition) in English or Spanish.

---

## What's in this folder

```
aphon_deploy/
├── app.py            ← Flask application (all code + HTML UI in one file)
├── requirements.txt  ← Python dependencies
├── render.yaml       ← Render.com one-click config
├── Procfile          ← Railway.app config
├── source.pdf        ← ⚠️  YOU MUST ADD THIS (the APHON 5th Edition PDF)
└── README.md         ← This file
```

> **Before deploying:** Copy your APHON 5th Edition PDF into this folder
> and rename it `source.pdf`.

---

## Option A — Deploy to Render (recommended)

**Cost:** Free tier (750 hrs/month, sleeps after 15 min of inactivity)
**Setup time:** ~10 minutes

### Steps

1. **Create a GitHub repository**
   - Go to [github.com](https://github.com) → New repository
   - Name it `aphon-fact-sheets` (private is fine)
   - Upload all files from this folder (including `source.pdf`)
   - Commit

2. **Connect to Render**
   - Go to [render.com](https://render.com) → Sign up (free)
   - Click **New → Web Service**
   - Connect your GitHub account and select your repo
   - Render will detect `render.yaml` automatically
   - Click **Create Web Service**

3. **Wait for build** (~2 minutes)
   - Render installs dependencies and starts the app
   - You'll get a URL like `https://aphon-fact-sheets.onrender.com`

4. **Share the URL** with your team — that's it!

### Notes on the free tier
- The service "sleeps" after 15 minutes of no traffic
- First request after sleeping takes ~30 seconds to wake up
- Upgrade to the $7/month "Starter" plan to keep it always-on

---

## Option B — Deploy to Railway

**Cost:** $5 credit free, then ~$0–3/month for low traffic

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select your repo (with all files including `source.pdf`)
3. Railway detects the `Procfile` and deploys automatically
4. Go to **Settings → Domains** to get your public URL

---

## Option C — Run locally (for testing)

```bash
# Install dependencies
pip install flask pypdf gunicorn

# Run development server
python app.py

# Or run with gunicorn (production-like)
gunicorn app:app --workers 2
```

Open http://localhost:5000

---

## Features

- **129 medications** fully indexed from the APHON 5th Edition
- **English & Spanish** fact sheets (original PDF pages, not re-typeset)
- **Autocomplete search** as you type
- **Brand name / alias support** — search "Rituxan", "MTX", "IVIG", "Zofran", etc.
- **Multi-page drug support** — drugs spanning multiple pages included in full
- **Instant download** — collated PDF with only the selected drugs

---

## Adding or updating medications

All medication page mappings are in `app.py` in the `MEDICATION_INDEX`
dictionary. Each entry maps a canonical drug name to its English and
Spanish page numbers (1-indexed) in `source.pdf`.

Brand name aliases are in the `ALIASES` dictionary.

---

## Security / access control

The app has no authentication by default — anyone with the URL can use it.

To restrict access, the simplest options are:
- **Render:** Add a `SECRET_KEY` environment variable and use HTTP Basic Auth
  (add ~10 lines of code to `app.py`)
- **Cloudflare Access:** Put Cloudflare in front of the Render URL and
  require Google/email login — free for up to 50 users

---

## Questions?

The app is a single Python file (`app.py`) — all logic and the HTML
interface live there. It has no database and no external dependencies
beyond Flask and pypdf.
