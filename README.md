# 🌐 Autonomous Opportunity Finder & Verification Engine

[![Automated Daily Scout](https://github.com/your-username/your-repo/actions/workflows/daily_finder.yml/badge.svg)](https://github.com/your-username/your-repo/actions/workflows/daily_finder.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade autonomous agent pipeline that scours the internet daily for **fully funded** and **high-stipend remote** technical internships, filters out predatory scams and ghost jobs, verifies eligibility for **Ghana-based undergraduates**, logs qualified listings into **Google Sheets**, and delivers a curated **Top 3 Daily Digest** directly to your email.

---

## 🎯 Target Tracks (18 Core Specializations)

The system actively monitors and categorizes opportunities across:

1. **AI Solutions / Agent Engineer Intern**
2. **Machine Learning Operations (MLOps) Intern**
3. **Embedded Systems Intern**
4. **Robotics / Mechatronics Intern**
5. **Hardware Engineering Intern**
6. **Controls & Instrumentation Intern**
7. **Process Automation / Industrial IoT (IIoT) Intern**
8. **Software Engineering (SWE) Intern**
9. **Backend Developer Intern (Python / Java)**
10. **Systems / Cloud Engineering Intern**
11. **Network Engineering / Infrastructure Intern**
12. **Cybersecurity / SOC Analyst Intern**
13. **Associate Product Manager (APM) Intern**
14. **Solutions Architecture / Solutions Engineering Intern**
15. **Technical Business Analyst Intern**
16. **Quantitative Modeling / Data Science Intern**
17. **Computational Research / Applied Math Intern**
18. **Developer Relations (DevRel) / Technical Community Intern**

---

## 🤖 Multi-Agent System (MAS) Architecture

The platform operates as an orchestrated team of **4 specialized autonomous agents**:

```
[ 1. SCOUT AGENT (Broad Ingestion) ]
  ├── Jobberman Ghana (All categories: Banking, Healthcare, Sales, Admin, Tech)
  ├── Ghana Enterprise Hubs (Zeepay, Hubtel, Amalitech, MEST, MTN)
  ├── Global Remote Feeds (Remotive across all fields, RemoteOK)
  ├── International Fellowship Hubs (United Nations, WHO, CERN, EPFL, OIST, KAUST)
  └── Wildcard ATS Engine (Greenhouse, Lever, Ashby - Any discipline)
                 │
                 ▼
[ 2. INVESTIGATOR AGENT (Deep Due Diligence & Link Audit) ]
  ├── Deep DOM Audit (Checks for active application forms, input file upload, apply buttons)
  ├── Expired-Job Banner Scan (Automatically drops closed, expired, or filled roles)
  ├── Company Intelligence Dossier (Researches company mission, HQ, size, and credibility)
  └── Fraud & Scam Sentry (Discards fee-charging extortion and fake recruiters)
                 │
                 ▼
[ 3. COGNITIVE EXTRACTION AGENT (Groq + Gemini Dual LLM Router) ]
  ├── Primary: Groq LLaMA Cloud (Ultra-fast structured JSON parsing under 400ms)
  ├── Failover: Google Gemini 3.6 Flash (Deep reasoning and quota fallback)
  └── Structured Fields: Field, Work Mode (Remote/Onsite), Paid/Unpaid, Location, Outside-Ghana Funding
                 │
                 ▼
[ 4. CURATOR & DISPATCH AGENT (Delivery) ]
  ├── Balanced Quota Ranker: Guarantees 1 Ghana Local + 1 Fully Funded Intl + 1 Global Remote
  ├── Google Sheets API: Logs rich rows with Company Dossiers
  └── Email Dispatcher: Delivers responsive HTML Top 3 morning digest
```

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
# Google Sheets (Optional for local testing; defaults to output/opportunities.csv)
GOOGLE_SHEET_ID=your_google_sheet_id_here
GOOGLE_SERVICE_ACCOUNT_PATH=credentials/service_account.json

# Email Notifications (Optional for local testing; defaults to output/latest_email.html)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
RECIPIENT_EMAIL=your_email@gmail.com
```

### 3. Run the Pipeline

```bash
# Run in Dry-Run mode (inspect CSV in output/ and HTML preview in browser):
python -m src.main --dry-run

# Run full live scout:
python -m src.main

# Fast test run with limits:
python -m src.main --limit 5 --skip-search
```

---

## 🤖 GitHub Actions Setup (100% Free 24/7 Automation)

You can run this pipeline completely serverless with zero monthly hosting costs using GitHub Actions.

### Step 1: Push to GitHub

```bash
git add .
git commit -m "feat: complete autonomous opportunity finder"
git remote add origin https://github.com/your-username/your-repo.git
git push -u origin main
```

### Step 2: Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** in your GitHub repository and add:

| Secret Name | Description | Example |
| :--- | :--- | :--- |
| `GOOGLE_SHEET_ID` | The ID from your Google Sheet URL | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full JSON content of your Google Cloud Service Account key | `{"type":"service_account",...}` |
| `SMTP_HOST` | Mail server host | `smtp.gmail.com` |
| `SMTP_PORT` | Mail server port | `587` |
| `SMTP_USER` | Sending email address | `yourname@gmail.com` |
| `SMTP_PASSWORD` | Google Account App Password | `abcd efgh ijkl mnop` |
| `RECIPIENT_EMAIL` | Where to send the Top 3 email | `yourname@gmail.com` |

### Step 3: Automated Schedule & Manual Trigger

* **Schedule:** The workflow `.github/workflows/daily_finder.yml` automatically triggers every morning at **08:00 UTC (8:00 AM Ghana Time)**.
* **Manual Run:** Go to the **Actions** tab in GitHub, select **Daily Autonomous Opportunity Scout**, and click **Run workflow**.

---

## 📊 Google Sheets Configuration

1. Create a new Google Sheet at [sheets.new](https://sheets.new).
2. Share the spreadsheet with your Google Cloud Service Account email (with **Editor** permissions).
3. Copy the Sheet ID from the URL (`https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`).
4. The system will automatically create and populate the following columns:
   * **Discovered Date**
   * **Track**
   * **Role Title**
   * **Company / Lab**
   * **Funding Tier**
   * **Benefits Breakdown** (✈️ Flight, 🏠 Housing, 💵 Stipend, 🛂 Visa)
   * **Location**
   * **Deadline**
   * **Ranking Score**
   * **Application URL**
   * **Verification Status**
   * **Source Channel**

---

## 🧪 Running Tests

The test suite validates scam detection, visa disqualification, funding tier classifications, and ranking weights:

```bash
pytest -v
```

---

## 📁 Project Structure

```
newProject/
├── .github/
│   └── workflows/
│       └── daily_finder.yml        # GitHub Actions 24/7 cron runner
├── config/
│   ├── candidate_profile.json      # Ghana Undergrad profile & funding rules
│   └── target_tracks.json          # 18 Technical tracks & query keywords
├── data/
│   └── seen_jobs.json              # SHA-256 deduplication cache
├── output/                         # Local run artifacts (CSV & HTML preview)
├── src/
│   ├── models.py                   # Pydantic v2 domain schemas
│   ├── scrapers/                   # ATS, Deep Search, Research Portals, Remote feeds
│   ├── verification/               # Scam, domain, and fee detectors
│   ├── evaluation/                 # Eligibility filter & Top-3 ranker
│   ├── storage/                    # Google Sheets & Deduplication
│   ├── notifications/              # Responsive HTML email digest
│   └── main.py                     # CLI & pipeline runner
├── tests/                          # 13 comprehensive unit tests
├── requirements.txt
└── README.md
```

---

## 🛡️ License

MIT License. Designed for students, researchers, and engineers seeking verified global opportunities.
