"""
scrapers/greenhouse.py — Scrapes jobs from companies using the Greenhouse ATS.

Greenhouse has a FREE public API! No API key needed.
Each company has a "board token" which is part of their jobs URL.

API endpoint:
  GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true

Documentation: https://developers.greenhouse.io/job-board.html

HOW TO FIND A COMPANY'S BOARD TOKEN:
  Visit: https://boards.greenhouse.io/COMPANY
  The slug in the URL is the board token.
  Example: https://boards.greenhouse.io/apple → token is "apple"
"""

import logging
import requests
from datetime import datetime
from config import GREENHOUSE_COMPANIES

log = logging.getLogger(__name__)

# Greenhouse public API base URL
GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"


def scrape_greenhouse_companies() -> list:
    """
    Loops through all companies in GREENHOUSE_COMPANIES and returns a list of jobs.
    Each job is a dict with standardized fields.
    """
    all_jobs = []

    for board_token, company_name in GREENHOUSE_COMPANIES.items():
        log.info(f"🌿 Scraping Greenhouse: {company_name} ({board_token})")
        jobs = _fetch_greenhouse_jobs(board_token, company_name)
        log.info(f"   Found {len(jobs)} jobs at {company_name}")
        all_jobs.extend(jobs)

    return all_jobs


def _fetch_greenhouse_jobs(board_token: str, company_name: str) -> list:
    """
    Fetches jobs for a single company from the Greenhouse API.
    Returns a list of standardized job dicts.
    """
    url = GREENHOUSE_API.format(token=board_token)

    try:
        response = requests.get(url, timeout=15)

        # 404 means the company doesn't use Greenhouse or the token is wrong
        if response.status_code == 404:
            log.warning(f"   ⚠️  {company_name} not found on Greenhouse (404). Check board token.")
            return []

        response.raise_for_status()  # Raise exception for other HTTP errors
        data = response.json()

    except requests.exceptions.Timeout:
        log.error(f"   ⏱️  Timeout fetching {company_name} from Greenhouse")
        return []
    except requests.exceptions.RequestException as e:
        log.error(f"   ❌ Error fetching {company_name}: {e}")
        return []
    except ValueError:
        log.error(f"   ❌ Invalid JSON response from Greenhouse for {company_name}")
        return []

    jobs = []
    raw_jobs = data.get("jobs", [])

    for raw_job in raw_jobs:
        job = _parse_greenhouse_job(raw_job, company_name, board_token)
        if job:
            jobs.append(job)

    return jobs


def _parse_greenhouse_job(raw_job: dict, company_name: str, board_token: str) -> dict | None:
    """
    Converts a raw Greenhouse API response into our standardized job dict.

    Greenhouse job fields:
      - id: unique integer
      - title: job title string
      - location: {name: "City, State"}
      - absolute_url: direct link to the job posting
      - updated_at: ISO timestamp when it was last updated
      - metadata: list of custom fields (pay, etc.) — varies by company
    """
    try:
        job_id = raw_job.get("id")
        title = raw_job.get("title", "")
        location_data = raw_job.get("location", {})
        location = location_data.get("name", "Not specified") if location_data else "Not specified"
        apply_url = raw_job.get("absolute_url", "")
        updated_at = raw_job.get("updated_at", "")

        # Format the date to be human-readable (e.g. "May 7, 2026")
        posted_date = _format_date(updated_at)

        # Try to extract pay from metadata (not all companies include this)
        pay = _extract_pay_from_metadata(raw_job.get("metadata", []))

        # Create a unique ID by combining company + job ID
        # This prevents collisions if two companies have jobs with the same ID
        unique_id = f"greenhouse_{board_token}_{job_id}"

        return {
            "id": unique_id,
            "title": title,
            "company": company_name,
            "location": location,
            "pay": pay,
            "posted_date": posted_date,
            "apply_by": "Not listed",  # Greenhouse doesn't usually provide this
            "url": apply_url,
            "source": "Greenhouse",
        }

    except Exception as e:
        log.error(f"Error parsing Greenhouse job: {e}")
        return None


def _format_date(iso_date: str) -> str:
    """Converts '2026-05-07T14:30:00-05:00' to 'May 7, 2026'"""
    if not iso_date:
        return "Not listed"
    try:
        # Handle ISO format with timezone offset
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return dt.strftime("%B %-d, %Y")  # e.g. "May 7, 2026"
    except Exception:
        return iso_date  # Return original if parsing fails


def _extract_pay_from_metadata(metadata: list) -> str:
    """
    Some Greenhouse companies include salary in custom metadata fields.
    We try to find it by looking for common field names.
    Returns 'Not listed' if nothing is found.
    """
    if not metadata:
        return "Not listed"

    # Common field names companies use for salary/pay
    pay_keywords = ["salary", "pay", "compensation", "wage", "rate"]

    for field in metadata:
        field_name = field.get("name", "").lower()
        field_value = field.get("value", "")

        if any(kw in field_name for kw in pay_keywords) and field_value:
            return str(field_value)

    return "Not listed"
