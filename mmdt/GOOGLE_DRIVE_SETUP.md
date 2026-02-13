# Google Drive Automation Setup Guide

## Overview
This feature automatically creates Google Drive folders and sends payment instructions when users submit paid subscription requests.

Uses OAuth 2.0 authentication with token caching for Google Drive and Sheets access.

## Implementation Status
✓ Code rewritten to use OAuth 2.0 flow
✓ Google API packages installed
✓ Email template created
✓ Django signal configured
✓ Uses existing OAuth client secret file

## Authentication Method

**Using OAuth 2.0 with Token Caching**

### Files Used:
- **OAuth Client Secret:** `mmdt/client_secret_476736580933-kfntrcjaerj90raof7oaqgdj6s0d5utk.apps.googleusercontent.com.json` (already have)
- **Saved Tokens:** `mmdt/google_token.json` (created automatically after first authorization)

### One-Time Authorization Required

**First time the automation runs**, it will:
1. Open a browser window
2. Ask you to sign in with your Google account
3. Ask you to click "Allow" to grant permissions
4. Save tokens to `google_token.json` for future use

**After first time**: Tokens are reused automatically, no browser needed.

### How to Do First-Time Authorization

**Option 1: Trigger via Test (Recommended)**
```bash
cd mmdt
python manage.py shell
```

```python
from blog.google_api_utils import get_credentials
creds = get_credentials()  # Browser will open for authorization
print("Authorization successful!")
```

**Option 2: Wait for Real Subscriber**
When first paid subscriber request is submitted, browser will open automatically.

**Important:** You must authorize with a Google account that has access to:
- The Drive folder (1Oa6fhtegbjpk29msrnQkYksANPhodqbw)
- The Google Sheet (17CeX0Q1Bf1tkK-IrKEHeym6BnMsUSdB0mXW8RFX3NlA)

### 2. Email Template

Payment amounts and bank details are already configured in `templates/emails/paid_user_confirmation.html`:
- 6-month plan: USD $12 / MMK 54,000 / BAHT 400
- Annual plan: USD $24 / MMK 108,000 / BAHT 800
- Bank: Bangkok Bank (Account: 860-0-290269, Name: Myo Thida)
- KPay: 09402741691 (Nuam Man Cing)

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
   - Bank transfer instructions (Bangkok Bank, KPay details)
   - Payment amounts for selected plan
   - Link to Google Drive folder for receipt upload
   - Deadline: 1 week after cohort registration closes
   - Note: Free waiver users receive different confirmation email

## Email Template Preview

To preview the email template, simply open the HTML file in a browser:
```bash
open mmdt/templates/emails/paid_user_confirmation.html
```

Or manually navigate to: `/Users/zno/MMDT/mmdt_web_app/mmdt/templates/emails/paid_user_confirmation.html`

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
- `templates/emails/paid_user_confirmation.html` - Payment email template for paid users
- `GOOGLE_DRIVE_SETUP.md` - This guide

**Modified files:**
- `blog/apps.py` - Register signals
- `blog/views.py` - Skip confirmation email for paid users (handled by signal)
- `.gitignore` - Ignore *.json files
- `requirements.txt` - Add Google API packages
- `mmdt/settings.py` - Add localhost to ALLOWED_HOSTS

## Security Notes

- Service account JSON key is sensitive - keep it secure
- Already added to .gitignore
- Never commit credentials to git
- Service account should have minimum required permissions
