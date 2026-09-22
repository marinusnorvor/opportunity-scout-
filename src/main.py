"""Multi-Agent Opportunity Intelligence System - Pipeline Orchestrator.

Orchestrates 4 specialized autonomous agents:
- Agent 1 (ScoutAgent): Ingests listings across Ghana, remote feeds, and global fellowships.
- Agent 2 (InvestigatorAgent): Deep link audit, active form detection & company due diligence.
- Agent 3 (CognitiveAgent): Groq LLaMA 3.3 70B & Gemini Flash structured intelligence extraction.
- Agent 4 (CuratorAgent): Balanced quota ranking (Ghana + Intl + Remote), Google Sheets & email delivery.
"""

import argparse
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure UTF-8 for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.agents import (
    ScoutAgent,
    InvestigatorAgent,
    CognitiveAgent,
    CuratorAgent,
)
from src.storage import Deduplicator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("SystemOrchestrator")


def run_pipeline(
    dry_run: bool = False,
    limit: int = 15,
    skip_deep_search: bool = False,
) -> None:
    """Execute the multi-agent opportunity intelligence pipeline."""
    load_dotenv()
    logger.info("=" * 65)
    logger.info("🚀 STARTING MULTI-AGENT OPPORTUNITY INTELLIGENCE SYSTEM")
    logger.info("=" * 65)

    # 1. Initialize Autonomous Agents & Deduplication
    scout = ScoutAgent()
    investigator = InvestigatorAgent()
    cognitive = CognitiveAgent()
    curator = CuratorAgent()
    deduplicator = Deduplicator()

    # 2. Agent 1: Scout Agent (Ingestion across all channels)
    logger.info("\n--- [AGENT 1: SCOUT AGENT] Multi-Source Ingestion ---")
    raw_candidates = scout.scout_all(
        limit_per_source=limit,
        skip_deep_search=skip_deep_search,
    )
    total_scanned = len(raw_candidates)

    # Filter out previously processed opportunities
    unseen_jobs = deduplicator.filter_unseen(raw_candidates)
    logger.info(f"[ScoutAgent] Raw candidates: {total_scanned} | Brand new (unseen): {len(unseen_jobs)}")

    # 3. Agent 2: Investigator Agent (Deep Link Audit & Company Intelligence)
    logger.info("\n--- [AGENT 2: INVESTIGATOR AGENT] Deep Link & Due Diligence Audit ---")
    verified_jobs = []
    dropped_count = 0

    for job in unseen_jobs:
        report = investigator.investigate(job)
        if report.is_legitimate and report.is_link_active:
            job.is_verified = True
            job.verification_reason = report.reason
            verified_jobs.append(job)
        else:
            dropped_count += 1
            logger.info(f"🚫 [DROPPED / DEAD / SCAM] '{job.title}' @ '{job.company}' -> {report.reason}")

    logger.info(f"[InvestigatorAgent] Verified active: {len(verified_jobs)} | Dropped (404/expired/scam): {dropped_count}")

    # 4. Agent 3: Cognitive Extraction Agent (Groq + Gemini LLM Parsing)
    logger.info("\n--- [AGENT 3: COGNITIVE AGENT] Groq & Gemini Intelligence Extraction ---")
    enriched_jobs = []
    for job in verified_jobs:
        enriched_job = cognitive.analyze(job)
        enriched_jobs.append(enriched_job)
        logger.info(
            f"🧠 [Extracted] {job.title} @ {job.company} | Field: {job.field_category} | "
            f"Mode: {job.work_mode.value} | Funding: {job.outside_ghana_funding} | Pay: {job.compensation_details}"
        )

    # 5. Agent 4: Curator & Dispatch Agent (Ranking, Google Sheets & Top 3 Email)
    logger.info("\n--- [AGENT 4: CURATOR AGENT] Balanced Quota Ranking & Delivery ---")
    top_3_curated = curator.select_balanced_top_3(enriched_jobs)

    logger.info("\n" + "=" * 65)
    logger.info("🏆 CURATED TOP 3 DIVERSE OPPORTUNITIES FOR TODAY:")
    logger.info("=" * 65)
    for idx, opp in enumerate(top_3_curated, start=1):
        dossier = opp.company_dossier
        logger.info(
            f"#{idx} [{opp.ranking_score:.1f}/100] {opp.title} @ {opp.company}\n"
            f"    Field: {opp.field_category} | Mode: {opp.work_mode.value}\n"
            f"    Company Overview: {dossier.overview[:90]}...\n"
            f"    Funding (Outside Ghana): {opp.outside_ghana_funding} | Pay: {opp.compensation_details}\n"
            f"    Proof: {opp.application_proof}\n"
            f"    Apply: {opp.url}"
        )

    # Deliver to Google Sheets and Dispatch Email
    curator.deliver(
        all_verified_jobs=enriched_jobs,
        top_3_jobs=top_3_curated,
        total_scanned=total_scanned,
        dry_run=dry_run,
    )

    # Save deduplication cache
    if not dry_run:
        for job in unseen_jobs:
            deduplicator.mark_seen(job)
        deduplicator.save()
    else:
        logger.info("[Dry Run] Skipping deduplication cache update.")

    logger.info("\n✅ MULTI-AGENT INTELLIGENCE PIPELINE COMPLETED SUCCESSFULLY.")


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Opportunity Intelligence System")
    parser.add_argument("--dry-run", action="store_true", help="Run without live SMTP email or committing cache")
    parser.add_argument("--limit", type=int, default=10, help="Limit items per scraper source")
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
