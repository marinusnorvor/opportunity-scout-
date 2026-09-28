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


def test_head_and_tail_slicing_preserves_footer_benefits(cognitive_agent):
    """Verify that a 4000+ character description preserves both header and footer compensation."""
    intro = "Welcome to our company. We are looking for an ambitious engineering intern. " * 60  # ~4,500 chars
    footer = "Benefits & Compensation: Full roundtrip flight covered, free accommodation, monthly stipend of $3,500 USD."
    long_desc = intro + footer

    opp = JobOpportunity(
        id="test-long-1",
        title="Software Intern",
        company="Global Tech",
        location="Remote",
        url="https://company.com/apply",
        source="ATS",
        description_snippet=long_desc,
    )
    prompt = cognitive_agent._prepare_prompt_text(opp)

    assert "roundtrip flight covered" in prompt
    assert "$3,500 USD" in prompt
    assert "[... middle section omitted ...]" in prompt


def test_json_cleaning_with_markdown_fences(cognitive_agent):
    """Verify that JSON wrapped in markdown backticks parses correctly without throwing error."""
    raw_markdown_json = """```json
    {
      "field": "Finance & FinTech",
      "work_mode": "Remote",
      "is_paid": true,
      "compensation_details": "$4,000/mo",
      "location": "Remote",
      "is_ghana": false,
      "outside_ghana_funding": "N/A",
      "deadline": "Rolling / Open",
      "summary": "Great remote finance role"
    }
    ```"""
    cleaned = cognitive_agent._clean_json_output(raw_markdown_json)
    assert cleaned is not None
    assert cleaned["field"] == "Finance & FinTech"
    assert cleaned["is_paid"] is True


def test_json_cleaning_with_conversational_text(cognitive_agent):
    """Verify that extra conversational preface from LLM is safely stripped."""
    chatter_json = """Here is the structured JSON you requested:
    {
      "field": "Healthcare",
      "work_mode": "Onsite",
      "is_paid": true
    }
    I hope this helps!"""
    cleaned = cognitive_agent._clean_json_output(chatter_json)
    assert cleaned is not None
    assert cleaned["field"] == "Healthcare"
    assert cleaned["is_paid"] is True

