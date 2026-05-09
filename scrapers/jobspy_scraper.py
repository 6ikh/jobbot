"""
scrapers/jobspy_scraper.py — Scrapes LinkedIn jobs using Apify.
Actor: curious_coder/linkedin-jobs-scraper
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
    Builds a LinkedIn job search URL.
    f_E=2,3 = Entry Level + Associate
    f_JT=F  = Full-time
    f_TPR=r604800 = Last 7 days
    """
    params = {
        "keywords": search_term,
        "location": APIFY_LOCATION,
        "f_E": "2,3",
        "f_JT": "F",
        "f_TPR": "r604800",
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
        log.info(f"      Got {len(jobs)} parsed jobs")

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
    Runs one LinkedIn search via Apify.
    """
    try:
        search_url = _build_linkedin_url(search_term)

        run_input = {
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
            log.warning(f"   No run object for '{search_term}'")
            return []

        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            log.warning(f"   No dataset ID for '{search_term}'")
            return []

        items = list(client.dataset(dataset_id).iterate_items())
        log.info(f"      Raw dataset items: {len(items)}")

        # Log the first item's keys so we can see the actual field names
        if items:
            log.info(f"      First item keys: {list(items[0].keys())}")
            log.info(f"      First item sample: {dict(list(items[0].items())[:5])}")

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
    Converts a raw Apify result into our standardized job dict.
    Tries multiple field name variations since different actor versions
    use different field names.
    """
    try:
        # Try all known field name variations for each field
        title = (
            item.get("title") or
            item.get("jobTitle") or
            item.get("job_title") or
            item.get("name") or
            ""
        ).strip()

        company = (
            item.get("companyName") or
            item.get("company") or
            item.get("company_name") or
            item.get("organizationName") or
            ""
        ).strip()

        location = (
            item.get("location") or
            item.get("jobLocation") or
            item.get("place") or
            "Not specified"
        ).strip()

        url = (
            item.get("jobUrl") or
            item.get("url") or
            item.get("link") or
            item.get("applyUrl") or
            item.get("job_url") or
            ""
        ).strip()

        posted_raw = (
            item.get("postedAt") or
            item.get("publishedAt") or
            item.get("datePosted") or
            item.get("posted_date") or
            item.get("date") or
            ""
        )

        salary = (
            item.get("salary") or
            item.get("salaryRange") or
            item.get("compensation") or
            ""
        )

        if not title or not url:
            # Log what we got so we can debug
            log.debug(f"      Skipping item — missing title or url. Keys: {list(item.keys())}")
            return None

        posted_date = _format_posted_date(posted_raw)
        salary_str = str(salary).strip() if salary else "Not listed"
        if salary_str.lower() in ("none", "null", ""):
            salary_str = "Not listed"

        return {
            "id": f"apify_linkedin_{url}",
            "title": title,
            "company": company,
            "location": location,
            "pay": salary_str,
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
        if any(w in posted_raw for w in ["ago", "day", "hour", "week", "month"]):
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
        if target.lower().strip() in company_lower or company_lower in target.lower().strip():
            return True
    return False
