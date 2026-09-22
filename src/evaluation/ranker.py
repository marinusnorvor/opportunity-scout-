"""Opportunity Scoring and Top-N Ranking Engine."""

import logging
from typing import List, Set
from src.models import JobOpportunity, FundingTier

logger = logging.getLogger(__name__)


class OpportunityRanker:
    """Calculates multi-criteria weighted scores and selects the top daily opportunities."""

    # High-reputation companies and institutions
    PRESTIGIOUS_ENTITIES = [
        "cern", "epfl", "eth zurich", "oist", "kaust", "max planck",
        "google", "meta", "microsoft", "apple", "amazon", "anthropic",
        "huggingface", "cohere", "canonical", "cloudflare", "datadog",
        "palantir", "scale ai", "outreachy", "linux foundation", "mila"
    ]

    def __init__(
        self,
        weight_funding: float = 0.35,
        weight_track: float = 0.30,
        weight_reputation: float = 0.20,
        weight_freshness: float = 0.15,
    ):
        self.w_funding = weight_funding
        self.w_track = weight_track
        self.w_reputation = weight_reputation
        self.w_freshness = weight_freshness

    def score_opportunity(self, opp: JobOpportunity) -> float:
        """Calculate a composite 0-100 score for an opportunity."""
        # 1. Funding Score (0 - 100)
        if opp.funding_tier == FundingTier.TIER_1_FULLY_FUNDED:
            s_funding = 100.0
        elif opp.funding_tier == FundingTier.TIER_2_GLOBAL_REMOTE_PAID:
            s_funding = 85.0
        elif opp.funding_tier == FundingTier.TIER_3_PARTIALLY_FUNDED:
            s_funding = 65.0
        else:
            s_funding = 30.0

        # 2. Track & Role Match Score (0 - 100)
        s_track = (opp.eligibility_score or 0.5) * 100.0

        # 3. Reputation Score (0 - 100)
        company_lower = opp.company.lower()
        if any(prest in company_lower for prest in self.PRESTIGIOUS_ENTITIES):
            s_reputation = 100.0
        elif opp.source.startswith("Greenhouse") or opp.source.startswith("Lever"):
            s_reputation = 75.0
        else:
            s_reputation = 60.0

        # 4. Freshness / Completeness Score
        s_freshness = 75.0
        if opp.deadline and opp.deadline != "Rolling / Open":
            s_freshness = 90.0

        total_score = (
            (self.w_funding * s_funding)
            + (self.w_track * s_track)
            + (self.w_reputation * s_reputation)
            + (self.w_freshness * s_freshness)
        )

        opp.ranking_score = round(total_score, 1)
        return opp.ranking_score

    def rank(self, opportunities: List[JobOpportunity]) -> List[JobOpportunity]:
        """Score all opportunities and return them sorted descending by rank."""
        for opp in opportunities:
            self.score_opportunity(opp)

        return sorted(opportunities, key=lambda x: x.ranking_score, reverse=True)

    def select_top_n(self, opportunities: List[JobOpportunity], n: int = 3) -> List[JobOpportunity]:
        """Select top N opportunities while prioritizing diversity across tracks."""
        ranked = self.rank(opportunities)
        if len(ranked) <= n:
            return ranked

        selected: List[JobOpportunity] = []
        seen_tracks: Set[str] = set()

        # First pass: Pick the highest scoring role from distinct tracks
        for opp in ranked:
            track = opp.track_name or "General"
            if track not in seen_tracks:
                selected.append(opp)
                seen_tracks.add(track)
                if len(selected) == n:
                    break

        # Second pass: If we still need more to reach N, fill with the next best overall
        if len(selected) < n:
            for opp in ranked:
                if opp not in selected:
                    selected.append(opp)
                    if len(selected) == n:
                        break

        logger.info(f"[OpportunityRanker] Selected Top {len(selected)} diverse opportunities.")
        return selected
