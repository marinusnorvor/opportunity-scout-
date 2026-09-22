"""Unit tests for the Ranking and Top-N Selection Engine."""

import pytest
from src.models import JobOpportunity, FundingTier
from src.evaluation.ranker import OpportunityRanker


@pytest.fixture
def ranker():
    return OpportunityRanker()


def test_tier1_prestige_scoring(ranker):
    """Ensure Tier 1 prestigious research outranks generic unverified roles."""
    cern_job = JobOpportunity(
        id="cern-1",
        title="Summer Research Intern",
        company="CERN",
        location="Switzerland",
        url="https://cern.ch/jobs/1",
        source="Research Portal",
        funding_tier=FundingTier.TIER_1_FULLY_FUNDED,
        eligibility_score=0.9,
    )
    generic_job = JobOpportunity(
        id="generic-1",
        title="General Intern",
        company="Unknown Startup",
        location="Remote",
        url="https://generic.com/1",
        source="Deep Search",
        funding_tier=FundingTier.TIER_3_PARTIALLY_FUNDED,
        eligibility_score=0.5,
    )

    score_cern = ranker.score_opportunity(cern_job)
    score_generic = ranker.score_opportunity(generic_job)

    assert score_cern > score_generic
    assert score_cern >= 85.0


def test_top_3_diversity_selection(ranker):
    """Verify that select_top_n selects diverse tracks rather than 3 identical ones."""
    jobs = [
        JobOpportunity(
            id="j1", title="AI Agent Intern 1", company="AI Corp", location="Remote",
            url="https://ai.com/1", source="ATS", track_name="AI Solutions / Agent Engineer Intern",
            funding_tier=FundingTier.TIER_2_GLOBAL_REMOTE_PAID, eligibility_score=0.95
        ),
        JobOpportunity(
            id="j2", title="AI Agent Intern 2", company="AI Corp 2", location="Remote",
            url="https://ai.com/2", source="ATS", track_name="AI Solutions / Agent Engineer Intern",
            funding_tier=FundingTier.TIER_2_GLOBAL_REMOTE_PAID, eligibility_score=0.94
        ),
        JobOpportunity(
            id="j3", title="Robotics Intern", company="RoboLab", location="Remote",
            url="https://robo.com/1", source="ATS", track_name="Robotics / Mechatronics Intern",
            funding_tier=FundingTier.TIER_2_GLOBAL_REMOTE_PAID, eligibility_score=0.90
        ),
        JobOpportunity(
            id="j4", title="Cloud SRE Intern", company="CloudNet", location="Remote",
            url="https://cloud.com/1", source="ATS", track_name="Systems / Cloud Engineering Intern",
            funding_tier=FundingTier.TIER_2_GLOBAL_REMOTE_PAID, eligibility_score=0.88
        ),
    ]

    top_3 = ranker.select_top_n(jobs, n=3)
    assert len(top_3) == 3

    tracks = [j.track_name for j in top_3]
    # Check that Robotics or Cloud is included for diversity despite AI jobs having highest raw score
    assert "Robotics / Mechatronics Intern" in tracks
    assert "Systems / Cloud Engineering Intern" in tracks
