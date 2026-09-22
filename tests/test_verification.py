"""Unit tests for the Scam and Integrity Verification Engine."""

import pytest
from src.models import JobOpportunity
from src.verification.scam_verifier import ScamVerifier


@pytest.fixture
def verifier():
    return ScamVerifier()


def test_trusted_ats_verification(verifier):
    """Ensure trusted ATS links are marked legitimate."""
    job = JobOpportunity(
        id="test-1",
        title="Software Engineering Intern",
        company="Datadog",
        location="Remote",
        url="https://boards.greenhouse.io/datadog/jobs/123456",
        source="Greenhouse",
        description_snippet="Join our backend systems team as an intern."
    )
    report = verifier.verify(job)
    assert report.is_legitimate is True
    assert report.trust_score >= 0.8
    assert len(report.flags) == 0


def test_suspicious_form_rejection(verifier):
    """Reject applications hosted on suspicious free form portals."""
    job = JobOpportunity(
        id="test-2",
        title="AI Research Intern",
        company="Shady Tech",
        location="Worldwide",
        url="https://forms.gle/xyz123fakeform",
        source="Deep Search",
        description_snippet="Fill out this Google Form to apply for our AI internship."
    )
    report = verifier.verify(job)
    assert report.is_legitimate is False
    assert any("suspicious" in f.lower() for f in report.flags)


def test_financial_red_flag_rejection(verifier):
    """Reject postings that demand training or application fees."""
    job = JobOpportunity(
        id="test-3",
        title="Robotics Engineer Intern",
        company="RoboCorp",
        location="Remote",
        url="https://robocorp-fake.com/careers",
        source="Deep Search",
        description_snippet="Selected interns must pay a $150 training fee for certification."
    )
    report = verifier.verify(job)
    assert report.is_legitimate is False
    assert any("Financial Red Flag" in f for f in report.flags)


def test_consumer_webmail_flag(verifier):
    """Flag enterprise postings asking applicants to email free Gmail accounts."""
    job = JobOpportunity(
        id="test-4",
        title="Cloud Infrastructure Intern",
        company="Global Enterprise Systems Inc",
        location="Remote",
        url="https://boards.greenhouse.io/globalent/jobs/999",
        source="Greenhouse",
        description_snippet="Please send your CV directly to recruiter123@gmail.com for expedited review."
    )
    report = verifier.verify(job)
    assert any("free webmail" in f for f in report.flags)
