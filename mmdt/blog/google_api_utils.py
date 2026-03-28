"""
Google Drive and Sheets API utilities for subscriber automation.
Uses OAuth 2.0 flow with token caching.
"""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import gspread
from django.conf import settings


PARENT_FOLDER_ID = getattr(settings, "GOOGLE_PARENT_FOLDER_ID", "")
SPREADSHEET_ID = getattr(settings, "GOOGLE_SPREADSHEET_ID", "")
MMDT_ADMIN_EMAIL = getattr(
    settings,
    "GOOGLE_ADMIN_EMAIL",
    getattr(settings, "EMAIL_HOST_USER", ""),
)

# OAuth credentials files
OAUTH_CLIENT_SECRET_FILE = getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET_FILE", "")
TOKEN_FILE = getattr(settings, "GOOGLE_TOKEN_FILE", "")

# Scopes for Google APIs
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
]


def get_credentials():
    """
    Get Google API credentials using OAuth 2.0 flow.

    First time: Opens browser for authorization and saves tokens.
    Subsequent times: Reuses saved tokens and refreshes if expired.

    Returns:
        google.oauth2.credentials.Credentials

    Raises:
        FileNotFoundError: If OAuth client secret file doesn't exist
    """
    creds = None

    # Load saved tokens if they exist
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Warning: Failed to load saved tokens: {e}")
            creds = None

    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired tokens
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Warning: Failed to refresh token: {e}")
                creds = None

        if not creds:
            # Run OAuth flow (opens browser for first-time authorization)
            if not os.path.exists(OAUTH_CLIENT_SECRET_FILE):
                raise FileNotFoundError(
                    f"OAuth client secret file not found at {OAUTH_CLIENT_SECRET_FILE}"
                )

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    OAUTH_CLIENT_SECRET_FILE,
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"Error during OAuth flow: {e}")
                raise

        # Save tokens for next time
        try:
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            print(f"Warning: Failed to save tokens: {e}")

    return creds


def create_subscriber_folder(subscriber_request):
    """
    Create Google Drive folder for subscriber and set permissions.

    Args:
        subscriber_request: SubscriberRequest instance

    Returns:
        str: URL of the created folder, or None if creation fails
    """
    try:
        credentials = get_credentials()
        drive_service = build('drive', 'v3', credentials=credentials)

        # Create cohort folder if it doesn't exist
        cohort_folder_id = get_or_create_cohort_folder(
            drive_service,
            subscriber_request.cohort.cohort_id if hasattr(subscriber_request, 'cohort') and subscriber_request.cohort else 'NO_COHORT'
        )

        # Create user folder: fullname|email
        folder_name = f"{subscriber_request.name}|{subscriber_request.email}"

        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [cohort_folder_id]
        }

        folder = drive_service.files().create(
            body=folder_metadata,
            fields='id, webViewLink'
        ).execute()

        folder_id = folder.get('id')
        folder_url = folder.get('webViewLink')

        # Set permissions: Edit access for user and MMDT admin
        permissions = [
            {
                'type': 'user',
                'role': 'writer',
                'emailAddress': subscriber_request.email
            },
            {
                'type': 'user',
                'role': 'writer',
                'emailAddress': MMDT_ADMIN_EMAIL
            }
        ]

        for permission in permissions:
            drive_service.permissions().create(
                fileId=folder_id,
                body=permission,
                sendNotificationEmail=False
            ).execute()

        return folder_url

    except FileNotFoundError as e:
        print(f"Service account file not found: {e}")
        return None
    except Exception as e:
        print(f"Error creating Google Drive folder: {e}")
        return None


def get_or_create_cohort_folder(drive_service, cohort_id):
    """
    Get or create cohort folder under parent folder.

    Args:
        drive_service: Google Drive API service instance
        cohort_id: Cohort ID string

    Returns:
        str: Folder ID of cohort folder
    """
    # Search for existing cohort folder
    query = (
        f"name='{cohort_id}' and "
        f"'{PARENT_FOLDER_ID}' in parents and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"trashed=false"
    )

    results = drive_service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()

    files = results.get('files', [])

    if files:
        return files[0]['id']

    # Create new cohort folder
    folder_metadata = {
        'name': cohort_id,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [PARENT_FOLDER_ID]
    }

    folder = drive_service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()

    return folder.get('id')


def log_to_spreadsheet(subscriber_request, folder_url):
    """
    Log subscriber request data to Google Sheet.

    Args:
        subscriber_request: SubscriberRequest instance
        folder_url: URL of the created Google Drive folder

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        credentials = get_credentials()
        gc = gspread.authorize(credentials)

        # Open the spreadsheet
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet('raw_registration')

        # Prepare row data based on sheet columns:
        # name, email, tele_name, country, plan, status, created_at, payment_url
        plan_display = subscriber_request.get_plan_display()

        row_data = [
            subscriber_request.name,
            subscriber_request.email,
            subscriber_request.telegram_username or '',
            subscriber_request.country,
            plan_display,
            subscriber_request.get_status_display(),
            subscriber_request.created_at.strftime('%b. %-d, %Y, %-I:%M %p'),
            folder_url or ''
        ]

        # Append row to sheet
        worksheet.append_row(row_data)

        return True

    except FileNotFoundError as e:
        print(f"Service account file not found: {e}")
        return False
    except Exception as e:
        print(f"Error logging to Google Sheet: {e}")
        return False


def _find_row_number_by_email_column_b(worksheet, email):
    """Return 1-based row number where column B matches email (case-insensitive), or None."""
    try:
        rows = worksheet.get_all_values()
    except Exception as e:
        print(f"Error reading sheet rows: {e}")
        return None
    target = (email or '').strip().lower()
    for i, row in enumerate(rows, start=1):
        if len(row) >= 2 and row[1].strip().lower() == target:
            return i
    return None


def upsert_log_to_spreadsheet(subscriber_request, folder_url):
    """
    Insert or update a row in raw_registration for this subscriber.
    If column B already has this email, update that row; otherwise append.

    Args:
        subscriber_request: SubscriberRequest instance
        folder_url: Google Drive folder URL (may be empty string)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        credentials = get_credentials()
        gc = gspread.authorize(credentials)

        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet('raw_registration')

        plan_display = subscriber_request.get_plan_display()
        row_data = [
            subscriber_request.name,
            subscriber_request.email,
            subscriber_request.telegram_username or '',
            subscriber_request.country,
            plan_display,
            subscriber_request.get_status_display(),
            subscriber_request.created_at.strftime('%b. %-d, %Y, %-I:%M %p'),
            folder_url or '',
        ]

        row_num = _find_row_number_by_email_column_b(worksheet, subscriber_request.email)
        if row_num:
            worksheet.update(
                f'A{row_num}:H{row_num}',
                [row_data],
                value_input_option='USER_ENTERED',
            )
        else:
            worksheet.append_row(row_data)

        return True

    except FileNotFoundError as e:
        print(f"Service account file not found: {e}")
        return False
    except Exception as e:
        print(f"Error upserting to Google Sheet: {e}")
        return False


def get_or_create_subscriber_folder_url(subscriber_request):
    """
    For new subscriber requests:
    1. If raw_registration already has this email with a folder URL (column H), reuse it
       (``find_url_in_spreadsheet``).
    2. Otherwise get or create the folder under the cohort (``get_folder_upload_url``:
       searches Drive by ``fullname|email``, then creates if missing).
    3. Upsert the spreadsheet row (update existing row or append).

    Args:
        subscriber_request: SubscriberRequest instance

    Returns:
        str: Folder URL, or None if folder creation failed and no existing URL in sheet.
    """
    try:
        existing_url = find_url_in_spreadsheet(
            subscriber_request.email, update_status=False
        )
        if existing_url:
            upsert_log_to_spreadsheet(subscriber_request, existing_url)
            return existing_url

        # Same as renewal path: prefer an existing Drive folder (name|email) before creating
        folder_url = get_folder_upload_url(subscriber_request)
        upsert_log_to_spreadsheet(subscriber_request, folder_url or '')
        return folder_url

    except Exception as e:
        print(f"Error in get_or_create_subscriber_folder_url: {e}")
        return None


def get_folder_upload_url(subscriber_request):
    """
    Get the upload URL for an existing subscriber's folder.
    If the folder doesn't exist, creates it.

    Args:
        subscriber_request: SubscriberRequest instance

    Returns:
        str: URL of the folder for uploading, or None if operation fails
    """
    try:
        credentials = get_credentials()
        drive_service = build('drive', 'v3', credentials=credentials)

        # Create cohort folder if it doesn't exist
        cohort_folder_id = get_or_create_cohort_folder(
            drive_service,
            subscriber_request.cohort.cohort_id if hasattr(subscriber_request, 'cohort') and subscriber_request.cohort else 'NO_COHORT'
        )

        # Search for existing user folder: fullname|email
        folder_name = f"{subscriber_request.name}|{subscriber_request.email}"

        query = (
            f"name='{folder_name}' and "
            f"'{cohort_folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"trashed=false"
        )

        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, webViewLink)'
        ).execute()

        files = results.get('files', [])

        if files:
            # Folder exists, return its URL
            return files[0].get('webViewLink')
        else:
            # Folder doesn't exist, create it
            return create_subscriber_folder(subscriber_request)

    except FileNotFoundError as e:
        print(f"Service account file not found: {e}")
        return None
    except Exception as e:
        print(f"Error getting folder upload URL: {e}")
        return None


def find_url_in_spreadsheet(email, update_status=False, plan=None):
    """
    Search for an existing entry in the Google Sheet by email.

    Args:
        email: User's email address to search for
        update_status: If True, update the status and plan columns
        plan: Renewal plan to update (e.g., '6month', '12month')

    Returns:
        str: Folder URL if found, None otherwise
    """
    try:
        credentials = get_credentials()
        gc = gspread.authorize(credentials)

        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet('raw_registration')

        # Find cell with matching email (column B = email)
        cell = worksheet.find(email)
        if cell:
            # Get the folder URL from the same row (column H = payment_url)
            row_values = worksheet.row_values(cell.row)
            if len(row_values) >= 8 and row_values[7]:
                if update_status:
                    # Update plan column (column E = index 5) and status column (column F = index 6)
                    if plan:
                        worksheet.update_cell(cell.row, 5, plan)
                    worksheet.update_cell(cell.row, 6, 'Renewal Requested')
                return row_values[7]

        return None

    except gspread.exceptions.CellNotFound:
        return None
    except Exception as e:
        print(f"Error searching spreadsheet: {e}")
        return None


def log_renewal_to_spreadsheet(subscriber_request, folder_url, plan):
    """
    Log renewal request data to Google Sheet.

    Args:
        subscriber_request: SubscriberRequest instance
        folder_url: URL of the Google Drive folder
        plan: Renewal plan selected

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        credentials = get_credentials()
        gc = gspread.authorize(credentials)

        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet('raw_registration')

        from django.utils import timezone

        # Prepare row data:
        # name, email, tele_name, country, plan, status, created_at, payment_url
        row_data = [
            subscriber_request.name,
            subscriber_request.email,
            subscriber_request.telegram_username or '',
            subscriber_request.country,
            plan,
            'Renewal Requested',
            timezone.now().strftime('%b. %-d, %Y, %-I:%M %p'),
            folder_url or ''
        ]

        worksheet.append_row(row_data)

        return True

    except Exception as e:
        print(f"Error logging renewal to Google Sheet: {e}")
        return False


def get_or_create_renewal_url(subscriber_request, plan):
    """
    Get existing URL from spreadsheet or create new folder and log to sheet.

    For renewal requests:
    1. First checks if user already has an entry in the spreadsheet
    2. If found, updates status to 'Renewal Requested' and returns the existing folder URL
    3. If not found, creates folder, logs to spreadsheet, and returns URL

    Args:
        subscriber_request: SubscriberRequest instance
        plan: Renewal plan selected

    Returns:
        tuple: (folder_url, is_existing) where is_existing indicates if URL was from sheet
               Returns (None, False) if operation fails
    """
    try:
        # First, check if URL exists in spreadsheet and update status/plan if found
        existing_url = find_url_in_spreadsheet(subscriber_request.email, update_status=True, plan=plan)
        if existing_url:
            return (existing_url, True)

        # No existing entry, create folder and log to sheet
        folder_url = get_folder_upload_url(subscriber_request)
        if folder_url:
            log_renewal_to_spreadsheet(subscriber_request, folder_url, plan)
            return (folder_url, False)

        return (None, False)

    except Exception as e:
        print(f"Error in get_or_create_renewal_url: {e}")
        return (None, False)
