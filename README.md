# 🚨 Discord Job Alert System
> Automatically scrapes entry-level jobs from 60+ top companies and posts them to Discord — completely FREE, runs every 15 minutes.

---

## 📋 Table of Contents
1. [What This Does](#what-this-does)
2. [Example Discord Alert](#example-discord-alert)
3. [How It Works](#how-it-works)
4. [Folder Structure](#folder-structure)
5. [Setup Guide (Step by Step)](#setup-guide)
   - Step 1: Install Python
   - Step 2: Create GitHub Repository
   - Step 3: Set Up Discord Webhook
   - Step 4: Add GitHub Secret
   - Step 5: Enable GitHub Actions
   - Step 6: Test Locally (Optional)
6. [Adding More Companies](#adding-more-companies)
7. [Adding More Job Titles](#adding-more-job-titles)
8. [Troubleshooting](#troubleshooting)
9. [Future Improvements](#future-improvements)

---

## What This Does

This system:
- ✅ Scrapes job postings from **Greenhouse**, **Lever**, and **Workday** ATS platforms
- ✅ Filters for only entry-level roles at target companies
- ✅ Skips senior/manager/director roles automatically
- ✅ Never reposts the same job twice (deduplication)
- ✅ Sends alerts to a Discord channel automatically
- ✅ Runs every 15 minutes using GitHub Actions
- ✅ Costs **$0** — uses only free tools

---

## Example Discord Alert

```
🚨 New Entry-Level Opportunity

Company: Tesla
Job Title: Supply Chain Analyst
Location: Austin, TX
Experience Level: Entry Level
Pay: Not listed
Posted: May 7, 2026
Apply By: Not listed

Apply:
https://tesla.wd1.myworkdayjobs.com/Tesla_External/job/Austin-TX/Supply-Chain-Analyst_R12345
```

---

## How It Works

```
GitHub Actions (every 15 min)
        ↓
    main.py runs
        ↓
Scrapes Greenhouse + Lever + Workday APIs
        ↓
Filters by job title keywords
Removes senior/manager/etc.
        ↓
Checks seen_jobs.json (skips already-posted jobs)
        ↓
Sends new jobs to Discord via webhook
        ↓
Updates seen_jobs.json and commits it back to GitHub
```

---

## Folder Structure

```
discord-job-alerts/
│
├── main.py                    # Entry point — runs everything
├── config.py                  # All your companies, titles, and filters
├── requirements.txt           # Python packages to install
├── seen_jobs.json             # Tracks jobs already posted (auto-updated)
├── .env.example               # Template for local environment variables
├── .gitignore                 # Files NOT to commit to GitHub
│
├── scrapers/
│   ├── __init__.py
│   ├── greenhouse.py          # Scrapes Greenhouse ATS companies
│   ├── lever.py               # Scrapes Lever ATS companies
│   └── workday.py             # Scrapes Workday ATS companies
│
├── utils/
│   ├── __init__.py
│   ├── deduplication.py       # Loads/saves seen_jobs.json
│   ├── discord.py             # Sends messages to Discord webhook
│   └── filters.py             # Filters jobs by title/level
│
└── .github/
    └── workflows/
        └── job_alerts.yml     # GitHub Actions automation schedule
```

---

## Setup Guide

### ✅ Step 1: Install Python

**Windows:**
1. Go to https://python.org/downloads
2. Download Python 3.11 or newer
3. Run the installer
4. ⚠️ IMPORTANT: Check "Add Python to PATH" during installation
5. Open Command Prompt and verify: `python --version`

**Mac:**
1. Open Terminal
2. Run: `brew install python` (if you have Homebrew)
   OR download from https://python.org/downloads
3. Verify: `python3 --version`

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install python3 python3-pip -y
python3 --version
```

---

### ✅ Step 2: Create a GitHub Repository

1. Go to https://github.com and create a free account if you don't have one
2. Click the **+** button → **New repository**
3. Name it `discord-job-alerts`
4. Set it to **Public** (required for unlimited free GitHub Actions minutes)
   - Private repos get 2,000 free minutes/month (still plenty)
5. Click **Create repository**
6. Upload all the files from this project to your repo

**To upload files:**
```bash
# Option A: Using Git (recommended)
git clone https://github.com/YOUR_USERNAME/discord-job-alerts.git
cd discord-job-alerts
# Copy all the project files into this folder
git add .
git commit -m "Initial commit"
git push

# Option B: Use GitHub's web interface
# Click "uploading an existing file" on your repo page
# Drag and drop all the files
```

---

### ✅ Step 3: Create a Discord Webhook

1. Open **Discord** (desktop or browser)
2. Go to the **server** where you want job alerts
3. Right-click the **channel** you want alerts in → **Edit Channel**
4. Click **Integrations** in the left sidebar
5. Click **Webhooks** → **New Webhook**
6. Give it a name like "Job Alert Bot"
7. Click **Copy Webhook URL**
8. Save this URL — you'll need it in the next step

> ⚠️ **KEEP THIS URL SECRET!** Anyone with this URL can post to your channel.

---

### ✅ Step 4: Add the Webhook URL as a GitHub Secret

We store the webhook URL as a GitHub Secret so it's never visible in your code.

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**
5. Name: `DISCORD_WEBHOOK_URL`
6. Value: Paste your Discord webhook URL
7. Click **Add secret**

---

### ✅ Step 5: Enable GitHub Actions

1. Go to your GitHub repository
2. Click the **Actions** tab
3. If prompted, click **I understand my workflows, go ahead and enable them**
4. You should see your workflow listed as "Job Alert Scraper"

**To test it immediately:**
1. Click on "Job Alert Scraper"
2. Click **Run workflow** → **Run workflow**
3. Watch it run! It should take about 1-2 minutes.
4. Check your Discord channel for job alerts.

---

### ✅ Step 6: Test Locally (Optional but Recommended)

Testing locally lets you see exactly what's happening before relying on GitHub.

```bash
# 1. Navigate to the project folder
cd discord-job-alerts

# 2. Create a virtual environment (keeps packages isolated)
python -m venv venv

# 3. Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up your environment variables
cp .env.example .env
# Open .env in a text editor and fill in your Discord webhook URL

# 6. Run the scraper
python main.py
```

You should see output like:
```
2026-05-07 14:30:00 [INFO] 🚀 Starting Discord Job Alert System...
2026-05-07 14:30:00 [INFO] 📋 Loaded 0 previously seen jobs
2026-05-07 14:30:01 [INFO] 🌿 Scraping Greenhouse: Boston Scientific
2026-05-07 14:30:02 [INFO]    Found 3 jobs at Boston Scientific
...
2026-05-07 14:30:45 [INFO] 🎉 Done! Posted 7 new jobs.
```

---

## Adding More Companies

### Adding a Greenhouse Company:
1. Find the company's Greenhouse board token:
   - Visit: `https://boards.greenhouse.io/COMPANY_NAME`
   - The slug in the URL is the token
2. Open `config.py`
3. Add to `GREENHOUSE_COMPANIES`:
```python
GREENHOUSE_COMPANIES = {
    ...
    "newcompany": "New Company Name",  # Add this line
}
```

### Adding a Lever Company:
1. Find the slug: visit `https://jobs.lever.co/COMPANY_SLUG`
2. Add to `LEVER_COMPANIES` in `config.py`:
```python
LEVER_COMPANIES = {
    ...
    "newslug": "New Company Name",  # Add this line
}
```

### Adding a Workday Company:
1. Find the Workday tenant: look for `TENANT.wd1.myworkdayjobs.com` in the URL
2. Add to `WORKDAY_TENANTS` in `scrapers/workday.py`:
```python
WORKDAY_TENANTS = {
    ...
    "New Company": ("tenant_name", "job_site_name"),  # Add this line
}
```

---

## Adding More Job Titles

Open `config.py` and add keywords to `TARGET_TITLES`:

```python
TARGET_TITLES = [
    ...
    "your new job title here",  # Will match any title containing this phrase
]
```

Matching is case-insensitive and partial, so `"analyst"` would match:
- "Supply Chain Analyst"
- "Data Analyst"  
- "Senior Analyst" ← but this would be caught by EXCLUDE_TITLE_KEYWORDS

---

## Troubleshooting

**❓ No jobs are showing up in Discord**
- Check that `DISCORD_WEBHOOK_URL` is set correctly in GitHub Secrets
- Run the workflow manually (Actions tab → Run workflow)
- Check the workflow logs for error messages

**❓ "404 Not Found" for a company**
- The company may have changed their ATS or board token
- Try visiting their career page directly to find the new URL

**❓ "403 Forbidden" for Workday companies**
- That company's Workday site blocks automated requests
- These companies need Playwright-based scraping (future improvement)

**❓ Same jobs keep getting posted**
- Make sure the GitHub Actions workflow is committing `seen_jobs.json`
- Check that the workflow has `permissions: contents: write`
- Look at your repo to confirm `seen_jobs.json` is being updated

**❓ GitHub Actions isn't running every 15 minutes**
- GitHub may delay scheduled workflows by up to 15-30 minutes when servers are busy
- This is normal — the schedule is not guaranteed to be exactly on time

---

## Future Improvements

When you're ready to scale up, here's what to add next:

1. **Playwright scraping** — for companies that block `requests`
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Multiple Discord channels** — send different job categories to different channels
   - Add `DISCORD_WEBHOOK_URL_SUPPLY_CHAIN`, `DISCORD_WEBHOOK_URL_CONSULTING`, etc.

3. **Email alerts** — send a daily digest email using Python's `smtplib` (free with Gmail)

4. **Location filtering** — only show jobs in specific cities or states

5. **Indeed / LinkedIn scraping** — much harder due to anti-bot measures, but possible

6. **Google Sheets logging** — log every job to a spreadsheet using `gspread`

7. **Salary filtering** — only show jobs above a minimum pay threshold

8. **Slack alerts** — same webhook concept works for Slack too

---

## Tech Stack

| Tool | Purpose | Cost |
|------|---------|------|
| Python | Programming language | Free |
| requests | HTTP requests to job APIs | Free |
| BeautifulSoup | HTML parsing | Free |
| Discord Webhooks | Sending alerts to Discord | Free |
| GitHub | Code hosting | Free |
| GitHub Actions | Automated scheduling | Free (public repos) |
| JSON file | Job deduplication storage | Free |

**Total monthly cost: $0.00** 🎉

---

*Built with ❤️ for entry-level job seekers*
