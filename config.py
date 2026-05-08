"""
config.py — All target companies, job titles, and filter keywords.
Edit this file to add/remove companies or job titles.
"""

# ─────────────────────────────────────────────
# GREENHOUSE ATS COMPANIES
# These companies use Greenhouse for hiring.
# The key is the "board_token" used in their API URL.
# Find it by visiting: https://boards.greenhouse.io/COMPANY_NAME
# ─────────────────────────────────────────────
GREENHOUSE_COMPANIES = {
    # MedTech
    "bostonscientifc": "Boston Scientific",
    "stryker": "Stryker",
    "medtronic": "Medtronic",
    "abbott": "Abbott",
    "bd": "Becton Dickinson",

    # Defense / Aerospace
    "collins": "Collins Aerospace",
    "l3harris": "L3Harris",

    # Consumer Goods
    "pepsico": "PepsiCo",
    "kraftheinz": "Kraft Heinz",
    "generalmills": "General Mills",
    "mondelez": "Mondelez",
    "colgatepalmolive": "Colgate-Palmolive",

    # Tech / EV
    "apple": "Apple",
    "rivian": "Rivian",
    "lucidmotors": "Lucid Motors",

    # Industrial
    "3m": "3M",
    "emerson": "Emerson Electric",
    "parkerhannifin": "Parker Hannifin",
    "eaton": "Eaton",
    "rockwellautomation": "Rockwell Automation",

    # Consulting
    "deloitte": "Deloitte",
    "accenture": "Accenture",
    "westmonroe": "West Monroe",

    # Retail / Ecommerce
    "nike": "Nike",
    "underarmour": "Under Armour",
}

# ─────────────────────────────────────────────
# LEVER ATS COMPANIES
# These companies use Lever for hiring.
# The key is the company slug used in their Lever URL.
# Find it by visiting: https://jobs.lever.co/COMPANY_SLUG
# ─────────────────────────────────────────────
LEVER_COMPANIES = {
    # Consulting
    "mckinsey": "McKinsey",
    "bain": "Bain",
    "oliverwyman": "Oliver Wyman",

    # Tech
    "salesforce": "Salesforce",

    # Retail
    "costco": "Costco",
}

# ─────────────────────────────────────────────
# WORKDAY COMPANIES
# These companies use Workday for hiring.
# Each entry needs a custom base URL.
# ─────────────────────────────────────────────
WORKDAY_COMPANIES = [
    {
        "name": "Tesla",
        "url": "https://www.tesla.com/careers/search#/?",
        "workday_id": "tesla",
    },
    {
        "name": "Amazon",
        "url": "https://www.amazon.jobs/en/search.json",
        "workday_id": "amazon",
    },
    {
        "name": "Walmart",
        "url": "https://careers.walmart.com/results",
        "workday_id": "walmart",
    },
    {
        "name": "Boeing",
        "url": "https://jobs.boeing.com/search-jobs",
        "workday_id": "boeing",
    },
    {
        "name": "Lockheed Martin",
        "url": "https://www.lockheedmartinjobs.com/search-jobs",
        "workday_id": "lockheedmartin",
    },
]

# ─────────────────────────────────────────────
# TARGET JOB TITLES
# Only jobs with these keywords in their title will be posted.
# Matching is case-insensitive and partial (e.g. "analyst" matches "Supply Chain Analyst").
# ─────────────────────────────────────────────
TARGET_TITLES = [
    # People-Facing / Sales
    "commercial leadership development",
    "sales leadership development",
    "business development associate",
    "client services associate",
    "implementation consultant",

    # Supply Chain / Operations
    "supply chain analyst",
    "procurement analyst",
    "sourcing analyst",
    "operations analyst",
    "demand planning analyst",
    "supply chain leadership development",
    "operations leadership development",
    "logistics analyst",
    "vendor management analyst",
    "strategic sourcing analyst",

    # Program / Project Management
    "associate program manager",
    "project coordinator",
    "operations program manager",
    "technical program manager associate",
    "pmo analyst",

    # Consulting / Strategy
    "associate consultant",
    "business analyst",
    "operations consultant",
    "supply chain consultant",
    "strategy & operations associate",
    "strategy and operations associate",
]

# ─────────────────────────────────────────────
# EXCLUSION KEYWORDS
# Jobs with ANY of these in the title will be skipped.
# ─────────────────────────────────────────────
EXCLUDE_TITLE_KEYWORDS = [
    "senior",
    " sr ",
    "sr.",
    "staff",
    "principal",
    "director",
    "manager",
    " lead",
    "architect",
    "vp ",
    "vice president",
    "head of",
]
