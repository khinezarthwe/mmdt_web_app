"""
Google Drive and Sheets API utilities for subscriber automation.
"""
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from django.conf import settings


# TODO: Update these constants when supervisor provides the information
PARENT_FOLDER_ID = '1Oa6fhtegbjpk29msrnQkYksANPhodqbw'
SPREADSHEET_ID = '17CeX0Q1Bf1tkK-IrKEHeym6BnMsUSdB0mXW8RFX3NlA'
MMDT_ADMIN_EMAIL = 'mmdt@istarvz.com'
SERVICE_ACCOUNT_FILE = os.path.join(settings.BASE_DIR, 'mmdt', 'service_account_key.json')

# TODO: Update payment amounts when supervisor provides them
PAYMENT_AMOUNTS = {
    '6month': 0,  # TODO: Set actual amount
    'annual': 0,  # TODO: Set actual amount
}

# Scopes for Google APIs
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
]


def get_credentials():
    """
    Get Google API credentials from service account file.

    Returns:
        google.oauth2.service_account.Credentials

    Raises:
        FileNotFoundError: If service account file doesn't exist
    """
    # TODO: Replace with actual service account key file when provided
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(
            f"Service account key file not found at {SERVICE_ACCOUNT_FILE}. "
            "Please obtain the service account JSON key from supervisor."
        )

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    return credentials


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
            subscriber_request.cohort.cohort_id if subscriber_request.cohort else 'NO_COHORT'
        )

        # Create user folder: fullname-email
        folder_name = f"{subscriber_request.name}-{subscriber_request.email}"

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
        # TODO: Log this error properly
        return None
    except Exception as e:
        print(f"Error creating Google Drive folder: {e}")
        # TODO: Log this error properly
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
        worksheet = spreadsheet.get_worksheet(0)  # First sheet

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
        # TODO: Log this error properly
        return False
    except Exception as e:
        print(f"Error logging to Google Sheet: {e}")
        # TODO: Log this error properly
        return False
