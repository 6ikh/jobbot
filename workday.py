"""
scrapers/workday.py — Scrapes jobs from companies using Workday ATS.

⚠️  IMPORTANT NOTE ABOUT WORKDAY:
Workday is much harder to scrape than Greenhouse or Lever.
Most Workday sites require JavaScript rendering or have anti-scraping protections.

This module uses a two-approach strategy:
  1. Try Workday's internal JSON API endpoint first (works for many companies)
  2. Fall back gracefully if blocked

Companies like Tesla, Amazon, Boeing use Workday but may have their own
custom career pages layered on top of it.

For companies that block scraping, we log a warning and skip them.
You can add Playwright-based scraping later for specific stubborn companies.

ADDING A NEW WORKDAY COMPANY:
Find the company's Workday tenant name. It's usually in their career URL:
  https://TENANT.wd1.myworkdayjobs.com/careers
The tenant is the subdomain before ".wd1.myworkdayjobs.com"
"""

import logging
import requests
from datetime import datetime
from config import WORKDAY_COMPANIES

log = logging.getLogger(__name__)

# Common Workday API pattern — many companies expose this endpoint
WORKDAY_API_PATTERN = "https://{tenant}.wd1.myworkdayjobs.com/wday/cxs/{tenant}/{job_site}/jobs"

# Headers that mimic a real browser (required to avoid blocks)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# Known Workday tenants for our target companies
# Format: company_name -> (tenant, job_site_name)
WORKDAY_TENANTS = {
    "Tesla": ("tesla", "Tesla_External"),
    "Boeing": ("boeing", "external"),
    "Lockheed Martin": ("lmco", "Experienced"),
    "Honeywell": ("honeywell", "Honeywell"),
    "GE": ("ge", "GE_ExternalSite"),
    "Caterpillar": ("cat", "CatCareers"),
    "Raytheon Technologies": ("rtx", "RTX"),
    "Northrop Grumman": ("northropgrumman", "Northrop_Grumman_External_Site"),
    "General Dynamics": ("gd", "GD_External"),
    "Procter & Gamble": ("pg", "External"),
    "Coca-Cola": ("coke", "Coca-Cola-Bottling-Co-Consolidated"),
    "Unilever": ("unileverna", "Professional"),
    "Google": ("google", "googleexternal"),
    "Microsoft": ("microsoftcareers", "External"),
    "Ford": ("ford", "ford-ext"),
    "GM": ("generalmotors", "Global"),
    "Deloitte": ("deloittecareers", "DeloitteUSA"),
    "KPMG": ("kpmg", "KPMG_Experienced"),
    "PwC": ("pwc", "External_Career_Site"),
    "EY": ("ey", "EY-Global-Unified-Careers"),
    "BCG": ("bcg", "BCGExternal"),
    "McKinsey": ("mckinsey", "external"),
    "SAP": ("sap", "SAPCareers"),
    "Oracle": ("oraclecorporation", "oracle-careers"),
    "IBM": ("ibm", "IBM-Careers"),
    "Walmart": ("walmart", "External"),
    "Target": ("target", "target-stores"),
    "Home Depot": ("homedepot", "External"),
    "Nike": ("nike", "External_Career_Site"),
    "Zimmer Biomet": ("zimmerbiomet", "ZimmerBiomet_External"),
    "Edwards Lifesciences": ("edwards", "Edwards"),
    "Baxter International": ("baxter", "Baxter"),
    "Intuitive Surgical": ("intuitivesurgical", "Intuitive-Surgical"),
    "Smith & Nephew": ("smithnephew", "global-careers"),
    "Siemens": ("siemens", "standard"),
    "Illinois Tool Works": ("itw", "ITW_Careers"),
    "Parker Hannifin": ("parker", "Parker-External"),
    "Rivian": ("rivian", "Rivian"),
    "Lucid Motors": ("lucidmotors", "External"),
    "Stellantis": ("stellantis", "Stellantis_External"),
    "Under Armour": ("underarmour", "underarmour"),
    "Costco": ("costco", "External"),
    "3M": ("3m", "3M_External_Requisition"),
}


def scrape_workday_companies() -> list:
    """
    Loops through all Workday companies and attempts to scrape their jobs.
    """
    all_jobs = []

    for tenant_name, (tenant, job_site) in WORKDAY_TENANTS.items():
        log.info(f"🏢 Scraping Workday: {tenant_name}")
        jobs = _fetch_workday_jobs(tenant_name, tenant, job_site)
        log.info(f"   Found {len(jobs)} jobs at {tenant_name}")
        all_jobs.extend(jobs)

    return all_jobs


def _fetch_workday_jobs(company_name: str, tenant: str, job_site: str) -> list:
    """
    Attempts to fetch jobs from Workday's internal API.

    Workday's CXS (Candidate Experience) API accepts POST requests
    with a JSON body to filter and paginate jobs.
    """
    api_url = WORKDAY_API_PATTERN.format(tenant=tenant, job_site=job_site)

    # Workday's API uses a POST with JSON body for filtering
    payload = {
        "appliedFacets": {},      # No filters — get all jobs
        "limit": 20,               # Max jobs per request
        "offset": 0,               # Start from the beginning
        "searchText": "",          # No keyword search — we filter ourselves
    }

    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=HEADERS,
            timeout=15,
        )

        if response.status_code in (403, 429):
            log.warning(f"   ⛔ {company_name} blocked scraping (status {response.status_code})")
            log.warning(f"      Consider using Playwright for this company in the future")
            return []

        if response.status_code == 404:
            log.warning(f"   ⚠️  {company_name} Workday URL not found — tenant/job_site may be wrong")
            return []

        response.raise_for_status()
        data = response.json()

    except requests.exceptions.Timeout:
        log.error(f"   ⏱️  Timeout fetching {company_name} from Workday")
        return []
    except requests.exceptions.RequestException as e:
        log.error(f"   ❌ Request error for {company_name}: {e}")
        return []
    except ValueError:
        log.error(f"   ❌ Invalid JSON from Workday for {company_name}")
        return []

    jobs = []
    raw_jobs = data.get("jobPostings", [])

    for raw_job in raw_jobs:
        job = _parse_workday_job(raw_job, company_name, tenant)
        if job:
            jobs.append(job)

    return jobs


def _parse_workday_job(raw_job: dict, company_name: str, tenant: str) -> dict | None:
    """
    Converts a Workday API job posting into our standardized dict.

    Workday job fields vary by company but common ones:
      - title: job title string
      - externalPath: relative URL path like "/External_Career_Site/job/Austin-TX/title_R123"
      - locationsText: "Austin, TX" or comma-separated if multiple
      - postedOn: "Posted 2 Days Ago" (relative text)
      - bulletFields: list of strings with job highlights
    """
    try:
        title = raw_job.get("title", "")
        external_path = raw_job.get("externalPath", "")
        location = raw_job.get("locationsText", "Not specified")
        posted_relative = raw_job.get("postedOn", "")

        # Build the full apply URL
        apply_url = f"https://{tenant}.wd1.myworkdayjobs.com{external_path}"

        # Create a unique ID from the path (it contains job requisition number)
        unique_id = f"workday_{tenant}_{external_path.replace('/', '_')}"

        return {
            "id": unique_id,
            "title": title,
            "company": company_name,
            "location": location,
            "pay": "Not listed",          # Workday rarely shows pay in API
            "posted_date": posted_relative or "Not listed",
            "apply_by": "Not listed",
            "url": apply_url,
            "source": "Workday",
        }

    except Exception as e:
        log.error(f"Error parsing Workday job: {e}")
        return None
