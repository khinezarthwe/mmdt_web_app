# JWT Authentication Implementation Guide

## Overview

Successfully implemented JWT authentication with Simple JWT and OpenAPI 3.0 documentation using drf-spectacular.

## What Was Implemented

### 1. JWT Authentication System
- Simple JWT with token rotation and blacklisting
- Access token lifetime: 1 hour
- Refresh token lifetime: 7 days
- Automatic token rotation on refresh
- Token blacklisting for secure logout

### 2. Multi-Device Session Tracking
- UserSession model to track devices
- Support for multiple simultaneous logins
- Device information tracking (client type, IP, user agent)
- Telegram-specific fields (telegram_user_id, telegram_username)
- Session revocation capabilities

### 3. API Versioning
- API endpoints under `/api/v1/`
- Easy to add v2, v3 in the future
- Clean URL structure

### 4. OpenAPI 3.0 Documentation
- Interactive Swagger UI
- ReDoc documentation
- Auto-generated from code
- JWT authentication integration

## API Endpoints

### Authentication Endpoints

#### 1. Login (Obtain Token)
```
POST /api/v1/auth/token/
```

**Request Body:**
```json
{
  "username": "username or email@example.com",
  "password": "yourpassword",
  "client_type": "telegram_bot",
  "device_name": "My Device",
  "telegram_user_id": 123456789,
  "telegram_username": "@username"
}
```

**Response:**
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
  "session_id": 123
}
```

#### 2. Refresh Token
```
POST /api/v1/auth/token/refresh/
```

**Request Body:**
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

#### 3. Logout (Single Device)
```
POST /api/v1/auth/logout/
```

**Request Body:**
```json
{
  "refresh": "your_refresh_token"
}
```

**Response:**
```json
{
  "message": "Logout successful",
  "detail": "Session revoked and token blacklisted"
}
```

#### 4. Logout All Devices
```
POST /api/v1/auth/logout/all/
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "message": "Logged out from 3 device(s)",
  "revoked_sessions": 3
}
```

### User Management Endpoints

#### 5. Get Current User Info
```
GET /api/v1/auth/users/me/
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "date_joined": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-15T12:30:00Z",
  "profile": {
    "expired": false,
    "expiry_date": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T12:30:00Z"
  }
}
```

#### 6. List All Users (Admin Only)
```
GET /api/v1/auth/users/
Authorization: Bearer your_access_token
```

### Session Management Endpoints

#### 7. List Active Sessions
```
GET /api/v1/auth/sessions/
Authorization: Bearer your_access_token
```

**Response:**
```json
[
  {
    "id": 1,
    "client_type": "telegram_bot",
    "device_name": "My Phone",
    "telegram_username": "@username",
    "created_at": "2024-01-15T10:00:00Z",
    "last_activity": "2024-01-15T12:30:00Z",
    "expires_at": "2024-01-22T10:00:00Z",
    "ip_address": "192.168.1.100",
    "is_active": true
  }
]
```

#### 8. Get Session Details
```
GET /api/v1/auth/sessions/{id}/
Authorization: Bearer your_access_token
```

#### 9. Revoke Specific Session
```
POST /api/v1/auth/sessions/{id}/revoke/
Authorization: Bearer your_access_token
```

#### 10. Revoke All Sessions
```
POST /api/v1/auth/sessions/revoke_all/
Authorization: Bearer your_access_token
```

**Request Body:**
```json
{
  "keep_current": false
}
```

## OpenAPI Documentation

### Access Documentation

1. **Swagger UI** (Interactive):
   ```
   http://127.0.0.1:8000/api/v1/schema/swagger-ui/
   ```

2. **ReDoc** (Clean Documentation):
   ```
   http://127.0.0.1:8000/api/v1/schema/redoc/
   ```

3. **OpenAPI JSON Schema**:
   ```
   http://127.0.0.1:8000/api/v1/schema/
   ```

### Using Swagger UI

1. Open Swagger UI in browser
2. Click "Authorize" button
3. Enter: `Bearer your_access_token`
4. Test endpoints directly from the browser

## For Telegram Bot Integration

### Login Flow

```python
import requests

# 1. Login and get tokens
response = requests.post('http://your-server/api/v1/auth/token/', json={
    'login': 'user@example.com',
    'password': 'password123',
    'client_type': 'telegram_bot',
    'telegram_user_id': 123456789,
    'telegram_username': '@bot_user'
})

tokens = response.json()
access_token = tokens['access']
refresh_token = tokens['refresh']

# 2. Make authenticated requests
headers = {'Authorization': f'Bearer {access_token}'}
user_info = requests.get('http://your-server/api/v1/auth/users/me/', headers=headers)

# 3. Refresh token when access token expires
refresh_response = requests.post('http://your-server/api/v1/auth/token/refresh/', json={
    'refresh': refresh_token
})

new_tokens = refresh_response.json()

# 4. Logout
requests.post('http://your-server/api/v1/auth/logout/', json={
    'refresh': refresh_token
})
```

## For Website Integration

### JavaScript Example

```javascript
// Login
async function login(email, password) {
  const response = await fetch('http://your-server/api/v1/auth/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: email,
      password: password,
      client_type: 'website',
      device_name: navigator.userAgent
    })
  });

  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  return data;
}

// Make authenticated request
async function fetchUserData() {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://your-server/api/v1/auth/users/me/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
}

// Refresh token
async function refreshToken() {
  const refresh = localStorage.getItem('refresh_token');
  const response = await fetch('http://your-server/api/v1/auth/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refresh })
  });

  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  if (data.refresh) {
    localStorage.setItem('refresh_token', data.refresh);
  }
}

// Logout
async function logout() {
  const refresh = localStorage.getItem('refresh_token');
  await fetch('http://your-server/api/v1/auth/logout/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refresh })
  });

  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}
```

## Security Features

1. **Token Expiration**: Access tokens expire after 1 hour
2. **Token Rotation**: New refresh token on each refresh
3. **Token Blacklisting**: Revoked tokens cannot be reused
4. **Session Tracking**: Monitor all active sessions
5. **Multi-Device Support**: Each device has its own session
6. **IP Tracking**: Track login locations
7. **User Agent Tracking**: Identify device types

## Database Schema

### UserSession Model

```sql
CREATE TABLE users_usersession (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    refresh_token_jti VARCHAR(255) UNIQUE,
    access_token_jti VARCHAR(255),
    client_type VARCHAR(50),
    device_name VARCHAR(255),
    ip_address VARCHAR(39),
    user_agent TEXT,
    telegram_user_id BIGINT,
    telegram_username VARCHAR(255),
    created_at TIMESTAMP,
    last_activity TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN
);
```

## Admin Interface

Access at: `http://127.0.0.1:8000/admin/`

Features:
- View all user sessions
- Revoke sessions manually
- Filter by client type, active status
- Search by username, device, IP

## Token Configuration

In `settings.py`:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

## Testing the Implementation

### Using cURL

```bash
# 1. Login
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "yourpassword",
    "client_type": "telegram_bot"
  }'

# 2. Get user info
curl -X GET http://127.0.0.1:8000/api/v1/auth/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 3. List sessions
curl -X GET http://127.0.0.1:8000/api/v1/auth/sessions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Next Steps

1. **Production Deployment**:
   - Use environment variables for SECRET_KEY
   - Enable HTTPS
   - Configure CORS properly
   - Set up rate limiting

2. **Monitoring**:
   - Add logging for authentication attempts
   - Monitor token refresh patterns
   - Alert on suspicious session activity

3. **Enhancements**:
   - Add 2FA support
   - Implement password reset flow
   - Add email verification
   - Create webhook for session events
