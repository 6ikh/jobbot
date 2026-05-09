"""
main.py — Entry point for the Discord Job Alert System.
Runs Apify LinkedIn scraper, filters results, deduplicates, and sends to Discord.
"""

import logging
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from utils.deduplication import load_seen_jobs, save_seen_jobs
from utils.discord import send_discord_alert
from utils.filters import is_valid_job
from scrapers.jobspy_scraper import scrape_all_jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)


def main():
    log.info("🚀 Starting Discord Job Alert System...")

    seen_jobs = load_seen_jobs()
    log.info(f"📋 Loaded {len(seen_jobs)} previously seen jobs")

    all_jobs = scrape_all_jobs()
    log.info(f"🔍 Found {len(all_jobs)} target-company jobs before filtering")

    new_jobs_posted = 0

    for job in all_jobs:
        job_id = job.get("id")

        if job_id in seen_jobs:
            continue

        if not is_valid_job(job):
            continue

        success = send_discord_alert(job)

        if success:
            seen_jobs.add(job_id)
            new_jobs_posted += 1
            log.info(f"✅ Posted: {job['title']} @ {job['company']}")
        else:
            log.warning(f"⚠️  Failed to post: {job['title']} @ {job['company']}")

    save_seen_jobs(seen_jobs)
    log.info(f"🎉 Done! Posted {new_jobs_posted} new jobs.")


if __name__ == "__main__":
    main()
