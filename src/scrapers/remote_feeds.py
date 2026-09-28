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
    REMOTEOK_API_URL = "https://remoteok.com/api"

    def __init__(self, categories: Optional[List[str]] = None, timeout: int = 15):
        super().__init__(name="RemoteFeedScraper", timeout=timeout)
        self.categories = categories or [
            "software-dev",
            "data",
            "product",
            "marketing",
            "finance-legal",
            "customer-support",
            "writing",
            "design",
        ]

    def fetch_opportunities(self, limit: Optional[int] = None) -> List[JobOpportunity]:
        """Fetch remote jobs from RemoteOK and Remotive and extract internship / entry opportunities."""
        opportunities: List[JobOpportunity] = []

        # 1. Ingest from RemoteOK open feed
        opportunities.extend(self._fetch_remoteok(limit=limit))

        # 2. Ingest from Remotive feeds if limit not reached
        if not limit or len(opportunities) < limit:
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

                    if not self._is_target_role(title, desc):
                        continue

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
                        field_category=category.replace("-", " ").title(),
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
        return opportunities[:limit] if limit else opportunities

    def _fetch_remoteok(self, limit: Optional[int] = None) -> List[JobOpportunity]:
        """Fetch verified entry/intern remote jobs from RemoteOK."""
        data = self.safe_get(self.REMOTEOK_API_URL, is_json=True)
        if not data or not isinstance(data, list):
            return []

        remoteok_jobs: List[JobOpportunity] = []
        for job in data[1:]:  # Skip legal notice header
            if not isinstance(job, dict):
                continue

            title = job.get("position", "")
            desc = self.clean_html(job.get("description", ""))
            location = job.get("location", "Worldwide")

            if not self._is_target_role(title, desc):
                continue

            if not self._is_global_remote(location):
                continue

            company = job.get("company", "Remote Employer")
            job_url = job.get("url") or f"https://remoteok.com/remote-jobs/{job.get('id')}"
            tags = job.get("tags", [])
            field = tags[0].replace("-", " ").title() if tags else "General / Operations"

            opp = JobOpportunity(
                id=self.generate_id(company, title, job_url),
                title=title,
                company=company,
                location=f"Remote ({location or 'Worldwide'})",
                url=job_url,
                source="RemoteOK Global Feed",
                field_category=field,
                work_mode=WorkMode.REMOTE_WORLDWIDE,
                is_paid=True,
                compensation_details=f"${job.get('salary_min', 0):,}-${job.get('salary_max', 0):,}/yr" if job.get("salary_min") else "Paid Remote",
                description_snippet=desc[:1200],
            )
            remoteok_jobs.append(opp)

            if limit and len(remoteok_jobs) >= limit:
                break

        return remoteok_jobs

    @staticmethod
    def _is_target_role(title: str, desc: str) -> bool:
        """Check for internship, trainee, apprentice, or junior role markers using word boundaries."""
        lowered = f"{title} {desc[:300]}".lower()
        patterns = [
            r"\bintern\b",
            r"\binternship\b",
            r"\btrainee\b",
            r"\bapprentice\b",
            r"\bstudent\b",
            r"\bfellow\b",
            r"\bfellowship\b",
            r"\bco-?op\b",
            r"\bjunior\b",
            r"\bentry[- ]level\b",
            r"\bassociate\b",
            r"\bcoordinator\b",
            r"\bassistant\b",
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
