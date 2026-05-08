"""
scrapers/lever.py — Scrapes jobs from companies using the Lever ATS.

Lever also has a FREE public API! No API key needed.
Each company has a "company slug" used in their API URL.

API endpoint:
  GET https://api.lever.co/v0/postings/{company_slug}?mode=json

Documentation: https://hire.lever.co/developer/postings

HOW TO FIND A COMPANY'S SLUG:
  Visit: https://jobs.lever.co/COMPANY_SLUG
  The part after jobs.lever.co/ is the slug.
  Example: https://jobs.lever.co/mckinsey → slug is "mckinsey"
"""

import logging
import requests
from datetime import datetime
from config import LEVER_COMPANIES

log = logging.getLogger(__name__)

# Lever public API base URL
LEVER_API = "https://api.lever.co/v0/postings/{slug}?mode=json"


def scrape_lever_companies() -> list:
    """
    Loops through all companies in LEVER_COMPANIES and returns a list of jobs.
    """
    all_jobs = []

    for slug, company_name in LEVER_COMPANIES.items():
        log.info(f"⚙️  Scraping Lever: {company_name} ({slug})")
        jobs = _fetch_lever_jobs(slug, company_name)
        log.info(f"   Found {len(jobs)} jobs at {company_name}")
        all_jobs.extend(jobs)

    return all_jobs


def _fetch_lever_jobs(slug: str, company_name: str) -> list:
    """
    Fetches jobs for a single company from the Lever API.
    """
    url = LEVER_API.format(slug=slug)

    try:
        response = requests.get(url, timeout=15)

        if response.status_code == 404:
            log.warning(f"   ⚠️  {company_name} not found on Lever (404). Check slug.")
            return []

        response.raise_for_status()
        data = response.json()

    except requests.exceptions.Timeout:
        log.error(f"   ⏱️  Timeout fetching {company_name} from Lever")
        return []
    except requests.exceptions.RequestException as e:
        log.error(f"   ❌ Error fetching {company_name}: {e}")
        return []
    except ValueError:
        log.error(f"   ❌ Invalid JSON from Lever for {company_name}")
        return []

    jobs = []

    # Lever returns a list of postings directly (not wrapped in a key)
    for raw_job in data:
        job = _parse_lever_job(raw_job, company_name, slug)
        if job:
            jobs.append(job)

    return jobs


def _parse_lever_job(raw_job: dict, company_name: str, slug: str) -> dict | None:
    """
    Converts a raw Lever API response into our standardized job dict.

    Lever job fields:
      - id: UUID string
      - text: job title
      - categories: {location, team, department, commitment}
      - hostedUrl: direct link to apply
      - createdAt: Unix timestamp in milliseconds
      - salaryRange: {min, max, currency, interval} — if provided
    """
    try:
        job_id = raw_job.get("id", "")
        title = raw_job.get("text", "")

        categories = raw_job.get("categories", {})
        location = categories.get("location", "Not specified") or "Not specified"

        apply_url = raw_job.get("hostedUrl", "")

        # Lever timestamps are in milliseconds since epoch
        created_ms = raw_job.get("createdAt", 0)
        posted_date = _format_lever_date(created_ms)

        pay = _extract_lever_pay(raw_job)

        unique_id = f"lever_{slug}_{job_id}"

        return {
            "id": unique_id,
            "title": title,
            "company": company_name,
            "location": location,
            "pay": pay,
            "posted_date": posted_date,
            "apply_by": "Not listed",
            "url": apply_url,
            "source": "Lever",
        }

    except Exception as e:
        log.error(f"Error parsing Lever job: {e}")
        return None


def _format_lever_date(created_ms: int) -> str:
    """Converts millisecond timestamp to 'May 7, 2026'"""
    if not created_ms:
        return "Not listed"
    try:
        dt = datetime.fromtimestamp(created_ms / 1000)
        return dt.strftime("%B %-d, %Y")
    except Exception:
        return "Not listed"


def _extract_lever_pay(raw_job: dict) -> str:
    """
    Lever sometimes includes salary range in a 'salaryRange' field.
    Example: {min: 50000, max: 70000, currency: "USD", interval: "per year"}
    """
    salary = raw_job.get("salaryRange")
    if not salary:
        return "Not listed"

    try:
        min_pay = salary.get("min")
        max_pay = salary.get("max")
        currency = salary.get("currency", "USD")
        interval = salary.get("interval", "per year")

        if min_pay and max_pay:
            return f"{currency} {min_pay:,} – {max_pay:,} {interval}"
        elif min_pay:
            return f"{currency} {min_pay:,}+ {interval}"
    except Exception:
        pass

    return "Not listed"
