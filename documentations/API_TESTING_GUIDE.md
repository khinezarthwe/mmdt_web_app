# API Testing Guide - Postman & Telegram Bot

## Server Information
- **Base URL**: `http://127.0.0.1:8000` (local development)
- **Production URL**: Replace with your production domain when deployed

---

## Testing with Postman

### 1. Import OpenAPI Schema (Recommended)

1. Open Postman
2. Click **Import** button (top left)
3. Select **Link** tab
4. Enter: `http://127.0.0.1:8000/api/v1/schema/`
5. Click **Continue** → **Import**

This will automatically create all endpoints with proper request/response formats.

### 2. Manual Setup in Postman

#### Step 1: Login and Get Tokens

**Request:**
```
POST http://127.0.0.1:8000/api/v1/auth/token/
```

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "username": "your_username_or_email",
  "password": "your_password",
  "client_type": "postman_test",
  "device_name": "Postman Testing"
}
```

**Expected Response:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "session_id": 1
}
```

**Save the tokens!** Copy both `access` and `refresh` tokens.

#### Step 2: Set Up Authorization in Postman

**Method 1: Collection-level (Recommended)**
1. Create a new Collection (e.g., "MMDT API")
2. Right-click collection → **Edit**
3. Go to **Authorization** tab
4. Type: Select **Bearer Token**
5. Token: Paste your `access` token
6. All requests in this collection will inherit this auth

**Method 2: Individual Request**
1. Open your request
2. Go to **Authorization** tab
3. Type: Select **Bearer Token**
4. Token: Paste your `access` token

#### Step 3: Test Authenticated Endpoints

**Get Current User Info:**
```
GET http://127.0.0.1:8000/api/v1/auth/users/me/
```
Authorization: Bearer {your_access_token}

**List Active Sessions:**
```
GET http://127.0.0.1:8000/api/v1/auth/sessions/
```
Authorization: Bearer {your_access_token}

**List All Users (Admin only):**
```
GET http://127.0.0.1:8000/api/v1/auth/users/
```
Authorization: Bearer {your_access_token}

#### Step 4: Refresh Access Token

When your access token expires (after 1 hour):

**Request:**
```
POST http://127.0.0.1:8000/api/v1/auth/token/refresh/
```

**Body (raw JSON):**
```json
{
  "refresh": "your_refresh_token"
}
```

**Response:**
```json
{
  "access": "new_access_token",
  "refresh": "new_refresh_token"
}
```

Update your Bearer token with the new `access` token.

#### Step 5: Logout

**Request:**
```
POST http://127.0.0.1:8000/api/v1/auth/logout/
```

**Body (raw JSON):**
```json
{
  "refresh": "your_refresh_token"
}
```

---

## Testing with Telegram Bot

### Prerequisites
Install required packages in your Telegram bot project:
```bash
pip install python-telegram-bot requests
```

### Basic Telegram Bot Integration

Create a file `telegram_bot_api_client.py`:

```python
import requests
from typing import Optional, Dict, Any

class MMDTAPIClient:
    """Client for interacting with MMDT API from Telegram bot."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def login(self, username: str, password: str, telegram_user_id: int,
              telegram_username: str) -> Dict[str, Any]:
        """
        Login user and store tokens.

        Args:
            username: Username or email
            password: User password
            telegram_user_id: Telegram user ID
            telegram_username: Telegram username

        Returns:
            API response with tokens and user info
        """
        url = f"{self.base_url}/api/v1/auth/token/"
        payload = {
            "username": username,
            "password": password,
            "client_type": "telegram_bot",
            "telegram_user_id": telegram_user_id,
            "telegram_username": telegram_username
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            self.access_token = data.get('access')
            self.refresh_token = data.get('refresh')

            return {
                'success': True,
                'user': data.get('user'),
                'session_id': data.get('session_id')
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        if not self.access_token:
            raise ValueError("Not authenticated. Please login first.")
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using refresh token.

        Returns:
            True if refresh successful, False otherwise
        """
        if not self.refresh_token:
            return False

        url = f"{self.base_url}/api/v1/auth/token/refresh/"
        payload = {"refresh": self.refresh_token}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            self.access_token = data.get('access')
            if 'refresh' in data:
                self.refresh_token = data.get('refresh')

            return True
        except requests.exceptions.RequestException:
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        url = f"{self.base_url}/api/v1/auth/users/me/"

        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            # Try to refresh token and retry
            if self.refresh_access_token():
                return self.get_user_info()
            return {
                'success': False,
                'error': str(e)
            }

    def get_active_sessions(self) -> Dict[str, Any]:
        """Get all active sessions for current user."""
        url = f"{self.base_url}/api/v1/auth/sessions/"

        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return {
                'success': True,
                'sessions': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def logout(self) -> bool:
        """Logout from current session."""
        if not self.refresh_token:
            return False

        url = f"{self.base_url}/api/v1/auth/logout/"
        payload = {"refresh": self.refresh_token}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()

            self.access_token = None
            self.refresh_token = None
            return True
        except requests.exceptions.RequestException:
            return False
```

### Example Telegram Bot Implementation

```python
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram_bot_api_client import MMDTAPIClient

# Store user sessions (in production, use database)
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when /start is issued."""
    await update.message.reply_text(
        "Welcome to MMDT Bot!\n\n"
        "Commands:\n"
        "/login <username> <password> - Login to your account\n"
        "/me - Get your user info\n"
        "/sessions - List active sessions\n"
        "/logout - Logout from current session"
    )

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /login command."""
    user_id = update.effective_user.id
    username_tg = update.effective_user.username

    # Parse arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /login <username> <password>"
        )
        return

    username = context.args[0]
    password = context.args[1]

    # Create API client
    client = MMDTAPIClient(base_url="http://127.0.0.1:8000")

    # Attempt login
    result = client.login(
        username=username,
        password=password,
        telegram_user_id=user_id,
        telegram_username=username_tg or "unknown"
    )

    if result['success']:
        # Store session
        user_sessions[user_id] = client

        user_info = result['user']
        await update.message.reply_text(
            f"✅ Login successful!\n\n"
            f"Welcome, {user_info['first_name']} {user_info['last_name']}\n"
            f"Username: {user_info['username']}\n"
            f"Email: {user_info['email']}\n"
            f"Session ID: {result['session_id']}"
        )
    else:
        await update.message.reply_text(
            f"❌ Login failed: {result['error']}"
        )

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /me command."""
    user_id = update.effective_user.id

    # Check if user is logged in
    if user_id not in user_sessions:
        await update.message.reply_text(
            "❌ You are not logged in. Use /login first."
        )
        return

    client = user_sessions[user_id]
    result = client.get_user_info()

    if result['success']:
        data = result['data']
        profile = data.get('profile', {})

        await update.message.reply_text(
            f"👤 Your Profile\n\n"
            f"Username: {data['username']}\n"
            f"Email: {data['email']}\n"
            f"Name: {data['first_name']} {data['last_name']}\n"
            f"Account Status: {'Active' if data['is_active'] else 'Inactive'}\n"
            f"Expired: {'Yes' if profile.get('expired') else 'No'}\n"
            f"Joined: {data['date_joined'][:10]}"
        )
    else:
        await update.message.reply_text(
            f"❌ Error: {result['error']}"
        )

async def sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sessions command."""
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text(
            "❌ You are not logged in. Use /login first."
        )
        return

    client = user_sessions[user_id]
    result = client.get_active_sessions()

    if result['success']:
        sessions_list = result['sessions']

        if not sessions_list:
            await update.message.reply_text("No active sessions found.")
            return

        message = "🔐 Active Sessions:\n\n"
        for i, session in enumerate(sessions_list, 1):
            message += (
                f"{i}. {session['client_type']}\n"
                f"   Device: {session.get('device_name', 'Unknown')}\n"
                f"   IP: {session.get('ip_address', 'Unknown')}\n"
                f"   Created: {session['created_at'][:10]}\n"
                f"   Expires: {session['expires_at'][:10]}\n\n"
            )

        await update.message.reply_text(message)
    else:
        await update.message.reply_text(
            f"❌ Error: {result['error']}"
        )

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /logout command."""
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text(
            "❌ You are not logged in."
        )
        return

    client = user_sessions[user_id]

    if client.logout():
        del user_sessions[user_id]
        await update.message.reply_text(
            "✅ Logged out successfully!"
        )
    else:
        await update.message.reply_text(
            "❌ Logout failed."
        )

def main():
    """Start the bot."""
    # Replace with your bot token
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(CommandHandler("me", me))
    application.add_handler(CommandHandler("sessions", sessions))
    application.add_handler(CommandHandler("logout", logout))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
```

### Testing the Telegram Bot

1. **Start your Django server**:
   ```bash
   python manage.py runserver
   ```

2. **Run your Telegram bot**:
   ```bash
   python telegram_bot.py
   ```

3. **Test commands in Telegram**:
   - `/start` - See available commands
   - `/login your_username your_password` - Login
   - `/me` - Get your profile info
   - `/sessions` - List active sessions
   - `/logout` - Logout

---

## Quick Test Script (Python)

Save as `test_api.py`:

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_login():
    """Test login endpoint."""
    print("Testing Login...")
    response = requests.post(f"{BASE_URL}/api/v1/auth/token/", json={
        "username": "admin",  # Change to your username
        "password": "your_password",  # Change to your password
        "client_type": "test_script"
    })

    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    return data

def test_user_info(access_token):
    """Test getting user info."""
    print("\nTesting Get User Info...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/api/v1/auth/users/me/", headers=headers)

    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_sessions(access_token):
    """Test getting sessions."""
    print("\nTesting Get Sessions...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/api/v1/auth/sessions/", headers=headers)

    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    # Login
    tokens = test_login()

    if 'access' in tokens:
        # Test authenticated endpoints
        test_user_info(tokens['access'])
        test_sessions(tokens['access'])
```

Run with:
```bash
python test_api.py
```

---

## Common Issues & Solutions

### Issue: "Authentication credentials were not provided"
**Solution**: Make sure you include `Authorization: Bearer <token>` header

### Issue: "Token is invalid or expired"
**Solutions**:
- Access token expires after 1 hour - use refresh endpoint
- Refresh token expires after 7 days - need to login again
- Token may have been blacklisted - login again

### Issue: "Invalid username/email or password"
**Solutions**:
- Check credentials are correct
- Check user exists in database
- Check user is active (not expired)

### Issue: CORS errors (from browser)
**Solution**: Add `django-cors-headers` to settings (for production)

---

## Next Steps

1. Test all endpoints in Postman
2. Integrate with your Telegram bot
3. Check session tracking in Django admin: `http://127.0.0.1:8000/admin/`
4. Review OpenAPI docs: `http://127.0.0.1:8000/api/v1/schema/swagger-ui/`
