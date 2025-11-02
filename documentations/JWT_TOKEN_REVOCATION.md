# JWT Token Revocation - Important Information

## Understanding JWT Token Revocation

### The Issue You're Experiencing

When you logout or revoke a session, you might notice that the **access token still works** for API calls. This is **expected behavior** with JWT tokens and not a bug.

## Why Does This Happen?

### JWT Tokens Are Stateless

**Access tokens** in JWT are designed to be **stateless** - meaning:
- The server doesn't store them in a database
- They carry all authentication information inside themselves
- They are validated by cryptographic signature, not database lookup
- **They cannot be revoked until they expire**

### What Gets Revoked

When you call logout endpoints:
- ✅ **Refresh token** → Blacklisted immediately
- ✅ **Session record** → Marked as inactive in database
- ❌ **Access token** → Remains valid until expiration (1 hour)

## Current Token Lifetimes

```python
ACCESS_TOKEN_LIFETIME = 1 hour       # Cannot be revoked early
REFRESH_TOKEN_LIFETIME = 7 days      # Can be blacklisted
```

## Security Implications

### This is Actually Secure By Design

1. **Short-lived access tokens** (1 hour) limit the risk window
2. **Refresh tokens** (7 days) can be blacklisted
3. **Performance benefit**: No database lookup on every request

### The Tradeoff

- **Performance**: Fast authentication (no DB queries)
- **Security**: Small window of vulnerability (1 hour max)

## Solutions

### Option 1: Accept the 1-Hour Window (Recommended)

**Current Setup:**
- Access token expires in 1 hour automatically
- After logout, user cannot get new access tokens (refresh is blacklisted)
- Maximum exposure: 1 hour

**Best For:**
- Most applications
- High-performance needs
- Standard security requirements

**No changes needed** - this is how most JWT systems work (GitHub, Auth0, etc.)

### Option 2: Implement Access Token Blacklist (High Security)

If you need immediate revocation, add middleware to check blacklist:

```python
# users/middleware.py
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

class CheckTokenBlacklistMiddleware(MiddlewareMixin):
    """
    Middleware to check if access token is blacklisted.
    WARNING: This adds a database query to EVERY authenticated request.
    """

    def process_request(self, request):
        auth_header = request.headers.get('Authorization', '')

        if auth_header.startswith('Bearer '):
            token_string = auth_header.split(' ')[1]

            try:
                # Decode token
                token = AccessToken(token_string)
                jti = str(token['jti'])

                # Check if blacklisted
                if OutstandingToken.objects.filter(jti=jti).exists():
                    outstanding = OutstandingToken.objects.get(jti=jti)
                    if BlacklistedToken.objects.filter(token=outstanding).exists():
                        # Token is blacklisted
                        from rest_framework.exceptions import AuthenticationFailed
                        raise AuthenticationFailed('Token has been revoked')

            except Exception:
                pass  # Let normal auth handle invalid tokens

        return None
```

**Add to settings.py:**
```python
MIDDLEWARE = [
    # ... existing middleware
    'users.middleware.CheckTokenBlacklistMiddleware',  # Add this
]
```

**Pros:**
- Immediate token revocation
- High security

**Cons:**
- Database query on EVERY request (performance impact)
- Defeats the stateless benefit of JWT
- May need caching (Redis) for scale

### Option 3: Reduce Access Token Lifetime

Make access tokens expire faster:

**In settings.py:**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),  # Instead of 1 hour
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}
```

**Pros:**
- Reduced risk window
- Still stateless

**Cons:**
- Users need to refresh tokens more often
- More network requests

### Option 4: Hybrid Approach (Recommended for Critical Operations)

Use short-lived tokens + blacklist check only for sensitive endpoints:

```python
# Decorate sensitive views
from users.decorators import check_token_blacklist

class SensitiveViewSet(viewsets.ModelViewSet):
    @check_token_blacklist  # Only check blacklist for sensitive operations
    def destroy(self, request, *args, **kwargs):
        # Delete operation
        pass
```

## Testing Token Revocation

### Test Refresh Token Revocation (Should Fail)

```bash
# 1. Login
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "pass"}'

# Save: access_token and refresh_token

# 2. Logout (blacklist refresh token)
curl -X POST http://127.0.0.1:8000/api/v1/auth/logout/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'

# 3. Try to refresh (THIS SHOULD FAIL)
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'

# Expected: Error - token is blacklisted
```

### Test Access Token (Still Works - Expected)

```bash
# 4. Use access token (STILL WORKS)
curl http://127.0.0.1:8000/api/v1/auth/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Expected: Success - access token valid until expiry
# Will automatically fail after 1 hour
```

## What Changes Were Made

### Fixed in Your Code

1. ✅ **OpenAPI warnings** - Added proper serializers
2. ✅ **Refresh token blacklisting** - Works correctly
3. ✅ **Session revocation** - Marks sessions as inactive
4. ✅ **Ordering warnings** - Added proper ordering to querysets

### Current Behavior (Correct)

- **Logout**: Blacklists refresh token, revokes session
- **Refresh**: Will fail if logged out (correct)
- **Access token**: Works until 1-hour expiration (expected JWT behavior)

## Recommendations

### For Your Use Case (Telegram Bot + Website)

**Recommended: Keep current setup**

Why:
1. 1-hour access token lifetime is reasonable
2. Telegram bots don't need instant revocation
3. Performance is better (no DB queries)
4. Standard industry practice

### If You Need Immediate Revocation

Implement **Option 4 (Hybrid)**:
- Normal endpoints: Stateless (fast)
- Critical operations: Check blacklist
- Best of both worlds

## Industry Standards

Most JWT implementations work this way:
- **GitHub**: Access tokens valid until expiry
- **Auth0**: Same behavior
- **Firebase**: Same behavior
- **OAuth 2.0**: Standard practice

Your implementation is **correct and secure** according to JWT best practices.

## Summary

| Token Type | Can Be Revoked? | How Long Valid? |
|------------|----------------|-----------------|
| Access Token | ❌ No (until expiry) | 1 hour |
| Refresh Token | ✅ Yes (immediately) | 7 days |

**Bottom Line**: After logout, users **cannot get new access tokens** (refresh is blocked), but existing access tokens work for up to 1 hour. This is **normal and secure JWT behavior**.

If you need immediate revocation, implement Option 2 or Option 4 above.
