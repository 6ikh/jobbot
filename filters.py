"""
utils/filters.py — Filters jobs by title keywords and exclusion rules.

This is where we decide whether a job is worth posting.
We check two things:
  1. Does the title match one of our TARGET_TITLES?
  2. Does the title contain any EXCLUDE_TITLE_KEYWORDS?
"""

import logging
from config import TARGET_TITLES, EXCLUDE_TITLE_KEYWORDS

log = logging.getLogger(__name__)


def is_valid_job(job: dict) -> bool:
    """
    Returns True if a job should be posted, False if it should be skipped.

    A job is valid if:
    - Its title contains at least one keyword from TARGET_TITLES
    - Its title does NOT contain any keyword from EXCLUDE_TITLE_KEYWORDS
    """
    title = job.get("title", "").lower()

    if not title:
        return False

    # Check if this is a senior/excluded level job
    for exclude_kw in EXCLUDE_TITLE_KEYWORDS:
        if exclude_kw.lower() in title:
            log.debug(f"⛔ Excluded '{job['title']}' — matched exclusion '{exclude_kw}'")
            return False

    # Check if the title matches any of our target roles
    for target_kw in TARGET_TITLES:
        if target_kw.lower() in title:
            log.debug(f"✅ Matched '{job['title']}' — matched target '{target_kw}'")
            return True

    # Title didn't match any target
    log.debug(f"⏭️  Skipped '{job['title']}' — no target keyword match")
    return False
