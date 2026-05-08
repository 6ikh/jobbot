"""
main.py — Entry point for the Discord Job Alert System
Runs all scrapers, filters results, deduplicates, and sends to Discord.
"""

import logging
import sys

# Load environment variables from .env file when running locally
# (On GitHub Actions, variables come from GitHub Secrets instead)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required in production
from utils.deduplication import load_seen_jobs, save_seen_jobs
from utils.discord import send_discord_alert
from utils.filters import is_valid_job
from scrapers.greenhouse import scrape_greenhouse_companies
from scrapers.lever import scrape_lever_companies
from scrapers.workday import scrape_workday_companies

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)


def main():
    log.info("🚀 Starting Discord Job Alert System...")

    # Load jobs we've already posted so we don't repost them
    seen_jobs = load_seen_jobs()
    log.info(f"📋 Loaded {len(seen_jobs)} previously seen jobs")

    # Collect all new jobs from every scraper
    all_jobs = []
    all_jobs += scrape_greenhouse_companies()
    all_jobs += scrape_lever_companies()
    all_jobs += scrape_workday_companies()

    log.info(f"🔍 Found {len(all_jobs)} total jobs before filtering")

    new_jobs_posted = 0

    for job in all_jobs:
        job_id = job.get("id")

        # Skip if we've already posted this job
        if job_id in seen_jobs:
            continue

        # Skip if it doesn't pass our title/level filters
        if not is_valid_job(job):
            continue

        # Send to Discord
        success = send_discord_alert(job)

        if success:
            seen_jobs.add(job_id)
            new_jobs_posted += 1
            log.info(f"✅ Posted: {job['title']} @ {job['company']}")
        else:
            log.warning(f"⚠️  Failed to post: {job['title']} @ {job['company']}")

    # Save updated seen jobs back to file
    save_seen_jobs(seen_jobs)

    log.info(f"🎉 Done! Posted {new_jobs_posted} new jobs.")


if __name__ == "__main__":
    main()
