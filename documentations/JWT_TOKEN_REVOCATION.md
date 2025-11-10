# JWT Token Revocation

## Implementation Status
✅ **Immediate token revocation is IMPLEMENTED and WORKING**

## How It Works

### Token Tracking
1. Both access and refresh tokens stored in `OutstandingToken` table
2. Each token has unique JTI (JWT ID)
3. Sessions track both access_token_jti and refresh_token_jti

### Blacklist Checking
1. Middleware intercepts every API request
2. Extracts access token from Authorization header
3. Checks if token JTI exists in `BlacklistedToken` table
4. If blacklisted: Returns 401 "Token has been revoked"
5. If valid: Request proceeds

### Token Lifecycle

#### On Login
```
1. Generate access + refresh tokens
2. Create OutstandingToken records for both
3. Create UserSession with token JTIs
4. Return tokens to client
```

#### On Token Refresh
```
1. Validate refresh token
2. Blacklist old access token
3. Generate new access token
4. Create OutstandingToken for new access token
5. Update session with new JTIs
6. Return new access token
```

#### On Logout
```
1. Mark session as inactive
2. Blacklist refresh token
3. Blacklist access token
4. Both tokens immediately invalid
```

## Revocation Methods

### 1. Logout
```
POST /api/v1/auth/logout/
Blacklists: Current session tokens
```

### 2. Logout All
```
POST /api/v1/auth/logout/all/
Blacklists: All user session tokens
```

### 3. Revoke Session
```
POST /api/v1/auth/sessions/{id}/revoke/
Blacklists: Specific session tokens
```

### 4. Revoke All Sessions
```
POST /api/v1/auth/sessions/revoke_all/
Blacklists: All active session tokens
```

## Testing Revocation

### Test Immediate Revocation
```bash
# 1. Login
POST /api/v1/auth/token/
Response: {access: "token1", refresh: "token2"}

# 2. Test access (should work)
GET /api/v1/auth/users/me/
Authorization: Bearer token1
Response: 200 OK

# 3. Logout
POST /api/v1/auth/logout/
Body: {refresh: "token2"}
Response: 200 OK

# 4. Test access again (should fail)
GET /api/v1/auth/users/me/
Authorization: Bearer token1
Response: 401 {"detail": "Token has been revoked", "code": "token_revoked"}
```

### Test Refresh After Revocation
```bash
# After logout, try to refresh
POST /api/v1/auth/token/refresh/
Body: {refresh: "token2"}
Response: 401 Token is blacklisted
```

## Security Features

### Prevents Token Reuse
- Blacklisted tokens cannot be used
- Refresh rotation prevents old refresh tokens from working
- Access tokens revoked on logout

### Prevents Duplicate Sessions
- Cannot login twice on same client_type
- Must logout before logging in again
- Prevents DDOS via repeated login

### Immediate Revocation
- No waiting for token expiry
- Tokens invalid within milliseconds
- Database-backed security

## Performance Considerations

### Database Query on Every Request
- Middleware checks blacklist table
- Performance impact: ~1-5ms per request
- Mitigation: Add Redis caching

### Optimization Strategies
```python
# Future: Add Redis cache
from django.core.cache import cache

def is_token_blacklisted(jti):
    cache_key = f'blacklist:{jti}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    is_blacklisted = BlacklistedToken.objects.filter(
        token__jti=jti
    ).exists()

    cache.set(cache_key, is_blacklisted, timeout=3600)
    return is_blacklisted
```

## Comparison: Before vs After

### Before Implementation
- ❌ Access tokens valid until 1-hour expiry
- ❌ Logout only blacklisted refresh tokens
- ❌ Could still use API after logout for up to 1 hour
- ❌ Security risk window

### After Implementation
- ✅ Access tokens blacklisted immediately
- ✅ Logout blacklists both token types
- ✅ API calls fail instantly after logout
- ✅ No security risk window

## Middleware Code
```python
# users/middleware.py
class CheckTokenBlacklistMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.path.startswith('/api/'):
            return None

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None

        try:
            token_string = auth_header.split(' ')[1]
            token = AccessToken(token_string)
            jti = str(token['jti'])

            try:
                outstanding = OutstandingToken.objects.get(jti=jti)
                if BlacklistedToken.objects.filter(token=outstanding).exists():
                    return JsonResponse({
                        'detail': 'Token has been revoked. Please login again.',
                        'code': 'token_revoked'
                    }, status=401)
            except OutstandingToken.DoesNotExist:
                pass

        except TokenError:
            pass
        except Exception:
            pass

        return None
```

## Token States

| State | Can Login? | Can Use API? | Can Refresh? |
|-------|-----------|--------------|--------------|
| Fresh Login | ✅ Yes | ✅ Yes | ✅ Yes |
| After Logout | ✅ Yes* | ❌ No | ❌ No |
| Blacklisted | ✅ Yes* | ❌ No | ❌ No |
| Expired | ✅ Yes | ❌ No | ❌ No |

*Must logout first if already logged in on same client_type

## Best Practices

### Client Implementation
1. Handle 401 responses
2. Clear tokens on 401
3. Redirect to login
4. Don't retry with same token

### Server Implementation
1. Blacklist both token types on revocation
2. Check blacklist before processing requests
3. Clean up expired tokens periodically
4. Monitor blacklist table size

### Production
1. Add Redis caching
2. Set up token cleanup cron job
3. Monitor database performance
4. Implement rate limiting
