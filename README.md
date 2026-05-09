# 🚨 Discord Job Alert System
> Automatically scrapes entry-level jobs from LinkedIn and posts them to Discord — completely FREE, runs every 5 minutes.

---

## 📋 Table of Contents
1. [What This Does](#what-this-does)
2. [Example Discord Alert](#example-discord-alert)
3. [How It Works](#how-it-works)
4. [Folder Structure](#folder-structure)
5. [Setup Guide](#setup-guide)
6. [Adding More Companies](#adding-more-companies)
7. [Adding More Job Titles](#adding-more-job-titles)
8. [Troubleshooting](#troubleshooting)
9. [Tech Stack](#tech-stack)

---

## What This Does

- ✅ Scrapes **LinkedIn** job postings via Apify (bypasses LinkedIn's IP blocks)
- ✅ Filters for only entry-level + associate roles at 78 target companies
- ✅ Skips senior / manager / director / lead roles automatically
- ✅ Never reposts the same job twice (deduplication via `seen_jobs.json`)
- ✅ Sends formatted alerts to a Discord channel automatically
- ✅ Runs every 5 minutes using GitHub Actions
- ✅ Costs **$0** — Apify free tier covers the usage

---

## Example Discord Alert

```
🚨 New Entry-Level Opportunity

Company: Tesla
Job Title: Supply Chain Analyst
Location: Austin, TX
Experience Level: Entry Level
Pay: $65,000/yr
Posted: 2 days ago
Apply By: Not listed

Apply:
https://www.linkedin.com/jobs/view/123456789
```

---

## How It Works

```
GitHub Actions (every 5 minutes)
        ↓
    main.py runs
        ↓
For each of 17 job title searches:
  → Builds a LinkedIn search URL with entry-level filter
  → Sends URL to Apify (runs on residential IP — LinkedIn can't block it)
  → Apify scrapes LinkedIn and returns job results
        ↓
Filters by target company name (78 companies)
Filters by job title keywords
Removes senior/manager/lead/director jobs
        ↓
Checks seen_jobs.json — skips already-posted jobs
        ↓
Sends new jobs to Discord via webhook
        ↓
Updates seen_jobs.json → commits back to GitHub
```

---

## Folder Structure

```
jobbot/
│
├── main.py                        # Entry point — runs everything
├── config.py                      # Companies, job titles, Apify settings
├── requirements.txt               # Python packages (apify-client, requests)
├── seen_jobs.json                 # Tracks posted jobs (auto-updated by Actions)
├── .env.example                   # Template for local development
├── .gitignore
│
├── scrapers/
│   ├── __init__.py
│   └── jobspy_scraper.py          # Apify/LinkedIn scraper
│
├── utils/
│   ├── __init__.py
│   ├── deduplication.py           # Loads/saves seen_jobs.json
│   ├── discord.py                 # Formats and sends Discord messages
│   └── filters.py                 # Filters jobs by title and exclusion keywords
│
└── .github/
    └── workflows/
        └── job_alerts.yml         # GitHub Actions — runs every 5 minutes
```

---

## Setup Guide

### ✅ Step 1: GitHub Repository
Your repo is already set up. All files should be at the root level (not inside a subfolder), with `utils/` and `scrapers/` as subfolders.

---

### ✅ Step 2: Discord Webhook
1. Open Discord → go to the channel you want alerts in
2. Click the ⚙️ gear (Edit Channel) → **Integrations** → **Webhooks** → **New Webhook**
3. Name it "Job Alert Bot" → click **Copy Webhook URL**
4. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: paste your webhook URL

---

### ✅ Step 3: Apify Account (Free)
Apify is used to scrape LinkedIn without getting blocked. GitHub Actions servers have datacenter IPs that LinkedIn blocks — Apify routes through residential IPs instead.

1. Go to **https://apify.com** → Sign Up Free (no credit card needed)
2. Verify your email
3. Go to **https://console.apify.com/account/integrations**
4. Copy your **Personal API token**
5. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   - Name: `APIFY_API_TOKEN`
   - Value: paste your token

**Apify free tier:** $5 of credits per month, resets monthly. Each LinkedIn search costs roughly $0.01–0.05. At 17 searches per run, every 5 minutes, you'll use well under $5/month.

---

### ✅ Step 4: Run It
1. Go to your GitHub repo → **Actions** tab
2. Click **Job Alert Scraper** in the left sidebar
3. Click **Run workflow** → **Run workflow**
4. Each run takes about 10–15 minutes (17 Apify searches × ~45 seconds each)
5. Check your Discord channel for alerts

---

### ✅ Step 5: Local Testing (Optional)
```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/jobbot.git
cd jobbot

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and fill in DISCORD_WEBHOOK_URL and APIFY_API_TOKEN

# Run
python main.py
```

---

## Adding More Companies

Open `config.py` and add to `TARGET_COMPANIES_LIST`:

```python
TARGET_COMPANIES_LIST = [
    ...
    "New Company Name",    # Add this line
]
```

Matching is fuzzy — `"Boston Scientific"` will match `"Boston Scientific Corporation"`.

---

## Adding More Job Titles

Open `config.py` and add to `TARGET_TITLES`:

```python
TARGET_TITLES = [
    ...
    "new job title here",    # Apify will search LinkedIn for this
]
```

Note: each title = one Apify search = ~$0.01–0.05 of credits. Keep the list focused.

---

## Troubleshooting

**❓ Nothing showing in Discord**
- Check Actions logs → expand "Run job scraper" → look for errors
- Verify both `DISCORD_WEBHOOK_URL` and `APIFY_API_TOKEN` are in GitHub Secrets
- Check `seen_jobs.json` — if it has IDs, jobs were found but already posted previously

**❓ "APIFY_API_TOKEN is not set"**
- The secret name must be exactly `APIFY_API_TOKEN` (all caps, underscores)

**❓ "Got 0 raw results" for every search**
- This means Apify ran successfully but returned no data — likely a field name mismatch
- Check the logs for `First item keys:` line which shows the actual field names returned
- Share those logs for a fix

**❓ Run takes too long / times out**
- Reduce `APIFY_RESULTS_PER_SEARCH` in `config.py` from 15 to 10
- Reduce `TARGET_TITLES` list length
- GitHub Actions has a 6-hour job timeout so it won't be killed, just slow

**❓ Apify credits running out**
- Reduce `APIFY_RESULTS_PER_SEARCH` in `config.py`
- Change the schedule in `job_alerts.yml` from `*/5` to `*/15` (every 15 min)
- Remove less important titles from `TARGET_TITLES`

**❓ Jobs from wrong companies showing up**
- The company filter is fuzzy — `"target"` matches both Target (retail) and any company with "target" in its name
- Make company names more specific in `TARGET_COMPANIES_LIST` if needed

---

## Tech Stack

| Tool | Purpose | Cost |
|------|---------|------|
| Python | Programming language | Free |
| apify-client | Calls Apify API to run LinkedIn scraper | Free |
| Apify | Scrapes LinkedIn using residential IPs | Free ($5/mo credit) |
| curious_coder/linkedin-jobs-scraper | The Apify actor that does the actual scraping | Free |
| Discord Webhooks | Posts job alerts to Discord | Free |
| GitHub | Code hosting | Free |
| GitHub Actions | Runs scraper every 5 minutes automatically | Free |
| seen_jobs.json | Deduplication — tracks already-posted jobs | Free |

**Total monthly cost: $0.00** 🎉

---

## How Deduplication Works

Every time a job is posted to Discord, its unique ID (based on the LinkedIn URL) is saved to `seen_jobs.json`. On the next run, any job whose ID is already in that file is skipped entirely — it will never be posted again even if LinkedIn keeps showing it in search results.

GitHub Actions automatically commits the updated `seen_jobs.json` back to your repo after every run, so the deduplication persists across all future runs.

---

## Changing the Schedule

Edit `.github/workflows/job_alerts.yml`:

```yaml
schedule:
  - cron: "*/5 * * * *"    # every 5 minutes (current)
  - cron: "*/15 * * * *"   # every 15 minutes
  - cron: "0 * * * *"      # every hour
  - cron: "0 9 * * *"      # once daily at 9am UTC
```

Note: GitHub's minimum is 5 minutes. Scheduled runs may be delayed 5–15 min when GitHub servers are busy.

---

*Built for entry-level job seekers — good luck out there* 🎯
