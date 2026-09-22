"""Deduplication Engine maintaining persistent state across runs."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.models import JobOpportunity

logger = logging.getLogger(__name__)


class Deduplicator:
    """Tracks seen opportunities to prevent duplicate logging or alerts."""

    def __init__(self, cache_file: Optional[Path] = None):
        if cache_file is None:
            cache_file = Path(__file__).resolve().parent.parent.parent / "data" / "seen_jobs.json"
        
        self.cache_file = cache_file
        self.cache_data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load seen cache from disk, initializing if absent."""
        if not self.cache_file.exists():
            return {"version": 1, "updated_at": datetime.now(timezone.utc).isoformat(), "seen": {}}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning(f"[Deduplicator] Could not read cache {self.cache_file}: {exc}. Starting fresh.")
            return {"version": 1, "updated_at": datetime.now(timezone.utc).isoformat(), "seen": {}}

    def is_seen(self, opp: JobOpportunity) -> bool:
        """Check if an opportunity was already processed."""
        return opp.id in self.cache_data.get("seen", {})

    def mark_seen(self, opp: JobOpportunity) -> None:
        """Add opportunity to seen cache."""
        seen_dict = self.cache_data.setdefault("seen", {})
        seen_dict[opp.id] = {
            "title": opp.title,
            "company": opp.company,
            "url": opp.url,
            "first_seen": datetime.now(timezone.utc).isoformat(),
        }

    def filter_unseen(self, opportunities: List[JobOpportunity]) -> List[JobOpportunity]:
        """Return only opportunities that have never been seen before."""
        new_jobs = [opp for opp in opportunities if not self.is_seen(opp)]
        logger.info(f"[Deduplicator] Filtered {len(opportunities)} jobs -> {len(new_jobs)} are brand new.")
        return new_jobs

    def save(self) -> None:
        """Persist cache atomically to disk."""
        self.cache_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        tmp_file = self.cache_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(self.cache_data, f, indent=2)
        tmp_file.replace(self.cache_file)
        logger.info(f"[Deduplicator] Successfully saved {len(self.cache_data.get('seen', {}))} seen entries.")
