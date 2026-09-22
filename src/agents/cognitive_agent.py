"""Agent 3: Cognitive Extraction Agent (Powered by Groq + Gemini LLM Router).

Performs nuanced structured intelligence extraction using Groq LLaMA 3.3 70B
with automatic failover to Google Gemini 2.5 Flash and local heuristic fallbacks.
"""

import json
import logging
import os
import re
from typing import Dict, Any, Optional
import requests
from src.models import (
    JobOpportunity,
    WorkMode,
    FundingTier,
)

logger = logging.getLogger("CognitiveAgent")


class CognitiveAgent:
    """Extracts structured intelligence (Field, Paid, Work Mode, Outside-Ghana Funding, Deadline)."""

    SYSTEM_PROMPT = """You are an expert Opportunity Intelligence Agent. Your job is to extract exact structured metadata from internship and fellowship postings.

You must output ONLY valid JSON matching this schema:
{
  "field": "Specific field/industry (e.g., Finance, Software & AI, Healthcare, Law & Policy, Marketing, Engineering, Media)",
  "work_mode": "Remote" or "Onsite" or "Hybrid",
  "is_paid": true or false,
  "compensation_details": "e.g., $3,000/mo, GHS 2,500/mo, Competitive Stipend, or Unpaid",
  "location": "City, Country (e.g., Accra, Ghana or Geneva, Switzerland or Remote)",
  "is_ghana": true if located in Ghana, else false,
  "outside_ghana_funding": "Fully Funded" if flight + accommodation + stipend are covered, else "Partially Funded" if partial stipend/housing, else "Self-Funded", or "N/A" if in Ghana or Remote,
  "deadline": "YYYY-MM-DD or Rolling / Open",
  "summary": "1 sentence summary of candidate eligibility and benefits"
}"""

    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        timeout: int = 15,
    ):
        self.groq_api_key = (groq_api_key or os.getenv("GROQ_API_KEY") or "").strip()
        self.gemini_api_key = (gemini_api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        self.timeout = timeout
        self.groq_client = self._init_groq()

    def _init_groq(self):
        """Initialize Groq client if API key is provided."""
        if not self.groq_api_key:
            return None
        try:
            from groq import Groq
            return Groq(api_key=self.groq_api_key)
        except Exception as exc:
            logger.warning(f"[CognitiveAgent] Could not initialize Groq client: {exc}")
            return None

    def analyze(self, opp: JobOpportunity) -> JobOpportunity:
        """Run cognitive analysis on the job opportunity using the dual LLM router."""
        logger.info(f"[CognitiveAgent] Analyzing intelligence for '{opp.title}' at '{opp.company}'...")
        prompt_text = (
            f"Title: {opp.title}\n"
            f"Company: {opp.company}\n"
            f"Location: {opp.location}\n"
            f"Source: {opp.source}\n"
            f"Description:\n{opp.description_snippet[:1500]}"
        )

        extracted_data = None

        # 1. Primary Engine: Groq LLaMA 3.3 70B (Fast, free tier)
        if self.groq_client:
            extracted_data = self._call_groq(prompt_text)

        # 2. Secondary Engine: Google Gemini Flash (Fallback)
        if not extracted_data and self.gemini_api_key:
            logger.info("[CognitiveAgent] Groq unavailable or unconfigured. Falling over to Gemini API...")
            extracted_data = self._call_gemini(prompt_text)

        # 3. Tertiary Engine: Intelligent Heuristic Fallback (Runs offline / zero-cost)
        if not extracted_data:
            logger.info("[CognitiveAgent] Running heuristic extraction fallback.")
            extracted_data = self._heuristic_fallback(opp)

        # Apply extracted attributes to domain model
        self._apply_extraction(opp, extracted_data)
        return opp

    def _call_groq(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Query Groq Cloud API for structured JSON extraction."""
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=600,
            )
            raw_content = response.choices[0].message.content
            return json.loads(raw_content)
        except Exception as exc:
            logger.warning(f"[CognitiveAgent] Groq API call failed: {exc}")
            return None

    def _call_gemini(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Query Google Gemini API endpoint as fallback."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{self.SYSTEM_PROMPT}\n\nAnalyze this listing:\n{prompt}"}
                    ]
                }
            ],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1},
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            logger.warning(f"[CognitiveAgent] Gemini API returned status {resp.status_code}: {resp.text[:120]}")
            return None
        except Exception as exc:
            logger.warning(f"[CognitiveAgent] Gemini API call failed: {exc}")
            return None

    def _heuristic_fallback(self, opp: JobOpportunity) -> Dict[str, Any]:
        """High-accuracy deterministic fallback parser when LLM API keys are not provided."""
        text = f"{opp.title} {opp.location} {opp.description_snippet}".lower()

        # Field classification
        field = "General / Professional"
        if any(w in text for w in ["finance", "bank", "accounting", "fintech", "investment", "audit"]):
            field = "Finance, Banking & Consulting"
        elif any(w in text for w in ["health", "medicine", "biomedical", "who.int", "nursing", "pharmacy"]):
            field = "Healthcare, Medicine & Public Health"
        elif any(w in text for w in ["software", "ai", "engineer", "data", "robotics", "cloud", "developer", "iot"]):
            field = "Technology & Software Engineering"
        elif any(w in text for w in ["law", "policy", "human rights", "international relations", "diplomatic", "un.org"]):
            field = "Law, Public Policy & International Affairs"
        elif any(w in text for w in ["marketing", "media", "writing", "content", "communications", "social media"]):
            field = "Media, Communications & Marketing"

        # Work Mode
        work_mode = "Remote" if "remote" in text or "worldwide" in text else "Onsite"
        if "hybrid" in text:
            work_mode = "Hybrid"

        # Location & Ghana detection
        is_ghana = "ghana" in text or "accra" in text or "kumasi" in text or opp.is_ghana
        location = "Accra, Ghana" if is_ghana else opp.location

        # Paid / Unpaid
        is_paid = True
        comp_details = "Paid Stipend"
        if any(w in text for w in ["unpaid", "for academic credit only", "volunteer"]):
            is_paid = False
            comp_details = "Unpaid"
        else:
            # Check for currency matching against raw text to preserve case
            raw_text = f"{opp.title} {opp.location} {opp.description_snippet}"
            stipend_match = re.search(r"(\$|€|£|ghs|chf|jpy)\s?[0-9,]+(?:\s*-\s*[0-9,]+)?(?:\s*(?:/hr|per\s+month|/month|stipend))?", raw_text, re.I)
            if stipend_match:
                comp_details = stipend_match.group(0)

        # Outside Ghana funding
        outside_funding = "N/A"
        if not is_ghana and work_mode != "Remote":
            flight = any(w in text for w in ["flight", "airfare", "travel ticket", "travel reimbursed"])
            housing = any(w in text for w in ["housing provided", "accommodation provided", "free housing"])
            if flight and housing:
                outside_funding = "Fully Funded"
            elif flight or housing or is_paid:
                outside_funding = "Partially Funded"
            else:
                outside_funding = "Self-Funded"

        return {
            "field": field,
            "work_mode": work_mode,
            "is_paid": is_paid,
            "compensation_details": comp_details,
            "location": location,
            "is_ghana": is_ghana,
            "outside_ghana_funding": outside_funding,
            "deadline": opp.deadline or "Rolling / Open",
            "summary": f"Verified opportunity in {field} with {comp_details}.",
        }

    def _apply_extraction(self, opp: JobOpportunity, data: Dict[str, Any]) -> None:
        """Map extracted attributes into domain model."""
        opp.field_category = data.get("field", opp.field_category)
        
        mode_str = data.get("work_mode", "Remote").lower()
        is_ghana = data.get("is_ghana", False)
        opp.is_ghana = is_ghana

        if mode_str == "remote":
            opp.work_mode = WorkMode.REMOTE_WORLDWIDE
        elif is_ghana:
            opp.work_mode = WorkMode.HYBRID_GHANA if "hybrid" in mode_str else WorkMode.ONSITE_GHANA
        else:
            opp.work_mode = WorkMode.HYBRID_ABROAD if "hybrid" in mode_str else WorkMode.ONSITE_ABROAD

        opp.is_paid = data.get("is_paid", True)
        opp.compensation_details = data.get("compensation_details", "Paid Stipend")
        opp.outside_ghana_funding = data.get("outside_ghana_funding", "N/A")

        # Map funding tier
        if opp.outside_ghana_funding == "Fully Funded":
            opp.funding_tier = FundingTier.TIER_1_FULLY_FUNDED
            opp.funding_benefits.flight_covered = True
            opp.funding_benefits.housing_covered = True
            opp.funding_benefits.stipend_provided = True
        elif opp.work_mode == WorkMode.REMOTE_WORLDWIDE and opp.is_paid:
            opp.funding_tier = FundingTier.TIER_2_GLOBAL_REMOTE_PAID
        elif is_ghana or opp.outside_ghana_funding == "Partially Funded":
            opp.funding_tier = FundingTier.TIER_3_LOCAL_OR_PARTIAL
        else:
            opp.funding_tier = FundingTier.UNPAID_OR_SELF_FUNDED

        if data.get("deadline") and data["deadline"] != "Rolling / Open":
            opp.deadline = data["deadline"]
