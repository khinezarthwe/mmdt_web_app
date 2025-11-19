# JWT Authentication Implementation

## Overview
JWT authentication with SimpleJWT, token blacklisting, session tracking, and immediate token revocation.

## Features
- JWT access and refresh tokens
- Token rotation on refresh
- Immediate token revocation via blacklist
- Multi-device session tracking
- One session per platform per user
- OpenAPI 3.0 documentation

## Configuration

### Token Settings
```python
# settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}
```

### Middleware
```python
# settings.py
MIDDLEWARE = [
    # ... other middleware
    'users.middleware.CheckTokenBlacklistMiddleware',  # Token blacklist check
]
```

## Authentication Flow

### 1. Login
- User provides credentials + client_type
- System checks for existing active session on same client_type
- If exists: Returns 401 "Already logged in"
- If not: Creates tokens and session

### 2. Token Usage
- Access token in Authorization header: `Bearer <token>`
- Middleware checks if token is blacklisted
- If blacklisted: Returns 401
- If valid: Request proceeds

### 3. Token Refresh
- Client sends refresh token
- System validates and creates new access token
- Old access token blacklisted
- Old refresh token blacklisted (if rotation enabled)
- Session updated with new token JTIs

### 4. Logout
- Marks session as inactive
- Blacklists both access and refresh tokens
- Tokens immediately invalid

## Session Management

### Session Model
```python
class UserSession(models.Model):
    user = ForeignKey(User)
    refresh_token_jti = CharField(max_length=255, unique=True)
    access_token_jti = CharField(max_length=255)
    client_type = CharField(max_length=50)
    device_name = CharField(max_length=255, null=True)
    telegram_user_id = BigIntegerField(null=True)
    telegram_username = CharField(max_length=255, null=True)
    ip_address = GenericIPAddressField(null=True)
    user_agent = TextField(null=True)
    created_at = DateTimeField(auto_now_add=True)
    last_activity = DateTimeField(auto_now=True)
    expires_at = DateTimeField()
    is_active = BooleanField(default=True)
```

### Session Rules
- One active session per user per client_type
- Different client_types can coexist (telegram + website + mobile)
- Attempting duplicate login on same client_type returns error

## Token Blacklisting

### How It Works
1. Access tokens stored in OutstandingToken table on creation
2. Middleware checks token JTI against BlacklistedToken table
3. Blacklisted tokens rejected immediately
4. Both access and refresh tokens blacklisted on logout/revoke

### Performance
- Database query on every authenticated request
- Recommended: Add Redis caching for production
- Tradeoff: Security vs Performance (immediate revocation)

## API Endpoints

### Auth
- `POST /api/v1/auth/token/` - Login
- `POST /api/v1/auth/token/refresh/` - Refresh token
- `POST /api/v1/auth/logout/` - Logout current session
- `POST /api/v1/auth/logout/all/` - Logout all sessions

### Users
- `GET /api/v1/auth/users/{id}/` - User details

### Sessions
- `GET /api/v1/auth/sessions/` - List active sessions
- `GET /api/v1/auth/sessions/{id}/` - Session details
- `POST /api/v1/auth/sessions/{id}/revoke/` - Revoke session
- `POST /api/v1/auth/sessions/revoke_all/` - Revoke all sessions

## Security

### Token Security
- Access tokens expire in 1 hour
- Refresh tokens expire in 7 days
- Automatic rotation prevents token reuse
- Blacklisting prevents revoked tokens from working

### Session Security
- IP address tracking
- User agent tracking
- Device identification
- Prevents session hijacking via duplicate login protection

### Best Practices
- Use HTTPS in production
- Store tokens securely (not in localStorage for web)
- Implement rate limiting on login endpoint
- Monitor failed login attempts
- Use environment variables for SECRET_KEY

## Database Schema

### OutstandingToken
- Stores both access and refresh tokens
- Indexed by JTI for fast lookup
- Links to user

### BlacklistedToken
- References OutstandingToken
- Checked by middleware on every request

### UserSession
- Tracks active sessions
- Links to tokens via JTI
- Stores device metadata

## Admin Interface
Access at `/admin/`
- View/manage sessions
- View/blacklist tokens
- Monitor user activity

## OpenAPI Documentation
- Swagger UI: `/api/v1/schema/swagger-ui/`
- ReDoc: `/api/v1/schema/redoc/`
- JSON Schema: `/api/v1/schema/`
