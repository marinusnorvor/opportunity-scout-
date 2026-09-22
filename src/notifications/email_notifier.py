"""Email Notification Dispatcher with Rich Responsive HTML Digest."""

import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional
from src.models import JobOpportunity

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Formats and dispatches the daily Top 3 opportunities email digest."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        recipient_email: Optional[str] = None,
    ):
        self.smtp_host = (smtp_host or os.getenv("SMTP_HOST") or "smtp.gmail.com").strip()
        
        raw_port = smtp_port or os.getenv("SMTP_PORT")
        if raw_port and str(raw_port).strip():
            try:
                self.smtp_port = int(str(raw_port).strip())
            except ValueError:
                self.smtp_port = 587
        else:
            self.smtp_port = 587

        self.smtp_user = (smtp_user or os.getenv("SMTP_USER") or "").strip() or None
        self.smtp_password = (smtp_password or os.getenv("SMTP_PASSWORD") or "").strip() or None
        self.recipient_email = (recipient_email or os.getenv("RECIPIENT_EMAIL") or "").strip() or None

    def send_top_opportunities_digest(
        self,
        top_opportunities: List[JobOpportunity],
        total_scanned: int = 0,
        total_eligible: int = 0,
        dry_run: bool = False,
    ) -> bool:
        """Construct and transmit the email digest.
        
        Args:
            top_opportunities: The Top N curated jobs.
            total_scanned: Total jobs scanned in this run.
            total_eligible: Total eligible jobs verified.
            dry_run: If True, writes preview to HTML file instead of sending SMTP.
            
        Returns:
            True if delivered/previewed successfully, False otherwise.
        """
        if not top_opportunities:
            logger.info("[EmailNotifier] No opportunities to send.")
            return False

        today_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        subject = f"🎯 [Top 3 Internships] Daily Digest - {today_str}"

        html_body = self._build_html_content(top_opportunities, today_str, total_scanned, total_eligible)
        text_body = self._build_text_content(top_opportunities, today_str)

        # In dry run mode or if credentials not provided, save HTML artifact
        preview_path = Path(__file__).resolve().parent.parent.parent / "output" / "latest_email.html"
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(html_body)
        logger.info(f"[EmailNotifier] Saved HTML email preview to {preview_path}")

        if dry_run or not self.smtp_user or not self.smtp_password or not self.recipient_email:
            logger.info("[EmailNotifier] Operating in Dry-Run / Preview mode. Email not transmitted via SMTP.")
            return True

        # Send via SMTP
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Opportunity Scout <{self.smtp_user}>"
            msg["To"] = self.recipient_email

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"[EmailNotifier] Successfully sent daily digest to {self.recipient_email}")
            return True
        except Exception as exc:
            logger.error(f"[EmailNotifier] Failed to send email: {exc}")
            return False

    def _build_html_content(
        self, jobs: List[JobOpportunity], date_str: str, total_scanned: int, total_eligible: int
    ) -> str:
        """Render high-polish, mobile-friendly HTML email template."""
        cards_html = ""

        for idx, job in enumerate(jobs, start=1):
            benefits = job.funding_benefits
            
            # Flight badge
            flight_badge = (
                '<span style="background: #e6f4ea; color: #137333; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 6px;">✈️ Flight Covered</span>'
                if benefits.flight_covered else ""
            )
            # Housing badge
            housing_badge = (
                '<span style="background: #e8f0fe; color: #1a73e8; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 6px;">🏠 Housing Provided</span>'
                if benefits.housing_covered else ""
            )
            # Stipend badge
            stipend_text = f"💵 Stipend ({benefits.stipend_details})" if benefits.stipend_details else "💵 Stipend Provided"
            stipend_badge = (
                f'<span style="background: #fef7e0; color: #b06000; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 6px;">{stipend_text}</span>'
                if benefits.stipend_provided else ""
            )
            # Visa badge
            visa_badge = (
                '<span style="background: #f3e8fd; color: #7627bb; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 6px;">🛂 Visa Support</span>'
                if benefits.visa_sponsorship else ""
            )

            all_badges = "".join([flight_badge, housing_badge, stipend_badge, visa_badge]) or "<span>Standard Paid Compensation</span>"

            dossier = job.company_dossier
            cards_html += f"""
            <div style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span style="background: #eef2ff; color: #3730a3; font-weight: 600; font-size: 12px; padding: 3px 8px; border-radius: 12px; text-transform: uppercase;">
                            #{idx} • {job.field_category or 'General Field'}
                        </span>
                        <h2 style="margin: 8px 0 4px 0; font-size: 18px; color: #111827; font-weight: 700;">
                            {job.title}
                        </h2>
                        <div style="font-size: 14px; color: #4b5563; margin-bottom: 10px;">
                            <strong>{job.company}</strong> &nbsp;•&nbsp; 📍 {job.location} &nbsp;•&nbsp; 🏆 Match Score: <strong>{job.ranking_score:.1f}/100</strong>
                        </div>
                    </div>
                </div>

                <div style="margin: 10px 0;">
                    {all_badges}
                </div>

                <!-- Company Intelligence Dossier -->
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 12px; font-size: 13px; color: #166534; margin-bottom: 12px;">
                    <div style="font-weight: 700; margin-bottom: 3px;">🏢 About {job.company} ({dossier.org_type}):</div>
                    <div>{dossier.overview}</div>
                    <div style="margin-top: 4px; font-size: 12px; color: #15803d;">
                        📍 <strong>HQ / Base:</strong> {dossier.headquarters} &nbsp;|&nbsp; 🛡️ {dossier.credibility_indicators}
                    </div>
                </div>

                <!-- Role Details & Proof -->
                <div style="background: #f9fafb; padding: 12px; border-radius: 6px; font-size: 13px; color: #374151; margin-bottom: 14px; border-left: 3px solid #4f46e5;">
                    <div style="font-weight: 600; margin-bottom: 4px; color: #1e1b4b;">Opportunity Overview:</div>
                    <div>{job.description_snippet[:240]}...</div>
                    <div style="margin-top: 6px; font-size: 12px; color: #6b7280;">
                        ⏳ <strong>Deadline:</strong> {job.deadline or 'Rolling Admissions'} &nbsp;|&nbsp; 
                        🔍 <strong>Application Proof:</strong> {job.application_proof}
                    </div>
                </div>

                <div>
                    <a href="{job.url}" style="display: inline-block; background: #4f46e5; color: #ffffff; text-decoration: none; padding: 10px 18px; border-radius: 6px; font-size: 13px; font-weight: 600;">
                        Apply Directly &rarr;
                    </a>
                </div>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Top Opportunities Digest</title>
        </head>
        <body style="margin: 0; padding: 20px; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            <div style="max-width: 680px; margin: 0 auto;">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); color: #ffffff; padding: 28px 24px; border-radius: 8px 8px 0 0; text-align: left;">
                    <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #a5b4fc; font-weight: 600;">Autonomous Opportunity Scout</span>
                    <h1 style="margin: 6px 0 10px 0; font-size: 22px; font-weight: 800;">Top 3 Curated Opportunities</h1>
                    <div style="font-size: 13px; color: #c7d2fe;">
                        📅 {date_str} &nbsp;|&nbsp; 👤 Candidate: Ghana Undergrad Profile
                    </div>
                </div>

                <!-- Stats banner -->
                <div style="background: #ffffff; padding: 14px 24px; border-bottom: 1px solid #e5e7eb; font-size: 13px; color: #4b5563;">
                    🔍 <strong>Scanned:</strong> {total_scanned} opportunities &nbsp;|&nbsp; 
                    ✅ <strong>Verified & Eligible:</strong> {total_eligible} roles &nbsp;|&nbsp; 
                    🎯 <strong>Showing:</strong> Top {len(jobs)} High-Value Matches
                </div>

                <!-- Cards list -->
                <div style="padding: 20px 0;">
                    {cards_html}
                </div>

                <!-- Footer -->
                <div style="text-align: center; padding: 16px; font-size: 12px; color: #9ca3af;">
                    Automated by Autonomous Opportunity Finder & Verification Engine<br>
                    Running seamlessly on GitHub Actions with zero server overhead.
                </div>

            </div>
        </body>
        </html>
        """

    def _build_text_content(self, jobs: List[JobOpportunity], date_str: str) -> str:
        """Render fallback plain-text version of digest."""
        lines = [
            f"=== TOP 3 CURATED OPPORTUNITIES ({date_str}) ===",
            "Target: Ghana Undergraduate (Fully Funded / Global Remote)",
            "",
        ]

        for idx, job in enumerate(jobs, start=1):
            lines.append(f"#{idx}: {job.title} at {job.company}")
            lines.append(f"Track: {job.track_name}")
            lines.append(f"Location: {job.location}")
            lines.append(f"Funding: {job.funding_tier.value}")
            lines.append(f"Score: {job.ranking_score:.1f}/100")
            lines.append(f"Deadline: {job.deadline or 'Rolling'}")
            lines.append(f"Apply Link: {job.url}")
            lines.append("-" * 40)

        return "\n".join(lines)
