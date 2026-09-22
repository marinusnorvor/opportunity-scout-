"""Data models for the Autonomous Opportunity Finder & Verification Engine."""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class FundingTier(str, Enum):
    """Funding classification tiers."""
    TIER_1_FULLY_FUNDED = "Tier 1: Fully Funded Abroad (Flight + Housing + Stipend)"
    TIER_2_GLOBAL_REMOTE_PAID = "Tier 2: Global Remote Paid (Work from Ghana)"
    TIER_3_PARTIALLY_FUNDED = "Tier 3: Partially Funded / Local High Stipend"
    UNPAID_OR_UNCLEAR = "Unpaid or Insufficient Funding"


class WorkMode(str, Enum):
    """Work authorization and physical presence modes."""
    REMOTE_WORLDWIDE = "Remote - Worldwide"
    ONSITE_ABROAD = "Onsite - Abroad"
    ONSITE_GHANA = "Onsite - Ghana"
    HYBRID_GHANA = "Hybrid - Ghana"
    RESTRICTED_ONSITE = "Restricted Onsite (Requires Local Citizenship/No Visa)"


class FundingBenefits(BaseModel):
    """Detailed breakdown of benefits and allowances."""
    flight_covered: bool = False
    housing_covered: bool = False
    stipend_provided: bool = False
    stipend_details: Optional[str] = None
    visa_sponsorship: bool = False
    application_fee_required: bool = False
    summary: str = "Standard opportunity"


class VerificationReport(BaseModel):
    """Integrity and scam analysis assessment."""
    is_legitimate: bool = True
    trust_score: float = 1.0  # 0.0 to 1.0
    domain: str = ""
    flags: List[str] = Field(default_factory=list)
    reason: str = "Verified legitimate domain & posting"


class EligibilityReport(BaseModel):
    """Candidate profile matching evaluation."""
    is_eligible: bool = True
    match_score: float = 1.0  # 0.0 to 1.0
    matched_track_id: Optional[str] = None
    matched_track_name: Optional[str] = None
    funding_tier: FundingTier = FundingTier.UNPAID_OR_UNCLEAR
    reasons: List[str] = Field(default_factory=list)


class JobOpportunity(BaseModel):
    """Core domain model representing a discovered internship opportunity."""
    id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    track_id: Optional[str] = None
    track_name: Optional[str] = None
    description_snippet: str = ""
    work_mode: WorkMode = WorkMode.REMOTE_WORLDWIDE
    funding_benefits: FundingBenefits = Field(default_factory=FundingBenefits)
    funding_tier: FundingTier = FundingTier.UNPAID_OR_UNCLEAR
    deadline: Optional[str] = None
    
    # Verification & Evaluation metadata
    is_verified: bool = False
    verification_reason: str = ""
    eligibility_score: float = 0.0
    ranking_score: float = 0.0
    
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
    discovered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_sheet_row(self) -> List[Any]:
        """Format as a flat row for Google Sheets logging."""
        benefits_list = []
        if self.funding_benefits.flight_covered:
            benefits_list.append("✈️ Flight Covered")
        if self.funding_benefits.housing_covered:
            benefits_list.append("🏠 Housing Provided")
        if self.funding_benefits.stipend_provided:
            stipend_text = f"💵 Stipend ({self.funding_benefits.stipend_details})" if self.funding_benefits.stipend_details else "💵 Stipend Provided"
            benefits_list.append(stipend_text)
        if self.funding_benefits.visa_sponsorship:
            benefits_list.append("🛂 Visa Sponsored")
        
        benefits_str = " | ".join(benefits_list) if benefits_list else "Not specified"

        return [
            self.discovered_at[:10],                # Date (YYYY-MM-DD)
            self.track_name or "General Technical",  # Track
            self.title,                             # Role Title
            self.company,                           # Company / Institution
            self.funding_tier.value,                # Funding Tier
            benefits_str,                           # Benefits Breakdown
            self.location,                          # Location / Work Mode
            self.deadline or "Rolling / Open",      # Deadline
            f"{self.ranking_score:.1f}/100",        # Score
            self.url,                               # Application URL
            "✅ Verified Legitimate" if self.is_verified else "⚠️ Needs Review", # Status
            self.source                             # Source Channel
        ]
