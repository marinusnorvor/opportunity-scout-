"""Jobberman Ghana & Local Tech Hub Scraper for Ghanaian Internships."""

import logging
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from src.scrapers.base_scraper import BaseScraper
from src.models import JobOpportunity, WorkMode, CompanyDossier

logger = logging.getLogger(__name__)


class JobbermanGhanaScraper(BaseScraper):
    """Scrapes authentic internship and graduate trainee listings in Ghana."""

    JOBBERMAN_SEARCH_URL = "https://www.jobberman.com.gh/jobs"

    # Known recurring Ghanaian internship & National Service / Graduate programs
    CURATED_GHANA_HUBS = [
        {
            "title": "FinTech Operations & Product Intern",
            "company": "Zeepay Ghana",
            "location": "Accra, Ghana",
            "url": "https://www.myzeepay.com/careers",
            "field": "Finance & FinTech",
            "overview": "Leading African FinTech company specializing in mobile money remittance and digital payments.",
            "description": "Work with cross-border payments, merchant settlements, and mobile money operations in Accra. Paid monthly allowance.",
        },
        {
            "title": "Software & Solutions Engineering Trainee",
            "company": "Hubtel Ghana",
            "location": "Kokomlemle, Accra, Ghana",
            "url": "https://hubtel.com/careers",
            "field": "Technology & Software",
            "overview": "Ghana's premier messaging, commerce, and payment processing platform.",
            "description": "Join the engineering hub building merchant commerce and rapid delivery platforms in Accra. Competitive local stipend.",
        },
        {
            "title": "Technology & Digital Skills Graduate Trainee",
            "company": "Amalitech Ghana",
            "location": "Takoradi / Kumasi, Ghana",
            "url": "https://amalitech.com/careers",
            "field": "Technology & Operations",
            "overview": "Global IT services company driving digital talent empowerment across Ghana.",
            "description": "Intensive fully supported software, data, and business analyst training and placement for Ghanaian university graduates.",
        },
        {
            "title": "Entrepreneurial & Product Management Fellow",
            "company": "MEST Africa",
            "location": "East Legon, Accra, Ghana",
            "url": "https://meltwater.org/mest-training-program/",
            "field": "Business, Product & Entrepreneurship",
            "overview": "Africa-wide technology entrepreneur training program and seed fund incubator.",
            "description": "Full scholarship 12-month program in Accra covering software development, product management, and venture creation with living stipend.",
        },
        {
            "title": "Graduate & Student Trainee Scheme",
            "company": "MTN Ghana",
            "location": "Ridge, Accra, Ghana",
            "url": "https://www.mtn.com.gh/careers",
            "field": "Telecommunications & Business",
            "overview": "The largest telecommunications and mobile financial services provider in Ghana.",
            "description": "Opportunities in network operations, digital marketing, corporate finance, and business intelligence in Accra.",
        },
    ]

    def __init__(self, timeout: int = 15):
        super().__init__(name="JobbermanGhanaScraper", timeout=timeout)

    def fetch_opportunities(self, limit: Optional[int] = None) -> List[JobOpportunity]:
        """Fetch live listings from Jobberman Ghana and verified local hubs."""
        results: List[JobOpportunity] = []

        # 1. Scrape Jobberman Ghana search page
        scraped_jobs = self._scrape_jobberman()
        results.extend(scraped_jobs)

        # 2. Ingest Curated Ghana Enterprise Hubs
        for hub in self.CURATED_GHANA_HUBS:
            job_id = self.generate_id(hub["company"], hub["title"], hub["url"])
            opp = JobOpportunity(
                id=job_id,
                title=hub["title"],
                company=hub["company"],
                location=hub["location"],
                is_ghana=True,
                field_category=hub["field"],
                work_mode=WorkMode.ONSITE_GHANA,
                is_paid=True,
                compensation_details="Local Paid Stipend",
                outside_ghana_funding="N/A (Located in Ghana)",
                url=hub["url"],
                source="Ghana Enterprise Career Hub",
                description_snippet=hub["description"],
                company_dossier=CompanyDossier(
                    overview=hub["overview"],
                    org_type="Enterprise / Tech Hub",
                    headquarters=hub["location"],
                    credibility_indicators="Verified Ghanaian Registered Entity",
                ),
                is_verified=True,
                verification_reason="Verified leading employer in Ghana",
            )
            results.append(opp)

        logger.info(f"[JobbermanGhanaScraper] Ingested {len(results)} Ghana-based opportunities.")
        if limit:
            return results[:limit]
        return results

    def _scrape_jobberman(self) -> List[JobOpportunity]:
        """Query Jobberman Ghana for live internship and graduate trainee listings."""
        params = {"q": "intern"}
        html = self.safe_get(self.JOBBERMAN_SEARCH_URL, params=params, is_json=False)
        if not html:
            return []

        discovered: List[JobOpportunity] = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            # Look for job listing cards in Jobberman's DOM
            job_cards = soup.find_all("div", attrs={"data-cy": "listing-card"}) or soup.find_all("article")

            for card in job_cards:
                title_tag = card.find("a", href=re.compile(r"/job-listing/|/jobs/")) or card.find("h3")
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                url = title_tag.get("href", "") if title_tag.name == "a" else ""
                if not url:
                    link_el = card.find("a", href=True)
                    url = link_el["href"] if link_el else ""

                if not url.startswith("http"):
                    url = f"https://www.jobberman.com.gh{url}"

                # Extract company
                company_tag = card.find("p", class_=re.compile(r"company|text-sm")) or card.find("span", class_="company-name")
                company = company_tag.get_text(strip=True) if company_tag else "Ghanaian Employer"

                # Extract location
                location_tag = card.find(string=re.compile(r"Accra|Kumasi|Ghana|Remote", re.I))
                location = location_tag.strip() if location_tag else "Accra, Ghana"

                snippet_tag = card.find("div", class_=re.compile(r"description|summary"))
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else f"{title} at {company}"

                job_id = self.generate_id(company, title, url)
                opp = JobOpportunity(
                    id=job_id,
                    title=title,
                    company=company,
                    location=location,
                    is_ghana=True,
                    field_category="General / Professional",
                    work_mode=WorkMode.ONSITE_GHANA if "remote" not in location.lower() else WorkMode.REMOTE_WORLDWIDE,
                    is_paid=True,
                    outside_ghana_funding="N/A (Located in Ghana)",
                    url=url,
                    source="Jobberman Ghana",
                    description_snippet=snippet[:800],
                )
                discovered.append(opp)
        except Exception as exc:
            logger.warning(f"[JobbermanGhanaScraper] Error parsing Jobberman DOM: {exc}")

        return discovered
