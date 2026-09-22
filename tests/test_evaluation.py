"""Unit tests for the Eligibility and Funding Classification Engine."""

import pytest
from src.models import JobOpportunity, FundingTier
from src.evaluation.eligibility_filter import EligibilityFilter


@pytest.fixture
def eligibility_filter():
    return EligibilityFilter()


def test_visa_disqualification(eligibility_filter):
    """Ensure non-sponsoring US-only roles are rejected for Ghana undergrad."""
    job = JobOpportunity(
        id="test-v1",
        title="Software Engineering Intern",
        company="US Tech Co",
        location="San Francisco, CA",
        url="https://boards.greenhouse.io/ustech/jobs/1",
        source="Greenhouse",
        description_snippet="Applicants must be a US Citizen. No visa sponsorship provided."
    )
    report = eligibility_filter.evaluate(job)
    assert report.is_eligible is False
    assert any("Disqualified" in r for r in report.reasons)


def test_unpaid_disqualification(eligibility_filter):
    """Ensure unpaid internships are automatically filtered out."""
    job = JobOpportunity(
        id="test-u1",
        title="Frontend Developer Intern",
        company="Startup A",
        location="Remote - Worldwide",
        url="https://boards.greenhouse.io/startupa/jobs/2",
        source="Greenhouse",
        description_snippet="This is an unpaid internship for college credit only."
    )
    report = eligibility_filter.evaluate(job)
    assert report.is_eligible is False


def test_tier1_fully_funded_classification(eligibility_filter):
    """Verify detection of Tier 1 fully funded international research."""
    job = JobOpportunity(
        id="test-f1",
        title="Summer Student Fellow",
        company="CERN",
        location="Geneva, Switzerland",
        url="https://careers.cern/summer-student",
        source="Research Portal",
        description_snippet="Roundtrip airfare ticket provided, free housing furnished, with 90 CHF/day monthly stipend."
    )
    report = eligibility_filter.evaluate(job)
    assert report.is_eligible is True
    assert report.funding_tier == FundingTier.TIER_1_FULLY_FUNDED
    assert job.funding_benefits.flight_covered is True
    assert job.funding_benefits.housing_covered is True
    assert job.funding_benefits.stipend_provided is True


def test_tier2_global_remote_paid(eligibility_filter):
    """Verify detection of Tier 2 global remote paid opportunities."""
    job = JobOpportunity(
        id="test-r1",
        title="AI Solutions Engineer Intern",
        company="Global Remote AI",
        location="Remote - Worldwide",
        url="https://jobs.lever.co/globalai/123",
        source="Lever",
        description_snippet="100% remote anywhere in the world. Competitive stipend of $2,500/month."
    )
    report = eligibility_filter.evaluate(job)
    assert report.is_eligible is True
    assert report.funding_tier == FundingTier.TIER_2_GLOBAL_REMOTE_PAID
    assert "AI Solutions" in report.matched_track_name


def test_target_track_matching(eligibility_filter):
    """Verify accurate matching for specialized tracks (e.g. Embedded & MLOps)."""
    job_embedded = JobOpportunity(
        id="test-e1",
        title="Firmware & Embedded Systems Intern",
        company="Hardware Corp",
        location="Remote - Worldwide",
        url="https://ashbyhq.com/hardware/1",
        source="Deep Search",
        description_snippet="Work on STM32 microcontrollers, RTOS, and Embedded C drivers. Paid stipend."
    )
    report = eligibility_filter.evaluate(job_embedded)
    assert "Embedded" in report.matched_track_name
