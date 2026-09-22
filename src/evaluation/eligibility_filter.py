"""Eligibility Filter tailored for Ghana-based Undergraduates seeking Funded / Remote roles."""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.models import (
    JobOpportunity,
    EligibilityReport,
    FundingBenefits,
    FundingTier,
    WorkMode,
)

logger = logging.getLogger(__name__)


class EligibilityFilter:
    """Evaluates candidate eligibility based on nationality, academic standing, and funding."""

    # Disqualifying visa phrases for someone without pre-existing US/EU/UK authorization
    VISA_DISQUALIFIERS = [
        r"\bmust\s+be\s+a\s+(?:u\.?s\.?|united\s+states)\s+citizen\b",
        r"\bu\.?s\.?\s+citizenship\s+required\b",
        r"\bgreen\s+card\s+(?:holder|required)\b",
        r"\bactive\s+security\s+clearance\s+required\b",
        r"\b(?:no|not\s+offering)\s+(?:visa\s+)?sponsorship\b",
        r"\bwithout\s+(?:the\s+need\s+for\s+)?(?:visa\s+)?sponsorship\b",
        r"\bmust\s+have\s+the\s+unrestricted\s+right\s+to\s+work\s+in\s+the\s+(?:uk|eu|us)\b",
        r"\bnot\s+eligible\s+for\s+sponsorship\b",
        r"\bdo\s+not\s+sponsor\b",
    ]

    # Explicit unpaid indicators
    UNPAID_MARKERS = [
        r"\bunpaid\s+internship\b",
        r"\bthis\s+is\s+an\s+unpaid\b",
        r"\bfor\s+(?:college\s+|academic\s+)?credit\s+only\b",
        r"\bvolunteer\s+internship\b",
    ]

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path(__file__).resolve().parent.parent.parent / "config"
        
        self.profile = self._load_json(config_dir / "candidate_profile.json")
        self.tracks_data = self._load_json(config_dir / "target_tracks.json")
        self.tracks = self.tracks_data.get("tracks", [])

    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        """Safely load JSON configuration file."""
        if not path.exists():
            logger.warning(f"Config file not found at {path}")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate(self, opp: JobOpportunity) -> EligibilityReport:
        """Run eligibility checks and benefit extraction on the opportunity."""
        full_text = f"{opp.title} {opp.location} {opp.description_snippet}".lower()
        reasons: List[str] = []

        # 1. Visa & Geographic Restriction Check
        is_ghana_local = "ghana" in full_text or "accra" in full_text
        is_global_remote = "remote" in opp.location.lower() and not any(
            restr in opp.location.lower() for restr in ["us only", "usa only", "uk only", "eu only", "canada only"]
        )

        # Check for hard visa disqualifiers
        for pattern in self.VISA_DISQUALIFIERS:
            if re.search(pattern, full_text):
                if not is_ghana_local:
                    return EligibilityReport(
                        is_eligible=False,
                        match_score=0.0,
                        funding_tier=FundingTier.UNPAID_OR_UNCLEAR,
                        reasons=[f"Disqualified: Requires local citizenship/No visa sponsorship ({pattern})"],
                    )

        # 2. Unpaid Check
        for pattern in self.UNPAID_MARKERS:
            if re.search(pattern, full_text):
                return EligibilityReport(
                    is_eligible=False,
                    match_score=0.0,
                    funding_tier=FundingTier.UNPAID_OR_UNCLEAR,
                    reasons=["Disqualified: Explicitly marked as unpaid / academic credit only"],
                )

        # 3. Extract Benefits & Funding Tier
        benefits = self._extract_benefits(full_text, opp)
        opp.funding_benefits = benefits

        funding_tier = self._determine_funding_tier(opp, is_global_remote, is_ghana_local)
        opp.funding_tier = funding_tier

        # If it's an international onsite role with ZERO travel/housing funding, disqualify
        if not is_ghana_local and not is_global_remote:
            if not benefits.flight_covered and not benefits.housing_covered and not benefits.visa_sponsorship:
                return EligibilityReport(
                    is_eligible=False,
                    match_score=0.2,
                    funding_tier=funding_tier,
                    reasons=["Disqualified: International onsite role without flight/housing sponsorship"],
                )

        # 4. Target Track Matching (Matching 18 technical roles)
        matched_track_id, matched_track_name, track_score = self._match_track(opp.title, opp.description_snippet)
        opp.track_id = matched_track_id
        opp.track_name = matched_track_name or opp.track_name or "General Technical Track"

        # 5. Calculate Final Eligibility Score
        match_score = track_score
        if funding_tier == FundingTier.TIER_1_FULLY_FUNDED:
            match_score = min(1.0, match_score + 0.3)
            reasons.append("Eligible: Tier 1 Fully Funded International Research/Internship")
        elif funding_tier == FundingTier.TIER_2_GLOBAL_REMOTE_PAID:
            match_score = min(1.0, match_score + 0.2)
            reasons.append("Eligible: Tier 2 Global Remote Paid (Hireable from Ghana)")
        elif is_ghana_local:
            match_score = min(1.0, match_score + 0.15)
            reasons.append("Eligible: Local opportunity in Ghana")
        else:
            reasons.append("Eligible: Qualified technical opportunity")

        return EligibilityReport(
            is_eligible=True,
            match_score=round(match_score, 2),
            matched_track_id=matched_track_id,
            matched_track_name=opp.track_name,
            funding_tier=funding_tier,
            reasons=reasons,
        )

    def _extract_benefits(self, text: str, opp: JobOpportunity) -> FundingBenefits:
        """Parse text for flight, accommodation, and stipend allowances."""
        benefits = opp.funding_benefits or FundingBenefits()

        # Flight / Travel
        flight_patterns = [
            r"\b(?:roundtrip|travel|flight)\s+(?:airfare|ticket|allowance|reimburse|covered|provided)\b",
            r"\btravel\s+(?:expenses?\s+)?(?:reimbursed|covered)\b",
            r"\bairfare\s+(?:included|provided)\b",
        ]
        if any(re.search(p, text) for p in flight_patterns):
            benefits.flight_covered = True

        # Housing / Accommodation
        housing_patterns = [
            r"\b(?:housing|accommodation|lodging|room)\s+(?:provided|covered|furnished|allowance|stipend)\b",
            r"\bfree\s+(?:housing|accommodation)\b",
            r"\bon-campus\s+housing\b",
        ]
        if any(re.search(p, text) for p in housing_patterns):
            benefits.housing_covered = True

        # Stipend / Salary
        stipend_patterns = [
            r"\b(?:monthly|weekly|hourly|daily)\s+(?:stipend|allowance|salary|rate)\b",
            r"\$\s?[0-9,]+(?:\s*-\s*\$?[0-9,]+)?\s*(?:/hr|per\s+hour|/month|per\s+month)",
            r"\bcompetitive\s+(?:stipend|compensation|pay)\b",
            r"\bstipend\s+of\b",
            r"\bpaid\s+internship\b",
        ]
        stipend_match = None
        for p in stipend_patterns:
            m = re.search(p, text)
            if m:
                benefits.stipend_provided = True
                stipend_match = m.group(0)
                break

        if stipend_match and not benefits.stipend_details:
            benefits.stipend_details = stipend_match

        # Visa
        if re.search(r"\b(?:visa\s+support|visa\s+sponsorship|invitation\s+letter|assist\s+with\s+visa)\b", text):
            benefits.visa_sponsorship = True

        return benefits

    def _determine_funding_tier(self, opp: JobOpportunity, is_remote: bool, is_ghana: bool) -> FundingTier:
        """Assign funding category tier."""
        b = opp.funding_benefits
        if b.flight_covered and (b.housing_covered or b.stipend_provided):
            return FundingTier.TIER_1_FULLY_FUNDED
        if is_remote and b.stipend_provided:
            return FundingTier.TIER_2_GLOBAL_REMOTE_PAID
        if b.stipend_provided or is_ghana:
            return FundingTier.TIER_3_PARTIALLY_FUNDED
        return FundingTier.UNPAID_OR_UNCLEAR

    def _match_track(self, title: str, description: str) -> tuple[Optional[str], Optional[str], float]:
        """Match against the 18 specific roles and calculate keyword relevance."""
        best_track_id = None
        best_track_name = None
        highest_score = 0.4  # Baseline for general match
        
        target_text = f"{title} {description}".lower()

        for track in self.tracks:
            track_id = track.get("id")
            track_name = track.get("name")
            keywords = track.get("keywords", [])

            matches = 0
            # Strong boost if track title is in job title
            if any(part.lower() in title.lower() for part in track_name.split("/")[0].split()):
                matches += 3

            for kw in keywords:
                if kw.lower() in target_text:
                    matches += 1

            score = min(1.0, 0.4 + (matches * 0.12))
            if score > highest_score:
                highest_score = score
                best_track_id = track_id
                best_track_name = track_name

        return best_track_id, best_track_name, highest_score
