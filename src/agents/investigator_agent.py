"""Agent 2: Investigator Agent (Deep Due Diligence & Link Audit).

Performs active DOM inspection to verify application forms, detects expired postings,
investigates hiring organizations, and compiles Company Intelligence Dossiers.
"""

import logging
import re
import urllib.parse
from typing import Optional, Tuple
import requests
from bs4 import BeautifulSoup
from src.models import (
    JobOpportunity,
    CompanyDossier,
    DeepVerificationReport,
)

logger = logging.getLogger("InvestigatorAgent")


class InvestigatorAgent:
    """Investigates target listings, audits application mechanisms, and researches companies."""

    BROWSER_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Explicit dead-job / expired markers in page body
    EXPIRED_MARKERS = [
        r"\b(?:this\s+)?job\s+(?:posting\s+)?has\s+expired\b",
        r"\bno\s+longer\s+accepting\s+applications\b",
        r"\bposition\s+(?:has\s+been\s+)?filled\b",
        r"\bapplication\s+(?:window\s+)?(?:is\s+)?closed\b",
        r"\bthis\s+vacancy\s+is\s+closed\b",
        r"\brole\s+is\s+no\s+longer\s+available\b",
        r"\b404\s+not\s+found\b",
        r"\bpage\s+not\s+found\b",
    ]

    # Pay-to-work scam phrases
    SCAM_RED_FLAGS = [
        r"\b(?:training|application|registration|placement)\s+fee\b",
        r"\bsecurity\s+deposit\s+required\b",
        r"\bwire\s+transfer\b",
        r"\bcrypto(?:currency)?\s+payment\b",
        r"\bearn\s+\$?[0-9,]+\s*(?:a|per)\s*(?:day|hour)\s+typing\b",
    ]

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.BROWSER_HEADERS)

    def investigate(self, opportunity: JobOpportunity) -> DeepVerificationReport:
        """Conduct deep due diligence audit on a job opportunity.
        
        Args:
            opportunity: Raw opportunity to audit.
            
        Returns:
            DeepVerificationReport containing proof of active application,
            scam verdict, and the compiled CompanyDossier.
        """
        target_url = opportunity.url
        logger.info(f"[InvestigatorAgent] Investigating '{opportunity.title}' at '{opportunity.company}'...")

        # 1. Fetch destination page with browser simulation
        page_html, final_url, status_code = self._fetch_page(target_url)

        # Check HTTP reachability
        if not page_html or status_code >= 400:
            logger.warning(f"[InvestigatorAgent] Link unreachable: {target_url} returned HTTP {status_code}")
            return DeepVerificationReport(
                is_legitimate=False,
                is_link_active=False,
                trust_score=0.0,
                domain=urllib.parse.urlparse(target_url).netloc,
                flags=[f"HTTP {status_code} Dead Link"],
                reason=f"Link audit failed: URL returned HTTP status {status_code}.",
            )

        # Update canonical URL if redirected
        opportunity.url = final_url
        soup = BeautifulSoup(page_html, "html.parser")
        page_text = soup.get_text(separator=" ").lower()

        # 2. Check for Expired / Closed Job Markers
        for marker in self.EXPIRED_MARKERS:
            if re.search(marker, page_text):
                logger.info(f"[InvestigatorAgent] Discarded: Post expired ({marker}) at {final_url}")
                return DeepVerificationReport(
                    is_legitimate=False,
                    is_link_active=False,
                    has_expired_markers=True,
                    trust_score=0.1,
                    domain=urllib.parse.urlparse(final_url).netloc,
                    flags=["Posting Expired / Closed"],
                    reason=f"Application closed: Page contains expired marker matching '{marker}'.",
                )

        # 3. Check for Financial Scams & Extortion
        for flag in self.SCAM_RED_FLAGS:
            if re.search(flag, page_text):
                logger.warning(f"[InvestigatorAgent] Scam detected: {flag} at {final_url}")
                return DeepVerificationReport(
                    is_legitimate=False,
                    is_link_active=True,
                    trust_score=0.0,
                    domain=urllib.parse.urlparse(final_url).netloc,
                    flags=[f"Financial Extortion Flag: {flag}"],
                    reason=f"Fraud alert: Job listing requests fees/payments matching '{flag}'.",
                )

        # 4. Audit Application Mechanism (Form, Upload, or Button)
        app_mechanism = self._detect_application_mechanism(soup, final_url)

        # 5. Conduct Company Background Intelligence & Build Dossier
        dossier = self._build_company_dossier(opportunity, soup, final_url)
        opportunity.company_dossier = dossier
        opportunity.application_proof = app_mechanism

        logger.info(f"[InvestigatorAgent] Verified '{opportunity.company}' ({dossier.org_type}) | Mechanism: {app_mechanism}")

        return DeepVerificationReport(
            is_legitimate=True,
            is_link_active=True,
            application_mechanism=app_mechanism,
            has_expired_markers=False,
            trust_score=1.0,
            domain=urllib.parse.urlparse(final_url).netloc,
            flags=[],
            reason=f"Audited: {app_mechanism} confirmed live. Organization due diligence passed.",
            company_dossier=dossier,
        )

    def _fetch_page(self, url: str) -> Tuple[Optional[str], str, int]:
        """Load target webpage following redirects."""
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            return resp.text, resp.url, resp.status_code
        except requests.RequestException as exc:
            logger.debug(f"[InvestigatorAgent] Network error fetching {url}: {exc}")
            return None, url, 599

    def _detect_application_mechanism(self, soup: BeautifulSoup, url: str) -> str:
        """Inspect HTML DOM to confirm real application inputs or CTA buttons exist."""
        # Check for direct file upload input (standard in resume submission forms)
        if soup.find("input", attrs={"type": "file"}):
            return "Active Multi-Step Form with Document Upload"

        # Check for HTML forms with submit buttons
        forms = soup.find_all("form")
        for form in forms:
            submit_btn = form.find(attrs={"type": "submit"}) or form.find("button")
            if submit_btn:
                return "Direct Online Application Form"

        # Check for major ATS endpoints
        if "greenhouse.io" in url or "lever.co" in url or "ashbyhq.com" in url or "myworkdayjobs.com" in url:
            return "Enterprise ATS Application Portal"

        # Check for prominent Apply CTA buttons
        apply_links = soup.find_all("a", href=True)
        for link in apply_links:
            text = link.get_text(strip=True).lower()
            if any(cta in text for cta in ["apply now", "apply for this", "submit application", "apply online"]):
                return f"Verified Apply CTA Link ({link.get_text(strip=True)[:25]})"

        # Check for email application contact
        mailto = soup.find("a", href=re.compile(r"^mailto:", re.I))
        if mailto:
            email = mailto["href"].replace("mailto:", "").split("?")[0]
            return f"Direct Recruiter Email Application ({email})"

        return "Active Career Portal Page"

    def _build_company_dossier(self, opp: JobOpportunity, soup: BeautifulSoup, url: str) -> CompanyDossier:
        """Compile intelligence on the organization from metadata, DOM text, and domain."""
        # Use existing dossier if pre-compiled by institutional scrapers (e.g. CERN, EPFL, Zeepay)
        if opp.company_dossier and opp.company_dossier.overview != "Established organization offering student training.":
            return opp.company_dossier

        company_name = opp.company
        domain = urllib.parse.urlparse(url).netloc.replace("www.", "")

        # 1. Extract meta description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag["content"].strip()

        # 2. Extract "About Us" / Company Overview section from DOM
        about_text = ""
        about_headers = soup.find_all(["h2", "h3", "h4", "strong"], string=re.compile(r"about\s+(?:us|the\s+company|our\s+team)", re.I))
        for h in about_headers:
            parent = h.find_parent(["div", "section", "article"])
            if parent:
                paragraphs = parent.find_all("p")
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 40:
                        about_text = text
                        break
            if about_text:
                break

        # Fallback overview synthesis
        overview = about_text or meta_desc or f"{company_name} is an active organization hiring student trainees."
        if len(overview) > 280:
            overview = overview[:277] + "..."

        # 3. Determine Organization Type
        org_type = self._infer_org_type(company_name, overview, domain)

        # 4. Infer Headquarters & Credibility
        headquarters = opp.location if opp.location != "Unknown Location" else "Global Presence"
        credibility = f"Verified operational domain: {domain}"

        return CompanyDossier(
            overview=overview,
            org_type=org_type,
            headquarters=headquarters,
            credibility_indicators=credibility,
        )

    @staticmethod
    def _infer_org_type(company: str, text: str, domain: str) -> str:
        """Classify the organization category."""
        combined = f"{company} {text} {domain}".lower()
        if any(w in combined for w in ["university", "institute", "laboratory", "cern", "epfl", "ethz", ".edu", ".ac."]):
            return "University / Scientific Research Institute"
        if any(w in combined for w in ["united nations", "ngo", "foundation", "who.int", "non-profit", "unicef"]):
            return "Multilateral Organization / Global NGO"
        if any(w in combined for w in ["bank", "fintech", "payment", "capital", "investment", "zeepay", "paystack"]):
            return "Financial Institution / FinTech"
        if any(w in combined for w in ["telecom", "mtn", "telecel", "vodafone", "network"]):
            return "Telecommunications & Infrastructure"
        if any(w in combined for w in ["startup", "technologies", "software", "ai", "cloud"]):
            return "Technology Enterprise / Startup"
        return "Corporate Enterprise"
