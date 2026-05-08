"""
utils/deduplication.py — Tracks jobs we've already posted.

We store a simple set of job IDs in a JSON file called seen_jobs.json.
Before posting any job, we check if its ID is already in this file.
If it is, we skip it. If not, we post it and add the ID to the file.
"""

import json
import os
import logging

log = logging.getLogger(__name__)

# Path to the file that stores seen job IDs
SEEN_JOBS_FILE = "seen_jobs.json"


def load_seen_jobs() -> set:
    """
    Load the set of job IDs we've already posted.
    Returns an empty set if the file doesn't exist yet.
    """
    if not os.path.exists(SEEN_JOBS_FILE):
        log.info(f"No {SEEN_JOBS_FILE} found — starting fresh.")
        return set()

    try:
        with open(SEEN_JOBS_FILE, "r") as f:
            data = json.load(f)
            # JSON stores lists, we want a set for fast lookups
            return set(data)
    except (json.JSONDecodeError, IOError) as e:
        log.error(f"Error reading {SEEN_JOBS_FILE}: {e}")
        return set()


def save_seen_jobs(seen_jobs: set):
    """
    Save the updated set of job IDs back to disk.
    We convert the set to a list because JSON doesn't support sets.
    """
    try:
        with open(SEEN_JOBS_FILE, "w") as f:
            json.dump(list(seen_jobs), f, indent=2)
        log.info(f"💾 Saved {len(seen_jobs)} job IDs to {SEEN_JOBS_FILE}")
    except IOError as e:
        log.error(f"Error saving {SEEN_JOBS_FILE}: {e}")
