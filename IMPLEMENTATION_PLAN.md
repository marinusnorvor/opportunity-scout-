# 📋 Multi-Agent Opportunity Intelligence System
## Comprehensive Implementation Plan (v2.0)

> **Document Status:** Planning & Architectural Blueprint  
> **Target Directory:** `C:\Users\marin\OneDrive\Desktop\newProject`  
> **Last Updated:** September 22, 2026  

---

## 1. Executive Summary & Goals

This project upgrades the existing internship scout into an autonomous, field-agnostic **Multi-Agent System (MAS)** powered by **Groq** (`llama-3.3-70b-versatile`) and **Google Gemini** (`gemini-2.5-flash`).

### Core Objectives:
1. **Field-Agnostic Discovery:** Remove all hardcoded technical-only restrictions. Find internships across **all fields** (Business, Healthcare, Law, Finance, Tech, Engineering, Media, Arts, Agriculture, NGOs, etc.).
2. **Deep Investigative Due Diligence (No Shallow Pings):**
   * Actually load and audit destination pages to confirm an active application form or submission button exists.
   * Conduct background intelligence on the hiring organization (what they do, headquarters, credibility, mission).
3. **Structured Attribute Intelligence:**
   * **Field / Industry** (e.g., Finance, Public Health, Software, Law)
   * **Work Mode** (`Remote`, `Onsite`, `Hybrid`)
   * **Compensation Status** (`Paid` with stipend details vs `Unpaid`)
   * **Location** (Specific city/country, flagged as Ghana vs Outside Ghana)
   * **Funding Status (If Outside Ghana):**
     * 🥇 **Fully Funded:** Flight + Housing + Monthly Stipend covered
     * 🥈 **Partially Funded:** Stipend or housing assistance
     * 🥉 **Self-Funded / Unfunded**
   * **Application Deadline** (Exact date or Rolling)
4. **Dual-Model Resilience (Groq + Gemini Free Tiers):**
   * Blazing-fast inference via Groq Cloud (under 400ms per record).
   * Automatic failover to Gemini Flash if Groq hits rate limits or encounters multi-page guidelines.
5. **Authentic Ghana Ingestion:** Direct integration with Ghanaian employment boards (Jobberman Ghana) and local multinational innovation hubs.
6. **Persistence & Delivery:**
   * Updated Google Sheets columns reflecting the company dossier and new attributes.
   * Curated Top 3 daily email digest with an organization spotlight.

---

## 2. Multi-Agent System (MAS) Architecture

```
                    ┌────────────────────────────────────────────────────────┐
                    │               1. SCOUT AGENT (Ingestion)               │
                    │  - Jobberman Ghana (All Categories & Internships)      │
                    │  - Global Remote Feeds (Remotive, RemoteOK)            │
                    │  - International Fellowship Hubs (UN, CERN, Erasmus)   │
                    │  - Wildcard ATS Dorker (Greenhouse, Lever, Ashby)      │
                    └───────────────────────────┬────────────────────────────┘
                                                │ Raw URLs & Postings
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │       2. INVESTIGATOR AGENT (Deep Due Diligence)       │
                    │  - Deep DOM Inspection: Confirms active "Apply" form   │
                    │  - Expired-Job Banner Scan: Drops filled/closed roles  │
                    │  - Company Intelligence: Researches mission & HQ       │
                    │  - Scam Check: Drops pay-to-work fee scams             │
                    └───────────────────────────┬────────────────────────────┘
                                                │ Live Links + Company Dossiers
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │     3. COGNITIVE EXTRACTION AGENT (Groq + Gemini)      │
                    │  - Primary: Groq LLaMA 3.3 70B (Fast structured JSON)  │
                    │  - Failover: Gemini 2.5 Flash (Deep context reasoning) │
                    │  - Extracts: Field, Remote/Onsite, Paid, Funding Tiers │
                    └───────────────────────────┬────────────────────────────┘
                                                │ Enriched Structured Models
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │         4. CURATOR & DISPATCH AGENT (Delivery)         │
                    │  - Quota Ranker: Guarantees Ghana + Intl + Remote mix  │
                    │  - Google Sheets API: Logs comprehensive rows          │
                    │  - Email Notifier: Dispatches Top 3 HTML digest        │
                    └────────────────────────────────────────────────────────┘
```

---

## 3. Step-by-Step Implementation Roadmap

### Phase 1: Environment & API Key Foundation
- [ ] Add `GROQ_API_KEY` and `GEMINI_API_KEY` to `.env.example` and configuration parser.
- [ ] Update `requirements.txt` to include `groq` official client.
- [ ] Update `config/candidate_profile.json` to reflect field-agnostic scope with Ghana base location.

### Phase 2: Enhanced Data Models (`src/models.py`)
- [ ] Create `CompanyDossier` model:
  * `overview`: 1–2 sentence summary of core business/mission.
  * `org_type`: Startup, Enterprise, University, NGO, Government.
  * `headquarters`: City, Country.
  * `credibility_indicators`: Verified domain, size, license.
- [ ] Create `DeepVerificationReport` model:
  * `is_link_active`: Boolean confirming application page is reachable.
  * `application_mechanism`: "Application Form Detected", "Email Submission", "ATS Direct".
  * `closure_indicators`: Checks for "expired" / "closed" flags.
- [ ] Update `JobOpportunity` model:
  * Replace fixed track with dynamic `field_category` string.
  * Add `company_dossier: CompanyDossier`.
  * Add `is_ghana: bool`.
  * Add `funding_tier`: Fully Funded, Partially Funded, Self-Funded, or N/A.

### Phase 3: Agent 1 — Scout Agent (Multi-Source Ingestion)
- [ ] Build `src/agents/scout_agent.py`:
  * **Jobberman Ghana Ingestion (`src/scrapers/jobberman_scraper.py`):** Ingests live listings across all industries in Ghana with "intern" or "trainee" markers.
  * **All-Category Remote Ingestion (`src/scrapers/remote_feeds.py`):** Expands beyond tech into sales, marketing, support, writing, and design.
  * **Fellowship Hubs (`src/scrapers/research_portals.py`):** Expands to include international organizations (UN, global fellowships, Erasmus, policy institutes).
  * **Wildcard ATS Dorker (`src/scrapers/deep_search.py`):** Searches for any company posting internship roles without filtering by tech keywords.

### Phase 4: Agent 2 — Investigator Agent (Due Diligence & Link Audit)
- [ ] Build `src/agents/investigator_agent.py`:
  * Fetches the destination page HTML with realistic headers and browser simulation.
  * Inspects DOM for active application indicators (form tags, input type `file` for resumes, "Submit Application" / "Apply Now" buttons).
  * Searches page body for explicit expiration markers:
    * `"this job has expired"`
    * `"no longer accepting applications"`
    * `"position filled"`
    * `"page not found"`
  * Scrapes or synthesizes the **Company Dossier** from the careers page "About Us" section or domain registry.
  * Enforces the scam filter (rejects application fee extortion).

### Phase 5: Agent 3 — Cognitive Extraction Agent (Groq + Gemini Router)
- [ ] Build `src/agents/cognitive_agent.py`:
  * Dual-engine client:
    * **Engine A:** Groq Cloud API with `llama-3.3-70b-versatile` using strict JSON schema output.
    * **Engine B:** Google Gemini API (`gemini-2.5-flash`) as automatic fallback on 429/500 errors.
  * System prompt instructs the model to extract:
    1. `field`: Specific industry / discipline.
    2. `work_mode`: `Remote`, `Onsite`, or `Hybrid`.
    3. `is_paid`: Boolean, plus stipend currency/amount if stated.
    4. `location`: City, Country, and whether it is in Ghana.
    5. `outside_ghana_funding`: `Fully Funded` (flight+housing+stipend), `Partially Funded`, or `Self-Funded`.
    6. `deadline`: Extracted date or "Rolling".

### Phase 6: Agent 4 — Curator & Dispatch Agent (Google Sheets & Email)
- [ ] Build `src/agents/curator_agent.py`:
  * **Balanced Ranking Algorithm:** Guarantees a balanced Top 3 digest:
    * 🇬🇭 Slot 1: Top Local Ghana Opportunity
    * ✈️ Slot 2: Top Fully Funded International Opportunity
    * 💻 Slot 3: Top Global Remote Paid Opportunity
  * **Google Sheets Adapter Update (`src/storage/sheets_adapter.py`):**
    * Headers: `Date`, `Field`, `Role Title`, `Company / Org`, `Company Overview`, `Work Mode`, `Compensation`, `Location`, `Outside-Ghana Funding`, `Deadline`, `Verified Apply Link`.
  * **Email Notifier Update (`src/notifications/email_notifier.py`):**
    * Rich HTML cards featuring the Company Dossier, application proof, and funding breakdown.

### Phase 7: GitHub Actions & Workflow Sync
- [ ] Update `.github/workflows/daily_finder.yml` to pass `GROQ_API_KEY` and `GEMINI_API_KEY` from secrets.
- [ ] Ensure backward compatibility for users running locally or in dry-run mode without API keys (safe fallback mode).

### Phase 8: Testing & Verification
- [ ] Unit tests for:
  * Deep link inspector (verifying form detection vs expired detection).
  * Company dossier synthesis.
  * Groq/Gemini JSON extraction schema validation.
  * Jobberman Ghana scraper parsing.
  * Balanced quota top-3 selection.
- [ ] Live dry-run verification to inspect generated `output/opportunities.csv` and `output/latest_email.html`.

---

## 4. Required Secrets Checklist for GitHub Actions

| Secret | Description | Where to get it |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | Free LLM inference key | [console.groq.com](https://console.groq.com/) |
| `GEMINI_API_KEY` | Free Gemini API key | [aistudio.google.com](https://aistudio.google.com/) |
| `GOOGLE_SHEET_ID` | Existing Sheet ID | Already configured |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Existing Service Account Key | Already configured |
| `SMTP_USER` & `SMTP_PASSWORD` | Sending email & App Password | Already configured |
| `RECIPIENT_EMAIL` | Alert recipient address | Already configured |

---

## 5. Architectural Guarantees
* **Zero Broken Links:** No opportunity is added to Google Sheets unless the Investigator Agent successfully navigates the page and detects an active application mechanism.
* **Rich Company Context:** Every single opportunity provides a clear snapshot of what the organization does and why it is legitimate.
* **100% Free Tier Compliance:** Operates completely within free tiers of GitHub Actions, Groq Cloud, Google Gemini, and Google Sheets.
