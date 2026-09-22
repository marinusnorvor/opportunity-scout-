"""Unit tests for Deduplication and CSV Fallback persistence."""

from pathlib import Path
from src.models import JobOpportunity, FundingTier
from src.storage.deduplicator import Deduplicator
from src.storage.sheets_adapter import GoogleSheetsAdapter


def test_deduplication_lifecycle(tmp_path):
    """Test seen cache recording, filtering, and persistence."""
    cache_file = tmp_path / "test_seen.json"
    dedup = Deduplicator(cache_file=cache_file)

    job1 = JobOpportunity(
        id="hash-123",
        title="MLOps Intern",
        company="Cohere",
        location="Remote",
        url="https://cohere.com/jobs/1",
        source="ATS",
    )
    job2 = JobOpportunity(
        id="hash-456",
        title="SWE Intern",
        company="Figma",
        location="Remote",
        url="https://figma.com/jobs/2",
        source="ATS",
    )

    assert dedup.is_seen(job1) is False
    dedup.mark_seen(job1)
    dedup.save()

    # Re-initialize new deduplicator from saved disk state
    dedup_reloaded = Deduplicator(cache_file=cache_file)
    assert dedup_reloaded.is_seen(job1) is True
    assert dedup_reloaded.is_seen(job2) is False

    unseen = dedup_reloaded.filter_unseen([job1, job2])
    assert len(unseen) == 1
    assert unseen[0].id == "hash-456"


def test_csv_fallback_append(tmp_path):
    """Test that GoogleSheetsAdapter safely writes to CSV when no API credentials exist."""
    csv_path = tmp_path / "test_output.csv"
    adapter = GoogleSheetsAdapter(fallback_csv_path=csv_path)

    job = JobOpportunity(
        id="test-csv-1",
        title="Backend Developer Intern",
        company="Scale AI",
        location="Remote",
        url="https://scale.com/jobs/1",
        source="Greenhouse",
        track_name="Backend Developer Intern (Python / Java)",
        funding_tier=FundingTier.TIER_2_GLOBAL_REMOTE_PAID,
        ranking_score=88.5,
    )

    rows_appended = adapter.append_opportunities([job])
    assert rows_appended == 1
    assert csv_path.exists()

    content = csv_path.read_text(encoding="utf-8")
    assert "Backend Developer Intern" in content
    assert "Scale AI" in content
