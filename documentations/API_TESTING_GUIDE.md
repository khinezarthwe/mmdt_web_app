# API Testing Guide

## Base URL
- Local: `http://127.0.0.1:8000`
- Production: Update with your domain

## Authentication Endpoints

### Login
```
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "username_or_email",
  "password": "password",
  "client_type": "telegram_bot|website|mobile|unknown",
  "device_name": "optional",
  "telegram_user_id": 123456,  // optional, for telegram
  "telegram_username": "string"  // optional, for telegram
}

Response 200:
{
  "refresh": "refresh_token",
  "access": "access_token",
  "user": {...},
  "session_id": 1
}

Response 401: Already logged in on this client_type
{
  "detail": "You are already logged in on telegram bot. Please logout first..."
}
```

### Refresh
```
POST /api/v1/auth/token/refresh/

{
  "refresh": "refresh_token"
}

Response 200:
{
  "access": "new_access_token",
  "refresh": "new_refresh_token"
}
```

### Logout
```
POST /api/v1/auth/logout/
Authorization: Bearer access_token

{
  "refresh": "refresh_token"
}

Response 200:
{
  "message": "Logout successful",
  "detail": "Session revoked and tokens blacklisted"
}
```

### Logout All
```
POST /api/v1/auth/logout/all/
Authorization: Bearer access_token

Response 200:
{
  "message": "Logged out from 3 device(s)",
  "revoked_sessions": 3
}
```

## User Endpoints

### Get Current User
```
GET /api/v1/auth/users/me/
Authorization: Bearer access_token

Response 200:
{
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  "first_name": "First",
  "last_name": "Last",
  "is_active": true,
  "is_staff": false,
  "profile": {
    "expired": false,
    "expiry_date": null
  }
}
```

### List Users (Admin)
```
GET /api/v1/auth/users/
Authorization: Bearer access_token

Response 200: Paginated list of users
```

### Get User by ID
```
GET /api/v1/auth/users/{id}/
Authorization: Bearer access_token
```

## Session Endpoints

### List Sessions
```
GET /api/v1/auth/sessions/
Authorization: Bearer access_token

Response 200:
[
  {
    "id": 1,
    "client_type": "telegram_bot",
    "device_name": "Device Name",
    "created_at": "2024-01-01T00:00:00Z",
    "last_activity": "2024-01-01T01:00:00Z",
    "expires_at": "2024-01-08T00:00:00Z",
    "ip_address": "127.0.0.1",
    "is_active": true
  }
]
```

### Get Session
```
GET /api/v1/auth/sessions/{id}/
Authorization: Bearer access_token
```

### Revoke Session
```
POST /api/v1/auth/sessions/{id}/revoke/
Authorization: Bearer access_token

Response 200:
{
  "message": "Session revoked successfully",
  "session_id": 1
}
```

### Revoke All Sessions
```
POST /api/v1/auth/sessions/revoke_all/
Authorization: Bearer access_token

{
  "keep_current": false
}

Response 200:
{
  "message": "3 session(s) revoked successfully",
  "revoked_count": 3
}
```

## Documentation

### Interactive API Docs
- Swagger UI: `http://127.0.0.1:8000/api/v1/schema/swagger-ui/`
- ReDoc: `http://127.0.0.1:8000/api/v1/schema/redoc/`
- OpenAPI Schema: `http://127.0.0.1:8000/api/v1/schema/`

### Import to Postman
1. Open Postman > Import
2. Enter URL: `http://127.0.0.1:8000/api/v1/schema/`
3. Import

## Token Lifetimes
- Access Token: 1 hour
- Refresh Token: 7 days
- Token rotation enabled
- Immediate revocation enabled

## Security Features
- One active session per client_type per user
- Prevents duplicate logins on same platform
- Access and refresh tokens both blacklisted on logout
- Middleware checks token blacklist on every request
- Session tracking with IP and user agent

## Common Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 401 Token Revoked
```json
{
  "detail": "Token has been revoked. Please login again.",
  "code": "token_revoked"
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```
