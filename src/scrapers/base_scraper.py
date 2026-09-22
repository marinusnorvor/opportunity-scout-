"""Abstract Base Scraper providing common networking, hashing, and utilities."""

import abc
import hashlib
import logging
import re
from typing import List, Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from src.models import JobOpportunity, WorkMode, FundingBenefits, FundingTier

logger = logging.getLogger(__name__)


class BaseScraper(abc.ABC):
    """Abstract base class for all opportunity scrapers and discovery engines."""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self, name: str, timeout: int = 15):
        self.name = name
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

    @abc.abstractmethod
    def fetch_opportunities(self, limit: Optional[int] = None) -> List[JobOpportunity]:
        """Fetch and parse opportunities from this source.
        
        Args:
            limit: Maximum number of opportunities to retrieve.
            
        Returns:
            List of JobOpportunity models.
        """
        pass

    @staticmethod
    def generate_id(company: str, title: str, url: str) -> str:
        """Create a deterministic SHA-256 hash for deduplication."""
        unique_string = f"{company.strip().lower()}|{title.strip().lower()}|{url.strip().lower()}"
        return hashlib.sha256(unique_string.encode("utf-8")).hexdigest()

    @staticmethod
    def clean_html(raw_html: str) -> str:
        """Strip HTML tags and normalize whitespace."""
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(separator=" ")
        return re.sub(r"\s+", " ", text).strip()

    def safe_get(self, url: str, params: Optional[Dict[str, Any]] = None, is_json: bool = True) -> Optional[Any]:
        """Execute a safe GET request with error handling and timeouts."""
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            if is_json:
                return response.json()
            return response.text
        except requests.RequestException as exc:
            logger.warning(f"[{self.name}] Failed request to {url}: {exc}")
            return None
