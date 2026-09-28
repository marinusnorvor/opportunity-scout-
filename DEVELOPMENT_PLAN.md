# Production Development & Reliability Plan (v2.2)

## 1. Project Objective & Core Guarantees
Build, harden, and maintain a 24/7 autonomous Multi-Agent System (MAS) that discovers, verifies, categorizes, and distributes top-tier internship opportunities across **all fields** (Tech, Finance, Health, Law, Media, Engineering, NGOs) without human intervention.

### Core Guarantees:
1. **No Broken Links:** The Investigator Agent audits the live DOM of every single URL; 404s, expired postings, and pay-to-work scams are discarded before curation.
2. **Field-Agnostic Breadth:** Opportunities span local Ghanaian enterprises, prestigious fully-funded international research fellowships (covering flights, housing, stipend), and global remote paid internships.
3. **Zero Secrets in Git:** Sensitive tokens (`GROQ_API_KEY`, `GEMINI_API_KEY`, Google Service Account JSON, SMTP passwords) are strictly stored in `.env` and GitHub Secrets.
4. **100% Free-Tier Operation:** Works seamlessly within free limits of GitHub Actions (cron `0 18 * * *` / 6:00 PM GMT), Groq Cloud (`openai/gpt-oss-20b`), Google Gemini (`gemini-3.6-flash`), and Google Sheets.

---

## 2. Architecture & Agent Specialization

```
[ Scout Agent ]        --> Discovers raw candidates across 5 channels (Ghana Hubs, Portals, Feeds, ATS, Search)
       │
[ Investigator Agent ] --> Deep DOM audit: confirms active forms/CTAs, checks soft-404s, drops scams, compiles company dossier
       │
[ Cognitive Agent ]    --> LLM extraction (Groq / Gemini fallback): extracts field, work mode, pay, outside-Ghana funding
       │
[ Curator Agent ]      --> Balanced quota ranking (1 Ghana Local + 1 Intl Funded + 1 Global Remote), Sheets log, Email digest
```

---

## 3. Active Task Roadmap & Status

### Phase A: Source URL Live Health & Verification
- [x] **Task A.1: International Fellowship Live URLs (`src/scrapers/research_portals.py`)**
  * CERN: Update to `https://home.cern/summer-student-programme` (Confirmed 200 OK).
  * EPFL: Update to `https://summer.epfl.ch/` (Confirmed 200 OK).
  * OIST: Update to `https://groups.oist.jp/grad/research-interns` (Confirmed 200 OK).
  * KAUST: Update to `https://vsrp.kaust.edu.sa/` (Confirmed 200 OK).
  * ETH Zurich: Verify `https://inf.ethz.ch/studies/summer-research-fellowship.html` (Confirmed 200 OK).
- [x] **Task A.2: Ghana Hubs Live URLs (`src/scrapers/jobberman_scraper.py`)**
  * MEST Africa: Update to `https://mestafrica.com/training-program/` (Confirmed 200 OK).
  * Hubtel Ghana: Update to `https://explore.hubtel.com/careers/` (Confirmed 200 OK).
  * Amalitech Ghana: Update to `https://www.amalitech.com/careers` (Confirmed 200 OK).
  * Telecel Ghana: Add `https://telecel.com.gh/` (Confirmed 200 OK).

### Phase B: Global Remote Feed Expansion
- [x] **Task B.1: RemoteOK Public API Integration (`src/scrapers/remote_feeds.py`)**
  * Integrate `https://remoteok.com/api` alongside Remotive to stream verified junior, entry-level, assistant, and intern roles worldwide.
  * Broaden keyword matching to encompass Operations, Finance, Marketing, HR, and Engineering.

### Phase C: Transport Resilience
- [x] **Task C.1: SSL & Certificate Graceful Fallback (`src/scrapers/base_scraper.py`)**
  * Prevent connection termination on corporate sites with incomplete certificate chains.

### Phase D: Verification & Delivery
- [x] **Task D.1: Run Full Pytest Suite (28 tests passing)**
- [x] **Task D.2: Run Live Pipeline End-to-End Dry Run (Verified 8/8 links active, 100% success)**
- [x] **Task D.3: Commit & Push Cleanly to GitHub (`origin/main`)**

---

## 4. Change Safety Checklist
- [x] Working code must not be altered destructively.
- [x] Every scraper modification must maintain the exact `JobOpportunity` schema.
- [x] All tests must pass before any git push.
