"""Scrapers and discovery engines."""
from .base_scraper import BaseScraper
from .ats_scraper import ATSScraper
from .deep_search import DeepSearchEngine
from .remote_feeds import RemoteFeedScraper
from .research_portals import ResearchPortalsScraper

__all__ = [
    "BaseScraper",
    "ATSScraper",
    "DeepSearchEngine",
    "RemoteFeedScraper",
    "ResearchPortalsScraper",
]
