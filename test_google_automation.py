"""
Test script for Google Drive automation.

This script tests the full automation workflow:
1. OAuth authorization
2. Google Drive folder creation
3. Google Sheets logging
4. Email sending

Run this before testing with real subscriber requests.
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mmdt'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mmdt.settings')
django.setup()

from blog.models import SubscriberRequest
from blog.google_api_utils import (
    get_credentials,
    create_subscriber_folder,
    log_to_spreadsheet
)
from blog.signals import send_payment_instructions_email


def test_oauth_authorization():
    """Test OAuth authorization and token caching."""
    print("\n=== Testing OAuth Authorization ===")
    try:
        creds = get_credentials()
        print("✓ OAuth authorization successful")
        print(f"  Token valid: {creds.valid}")
        print(f"  Token expiry: {creds.expiry}")
        return True
    except Exception as e:
        print(f"✗ OAuth authorization failed: {e}")
        return False


def test_folder_creation():
    """Test Google Drive folder creation with a mock subscriber."""
    print("\n=== Testing Google Drive Folder Creation ===")

    # Create a mock subscriber request
    class MockSubscriber:
        def __init__(self):
            self.name = "Test User"
            self.email = "test@example.com"
            self.plan = "6month"
            self.cohort = None

    try:
        mock_subscriber = MockSubscriber()
        folder_url = create_subscriber_folder(mock_subscriber)

        if folder_url:
            print(f"✓ Folder created successfully")
            print(f"  Folder URL: {folder_url}")
            return folder_url
        else:
            print("✗ Folder creation failed (returned None)")
            return None
    except Exception as e:
        print(f"✗ Folder creation failed: {e}")
        return None


def test_sheets_logging(folder_url):
    """Test Google Sheets logging with a mock subscriber."""
    print("\n=== Testing Google Sheets Logging ===")

    # Create a mock subscriber request
    class MockSubscriber:
        def __init__(self):
            self.name = "Test User"
            self.email = "test@example.com"
            self.telegram_username = "@testuser"
            self.country = "Myanmar"
            self.plan = "6month"
            self.status = "pending"

            from django.utils import timezone
            self.created_at = timezone.now()

        def get_plan_display(self):
            return "6-Month Plan"

        def get_status_display(self):
            return "Pending"

    try:
        mock_subscriber = MockSubscriber()
        success = log_to_spreadsheet(mock_subscriber, folder_url)

        if success:
            print(f"✓ Data logged to Google Sheets successfully")
            return True
        else:
            print("✗ Sheets logging failed (returned False)")
            return False
    except Exception as e:
        print(f"✗ Sheets logging failed: {e}")
        return False


def test_email_template():
    """Test email template rendering (doesn't send actual email)."""
    print("\n=== Testing Email Template Rendering ===")

    from django.template.loader import render_to_string

    try:
        context = {
            'name': 'Test User',
            'plan': '6-Month Plan',
            'folder_url': 'https://drive.google.com/test',
            'deadline': 'January 15, 2026',
        }

        html_message = render_to_string('emails/paid_user_confirmation.html', context)

        if html_message and 'Test User' in html_message:
            print(f"✓ Email template rendered successfully")
            print(f"  Template length: {len(html_message)} characters")
            return True
        else:
            print("✗ Email template rendering failed")
            return False
    except Exception as e:
        print(f"✗ Email template rendering failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Google Drive Automation Test Suite")
    print("=" * 60)

    results = {}

    # Test 1: OAuth Authorization
    results['oauth'] = test_oauth_authorization()

    if not results['oauth']:
        print("\n⚠ OAuth authorization failed. Please fix this before proceeding.")
        print("  Make sure the OAuth consent screen is configured correctly.")
        return

    # Test 2: Folder Creation
    folder_url = test_folder_creation()
    results['folder'] = folder_url is not None

    # Test 3: Sheets Logging
    results['sheets'] = test_sheets_logging(folder_url or "#")

    # Test 4: Email Template
    results['email'] = test_email_template()

    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name.capitalize():15s}: {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! The automation is ready to use.")
    else:
        print("✗ Some tests failed. Please review the errors above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
