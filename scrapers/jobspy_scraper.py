"""
scrapers/jobspy_scraper.py — Scrapes LinkedIn jobs using Apify.

WHY APIFY:
  LinkedIn blocks requests from cloud/datacenter IPs (like GitHub Actions).
  Apify routes requests through residential IPs that LinkedIn can't detect.
  Free tier gives 10,000 compute units/month — enough for continuous scraping.

HOW TO GET YOUR FREE APIFY API TOKEN:
  1. Go to https://apify.com and click "Sign Up Free"
  2. Verify your email
  3. Go to https://console.apify.com/account/integrations
  4. Copy your "Personal API token"
  5. Add it to GitHub Secrets as: APIFY_API_TOKEN

APIFY ACTOR USED:
  "curious_coder/linkedin-jobs-scraper"
  Actor docs: https://apify.com/curious_coder/linkedin-jobs-scraper

HOW APIFY BILLING WORKS (FREE TIER):
  - You get $5 free credits every month
  - Each LinkedIn job search costs roughly $0.01-0.05
  - At 15 searches per run, every 5 minutes = ~$0.15/day max
  - Well within the free $5/month limit
"""

import os
import logging
import time
from datetime import datetime

from config import (
    TARGET_COMPANIES_LIST,
    TARGET_TITLES,
    APIFY_RESULTS_PER_SEARCH,
    APIFY_JOB_TYPE,
    APIFY_EXPERIENCE_LEVEL,
    APIFY_LOCATION,
)

log = logging.getLogger(__name__)

# The Apify actor ID for LinkedIn Jobs scraper
LINKEDIN_ACTOR_ID = "curious_coder/linkedin-jobs-scraper"


def scrape_all_jobs() -> list:
    """
    Main function — searches LinkedIn for every target job title using Apify.
    Returns a list of standardized job dicts ready for Discord posting.
    """
    # Get API token from environment variable
    api_token = os.environ.get("APIFY_API_TOKEN", "")
    if not api_token:
        log.error("❌ APIFY_API_TOKEN environment variable is not set!")
        log.error("   Add it to GitHub Secrets or your .env file.")
        return []

    try:
        from apify_client import ApifyClient
    except ImportError:
        log.error("apify-client not installed. Run: pip install apify-client")
        return []

    client = ApifyClient(api_token)
    all_jobs = []
    seen_urls = set()  # Prevent duplicates within this run

    log.info(f"🔗 Scraping LinkedIn via Apify for {len(TARGET_TITLES)} search terms...")

    for title in TARGET_TITLES:
        log.info(f"   Searching LinkedIn: '{title}'")

        jobs = _run_linkedin_search(client, title)
        log.info(f"      Got {len(jobs)} raw results")

        for job in jobs:
            url = job.get("url", "")

            # Skip duplicate URLs within this run
            if url in seen_urls:
                continue

            # Only keep jobs from our target companies
            if not _is_target_company(job.get("company", "")):
                continue

            seen_urls.add(url)
            all_jobs.append(job)

        # Be polite between Apify calls
        time.sleep(2)

    log.info(f"✅ Total LinkedIn jobs from target companies: {len(all_jobs)}")
    return all_jobs


def _run_linkedin_search(client, search_term: str) -> list:
    """
    Runs a single LinkedIn job search via Apify and returns parsed jobs.
    
    Apify actors work by:
    1. You call .call() with input parameters
    2. Apify runs the actor on their cloud (using residential IPs)
    3. Results are stored in a "dataset"
    4. You fetch items from the dataset
    """
    try:
        # Input parameters for the LinkedIn Jobs Scraper actor
        # Full docs: https://apify.com/curious_coder/linkedin-jobs-scraper/input-schema
        run_input = {
            "searchTerms": [search_term],
            "location": APIFY_LOCATION,
            "count": APIFY_RESULTS_PER_SEARCH,
            "jobType": APIFY_JOB_TYPE,           # "full-time", "part-time", "contract", etc.
            "experienceLevel": APIFY_EXPERIENCE_LEVEL,  # "entry_level", "associate", etc.
            "proxy": {
                "useApifyProxy": True,            # Use Apify's residential proxy pool
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
        }

        # Run the actor and wait for it to finish
        # timeout_secs: max time to wait before giving up
        run = client.actor(LINKEDIN_ACTOR_ID).call(
            run_input=run_input,
            timeout_secs=120,  # Wait up to 2 minutes per search
        )

        if not run:
            log.warning(f"   Apify returned no run object for '{search_term}'")
            return []

        # Fetch results from the dataset
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            log.warning(f"   No dataset ID returned for '{search_term}'")
            return []

        items = list(client.dataset(dataset_id).iterate_items())
        log.debug(f"   Raw Apify items: {len(items)}")

        # Parse each item into our standardized format
        jobs = []
        for item in items:
            job = _parse_apify_item(item)
            if job:
                jobs.append(job)

        return jobs

    except Exception as e:
        log.error(f"   ❌ Apify error for '{search_term}': {e}")
        return []


def _parse_apify_item(item: dict) -> dict | None:
    """
    Converts a raw Apify LinkedIn result into our standardized job dict.

    Common fields returned by curious_coder/linkedin-jobs-scraper:
      - title: job title
      - companyName: company name
      - location: city, state/country
      - jobUrl: full LinkedIn URL
      - postedAt: relative string like "2 days ago" or ISO date
      - salary: salary string if listed (e.g. "$60,000/yr")
      - jobType: Full-time, Part-time, etc.
      - experienceLevel: Entry level, Associate, etc.
      - applicantsCount: number of applicants
    """
    try:
        title = str(item.get("title", "") or "").strip()
        company = str(item.get("companyName", "") or "").strip()
        location = str(item.get("location", "") or "Not specified").strip()
        url = str(item.get("jobUrl", "") or "").strip()
        posted_raw = item.get("postedAt", "")
        salary = str(item.get("salary", "") or "Not listed").strip()

        if not title or not url:
            return None

        # Format posted date
        posted_date = _format_posted_date(posted_raw)

        # Clean up salary
        if not salary or salary.lower() in ("none", "null", ""):
            salary = "Not listed"

        # Create unique ID from URL
        unique_id = f"apify_linkedin_{url}"

        return {
            "id": unique_id,
            "title": title,
            "company": company,
            "location": location,
            "pay": salary,
            "posted_date": posted_date,
            "apply_by": "Not listed",
            "url": url,
            "source": "LinkedIn",
        }

    except Exception as e:
        log.error(f"Error parsing Apify item: {e}")
        return None


def _format_posted_date(posted_raw) -> str:
    """
    Converts Apify's posted date to a readable string.
    Input could be: "2 days ago", "2026-05-07T14:30:00", or a datetime object.
    """
    if not posted_raw:
        return "Not listed"

    # If it's already a relative string like "2 days ago", return it directly
    if isinstance(posted_raw, str):
        if "ago" in posted_raw or "day" in posted_raw or "hour" in posted_raw:
            return posted_raw
        # Try parsing as ISO date
        try:
            dt = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
            return dt.strftime("%B %-d, %Y")
        except Exception:
            return posted_raw

    # If it's a datetime object
    try:
        if hasattr(posted_raw, "strftime"):
            return posted_raw.strftime("%B %-d, %Y")
    except Exception:
        pass

    return str(posted_raw)


def _is_target_company(company_name: str) -> bool:
    """
    Returns True if the company matches one of our target companies.
    Fuzzy match: "Boston Scientific Corporation" matches "Boston Scientific".
    """
    if not company_name:
        return False

    company_lower = company_name.lower().strip()

    for target in TARGET_COMPANIES_LIST:
        target_lower = target.lower().strip()
        if target_lower in company_lower or company_lower in target_lower:
            return True

    return False
