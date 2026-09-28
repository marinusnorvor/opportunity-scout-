"""Unit tests for RemoteFeedScraper (RemoteOK + Remotive integration)."""

import pytest
from src.scrapers.remote_feeds import RemoteFeedScraper
from src.models import WorkMode


@pytest.fixture
def remote_scraper():
    return RemoteFeedScraper()


def test_target_role_matching(remote_scraper):
    """Verify detection of various entry-level, student, assistant, and intern roles."""
    assert remote_scraper._is_target_role("Junior Digital Assets Operations Analyst", "entry role") is True
    assert remote_scraper._is_target_role("Marketing Student Assistant", "support team") is True
    assert remote_scraper._is_target_role("People Operations Coordinator", "coordinate HR") is True
    assert remote_scraper._is_target_role("Senior VP of Engineering", "10+ years experience") is False


def test_global_remote_filtering(remote_scraper):
    """Ensure Worldwide roles pass while restricted US/UK-only roles are filtered out."""
    assert remote_scraper._is_global_remote("Worldwide") is True
    assert remote_scraper._is_global_remote("Anywhere") is True
    assert remote_scraper._is_global_remote("Global") is True
    assert remote_scraper._is_global_remote("USA Only") is False
    assert remote_scraper._is_global_remote("US Only") is False


def test_remoteok_parsing_mock(remote_scraper, monkeypatch):
    """Verify parsing of RemoteOK JSON format into standard JobOpportunity schema."""
    sample_remoteok_data = [
        {"legal": "terms"},  # header item to skip
        {
            "id": "12345",
            "position": "Junior Operations Associate",
            "company": "Global FinTech",
            "location": "Worldwide",
            "description": "We are seeking a motivated junior operations associate. Paid remote.",
            "salary_min": 40000,
            "salary_max": 50000,
            "tags": ["finance", "operations"],
            "url": "https://remoteok.com/remote-jobs/12345",
        },
        {
            "id": "67890",
            "position": "Lead Principal Architect",
            "company": "Big Tech",
            "location": "Worldwide",
            "description": "Lead architecture team.",
            "url": "https://remoteok.com/remote-jobs/67890",
        },
    ]

    monkeypatch.setattr(remote_scraper, "safe_get", lambda url, is_json=True: sample_remoteok_data)

    jobs = remote_scraper._fetch_remoteok(limit=5)
    assert len(jobs) == 1
    assert jobs[0].title == "Junior Operations Associate"
    assert jobs[0].company == "Global FinTech"
    assert jobs[0].work_mode == WorkMode.REMOTE_WORLDWIDE
    assert jobs[0].is_paid is True
    assert "$40,000-$50,000/yr" in jobs[0].compensation_details
