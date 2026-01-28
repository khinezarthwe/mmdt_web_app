import os

import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from gspread.exceptions import WorksheetNotFound


class GoogleService:
    """
    Google Sheets service using OAuth 2.0 client credentials.
    
    Uses OAuth 2.0 flow with token caching for authentication.
    On first run, opens browser for authorization. Subsequent runs reuse saved tokens.
    """
    
    # Google Sheet ID and OAuth client configuration
    SPREADSHEET_ID = '<sheedIDhere>'
    CLIENT_ID = 'clientIDhere'
    
    def __init__(self, logger=None, credentials_file=None, token_file=None):
        """
        Initialize Google Service with OAuth 2.0 credentials.
        """
        self.logger = logger
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        # Determine file paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # OAuth client credentials file
        if credentials_file:
            self.credentials_file = credentials_file
        else:
            self.credentials_file = os.environ.get('OAUTH_CREDENTIALS_FILE')
            if not self.credentials_file:
                self.credentials_file = os.path.join(base_dir, 'service_credentials.json')
                if not os.path.exists(self.credentials_file):
                    self.credentials_file = "service_credentials.json"
        
        # Token file (for caching OAuth tokens)
        if token_file:
            self.token_file = token_file
        else:
            self.token_file = os.environ.get('OAUTH_TOKEN_FILE')
            if not self.token_file:
                self.token_file = os.path.join(base_dir, 'google_token.json')
                if not os.path.exists(self.token_file):
                    self.token_file = "google_token.json"
        
        self.cred = self._get_credentials()
        self.gc = None  # gspread client, initialized on first use
    
    def _get_credentials(self):
        """
        Get Google API credentials using OAuth 2.0 flow.
        
        First time: Opens browser for authorization and saves tokens.
        Subsequent times: Reuses saved tokens and refreshes if expired.
        
        Returns:
            google.oauth2.credentials.Credentials: OAuth credentials
        
        Raises:
            FileNotFoundError: If credentials file is not found
            Exception: If OAuth flow fails (e.g., org_internal error)
        """
        creds = None
        
        # Load saved tokens if they exist
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
                if self.logger:
                    self.logger.info("Loaded saved OAuth tokens")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to load saved tokens: {e}")
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh expired tokens
                try:
                    creds.refresh(Request())
                    if self.logger:
                        self.logger.info("Refreshed expired OAuth tokens")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Failed to refresh token: {e}")
                    creds = None
            
            if not creds:
                # Run OAuth flow (opens browser for first-time authorization)
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"OAuth credentials file not found at: {self.credentials_file}\n"
                        f"Please ensure service_credentials.json exists with your OAuth client ID and secret.\n"
                        f"Client ID: {self.CLIENT_ID}"
                    )
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file,
                        self.scopes
                    )
                    if self.logger:
                        self.logger.info("Starting OAuth flow - browser will open for authorization")
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(str(e).lower())
                
            
            # Save tokens for next time
            try:
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                if self.logger:
                    self.logger.info(f"Saved OAuth tokens to {self.token_file}")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to save tokens: {e}")
        
        return creds
    
    def _get_gspread_client(self):
        """
        Get or create gspread client.
        
        Returns:
            gspread.Client: Authorized gspread client
        """
        if self.gc is None:
            self.gc = gspread.authorize(self.cred)
        return self.gc
    
    def get_spreadsheet(self):
        """
        Get the configured Google Spreadsheet.
        
        Returns:
            gspread.Spreadsheet: The spreadsheet object
        """
        gc = self._get_gspread_client()
        return gc.open_by_key(self.SPREADSHEET_ID)
    
    def read_sheet(self, worksheet_index=0, worksheet_name=None):
        """
        Read data from a worksheet in the Google Sheet.
        
        Args:
            worksheet_index: Index of the worksheet (0-based). Default: 0 (first sheet)
            worksheet_name: Name of the worksheet. If provided, overrides worksheet_index
        
        Returns:
            list: List of rows, where each row is a list of cell values
        
        Raises:
            WorksheetNotFound: If the specified worksheet doesn't exist
        """
        try:
            spreadsheet = self.get_spreadsheet()
            
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.get_worksheet(worksheet_index)
            
            # Get all values from the worksheet
            data = worksheet.get_all_values()
            
            if self.logger:
                self.logger.info(f"Read {len(data)} rows from worksheet '{worksheet.title}'")
            
            return data
        
        except WorksheetNotFound as e:
            if self.logger:
                self.logger.error(f"Worksheet not found: {e}")
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error reading sheet: {e}")
            raise
    



if __name__ == "__main__":
    # Initialize the service
    service = GoogleService()
    
    # Read all data from the first worksheet
    data = service.read_sheet()
    print(f"Read {len(data)} rows")
    