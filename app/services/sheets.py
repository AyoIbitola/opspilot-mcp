import gspread
from oauth2client.service_account import ServiceAccountCredentials
from app.core.config import settings
from app.models.lead import Lead
import logging
import json
from typing import Set, Tuple, List
import os

logger = logging.getLogger(__name__)

class SheetsService:
    def __init__(self):
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.client = None
        self.sheet = None
        self.existing_urls: Set[str] = set()
        self.existing_authors: Set[Tuple[str, str]] = set() # (platform, handle)

        self._connect()

    def _connect(self):
        try:
            # Handle JSON string vs file path for GOOGLE_SERVICE_ACCOUNT_JSON
            creds_data = settings.GOOGLE_SERVICE_ACCOUNT_JSON
            
            # If it's a file path
            if os.path.exists(creds_data):
                creds = ServiceAccountCredentials.from_json_keyfile_name(creds_data, self.scope)
            else:
                # Assume it's a raw JSON string
                creds_dict = json.loads(creds_data)
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, self.scope)
            
            self.client = gspread.authorize(creds)
            try:
                self.sheet = self.client.open(settings.SPREADSHEET_NAME).sheet1
            except gspread.SpreadsheetNotFound:
                # Create it if it doesn't exist? PRD says "Sheet Name: OpsPilot Leads".
                # Usually we expect it to exist, or we create it.
                logger.info(f"Spreadsheet '{settings.SPREADSHEET_NAME}' not found, attempting to create.")
                sh = self.client.create(settings.SPREADSHEET_NAME)
                sh.share(creds.service_account_email, perm_type='user', role='owner') # Technically the service account owns it
                self.sheet = sh.sheet1
                # Initialize headers if new
                self.sheet.append_row([
                    "lead_id", "timestamp_utc", "platform", "author_handle", 
                    "author_profile_url", "post_url", "post_excerpt", 
                    "pain_summary", "pain_category", "urgency_score", 
                    "suggested_outreach_message", "lead_status", "notes", "last_updated_utc"
                ])
                
            self._load_deduplication_cache()
            
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")

    def _load_deduplication_cache(self):
        """Pre-fetch existing keys to avoid duplicates."""
        if not self.sheet:
            return
        
        try:
            records = self.sheet.get_all_records()
            for row in records:
                # Depending on how gspread returns data (int/str), ensure string matching
                p_url = str(row.get('post_url', ''))
                platform = str(row.get('platform', ''))
                handle = str(row.get('author_handle', ''))
                
                if p_url:
                    self.existing_urls.add(p_url)
                if platform and handle:
                    self.existing_authors.add((platform, handle))
            
            logger.info(f"Loaded deduplication cache: {len(self.existing_urls)} URLs, {len(self.existing_authors)} Authors.")
        except Exception as e:
            logger.error(f"Error loading cache: {e}")

    def is_duplicate(self, lead: Lead) -> bool:
        if lead.post_url in self.existing_urls:
            return True
        if (lead.platform, lead.author_handle) in self.existing_authors:
            return True
        return False

    def append_lead(self, lead: Lead) -> bool:
        if not self.sheet:
            return False
            
        if self.is_duplicate(lead):
            logger.info(f"Skipping duplicate: {lead.platform} - {lead.author_handle}")
            return False

        try:
            row = [
                lead.lead_id,
                lead.timestamp_utc,
                lead.platform,
                lead.author_handle,
                lead.author_profile_url,
                lead.post_url,
                lead.post_excerpt,
                lead.pain_summary,
                lead.pain_category,
                lead.urgency_score,
                lead.suggested_outreach_message,
                lead.lead_status,
                lead.notes,
                lead.last_updated_utc
            ]
            self.sheet.append_row(row)
            
            # Update cache
            self.existing_urls.add(lead.post_url)
            self.existing_authors.add((lead.platform, lead.author_handle))
            return True
        except Exception as e:
            error_str = str(e)
            if "storageQuotaExceeded" in error_str:
                logger.error("CRITICAL: Google Drive storage quota exceeded. Cannot save lead. Please free up space in the connected Google Drive account.")
            else:
                logger.error(f"Error writing to Sheet: {e}")
            return False
