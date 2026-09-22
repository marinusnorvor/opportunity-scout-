"""Google Sheets Persistence Adapter with graceful local CSV fallback."""

import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Optional
from src.models import JobOpportunity

logger = logging.getLogger(__name__)


class GoogleSheetsAdapter:
    """Manages appending verified opportunities into Google Sheets or local CSV."""

    HEADER_ROW = [
        "Discovered Date",
        "Track",
        "Role Title",
        "Company / Lab",
        "Funding Tier",
        "Benefits Breakdown",
        "Location",
        "Deadline",
        "Ranking Score",
        "Application URL",
        "Verification Status",
        "Source Channel",
    ]

    def __init__(
        self,
        sheet_id: Optional[str] = None,
        service_account_json: Optional[str] = None,
        service_account_path: Optional[str] = None,
        fallback_csv_path: Optional[Path] = None,
    ):
        self.sheet_id = sheet_id or os.getenv("GOOGLE_SHEET_ID")
        self.service_account_json = service_account_json or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        self.service_account_path = service_account_path or os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")
        
        self.fallback_csv_path = fallback_csv_path or (
            Path(__file__).resolve().parent.parent.parent / "output" / "opportunities.csv"
        )
        self.client = self._init_google_client()

    def _init_google_client(self):
        """Authenticate with Google Sheets API if credentials exist."""
        try:
            import gspread

            if self.service_account_json:
                cred_dict = json.loads(self.service_account_json)
                return gspread.service_account_from_dict(cred_dict)
            elif self.service_account_path and Path(self.service_account_path).exists():
                return gspread.service_account(filename=self.service_account_path)
            else:
                logger.info("[GoogleSheets] No Google service account configured. Operating in local CSV fallback mode.")
                return None
        except Exception as exc:
            logger.warning(f"[GoogleSheets] Failed to initialize Google Sheets client: {exc}. Using CSV fallback.")
            return None

    def append_opportunities(self, opportunities: List[JobOpportunity]) -> int:
        """Append list of opportunities to Google Sheet or CSV fallback.
        
        Returns:
            Number of rows appended.
        """
        if not opportunities:
            logger.info("[GoogleSheets] No new opportunities to append.")
            return 0

        rows = [opp.to_sheet_row() for opp in opportunities]

        # 1. Attempt Google Sheets append
        if self.client and self.sheet_id:
            try:
                sheet = self.client.open_by_key(self.sheet_id).sheet1
                # Initialize header if empty
                existing_values = sheet.row_values(1)
                if not existing_values:
                    sheet.append_row(self.HEADER_ROW)

                sheet.append_rows(rows)
                logger.info(f"[GoogleSheets] Successfully appended {len(rows)} rows to Google Sheet ({self.sheet_id}).")
                return len(rows)
            except Exception as exc:
                logger.error(f"[GoogleSheets] Error writing to Google Sheets: {exc}. Falling back to CSV.")

        # 2. Local CSV fallback
        return self._append_to_csv(rows)

    def _append_to_csv(self, rows: List[List[str]]) -> int:
        """Append rows to local CSV file."""
        self.fallback_csv_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = self.fallback_csv_path.exists()

        with open(self.fallback_csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists or self.fallback_csv_path.stat().st_size == 0:
                writer.writerow(self.HEADER_ROW)
            writer.writerows(rows)

        logger.info(f"[GoogleSheets] Logged {len(rows)} opportunities to local CSV: {self.fallback_csv_path}")
        return len(rows)
