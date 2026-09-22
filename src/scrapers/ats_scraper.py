"""Direct ATS API Scraper for Greenhouse, Lever, and Ashby."""

import logging
from typing import List, Optional, Dict, Any
from src.scrapers.base_scraper import BaseScraper
from src.models import JobOpportunity, WorkMode, FundingBenefits, FundingTier

logger = logging.getLogger(__name__)


class ATSScraper(BaseScraper):
    """Scrapes direct public ATS endpoints with zero HTML fragility."""

    # Curated tech, AI, robotics, and engineering companies using Greenhouse & Lever
    DEFAULT_GREENHOUSE_BOARDS = [
        "cloudflare",
        "scaleai",
        "huggingface",
        "cohere",
        "figma",
        "datadog",
        "anthropic",
        "canonical",
        "palantir",
        "anduril",
        "hashicorp",
        "elastic",
        "mongodb",
        "gitlab",
        "instacart",
        "reddit",
    ]

    DEFAULT_LEVER_COMPANIES = [
        "palantir",
        "astranis",
        "outreachy",
        "replit",
        "chainlink",
        "linear",
    ]

    def __init__(
        self,
        greenhouse_boards: Optional[List[str]] = None,
        lever_companies: Optional[List[str]] = None,
        timeout: int = 15,
    ):
        super().__init__(name="ATSScraper", timeout=timeout)
        self.greenhouse_boards = greenhouse_boards or self.DEFAULT_GREENHOUSE_BOARDS
        self.lever_companies = lever_companies or self.DEFAULT_LEVER_COMPANIES

    def fetch_opportunities(self, limit: Optional[int] = None) -> List[JobOpportunity]:
        """Fetch internship opportunities across Greenhouse and Lever boards."""
        results: List[JobOpportunity] = []

        # 1. Fetch from Greenhouse boards
        for board in self.greenhouse_boards:
            if limit and len(results) >= limit:
                break
            results.extend(self._fetch_greenhouse_board(board))

        # 2. Fetch from Lever boards
        for company in self.lever_companies:
            if limit and len(results) >= limit:
                break
            results.extend(self._fetch_lever_company(company))

        logger.info(f"[ATSScraper] Total raw opportunities collected: {len(results)}")
        if limit:
            return results[:limit]
        return results

    def _fetch_greenhouse_board(self, board_token: str) -> List[JobOpportunity]:
        """Fetch jobs from a Greenhouse board endpoint."""
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        data = self.safe_get(url, is_json=True)
        if not data or "jobs" not in data:
            return []

        opportunities: List[JobOpportunity] = []
        for job in data.get("jobs", []):
            title = job.get("title", "")
            # Filter for internship postings
            if not self._is_internship(title):
                continue

            job_url = job.get("absolute_url") or f"https://boards.greenhouse.io/{board_token}/jobs/{job.get('id')}"
            location = (job.get("location") or {}).get("name", "Unknown Location")
            raw_content = job.get("content", "")
            clean_desc = self.clean_html(raw_content)

            company_name = board_token.replace("-", " ").title()
            job_id = self.generate_id(company_name, title, job_url)

            opp = JobOpportunity(
                id=job_id,
                title=title,
                company=company_name,
                location=location,
                url=job_url,
                source=f"Greenhouse ({board_token})",
                description_snippet=clean_desc[:1200],
                raw_metadata={
                    "board_token": board_token,
                    "external_id": str(job.get("id")),
                    "updated_at": job.get("updated_at"),
                },
            )
            opportunities.append(opp)

        return opportunities

    def _fetch_lever_company(self, company: str) -> List[JobOpportunity]:
        """Fetch jobs from a Lever API endpoint."""
        url = f"https://api.lever.co/v0/postings/{company}"
        data = self.safe_get(url, is_json=True)
        if not data or not isinstance(data, list):
            return []

        opportunities: List[JobOpportunity] = []
        for job in data:
            title = job.get("text", "")
            if not self._is_internship(title):
                continue

            job_url = job.get("hostedUrl", "")
            categories = job.get("categories", {})
            location = categories.get("location", "Unknown Location")
            clean_desc = job.get("descriptionPlain", "")

            company_name = company.replace("-", " ").title()
            job_id = self.generate_id(company_name, title, job_url)

            opp = JobOpportunity(
                id=job_id,
                title=title,
                company=company_name,
                location=location,
                url=job_url,
                source=f"Lever ({company})",
                description_snippet=clean_desc[:1200],
                raw_metadata={
                    "company_slug": company,
                    "external_id": str(job.get("id")),
                    "commitment": categories.get("commitment"),
                },
            )
            opportunities.append(opp)

        return opportunities

    @staticmethod
    def _is_internship(text: str) -> bool:
        """Check if job title or text indicates an internship role using word boundaries."""
        lowered = text.lower()
        patterns = [
            r"\bintern\b",
            r"\binternship\b",
            r"\bco-?op\b",
            r"\bfellow\b",
            r"\bfellowship\b",
            r"\btrainee\b",
            r"\bstudent\b",
            r"\bundergraduate\b",
            r"\bapprentice\b",
        ]
        return any(re.search(p, lowered) for p in patterns)
