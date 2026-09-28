# 🧭 Opportunity Scout

[![Automated Daily Scout](https://github.com/marinusnorvor/opportunity-scout-/actions/workflows/daily_finder.yml/badge.svg)](https://github.com/marinusnorvor/opportunity-scout-/actions/workflows/daily_finder.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests Passing](https://img.shields.io/badge/tests-28%20passing-brightgreen.svg)]()

An autonomous, multi-agent intelligence system that discovers, deep-verifies, and delivers authentic technical and non-technical internships worldwide and across Ghana. 

Every evening at **6:00 PM GMT**, the system runs hands-free on GitHub Actions, audits real application forms to eliminate dead links and scams, categorizes compensation and travel/housing funding using Groq and Gemini AI, updates a live Google Sheet, and delivers a balanced **Top 3 Daily Digest** directly to my inbox.

---

## 💡 Why I Built This

Finding good student internships and graduate trainee opportunities as a young professional in Ghana (or anywhere in Africa) is frustrating:
1. **Broken and Expired Links:** Most job aggregators ping a URL, see a `200 OK`, and declare it active—even if the page actually says *"This vacancy has closed"* or silently redirected to a generic home screen.
2. **Ghost Jobs & Pay-to-Work Scams:** Too many listings demand "application processing fees" or "security deposits" before interviews.
3. **Tunnel Vision on Tech:** Most automated tools only track software engineering. Students in finance, operations, accounting, HR, health, and law are left searching manually.
4. **Funding Confusion:** When an opportunity is abroad, it's often unclear whether it's truly fully funded (flights + housing + stipend) or if you're expected to self-fund thousands of dollars.

**Opportunity Scout** fixes this with a 4-agent pipeline that conducts real due diligence on every single URL before it ever touches the database or email digest.

---

## 🤖 The Multi-Agent Architecture

```
[ AGENT 1: SCOUT ]
  ├── Jobberman Ghana & Verified Enterprise Hubs (Hubtel, Amalitech, MEST, Telecel)
  ├── Prestigious International Research Portals (CERN, EPFL, OIST, KAUST, ETH Zurich)
  ├── Global Remote Feeds (RemoteOK & Remotive across all job families)
  └── Enterprise ATS Boards (Greenhouse, Lever, Ashby)
         │
         ▼
[ AGENT 2: INVESTIGATOR (Deep Due Diligence) ]
  ├── DOM Audit: Confirms presence of <form>, file upload inputs, or verified apply CTAs
  ├── Soft-404 Detection: Catches URLs that silently bounce to generic /careers catalogs
  ├── Anti-Scam Sentry: Flags and drops registration/training fees and cryptocurrency requests
  └── Company Dossier: Compiles organization overview, headquarters, type, and credibility
         │
         ▼
[ AGENT 3: COGNITIVE EXTRACTION (Dual LLM Router) ]
  ├── Primary: Groq Cloud (openai/gpt-oss-20b) for sub-second structured JSON extraction
  ├── Secondary: Google Gemini (gemini-3.6-flash) automatic failover
  ├── Dual Head/Tail Slicing: Captures requirements at the top and footer stipend details
  └── Extracted Fields: Field, Work Mode, Compensation, Location, Outside-Ghana Funding Tier, Deadline
         │
         ▼
[ AGENT 4: CURATOR & DISPATCH ]
  ├── Balanced Quota Selection: 1 Ghana Local + 1 Fully Funded International + 1 Global Remote Paid
  ├── Master Logging: Appends verified rows with dossiers to Google Sheets (or CSV fallback)
  └── Morning Dispatch: Sends a responsive HTML email preview/digest with direct apply links
```

---

## 🎯 Daily Balanced Quota

To prevent fatigue, the system curates a balanced **Top 3** every day at **6:00 PM GMT**:

| Slot | Target Category | Example Verified Roles |
| :--- | :--- | :--- |
| **Slot 1** | **Ghana Local Enterprise** | Hubtel Ghana, Amalitech, MEST Africa, Telecel Ghana |
| **Slot 2** | **Tier-1 Fully Funded International** | CERN Summer Student Programme, EPFL E3 Fellowship, OIST Research Internships |
| **Slot 3** | **Global Remote Paid** | Operations, Marketing, People/HR, or Software roles open worldwide via RemoteOK & Remotive |

---

## 🛠️ Complete Setup Guide

You can run this project locally on your machine or deploy it to run 24/7 serverless on GitHub Actions for free.

### Prerequisites
- Python 3.10 or higher (Python 3.11+ recommended)
- A Google Cloud Service Account (for Google Sheets access)
- A free Groq Cloud API key
- A free Google Gemini API key (optional fallback)
- A Gmail account with an App Password (for email alerts)

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/marinusnorvor/opportunity-scout-.git
cd opportunity-scout-
```

Create and activate a virtual environment:

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

### Step 2: Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and fill in your details:

```ini
# Google Sheets Integration
GOOGLE_SHEET_ID=your_google_sheet_id_here
GOOGLE_SERVICE_ACCOUNT_PATH=credentials/service_account.json

# Email Notification Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_16_character_gmail_app_password
RECIPIENT_EMAIL=your_email@gmail.com

# LLM Providers (Free Tiers)
GROQ_API_KEY=gsk_your_groq_api_key_here
GEMINI_API_KEY=AIzaSy_your_gemini_api_key_here
```

---

### Step 3: Setting Up Google Sheets (Free)

1. Go to [Google Sheets](https://sheets.new) and create a blank spreadsheet.
2. Name it **Opportunity Scout 2026** (or anything you like).
3. Copy the Sheet ID from the browser URL:
   `https://docs.google.com/spreadsheets/d/<COPY_THIS_SHEET_ID>/edit`
4. Set up a **Google Cloud Service Account** in the [Google Cloud Console](https://console.cloud.google.com/):
   - Enable the **Google Sheets API** and **Google Drive API**.
   - Create a service account (e.g., `id-sheets-bot@...`).
   - Create and download a **JSON key**.
   - Place this file at `credentials/service_account.json` (ensure it remains gitignored).
5. **Important:** Open your Google Sheet, click **Share**, and grant **Editor** access to your service account email (`id-sheets-bot@...`).

---

### Step 4: Getting Free API Keys

1. **Groq Cloud API (Primary LLM):**
   - Head to [console.groq.com](https://console.groq.com/) and generate a free API key.
   - Groq provides free, ultra-low latency inference on open-source models (`openai/gpt-oss-20b`).
2. **Google Gemini API (Fallback LLM):**
   - Head to [Google AI Studio](https://aistudio.google.com/) and grab a free API key for `gemini-3.6-flash`.
3. **Gmail App Password (Email Digest):**
   - Go to your Google Account Settings → **Security** → Enable **2-Step Verification**.
   - Under 2-Step Verification, select **App passwords**.
   - Create a password named `Opportunity Scout` and copy the 16-character code into `SMTP_PASSWORD`.

---

### Step 5: Running Locally

You can test the pipeline anytime from the command line:

```bash
# 1. Preview mode (Dry run):
# Audits real sites, queries AI, and renders output/latest_email.html without sending SMTP
python -m src.main --dry-run

# 2. Fast test run (3 candidates per channel, skip deep web search):
python -m src.main --dry-run --limit 3 --skip-search

# 3. Full live execution:
python -m src.main
```

Check the generated preview email in your browser by opening `output/latest_email.html` or inspect `output/opportunities.csv`.

---

## ⏰ Automated 24/7 GitHub Actions Setup

The repository is configured to run completely free and serverless via GitHub Actions.

### Setting Repository Secrets
In your GitHub repo, navigate to **Settings → Secrets and variables → Actions** and add the following repository secrets:

| Secret Name | Description |
| :--- | :--- |
| `GOOGLE_SHEET_ID` | Your Google Spreadsheet ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | The entire contents of your `service_account.json` key file |
| `GROQ_API_KEY` | Your Groq Cloud API key |
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `SMTP_USER` | Your sending Gmail address |
| `SMTP_PASSWORD` | Your 16-character Gmail App Password |
| `RECIPIENT_EMAIL` | The email address where you want to receive the daily digest |
| `SMTP_HOST` | *(Optional, defaults to `smtp.gmail.com`)* |
| `SMTP_PORT` | *(Optional, defaults to `587`)* |

### Schedule
The workflow in [`.github/workflows/daily_finder.yml`](file:///.github/workflows/daily_finder.yml) automatically runs every day at:
- **`0 18 * * *` (6:00 PM GMT / Ghana Time)**

You can also trigger it manually at any time by going to the **Actions** tab on GitHub, selecting **Daily Autonomous Opportunity Scout**, and clicking **Run workflow**.

---

## 🧪 Testing

The system includes a 28-test verification suite covering edge cases, link verification, soft-404 detection, and LLM output sanitization:

```bash
pytest -v
```

All 28 tests pass in under 1 second.

---

## 📂 Project Structure

```
opportunity-scout-/
├── .github/
│   └── workflows/
│       └── daily_finder.yml       # 24/7 GitHub Actions runner (6:00 PM GMT cron)
├── credentials/                   # Local service account credentials (gitignored)
├── data/
│   └── seen_jobs.json             # SHA-256 deduplication cache (persists between runs)
├── output/                        # Dry-run email previews and CSV logs
├── src/
│   ├── agents/
│   │   ├── scout_agent.py         # Multi-channel raw candidate ingestion
│   │   ├── investigator_agent.py  # Live DOM audit & company intelligence dossier
│   │   ├── cognitive_agent.py     # Groq + Gemini LLM extraction & JSON cleaner
│   │   └── curator_agent.py       # Balanced quota scoring & Sheets/Email delivery
│   ├── scrapers/
│   │   ├── base_scraper.py        # Safe HTTP requests, SSL fallback, and retries
│   │   ├── jobberman_scraper.py   # Jobberman Ghana & local enterprise hubs
│   │   ├── research_portals.py    # CERN, EPFL, OIST, KAUST fellowship scrapers
│   │   ├── remote_feeds.py        # RemoteOK & Remotive global feeds
│   │   ├── ats_scraper.py         # Direct Greenhouse & Lever API scraper
│   │   └── deep_search.py         # Web discovery engine
│   ├── notifications/
│   │   └── email_notifier.py      # Responsive HTML email digest with cards
│   ├── storage/
│   │   ├── sheets_adapter.py      # Google Sheets live row logging
│   │   └── deduplicator.py        # Hash-based duplicate prevention
│   ├── models.py                  # Pydantic v2 schemas
│   └── main.py                    # Main pipeline orchestrator & CLI
├── tests/                         # 28 comprehensive unit tests
├── DEVELOPMENT_PLAN.md            # Technical roadmap and safety constraints
├── requirements.txt
└── README.md
```

---

## 👤 Author

Built by **Marinus Norvor**  
GitHub: [@marinusnorvor](https://github.com/marinusnorvor)

Feel free to open an issue or submit a pull request if you'd like to suggest additional fellowship programs or verified local hubs!
