"""Verification Engine for Fraud, Scam, and Ghost-Job Detection.

Enforces multi-stage integrity checks on domains, payment requests,
recruitment contact authenticity, and predatory internship schemes.
"""

import logging
import re
import urllib.parse
from typing import List, Tuple
from src.models import JobOpportunity, VerificationReport

logger = logging.getLogger(__name__)


class ScamVerifier:
    """Evaluates job listings to differentiate legitimate opportunities from scams."""

    # Domains with verified corporate ATS infrastructure
    TRUSTED_ATS_DOMAINS = [
        "greenhouse.io",
        "boards.greenhouse.io",
        "lever.co",
        "jobs.lever.co",
        "ashbyhq.com",
        "myworkdayjobs.com",
        "smartrecruiters.com",
        "jobvite.com",
        "workable.com",
        "bamboohr.com",
        "rippling-ats.com",
        "linkedin.com",
        "remotive.com",
        "outreachy.org",
        "summerofcode.withgoogle.com",
    ]

    # Accredited academic, research, and governmental domains
    TRUSTED_INSTITUTIONAL_SUFFIXES = [
        ".edu",
        ".gov",
        ".ac.uk",
        ".ac.jp",
        ".edu.gh",
        "cern",
        "epfl.ch",
        "ethz.ch",
        "oist.jp",
        "kaust.edu.sa",
        "mpg.de",
    ]

    # Suspicious domain patterns often used in recruitment scams
    SUSPICIOUS_DOMAINS = [
        "forms.gle",
        "docs.google.com/forms",
        "t.me",
        "telegram.me",
        "wa.me",
        "api.whatsapp.com",
        "bit.ly",
        "tinyurl.com",
        "cutt.ly",
    ]

    # Explicit financial extortion or pay-to-work phrases
    FINANCIAL_RED_FLAGS = [
        r"\b(?:application|processing|registration|administration)\s+fee\b",
        r"\b(?:training|onboarding|course)\s+fee\b",
        r"\b(?:security|refundable)\s+deposit\b",
        r"\bpay\s+(?:us|for)\s+(?:your\s+)?training\b",
        r"\bpurchase\s+(?:your\s+own\s+)?(?:equipment|software)\s+from\s+our\s+vendor\b",
        r"\bwire\s+transfer\b",
        r"\bcrypto(?:currency)?\s+payment\b",
        r"\bbank\s+account\s+verification\s+fee\b",
        r"\bearn\s+\$?[0-9,]+\s*(?:a|per)\s*(?:day|hour)\s+typing\b",
        r"\bno\s+experience\s+needed\s+earn\s+\$[0-9,]+\b",
    ]

    # Free webmail providers that should NOT be used by enterprise recruiters
    CONSUMER_WEBMAIL_PROVIDERS = [
        "@gmail.com",
        "@yahoo.com",
        "@hotmail.com",
        "@outlook.com",
        "@aol.com",
        "@proton.me",
        "@protonmail.com",
    ]

    def verify(self, opportunity: JobOpportunity) -> VerificationReport:
        """Run full battery of scam and legitimacy checks on a job opportunity.
        
        Args:
            opportunity: The job opportunity model to evaluate.
            
        Returns:
            VerificationReport containing pass/fail verdict, score, flags, and reasons.
        """
        flags: List[str] = []
        trust_score = 1.0
        parsed_url = urllib.parse.urlparse(opportunity.url)
        domain = parsed_url.netloc.lower()

        # 1. Domain Check
        domain_trust, domain_reason = self._check_domain_reputation(opportunity.url, domain)
        if not domain_trust:
            flags.append(f"Untrusted Domain: {domain_reason}")
            trust_score -= 0.6
        elif "Trusted ATS" in domain_reason or "Institutional" in domain_reason:
            trust_score += 0.1  # Bonus confidence for verified infrastructure

        # 2. Financial Red Flags Scan
        text_to_scan = f"{opportunity.title} {opportunity.description_snippet}".lower()
        found_red_flags = self._scan_financial_red_flags(text_to_scan)
        if found_red_flags:
            for rf in found_red_flags:
                flags.append(f"Financial Red Flag: Contains scam phrase matching '{rf}'")
            trust_score -= 0.8

        # 3. Consumer Webmail Recruiter Check
        webmail_flag = self._check_consumer_webmail(opportunity.company, text_to_scan)
        if webmail_flag:
            flags.append(webmail_flag)
            trust_score -= 0.4

        # 4. Final Verdict
        trust_score = max(0.0, min(1.0, trust_score))
        is_legitimate = trust_score >= 0.5 and len(found_red_flags) == 0

        reason = (
            "Verified legitimate: Passed domain trust and integrity scans."
            if is_legitimate
            else f"Flagged as high-risk / potential scam: {'; '.join(flags)}"
        )

        logger.debug(f"[ScamVerifier] '{opportunity.title}' at '{opportunity.company}' -> score={trust_score:.2f}, leg={is_legitimate}")

        return VerificationReport(
            is_legitimate=is_legitimate,
            trust_score=trust_score,
            domain=domain,
            flags=flags,
            reason=reason,
        )

    def _check_domain_reputation(self, url: str, domain: str) -> Tuple[bool, str]:
        """Verify if the host domain is trusted, neutral, or suspicious."""
        # Check suspicious list
        for susp in self.SUSPICIOUS_DOMAINS:
            if susp in url.lower():
                return False, f"Uses suspicious free application portal/shortener ({susp})"

        # Check known ATS
        for ats in self.TRUSTED_ATS_DOMAINS:
            if domain.endswith(ats) or ats in domain:
                return True, f"Trusted ATS Infrastructure ({ats})"

        # Check educational / research suffixes
        for inst in self.TRUSTED_INSTITUTIONAL_SUFFIXES:
            if domain.endswith(inst) or inst in domain:
                return True, f"Institutional Domain ({inst})"

        # If it's a regular corporate domain (e.g. stripe.com, google.com)
        if "." in domain and not domain.startswith("localhost"):
            return True, "Standard Corporate Domain"

        return False, "Unrecognized or invalid domain structure"

    def _scan_financial_red_flags(self, text: str) -> List[str]:
        """Search text for pay-to-work and extortion markers."""
        detected = []
        for pattern in self.FINANCIAL_RED_FLAGS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                detected.append(match.group(0))
        return detected

    def _check_consumer_webmail(self, company: str, text: str) -> str:
        """Flag enterprise claims using disposable or free consumer email addresses."""
        # If company has "Corp", "Inc", "Technologies", "Laboratories" but uses free gmail in posting
        for provider in self.CONSUMER_WEBMAIL_PROVIDERS:
            if provider in text:
                # Find the full email
                email_match = re.search(r"[\w\.-]+" + re.escape(provider), text)
                found_email = email_match.group(0) if email_match else provider
                return f"Unprofessional contact method: Recruiter uses free webmail ({found_email})"
        return ""
