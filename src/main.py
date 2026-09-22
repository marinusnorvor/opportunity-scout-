"""Autonomous Opportunity Finder & Verification Engine - Pipeline Orchestrator."""

import argparse
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.scrapers import (
    ATSScraper,
    DeepSearchEngine,
    RemoteFeedScraper,
    ResearchPortalsScraper,
)
from src.verification import ScamVerifier
from src.evaluation import EligibilityFilter, OpportunityRanker
from src.storage import Deduplicator, GoogleSheetsAdapter
from src.notifications import EmailNotifier

# Configure UTF-8 for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("PipelineOrchestrator")


def run_pipeline(
    dry_run: bool = False,
    limit: int = 20,
    skip_deep_search: bool = False,
) -> None:
    """Execute the end-to-end autonomous discovery and verification pipeline."""
    load_dotenv()
    logger.info("=" * 60)
    logger.info("🚀 STARTING AUTONOMOUS OPPORTUNITY DISCOVERY PIPELINE")
    logger.info("=" * 60)

    # 1. Initialize Core Engines
    deduplicator = Deduplicator()
    verifier = ScamVerifier()
    eligibility_filter = EligibilityFilter()
    ranker = OpportunityRanker()
    sheets_adapter = GoogleSheetsAdapter()
    email_notifier = EmailNotifier()

    # 2. Ingestion: Run Scrapers
    scrapers = [
        ResearchPortalsScraper(),
        RemoteFeedScraper(),
        ATSScraper(),
    ]
    if not skip_deep_search:
        scrapers.append(DeepSearchEngine())

    all_raw_jobs = []
    for scraper in scrapers:
        try:
            logger.info(f"==> Launching {scraper.name}...")
            jobs = scraper.fetch_opportunities(limit=limit)
            all_raw_jobs.extend(jobs)
            logger.info(f"[{scraper.name}] Retrieved {len(jobs)} candidates.")
        except Exception as exc:
            logger.error(f"[{scraper.name}] Unexpected scraper failure: {exc}")

    total_scanned = len(all_raw_jobs)
    logger.info(f"\n📊 Total raw opportunities collected: {total_scanned}")

    # 3. Deduplication: Filter out already processed opportunities
    fresh_jobs = deduplicator.filter_unseen(all_raw_jobs)
    logger.info(f"✨ Brand new (unseen) opportunities: {len(fresh_jobs)}")

    # 4. Verification (Real vs. Fake / Scam Detection)
    verified_jobs = []
    scam_count = 0
    for job in fresh_jobs:
        report = verifier.verify(job)
        if report.is_legitimate:
            job.is_verified = True
            job.verification_reason = report.reason
            verified_jobs.append(job)
        else:
            scam_count += 1
            logger.warning(f"🚫 [SCAM/UNTRUSTED REJECTED] '{job.title}' at '{job.company}' -> {report.reason}")

    logger.info(f"🛡️ Verification complete: {len(verified_jobs)} legitimate, {scam_count} rejected.")

    # 5. Eligibility & Funding Filtering (Ghana Undergrad + Remote/Fully-Funded)
    eligible_jobs = []
    ineligible_count = 0
    for job in verified_jobs:
        report = eligibility_filter.evaluate(job)
        if report.is_eligible:
            job.eligibility_score = report.match_score
            eligible_jobs.append(job)
        else:
            ineligible_count += 1
            logger.info(f"❌ [INELIGIBLE] '{job.title}' at '{job.company}' -> {report.reasons[0] if report.reasons else 'Failed criteria'}")

    total_eligible = len(eligible_jobs)
    logger.info(f"🎯 Eligibility screening complete: {total_eligible} match criteria ({ineligible_count} ineligible).")

    # 6. Ranking & Top-3 Selection
    ranked_jobs = ranker.rank(eligible_jobs)
    top_3_jobs = ranker.select_top_n(ranked_jobs, n=3)

    logger.info("\n" + "=" * 60)
    logger.info("🏆 TOP 3 PROMISING OPPORTUNITIES SELECTED FOR TODAY:")
    logger.info("=" * 60)
    for idx, opp in enumerate(top_3_jobs, start=1):
        logger.info(
            f"#{idx} [{opp.ranking_score:.1f}/100] {opp.title} @ {opp.company}\n"
            f"    Track: {opp.track_name}\n"
            f"    Funding: {opp.funding_tier.value}\n"
            f"    URL: {opp.url}"
        )

    # 7. Persistence (Google Sheets / CSV Fallback)
    if not dry_run:
        sheets_adapter.append_opportunities(ranked_jobs)
        for job in fresh_jobs:
            deduplicator.mark_seen(job)
        deduplicator.save()
    else:
        logger.info("[Dry Run] Skipping Google Sheets append and seen_jobs cache update.")
        # Still record to CSV in dry-run for inspection
        sheets_adapter.append_opportunities(ranked_jobs)

    # 8. Notification (Top 3 Email Digest / HTML Preview)
    email_notifier.send_top_opportunities_digest(
        top_opportunities=top_3_jobs,
        total_scanned=total_scanned,
        total_eligible=total_eligible,
        dry_run=dry_run,
    )

    logger.info("\n✅ PIPELINE RUN COMPLETED SUCCESSFULLY.")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Opportunity Finder & Verification Engine")
    parser.add_argument("--dry-run", action="store_true", help="Run without sending real emails or committing cache")
    parser.add_argument("--limit", type=int, default=15, help="Limit items per scraper source")
    parser.add_argument("--skip-search", action="store_true", help="Skip web search dorking for quick testing")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    run_pipeline(
        dry_run=args.dry_run,
        limit=args.limit,
        skip_deep_search=args.skip_search,
    )


if __name__ == "__main__":
    main()
