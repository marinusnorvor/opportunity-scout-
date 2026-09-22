"""Unit tests for Agent 3: Cognitive Extraction Agent."""

import pytest
from src.agents.cognitive_agent import CognitiveAgent
from src.models import JobOpportunity, WorkMode, FundingTier


@pytest.fixture
def cognitive_agent():
    return CognitiveAgent()


def test_heuristic_finance_internship_extraction(cognitive_agent):
    """Verify field, compensation, and Ghana detection for finance roles."""
    opp = JobOpportunity(
        id="test-fin-1",
        title="Investment Banking & Private Equity Intern",
        company="Accra Capital Partners",
        location="Accra, Ghana",
        url="https://accracapital.com/careers/1",
        source="Jobberman Ghana",
        description_snippet="Join our M&A transaction advisory team in Accra. Monthly stipend of GHS 2,500.",
    )
    analyzed = cognitive_agent.analyze(opp)

    assert "Finance" in analyzed.field_category
    assert analyzed.is_paid is True
    assert "GHS 2,500" in analyzed.compensation_details
    assert analyzed.is_ghana is True
    assert analyzed.work_mode in [WorkMode.ONSITE_GHANA, WorkMode.HYBRID_GHANA]


def test_heuristic_fully_funded_extraction(cognitive_agent):
    """Verify detection of Fully Funded status for international research."""
    opp = JobOpportunity(
        id="test-fund-1",
        title="Student Research Fellow",
        company="OIST Japan",
        location="Okinawa, Japan",
        url="https://oist.jp/internship",
        source="Research Portal",
        description_snippet="Direct roundtrip airfare flight covered, free furnished accommodation provided, with daily stipend.",
    )
    analyzed = cognitive_agent.analyze(opp)

    assert analyzed.outside_ghana_funding == "Fully Funded"
    assert analyzed.funding_tier == FundingTier.TIER_1_FULLY_FUNDED
    assert analyzed.is_ghana is False
