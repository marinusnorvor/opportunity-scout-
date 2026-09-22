"""Unit tests for Agent 4: Curator Agent (Balanced Quota Ranking)."""

import pytest
from src.agents.curator_agent import CuratorAgent
from src.models import JobOpportunity, WorkMode, CompanyDossier


@pytest.fixture
def curator_agent():
    return CuratorAgent()


def test_balanced_quota_selection(curator_agent):
    """Verify that select_balanced_top_3 picks 1 Ghana + 1 Fully Funded Intl + 1 Global Remote."""
    jobs = [
        # Job 1: Ghana local
        JobOpportunity(
            id="gh-1",
            title="FinTech Operations Trainee",
            company="Zeepay Ghana",
            location="Accra, Ghana",
            is_ghana=True,
            work_mode=WorkMode.ONSITE_GHANA,
            is_paid=True,
            outside_ghana_funding="N/A",
            url="https://zeepay.com/apply",
            source="Ghana Hub",
            company_dossier=CompanyDossier(org_type="Financial Institution / FinTech"),
        ),
        # Job 2: Fully Funded International
        JobOpportunity(
            id="intl-1",
            title="Summer Student Programme",
            company="CERN",
            location="Geneva, Switzerland",
            is_ghana=False,
            work_mode=WorkMode.ONSITE_ABROAD,
            is_paid=True,
            outside_ghana_funding="Fully Funded",
            url="https://cern.ch/apply",
            source="Portal",
            company_dossier=CompanyDossier(org_type="University / Scientific Research Institute"),
        ),
        # Job 3: Global Remote Paid
        JobOpportunity(
            id="rem-1",
            title="Customer Operations & Marketing Intern",
            company="Remote First Inc",
            location="Remote - Worldwide",
            is_ghana=False,
            work_mode=WorkMode.REMOTE_WORLDWIDE,
            is_paid=True,
            outside_ghana_funding="N/A",
            url="https://remotefirst.com/apply",
            source="Remotive",
        ),
        # Job 4: Additional high-scoring international role
        JobOpportunity(
            id="intl-2",
            title="Research Fellow",
            company="EPFL",
            location="Lausanne, Switzerland",
            is_ghana=False,
            work_mode=WorkMode.ONSITE_ABROAD,
            is_paid=True,
            outside_ghana_funding="Fully Funded",
            url="https://epfl.ch/apply",
            source="Portal",
        ),
    ]

    top_3 = curator_agent.select_balanced_top_3(jobs)
    assert len(top_3) == 3

    has_ghana = any(j.is_ghana for j in top_3)
    has_fully_funded = any(j.outside_ghana_funding == "Fully Funded" for j in top_3)
    has_remote = any(j.work_mode == WorkMode.REMOTE_WORLDWIDE for j in top_3)

    assert has_ghana is True
    assert has_fully_funded is True
    assert has_remote is True
