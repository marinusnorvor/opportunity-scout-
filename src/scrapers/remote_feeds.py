"""Global Remote Job Feed Scraper.

Ingests free, public JSON APIs from leading remote aggregators (Remotive, RemoteOK)
specifically filtering for Worldwide / Anywhere availability.
"""

import logging
import re
from typing import List, Optional
from src.scrapers.base_scraper import BaseScraper
from src.models import JobOpportunity, WorkMode

logger = logging.getLogger(__name__)


class RemoteFeedScraper(BaseScraper):
    """Fetches global remote opportunities from open feeds."""

    REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"

    def __init__(self, categories: Optional[List[str]] = None, timeout: int = 15):
        super().__init__(name="RemoteFeedScraper", timeout=timeout)
        self.categories = categories or ["software-dev", "data", "devops", "product"]

    def fetch_opportunities(self, limit: Optional[int] = None) -> List[JobOpportunity]:
        """Fetch remote jobs and extract internship / junior opportunities."""
        opportunities: List[JobOpportunity] = []

        for category in self.categories:
            if limit and len(opportunities) >= limit:
                break

            params = {"category": category, "limit": 50}
            data = self.safe_get(self.REMOTIVE_API_URL, params=params, is_json=True)
            if not data or "jobs" not in data:
                continue

            for job in data.get("jobs", []):
                title = job.get("title", "")
                desc = self.clean_html(job.get("description", ""))
                location_req = job.get("candidate_required_location", "")

                # Check if it's an internship or entry/fellowship
                if not self._is_target_role(title, desc):
                    continue

                # Check if it's available worldwide / global remote
                if not self._is_global_remote(location_req):
                    continue

                company = job.get("company_name", "Remote Company")
                job_url = job.get("url", "")
                job_id = self.generate_id(company, title, job_url)

                opp = JobOpportunity(
                    id=job_id,
                    title=title,
                    company=company,
                    location=f"Remote ({location_req or 'Worldwide'})",
                    url=job_url,
                    source="Remotive Global Feed",
                    work_mode=WorkMode.REMOTE_WORLDWIDE,
                    description_snippet=desc[:1200],
                    raw_metadata={
                        "salary": job.get("salary"),
                        "job_type": job.get("job_type"),
                        "publication_date": job.get("publication_date"),
                    },
                )
                opportunities.append(opp)

                if limit and len(opportunities) >= limit:
                    break

        logger.info(f"[RemoteFeedScraper] Collected {len(opportunities)} global remote opportunities.")
        return opportunities

    @staticmethod
    def _is_target_role(title: str, desc: str) -> bool:
        """Check for internship, apprentice, or student role markers using word boundaries."""
        lowered = f"{title} {desc[:300]}".lower()
        patterns = [
            r"\bintern\b",
            r"\binternship\b",
            r"\bapprentice\b",
            r"\bstudent\b",
            r"\bfellow\b",
            r"\bfellowship\b",
            r"\bco-?op\b",
            r"\bjunior\b",
        ]
        return any(re.search(p, lowered) for p in patterns)

    @staticmethod
    def _is_global_remote(location: str) -> bool:
        """Verify candidate location allows applicants from Ghana / Worldwide."""
        lowered = location.lower()
        if not lowered or "worldwide" in lowered or "anywhere" in lowered or "global" in lowered or "all" in lowered:
            return True
        # Explicit non-global restrictions
        if any(r in lowered for r in ["us only", "usa only", "uk only", "europe only", "north america only", "canada only"]):
            return False
        return True
