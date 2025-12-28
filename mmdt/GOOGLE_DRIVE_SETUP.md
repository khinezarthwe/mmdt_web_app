# Google Drive Automation Setup Guide

## Overview
This feature automatically creates Google Drive folders and sends payment instructions when users submit paid subscription requests.

## Implementation Status
✓ Code structure complete with TODO placeholders
✓ Google API packages installed
✓ Email template created
✓ Django signal configured

## Required Configuration

### 1. Service Account Credentials

**File needed:** Service account JSON key file
**Location:** `mmdt/service_account_key.json` (in project root's mmdt folder)

**Steps:**
1. Ask supervisor for service account JSON key file for `mmdt-service-account@mmdt-472812.iam.gserviceaccount.com`
2. Save it as `service_account_key.json` in the `mmdt/` directory (same folder as settings.py)
3. Verify it's not tracked by git (already in .gitignore)
4. File path will be: `<project_root>/mmdt/service_account_key.json`

### 2. Payment Amounts

**File to update:** `blog/google_api_utils.py`
**Line:** ~18-21

```python
PAYMENT_AMOUNTS = {
    '6month': 0,  # TODO: Set actual amount
    'annual': 0,  # TODO: Set actual amount
}
```

**Ask supervisor:**
- 6-month plan price: ?
- Annual plan price: ?
- Currency (USD, MMK, etc.): ?

### 3. Bank Transfer Details

**File to update:** `templates/emails/payment_instructions.html`
**Lines:** ~23-26

```html
<p><strong>Bank Name:</strong> [BANK_NAME]</p>
<p><strong>Account Number:</strong> [ACCOUNT_NUMBER]</p>
<p><strong>Account Holder:</strong> [ACCOUNT_HOLDER_NAME]</p>
```

**Ask supervisor for:**
- Bank name
- Account number
- Account holder name

### 4. Currency Setting

**File to update:** `blog/signals.py`
**Line:** ~68

```python
currency = "USD"  # TODO: Ask supervisor for currency
```

## How It Works

### Trigger
When a user submits a SubscriberRequest with `free_waiver=False` (paid subscription)

### Automated Process
1. **Create Google Drive Folder**
   - Structure: `cohort-id/fullname-email/`
   - Location: Under parent folder 1Oa6fhtegbjpk29msrnQkYksANPhodqbw
   - Permissions: Edit access for user's email and mmdt@istarvz.com

2. **Log to Google Sheets**
   - Spreadsheet: 17CeX0Q1Bf1tkK-IrKEHeym6BnMsUSdB0mXW8RFX3NlA
   - Columns: name, email, tele_name, country, plan, status, created_at, payment_url

3. **Send Payment Email**
   - Bank transfer instructions
   - Transfer reference: "FullName-MMDT"
   - Payment amount based on plan
   - Link to Google Drive folder
   - Deadline: 1 week after cohort registration closes

## Email Template Preview

To preview the email template, simply open the HTML file in a browser:
```bash
open mmdt/templates/emails/payment_instructions.html
```

Or manually navigate to: `/Users/zno/MMDT/mmdt_web_app/mmdt/templates/emails/payment_instructions.html`

Note: Template variables like `{{ name }}` will show as-is in browser. To see with real data, use Django shell test below.

## Testing

### Before Service Account Credentials
The automation will fail gracefully:
- Folder creation will fail and print warning
- Google Sheets logging will fail and print warning
- Email will still be sent (with placeholder folder link)

### After Service Account Credentials
1. Create test SubscriberRequest with `free_waiver=False`
2. Check console for success/error messages
3. Verify folder created in Google Drive
4. Verify data logged to Google Sheet
5. Check email inbox for payment instructions

## Error Handling

Current implementation:
- Prints errors to console
- Continues execution even if folder/sheet operations fail
- Email still sent to user

**TODO:** Implement proper logging and admin notifications for failures

## Files Created/Modified

**New files:**
- `blog/google_api_utils.py` - Google API integration
- `blog/signals.py` - Automation trigger
- `templates/emails/payment_instructions.html` - Email template
- `GOOGLE_DRIVE_SETUP.md` - This guide

**Modified files:**
- `blog/apps.py` - Register signals
- `.gitignore` - Ignore *.json files
- `requirements.txt` - Add Google API packages

## Security Notes

- Service account JSON key is sensitive - keep it secure
- Already added to .gitignore
- Never commit credentials to git
- Service account should have minimum required permissions
