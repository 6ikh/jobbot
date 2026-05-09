"""
scrapers/jobspy_scraper.py — Scrapes LinkedIn jobs using Apify.

ACTOR USED: curious_coder/linkedin-jobs-scraper
This actor requires LinkedIn search URLs as input (not plain search terms).
We build the URLs ourselves using LinkedIn's search parameters.

LinkedIn URL parameters used:
  keywords  = job title search term
  location  = United States
  f_E       = experience level (2=Entry level, 3=Associate)
  f_JT      = job type (F=Full-time)
  f_TPR     = time posted (r604800 = last 7 days)
"""

import os
import logging
import time
import urllib.parse
from datetime import datetime

from config import (
    TARGET_COMPANIES_LIST,
    TARGET_TITLES,
    APIFY_RESULTS_PER_SEARCH,
    APIFY_LOCATION,
)

log = logging.getLogger(__name__)

LINKEDIN_ACTOR_ID = "curious_coder/linkedin-jobs-scraper"


def _build_linkedin_url(search_term: str) -> str:
    """
    Builds a LinkedIn job search URL for a given search term.
    
    f_E=2,3 means Entry Level + Associate (covers both)
    f_JT=F  means Full-time only
    f_TPR=r604800 means posted in the last 7 days
    """
    params = {
        "keywords": search_term,
        "location": APIFY_LOCATION,
        "f_E": "2,3",          # Entry level + Associate
        "f_JT": "F",           # Full-time
        "f_TPR": "r604800",    # Last 7 days
        "position": "1",
        "pageNum": "0",
    }
    return "https://www.linkedin.com/jobs/search/?" + urllib.parse.urlencode(params)


def scrape_all_jobs() -> list:
    """
    Searches LinkedIn for every target job title via Apify.
    Returns a list of standardized job dicts.
    """
    api_token = os.environ.get("APIFY_API_TOKEN", "")
    if not api_token:
        log.error("❌ APIFY_API_TOKEN environment variable is not set!")
        return []

    try:
        from apify_client import ApifyClient
    except ImportError:
        log.error("apify-client not installed. Run: pip install apify-client")
        return []

    client = ApifyClient(api_token)
    all_jobs = []
    seen_urls = set()

    log.info(f"🔗 Scraping LinkedIn via Apify for {len(TARGET_TITLES)} search terms...")

    for title in TARGET_TITLES:
        log.info(f"   Searching: '{title}'")

        jobs = _run_linkedin_search(client, title)
        log.info(f"      Got {len(jobs)} raw results")

        for job in jobs:
            url = job.get("url", "")
            if url in seen_urls:
                continue
            if not _is_target_company(job.get("company", "")):
                continue
            seen_urls.add(url)
            all_jobs.append(job)

        time.sleep(2)

    log.info(f"✅ Total LinkedIn jobs from target companies: {len(all_jobs)}")
    return all_jobs


def _run_linkedin_search(client, search_term: str) -> list:
    """
    Runs one LinkedIn search via Apify using a properly formatted URL.
    """
    try:
        search_url = _build_linkedin_url(search_term)
        log.debug(f"   URL: {search_url}")

        run_input = {
            # This actor requires 'urls' — a list of LinkedIn search page URLs
            "urls": [search_url],
            "count": APIFY_RESULTS_PER_SEARCH,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
        }

        run = client.actor(LINKEDIN_ACTOR_ID).call(
            run_input=run_input,
            timeout_secs=120,
        )

        if not run:
            log.warning(f"   No run object returned for '{search_term}'")
            return []

        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            log.warning(f"   No dataset ID for '{search_term}'")
            return []

        items = list(client.dataset(dataset_id).iterate_items())
        log.debug(f"   Raw items: {len(items)}")

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
    """
    try:
        title = str(item.get("title", "") or "").strip()
        company = str(item.get("companyName", "") or "").strip()
        location = str(item.get("location", "") or "Not specified").strip()
        url = str(item.get("jobUrl", "") or "").strip()
        posted_raw = item.get("postedAt", "")
        salary = str(item.get("salary", "") or "").strip()

        if not title or not url:
            return None

        posted_date = _format_posted_date(posted_raw)

        if not salary or salary.lower() in ("none", "null", ""):
            salary = "Not listed"

        return {
            "id": f"apify_linkedin_{url}",
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
    if not posted_raw:
        return "Not listed"
    if isinstance(posted_raw, str):
        if any(word in posted_raw for word in ["ago", "day", "hour", "week", "month"]):
            return posted_raw
        try:
            dt = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
            return dt.strftime("%B %-d, %Y")
        except Exception:
            return posted_raw
    try:
        if hasattr(posted_raw, "strftime"):
            return posted_raw.strftime("%B %-d, %Y")
    except Exception:
        pass
    return str(posted_raw)


def _is_target_company(company_name: str) -> bool:
    if not company_name:
        return False
    company_lower = company_name.lower().strip()
    for target in TARGET_COMPANIES_LIST:
        target_lower = target.lower().strip()
        if target_lower in company_lower or company_lower in target_lower:
            return True
    return False
