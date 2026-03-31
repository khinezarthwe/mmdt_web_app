"""
Google Drive and Sheets API utilities for subscriber automation.
Uses OAuth 2.0 flow with token caching.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import gspread
from django.conf import settings

if TYPE_CHECKING:
    from users.models import UserProfile

logger = logging.getLogger(__name__)

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

NO_COHORT_FOLDER_NAME = "NO_COHORT"


def resolve_drive_cohort_id(
    subscriber_request,
    user_profile: Optional["UserProfile"] = None,
) -> str:
    """
    Cohort folder name under PARENT_FOLDER_ID (same string used for Drive folder name).

    Prefer ``SubscriberRequest.cohort`` (new signups). For renewals, the original
    request may have no cohort while ``UserProfile.current_cohort`` is set — use that.
    """
    cohort = getattr(subscriber_request, "cohort", None)
    if cohort is not None:
        cid = cohort.cohort_id
        logger.debug(
            "resolve_drive_cohort_id: SubscriberRequest.cohort_id=%s email=%s",
            cid,
            subscriber_request.email,
        )
        return cid

    if user_profile is not None:
        current = getattr(user_profile, "current_cohort", None)
        if current is not None:
            cid = current.cohort_id
            logger.info(
                "resolve_drive_cohort_id: UserProfile.current_cohort=%s "
                "(SubscriberRequest.cohort unset) email=%s",
                cid,
                subscriber_request.email,
            )
            return cid

    logger.warning(
        "resolve_drive_cohort_id: using %s (no cohort on SubscriberRequest or profile) email=%s",
        NO_COHORT_FOLDER_NAME,
        subscriber_request.email,
    )
    return NO_COHORT_FOLDER_NAME


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
            logger.warning("Failed to load saved tokens: %s", e)
            creds = None

    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired tokens
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning("Failed to refresh token: %s", e)
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
                logger.error("Error during OAuth flow: %s", e)
                raise

        # Save tokens for next time
        try:
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            logger.warning("Failed to save tokens: %s", e)

    return creds


def create_subscriber_folder(subscriber_request, user_profile: Optional["UserProfile"] = None):
    """
    Create Google Drive folder for subscriber and set permissions.

    Args:
        subscriber_request: SubscriberRequest instance
        user_profile: Optional UserProfile (pass for renewals when ``subscriber_request.cohort`` may be null)

    Returns:
        str: URL of the created folder, or None if creation fails
    """
    try:
        credentials = get_credentials()
        drive_service = build('drive', 'v3', credentials=credentials)

        cohort_id = resolve_drive_cohort_id(subscriber_request, user_profile)
        cohort_folder_id = get_or_create_cohort_folder(drive_service, cohort_id)

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

        logger.info(
            "Drive folder created for subscriber email=%s spreadsheet_id=%s folder_id=%s",
            subscriber_request.email,
            SPREADSHEET_ID or "(unset)",
            folder_id,
        )
        return folder_url

    except FileNotFoundError as e:
        logger.error("OAuth client secret not found while creating folder: %s", e)
        return None
    except Exception as e:
        logger.exception("Error creating Google Drive folder for email=%s", getattr(subscriber_request, "email", ""))
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
        logger.info(
            "Sheet append raw_registration email=%s spreadsheet_id=%s column_H_has_url=%s",
            subscriber_request.email,
            SPREADSHEET_ID or "(unset)",
            bool(folder_url),
        )

        return True

    except FileNotFoundError as e:
        logger.error("OAuth credentials missing for log_to_spreadsheet: %s", e)
        return False
    except Exception as e:
        logger.exception(
            "log_to_spreadsheet failed email=%s spreadsheet_id=%s",
            getattr(subscriber_request, "email", ""),
            SPREADSHEET_ID or "(unset)",
        )
        return False


def _find_row_number_by_email_column_b(worksheet, email):
    """Return 1-based row number where column B matches email (case-insensitive), or None."""
    try:
        rows = worksheet.get_all_values()
    except Exception as e:
        logger.warning("Error reading sheet rows for email lookup: %s", e)
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
            logger.info(
                "Sheet upsert UPDATE row=%s worksheet=raw_registration email=%s "
                "spreadsheet_id=%s column_H_has_url=%s",
                row_num,
                subscriber_request.email,
                SPREADSHEET_ID or "(unset)",
                bool(folder_url),
            )
        else:
            worksheet.append_row(row_data)
            logger.info(
                "Sheet upsert APPEND worksheet=raw_registration email=%s spreadsheet_id=%s "
                "column_H_has_url=%s",
                subscriber_request.email,
                SPREADSHEET_ID or "(unset)",
                bool(folder_url),
            )

        return True

    except FileNotFoundError as e:
        logger.error("OAuth credentials missing for upsert_log_to_spreadsheet: %s", e)
        return False
    except Exception as e:
        logger.exception(
            "upsert_log_to_spreadsheet failed email=%s spreadsheet_id=%s",
            getattr(subscriber_request, "email", ""),
            SPREADSHEET_ID or "(unset)",
        )
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
            logger.info(
                "Subscriber folder: reused URL from sheet column H email=%s spreadsheet_id=%s",
                subscriber_request.email,
                SPREADSHEET_ID or "(unset)",
            )
            upsert_log_to_spreadsheet(subscriber_request, existing_url)
            return existing_url

        # Same as renewal path: prefer an existing Drive folder (name|email) before creating
        folder_url = get_folder_upload_url(subscriber_request)
        logger.info(
            "Subscriber folder: resolved from Drive (existing or new) email=%s spreadsheet_id=%s "
            "has_url=%s",
            subscriber_request.email,
            SPREADSHEET_ID or "(unset)",
            bool(folder_url),
        )
        upsert_log_to_spreadsheet(subscriber_request, folder_url or '')
        return folder_url

    except Exception as e:
        logger.exception(
            "get_or_create_subscriber_folder_url failed email=%s",
            getattr(subscriber_request, "email", ""),
        )
        return None


def get_folder_upload_url(
    subscriber_request,
    user_profile: Optional["UserProfile"] = None,
):
    """
    Get the upload URL for an existing subscriber's folder.
    If the folder doesn't exist, creates it.

    Args:
        subscriber_request: SubscriberRequest instance
        user_profile: Optional UserProfile (renewals: supply so cohort matches profile when request has no cohort)

    Returns:
        str: URL of the folder for uploading, or None if operation fails
    """
    try:
        credentials = get_credentials()
        drive_service = build('drive', 'v3', credentials=credentials)

        cohort_id = resolve_drive_cohort_id(subscriber_request, user_profile)
        cohort_folder_id = get_or_create_cohort_folder(drive_service, cohort_id)

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
            url = files[0].get('webViewLink')
            logger.info(
                "Drive folder found by name email=%s spreadsheet_id=%s",
                subscriber_request.email,
                SPREADSHEET_ID or "(unset)",
            )
            return url
        logger.info(
            "Drive folder not found; creating new email=%s spreadsheet_id=%s",
            subscriber_request.email,
            SPREADSHEET_ID or "(unset)",
        )
        return create_subscriber_folder(subscriber_request, user_profile=user_profile)

    except FileNotFoundError as e:
        logger.error("OAuth credentials missing for get_folder_upload_url: %s", e)
        return None
    except Exception as e:
        logger.exception(
            "get_folder_upload_url failed email=%s",
            getattr(subscriber_request, "email", ""),
        )
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
                logger.info(
                    "Sheet lookup: folder URL in column H row=%s email=%s spreadsheet_id=%s "
                    "update_status=%s",
                    cell.row,
                    email,
                    SPREADSHEET_ID or "(unset)",
                    update_status,
                )
                return row_values[7]

        logger.info(
            "Sheet lookup: no folder URL in column H for email=%s spreadsheet_id=%s",
            email,
            SPREADSHEET_ID or "(unset)",
        )
        return None

    except gspread.exceptions.CellNotFound:
        logger.info(
            "Sheet lookup: email not found in column B email=%s spreadsheet_id=%s",
            email,
            SPREADSHEET_ID or "(unset)",
        )
        return None
    except Exception as e:
        logger.exception(
            "find_url_in_spreadsheet failed email=%s spreadsheet_id=%s",
            email,
            SPREADSHEET_ID or "(unset)",
        )
        return None


def upsert_renewal_to_spreadsheet(subscriber_request, folder_url, plan):
    """
    Insert or update a renewal row in raw_registration (key: email in column B).

    Always upserts so duplicate API calls or retries cannot create two rows for the same email.

    Args:
        subscriber_request: SubscriberRequest instance
        folder_url: URL of the Google Drive folder
        plan: Renewal plan selected (e.g. '6month', 'annual')

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        credentials = get_credentials()
        gc = gspread.authorize(credentials)

        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet('raw_registration')

        from django.utils import timezone

        # name, email, tele_name, country, plan, status, created_at, payment_url
        row_data = [
            subscriber_request.name,
            subscriber_request.email,
            subscriber_request.telegram_username or '',
            subscriber_request.country,
            plan,
            'Renewal Requested',
            timezone.now().strftime('%b. %-d, %Y, %-I:%M %p'),
            folder_url or '',
        ]

        row_num = _find_row_number_by_email_column_b(worksheet, subscriber_request.email)
        if row_num:
            worksheet.update(
                f'A{row_num}:H{row_num}',
                [row_data],
                value_input_option='USER_ENTERED',
            )
            logger.info(
                "Renewal sheet upsert UPDATE row=%s email=%s spreadsheet_id=%s plan=%s "
                "column_H_has_url=%s",
                row_num,
                subscriber_request.email,
                SPREADSHEET_ID or "(unset)",
                plan,
                bool(folder_url),
            )
        else:
            worksheet.append_row(row_data)
            logger.info(
                "Renewal sheet upsert APPEND email=%s spreadsheet_id=%s plan=%s column_H_has_url=%s",
                subscriber_request.email,
                SPREADSHEET_ID or "(unset)",
                plan,
                bool(folder_url),
            )

        return True

    except Exception as e:
        logger.exception(
            "upsert_renewal_to_spreadsheet failed email=%s spreadsheet_id=%s",
            getattr(subscriber_request, "email", ""),
            SPREADSHEET_ID or "(unset)",
        )
        return False


def get_or_create_renewal_url(
    subscriber_request,
    plan,
    user_profile: Optional["UserProfile"] = None,
):
    """
    Get existing URL from spreadsheet or create new folder and log to sheet.

    For renewal requests:
    1. First checks if user already has an entry in the spreadsheet
    2. If found, updates status to 'Renewal Requested' and returns the existing folder URL
    3. If not found, creates folder, upserts spreadsheet row (by email), and returns URL

    Args:
        subscriber_request: SubscriberRequest instance
        plan: Renewal plan selected
        user_profile: UserProfile for the renewing user (used for Drive cohort when request has no cohort)

    Returns:
        tuple: (folder_url, is_existing) where is_existing indicates if URL was from sheet
               Returns (None, False) if operation fails
    """
    try:
        # First, check if URL exists in spreadsheet and update status/plan if found
        existing_url = find_url_in_spreadsheet(subscriber_request.email, update_status=True, plan=plan)
        if existing_url:
            logger.info(
                "Renewal: reused folder URL from sheet email=%s spreadsheet_id=%s plan=%s",
                subscriber_request.email,
                SPREADSHEET_ID or "(unset)",
                plan,
            )
            return (existing_url, True)

        # No existing entry, create folder and log to sheet
        folder_url = get_folder_upload_url(subscriber_request, user_profile=user_profile)
        if folder_url:
            upsert_renewal_to_spreadsheet(subscriber_request, folder_url, plan)
            logger.info(
                "Renewal: new Drive resolution + sheet upsert email=%s spreadsheet_id=%s plan=%s",
                subscriber_request.email,
                SPREADSHEET_ID or "(unset)",
                plan,
            )
            return (folder_url, False)

        logger.error(
            "Renewal: no folder URL from Drive email=%s spreadsheet_id=%s",
            subscriber_request.email,
            SPREADSHEET_ID or "(unset)",
        )
        return (None, False)

    except Exception as e:
        logger.exception(
            "get_or_create_renewal_url failed email=%s",
            getattr(subscriber_request, "email", ""),
        )
        return (None, False)
