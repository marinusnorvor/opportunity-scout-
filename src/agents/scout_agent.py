"""Agent 1: Scout Agent (Field-Agnostic Multi-Source Ingestion Specialist)."""

import logging
from typing import List, Optional
from src.models import JobOpportunity
from src.scrapers import (
    ATSScraper,
    DeepSearchEngine,
    RemoteFeedScraper,
    ResearchPortalsScraper,
)
from src.scrapers.jobberman_scraper import JobbermanGhanaScraper

logger = logging.getLogger("ScoutAgent")


class ScoutAgent:
    """Discovers raw internship listings across any field without restrictions."""

    def __init__(self, timeout: int = 15):
        self.scrapers = [
            JobbermanGhanaScraper(timeout=timeout),
            ResearchPortalsScraper(timeout=timeout),
            RemoteFeedScraper(timeout=timeout),
            ATSScraper(timeout=timeout),
            DeepSearchEngine(timeout=timeout),
        ]

    def scout_all(
        self,
        limit_per_source: int = 10,
        skip_deep_search: bool = False,
    ) -> List[JobOpportunity]:
        """Execute discovery across all ingestion channels.
        
        Args:
            limit_per_source: Max items per source.
            skip_deep_search: Flag to skip slower search engine queries in quick tests.
            
        Returns:
            List of raw, unverified JobOpportunity candidates.
        """
        all_candidates: List[JobOpportunity] = []

        for scraper in self.scrapers:
            if skip_deep_search and isinstance(scraper, DeepSearchEngine):
                logger.info("[ScoutAgent] Skipping DeepSearchEngine as requested.")
                continue

            try:
                logger.info(f"[ScoutAgent] Launching channel: {scraper.name}...")
                jobs = scraper.fetch_opportunities(limit=limit_per_source)
                all_candidates.extend(jobs)
                logger.info(f"[ScoutAgent] Channel '{scraper.name}' produced {len(jobs)} candidates.")
            except Exception as exc:
                logger.error(f"[ScoutAgent] Error running {scraper.name}: {exc}")

        logger.info(f"[ScoutAgent] Completed scouting. Total raw candidates: {len(all_candidates)}")
        return all_candidates
