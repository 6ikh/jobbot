"""
scrapers/jobspy_scraper.py — Scrapes LinkedIn jobs using Apify.

COST OPTIMIZATION:
  Instead of calling Apify 17 times (once per search term), we now call it
  ONCE with all 17 URLs in a single run. This eliminates 16 container startup
  costs per scrape, reducing credit usage by ~90%.

  Old approach: 17 runs × $0.01 startup + results = ~$0.17/scrape
  New approach: 1 run  × $0.01 startup + results = ~$0.02/scrape
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
    Sends ALL search URLs to Apify in a single run.
    One container startup, one dataset, all results.
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

    # Build ALL search URLs upfront
    all_urls = [_build_linkedin_url(title) for title in TARGET_TITLES]
    log.info(f"🔗 Sending {len(all_urls)} LinkedIn search URLs to Apify in ONE run...")
    for i, (title, url) in enumerate(zip(TARGET_TITLES, all_urls)):
        log.info(f"   [{i+1}] {title}")

    # Single Apify call with all URLs
    # total results = number of URLs × APIFY_RESULTS_PER_SEARCH
    run_input = {
        "urls": all_urls,                               # All 17 URLs at once
        "count": APIFY_RESULTS_PER_SEARCH,              # Results per URL
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        },
    }

    try:
        run = client.actor(LINKEDIN_ACTOR_ID).call(
            run_input=run_input,
            timeout_secs=300,  # 5 min max — single run handles all searches
        )

        if not run:
            log.error("❌ Apify returned no run object")
            return []

        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            log.error("❌ No dataset ID returned from Apify")
            return []

        items = list(client.dataset(dataset_id).iterate_items())
        log.info(f"📦 Apify returned {len(items)} total raw results")

        # Log first item's field names so we can verify parsing
        if items:
            log.info(f"   First item keys: {list(items[0].keys())}")
            log.info(f"   First item sample: { {k: items[0][k] for k in list(items[0].keys())[:6]} }")

    except Exception as e:
        log.error(f"❌ Apify run failed: {e}")
        return []

    # Parse all results and filter by target company
    all_jobs = []
    seen_urls = set()

    for item in items:
        job = _parse_apify_item(item)
        if not job:
            continue
        url = job.get("url", "")
        if url in seen_urls:
            continue
        if not _is_target_company(job.get("company", "")):
            continue
        seen_urls.add(url)
        all_jobs.append(job)

    log.info(f"✅ {len(all_jobs)} jobs matched target companies (from {len(items)} total)")
    return all_jobs


def _parse_apify_item(item: dict) -> dict | None:
    """
    Converts a raw Apify result into our standardized job dict.
    Tries multiple field name variations.
    """
    try:
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
            log.debug(f"Skipping — missing title/url. Keys: {list(item.keys())}")
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
        log.error(f"Error parsing item: {e}")
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
