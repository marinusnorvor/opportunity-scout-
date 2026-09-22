"""Data models for the Multi-Agent Opportunity Intelligence System."""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class FundingTier(str, Enum):
    """Funding classification tiers."""
    TIER_1_FULLY_FUNDED = "Tier 1: Fully Funded Abroad (Flight + Housing + Stipend)"
    TIER_2_GLOBAL_REMOTE_PAID = "Tier 2: Global Remote Paid (Work from Ghana)"
    TIER_3_LOCAL_OR_PARTIAL = "Tier 3: Local Ghana Paid / Partially Funded"
    TIER_3_PARTIALLY_FUNDED = "Tier 3: Local Ghana Paid / Partially Funded"
    UNPAID_OR_SELF_FUNDED = "Unpaid or Self-Funded"
    UNPAID_OR_UNCLEAR = "Unpaid or Self-Funded"


class WorkMode(str, Enum):
    """Work authorization and physical presence modes."""
    REMOTE_WORLDWIDE = "Remote - Worldwide"
    ONSITE_GHANA = "Onsite - Ghana"
    HYBRID_GHANA = "Hybrid - Ghana"
    ONSITE_ABROAD = "Onsite - Abroad"
    HYBRID_ABROAD = "Hybrid - Abroad"
    UNSPECIFIED = "Unspecified / Flexible"


class CompanyDossier(BaseModel):
    """Background due diligence intelligence on the hiring organization."""
    overview: str = "Established organization offering student training."
    org_type: str = "Corporate / Enterprise"  # Startup, Enterprise, University, NGO, Govt, Financial
    headquarters: str = "Location unspecified"
    credibility_indicators: str = "Verified domain & professional presence"


class FundingBenefits(BaseModel):
    """Allowances and financial support breakdown."""
    flight_covered: bool = False
    housing_covered: bool = False
    stipend_provided: bool = False
    stipend_details: Optional[str] = None
    visa_sponsorship: bool = False
    application_fee_required: bool = False
    summary: str = "Standard compensation"


class DeepVerificationReport(BaseModel):
    """Integrity, DOM application-form audit, and company due diligence."""
    is_legitimate: bool = True
    is_link_active: bool = True
    application_mechanism: str = "Application Mechanism Verified"
    has_expired_markers: bool = False
    trust_score: float = 1.0
    domain: str = ""
    flags: List[str] = Field(default_factory=list)
    reason: str = "Link audited: Active application mechanism and verified organization."
    company_dossier: CompanyDossier = Field(default_factory=CompanyDossier)


# Backwards compatibility alias for ScamVerifier
VerificationReport = DeepVerificationReport


class EligibilityReport(BaseModel):
    """Candidate profile matching evaluation."""
    is_eligible: bool = True
    match_score: float = 1.0  # 0.0 to 1.0
    field_category: str = "General"
    matched_track_id: Optional[str] = None
    matched_track_name: Optional[str] = None
    funding_tier: FundingTier = FundingTier.UNPAID_OR_SELF_FUNDED
    reasons: List[str] = Field(default_factory=list)


class JobOpportunity(BaseModel):
    """Domain model representing an audited, field-agnostic internship."""
    id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    
    # Field & Work Mode
    field_category: str = "General"  # Business, Healthcare, Tech, Law, Finance, Media, etc.
    work_mode: WorkMode = WorkMode.REMOTE_WORLDWIDE
    is_ghana: bool = False
    
    # Compensation & Funding
    is_paid: bool = True
    compensation_details: str = "Paid Stipend"
    outside_ghana_funding: str = "N/A"  # Fully Funded, Partially Funded, Self-Funded, or N/A
    funding_tier: FundingTier = FundingTier.TIER_3_LOCAL_OR_PARTIAL
    funding_benefits: FundingBenefits = Field(default_factory=FundingBenefits)
    
    description_snippet: str = ""
    deadline: Optional[str] = None
    
    # Due Diligence & Verification Metadata
    company_dossier: CompanyDossier = Field(default_factory=CompanyDossier)
    is_verified: bool = False
    verification_reason: str = ""
    application_proof: str = "Verified Live Link"
    eligibility_score: float = 0.0
    ranking_score: float = 0.0
    
    # Legacy track fields for backward compatibility
    track_id: Optional[str] = None
    track_name: Optional[str] = None
    
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
    discovered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_sheet_row(self) -> List[Any]:
        """Format as a flat row for Google Sheets logging."""
        comp_str = self.compensation_details if self.is_paid else "Unpaid"
        
        return [
            self.discovered_at[:10],                                # Discovered Date
            self.field_category,                                    # Field / Industry
            self.title,                                             # Role Title
            self.company,                                           # Company / Organization
            self.company_dossier.overview,                          # Company Overview / Mission
            self.work_mode.value,                                   # Work Mode (Remote/Onsite)
            comp_str,                                               # Compensation Status
            self.location,                                          # Location
            self.outside_ghana_funding,                             # Outside-Ghana Funding (Fully Funded/etc)
            self.deadline or "Rolling / Open",                      # Deadline
            f"{self.ranking_score:.1f}/100",                        # Score
            self.url,                                               # Verified Application URL
            self.application_proof,                                 # Verification Proof (DOM audited)
            self.source                                             # Source Channel
        ]
