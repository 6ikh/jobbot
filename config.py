"""
config.py — All settings for the Discord Job Alert System.
Edit this file to change companies, job titles, or search settings.
"""

# ─────────────────────────────────────────────
# APIFY / LINKEDIN SEARCH SETTINGS
# ─────────────────────────────────────────────

# How many results to fetch per job title search
# Keep at 10-25 to stay within Apify free tier limits
APIFY_RESULTS_PER_SEARCH = 10

# Location to search within
APIFY_LOCATION = "United States"

# Job type filter
# Options: "full-time", "part-time", "contract", "temporary", "internship", "" (all)
APIFY_JOB_TYPE = "full-time"

# Experience level filter — this is the key one for entry-level focus
# Options: "internship", "entry_level", "associate", "mid_senior_level", "director", "" (all)
# Use "entry_level,associate" to catch both entry-level and associate postings
APIFY_EXPERIENCE_LEVEL = "entry_level,associate"


# ─────────────────────────────────────────────
# TARGET COMPANIES
# Jobs will only be posted if the company matches one of these.
# Matching is fuzzy — "Boston Scientific Corporation" matches "Boston Scientific"
# ─────────────────────────────────────────────
TARGET_COMPANIES_LIST = [
    # MedTech / Medical Device
    "Boston Scientific",
    "Stryker",
    "Medtronic",
    "Zimmer Biomet",
    "Abbott",
    "Becton Dickinson",
    "BD",
    "Edwards Lifesciences",
    "Baxter",
    "Intuitive Surgical",
    "Smith & Nephew",

    # Defense / Aerospace
    "Raytheon",
    "RTX",
    "Collins Aerospace",
    "Lockheed Martin",
    "Northrop Grumman",
    "General Dynamics",
    "L3Harris",
    "Boeing",
    "Honeywell",

    # Consumer Goods
    "PepsiCo",
    "Coca-Cola",
    "Procter & Gamble",
    "P&G",
    "Unilever",
    "Kraft Heinz",
    "General Mills",
    "Kellogg",
    "Mondelez",
    "Nestle",
    "Colgate-Palmolive",

    # Tech / EV
    "Tesla",
    "Apple",
    "Amazon",
    "Google",
    "Microsoft",
    "Rivian",
    "Lucid Motors",
    "Ford",
    "General Motors",
    "GM",
    "Stellantis",

    # Industrial
    "GE",
    "General Electric",
    "3M",
    "Caterpillar",
    "Emerson Electric",
    "Parker Hannifin",
    "Eaton",
    "Illinois Tool Works",
    "ITW",
    "Rockwell Automation",
    "Siemens",

    # Consulting
    "Deloitte",
    "KPMG",
    "PwC",
    "PricewaterhouseCoopers",
    "EY",
    "Ernst & Young",
    "Accenture",
    "McKinsey",
    "BCG",
    "Boston Consulting Group",
    "Bain",
    "Oliver Wyman",
    "West Monroe",

    # Cloud / Tech
    "AWS",
    "Amazon Web Services",
    "Salesforce",
    "Oracle",
    "SAP",
    "IBM",

    # Retail / Ecommerce
    "Walmart",
    "Target",
    "Home Depot",
    "Costco",
    "Nike",
    "Under Armour",
]


# ─────────────────────────────────────────────
# TARGET JOB TITLES
# Apify will search LinkedIn for each of these one by one.
# These are search queries — add "entry level" to get better results.
# Fewer searches = less Apify credit usage.
# ─────────────────────────────────────────────
TARGET_TITLES = [
    # Supply Chain / Operations
    "supply chain analyst",
    "procurement analyst",
    "operations analyst",
    "demand planning analyst",
    "logistics analyst",
    "strategic sourcing analyst",
    "vendor management analyst",

    # Leadership Development Programs
    "supply chain leadership development program",
    "operations leadership development program",
    "commercial leadership development program",
    "sales leadership development program",

    # Program / Project Management
    "associate program manager",
    "project coordinator",
    "PMO analyst",

    # Consulting / Strategy
    "associate consultant",
    "business analyst",
    "strategy operations associate",
]


# ─────────────────────────────────────────────
# EXCLUSION KEYWORDS
# Jobs with ANY of these words in the title are skipped.
# Uses word-boundary matching — "lead" won't block "leadership"
# ─────────────────────────────────────────────
EXCLUDE_TITLE_KEYWORDS = [
    "senior",
    "sr",
    "staff",
    "principal",
    "director",
    "manager",
    "lead",
    "architect",
    "vp",
    "vice president",
    "head of",
]
