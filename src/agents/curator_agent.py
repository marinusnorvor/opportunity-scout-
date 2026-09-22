"""Agent 4: Curator & Dispatch Agent (Persistence, Quota Ranking & Delivery).

Enforces a balanced Top 3 mix (1 Ghana Local, 1 Fully Funded International, 1 Global Remote),
appends rich rows to Google Sheets, and dispatches the HTML morning email digest.
"""

import logging
from typing import List, Optional
from src.models import (
    JobOpportunity,
    FundingTier,
    WorkMode,
)
from src.storage.sheets_adapter import GoogleSheetsAdapter
from src.notifications.email_notifier import EmailNotifier

logger = logging.getLogger("CuratorAgent")


class CuratorAgent:
    """Ranks opportunities, guarantees geographic diversity, and orchestrates delivery."""

    def __init__(
        self,
        sheets_adapter: Optional[GoogleSheetsAdapter] = None,
        email_notifier: Optional[EmailNotifier] = None,
    ):
        self.sheets = sheets_adapter or GoogleSheetsAdapter()
        self.notifier = email_notifier or EmailNotifier()

    def score_opportunity(self, opp: JobOpportunity) -> float:
        """Calculate multi-criteria 0-100 score."""
        score = 50.0

        # Funding & Compensation
        if opp.outside_ghana_funding == "Fully Funded":
            score += 40.0
        elif opp.work_mode == WorkMode.REMOTE_WORLDWIDE and opp.is_paid:
            score += 30.0
        elif opp.is_ghana and opp.is_paid:
            score += 25.0
        elif not opp.is_paid:
            score -= 30.0

        # Company Dossier & Reputation bonus
        if opp.company_dossier and opp.company_dossier.org_type in [
            "University / Scientific Research Institute",
            "Multilateral Organization / Global NGO",
            "Financial Institution / FinTech",
        ]:
            score += 10.0

        # Application proof bonus
        if "Form" in opp.application_proof or "Portal" in opp.application_proof:
            score += 5.0

        opp.ranking_score = round(max(0.0, min(100.0, score)), 1)
        return opp.ranking_score

    def rank(self, opportunities: List[JobOpportunity]) -> List[JobOpportunity]:
        """Score and sort all opportunities descending."""
        for opp in opportunities:
            self.score_opportunity(opp)
        return sorted(opportunities, key=lambda x: x.ranking_score, reverse=True)

    def select_balanced_top_3(self, opportunities: List[JobOpportunity]) -> List[JobOpportunity]:
        """Select a balanced Top 3: 1 Ghana Local + 1 Fully Funded International + 1 Global Remote."""
        ranked = self.rank(opportunities)
        selected: List[JobOpportunity] = []
        used_ids = set()

        # 1. Best Ghana Local Role
        ghana_jobs = [j for j in ranked if j.is_ghana and j.id not in used_ids]
        if ghana_jobs:
            selected.append(ghana_jobs[0])
            used_ids.add(ghana_jobs[0].id)

        # 2. Best Fully Funded International Role
        funded_jobs = [
            j for j in ranked
            if (not j.is_ghana) and (j.outside_ghana_funding == "Fully Funded") and j.id not in used_ids
        ]
        if funded_jobs:
            selected.append(funded_jobs[0])
            used_ids.add(funded_jobs[0].id)

        # 3. Best Global Remote Role
        remote_jobs = [
            j for j in ranked
            if j.work_mode == WorkMode.REMOTE_WORLDWIDE and j.is_paid and j.id not in used_ids
        ]
        if remote_jobs:
            selected.append(remote_jobs[0])
            used_ids.add(remote_jobs[0].id)

        # Fill remaining slots with the best overall roles if any slot was empty
        if len(selected) < 3:
            for job in ranked:
                if job.id not in used_ids:
                    selected.append(job)
                    used_ids.add(job.id)
                    if len(selected) == 3:
                        break

        logger.info(f"[CuratorAgent] Selected Top {len(selected)} balanced opportunities for today.")
        return selected

    def deliver(
        self,
        all_verified_jobs: List[JobOpportunity],
        top_3_jobs: List[JobOpportunity],
        total_scanned: int,
        dry_run: bool = False,
    ) -> None:
        """Persist verified listings into Google Sheets and dispatch the morning email."""
        logger.info(f"[CuratorAgent] Logging {len(all_verified_jobs)} verified rows to Google Sheets/CSV...")
        self.sheets.append_opportunities(all_verified_jobs)

        logger.info(f"[CuratorAgent] Dispatching Top {len(top_3_jobs)} morning email digest...")
        self.notifier.send_top_opportunities_digest(
            top_opportunities=top_3_jobs,
            total_scanned=total_scanned,
            total_eligible=len(all_verified_jobs),
            dry_run=dry_run,
        )
