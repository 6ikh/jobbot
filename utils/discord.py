"""
utils/discord.py — Sends job alerts to Discord via webhook.

A Discord webhook is a special URL that lets you POST messages
into a Discord channel without needing a full bot.

HOW TO GET YOUR WEBHOOK URL:
1. Open Discord
2. Go to the channel you want job alerts in
3. Click the gear icon (Edit Channel)
4. Click "Integrations" → "Webhooks"
5. Click "New Webhook"
6. Copy the Webhook URL
7. Add it to your GitHub repo as a Secret named DISCORD_WEBHOOK_URL
"""

import os
import time
import logging
import requests

log = logging.getLogger(__name__)

# The webhook URL is stored as an environment variable for security.
# Never hardcode it in your code!
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")


def format_job_message(job: dict) -> dict:
    """
    Formats a job dictionary into a Discord embed message.

    Discord embeds are rich message cards with colors, fields, and links.
    This creates the 🚨 New Entry-Level Opportunity format you requested.

    job dict should have:
        - title: str
        - company: str
        - location: str (optional)
        - pay: str (optional)
        - posted_date: str (optional)
        - apply_by: str (optional)
        - url: str
        - source: str (which ATS it came from)
    """

    title = job.get("title", "Unknown Title")
    company = job.get("company", "Unknown Company")
    location = job.get("location", "Not specified")
    pay = job.get("pay", "Not listed")
    posted_date = job.get("posted_date", "Not listed")
    apply_by = job.get("apply_by", "Not listed")
    url = job.get("url", "")

    # Build the message body
    # Using Discord's markdown formatting
    content = (
        f"🚨 **New Entry-Level Opportunity**\n\n"
        f"**Company:** {company}\n"
        f"**Job Title:** {title}\n"
        f"**Location:** {location}\n"
        f"**Experience Level:** Entry Level\n"
        f"**Pay:** {pay}\n"
        f"**Posted:** {posted_date}\n"
        f"**Apply By:** {apply_by}\n\n"
        f"**Apply:**\n{url}"
    )

    # Discord webhook payload format
    return {
        "content": content,
        # Optional: username override for the webhook
        "username": "Job Alert Bot 🤖",
    }


def send_discord_alert(job: dict) -> bool:
    """
    Sends a single job alert to Discord.

    Returns True if successful, False if it failed.

    Discord rate limits: 5 requests per 2 seconds per webhook.
    We add a small sleep to be safe.
    """
    if not DISCORD_WEBHOOK_URL:
        log.error("❌ DISCORD_WEBHOOK_URL environment variable is not set!")
        log.error("Add it to your GitHub Secrets or .env file.")
        return False

    payload = format_job_message(job)

    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=10  # Don't hang forever
        )

        # 204 = success (no content) for Discord webhooks
        if response.status_code in (200, 204):
            # Be polite to Discord's rate limiter — wait 1 second between posts
            time.sleep(1)
            return True
        else:
            log.error(f"Discord returned {response.status_code}: {response.text}")
            return False

    except requests.exceptions.Timeout:
        log.error("Discord request timed out.")
        return False
    except requests.exceptions.ConnectionError:
        log.error("Could not connect to Discord.")
        return False
    except Exception as e:
        log.error(f"Unexpected error sending to Discord: {e}")
        return False
