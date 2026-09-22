"""Storage and persistence package."""
from .deduplicator import Deduplicator
from .sheets_adapter import GoogleSheetsAdapter

__all__ = ["Deduplicator", "GoogleSheetsAdapter"]
