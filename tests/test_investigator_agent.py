"""Unit tests for Agent 2: Investigator Agent (Due Diligence & DOM Audit)."""

import pytest
from bs4 import BeautifulSoup
from src.agents.investigator_agent import InvestigatorAgent
from src.models import JobOpportunity


@pytest.fixture
def investigator():
    return InvestigatorAgent()


def test_detect_application_form_mechanism(investigator):
    """Ensure HTML forms with file upload are recognized as active application forms."""
    html = """
    <html>
        <body>
            <h1>Data Analyst Trainee</h1>
            <form action="/submit" method="POST">
                <input type="text" name="candidate_name" />
                <input type="file" name="resume" />
                <button type="submit">Submit Application</button>
            </form>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    mechanism = investigator._detect_application_mechanism(soup, "https://company.com/apply")
    assert "Active Multi-Step Form" in mechanism or "Application Form" in mechanism


def test_detect_ats_portal(investigator):
    """Ensure Greenhouse/Lever links are recognized as enterprise ATS portals."""
    soup = BeautifulSoup("<html><body><h1>Job</h1></body></html>", "html.parser")
    mechanism = investigator._detect_application_mechanism(soup, "https://boards.greenhouse.io/datadog/jobs/123")
    assert "Enterprise ATS" in mechanism


def test_infer_organization_types(investigator):
    """Verify categorization of organization types for company dossiers."""
    assert "University" in investigator._infer_org_type("EPFL", "Swiss institute of technology", "epfl.ch")
    assert "Multilateral" in investigator._infer_org_type("United Nations", "Global intergovernmental organization", "un.org")
    assert "FinTech" in investigator._infer_org_type("Zeepay", "Mobile money remittance", "myzeepay.com")
    assert "Telecommunications" in investigator._infer_org_type("MTN Ghana", "Mobile telecom provider", "mtn.com.gh")


def test_rejection_of_expired_posting(investigator, monkeypatch):
    """Ensure InvestigatorAgent drops postings that display expired job banners."""
    expired_html = "<html><body><h1>This job posting has expired</h1><p>Check back later.</p></body></html>"
    monkeypatch.setattr(investigator, "_fetch_page", lambda url: (expired_html, url, 200))

    opp = JobOpportunity(
        id="test-exp-1",
        title="Software Intern",
        company="Old Co",
        location="Remote",
        url="https://company.com/jobs/expired",
        source="Test",
    )
    report = investigator.investigate(opp)
    assert report.is_link_active is False
    assert report.has_expired_markers is True
    assert "expired" in report.reason.lower()
