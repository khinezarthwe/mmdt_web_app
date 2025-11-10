from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.exceptions import TokenError
from django.http import JsonResponse


class CheckTokenBlacklistMiddleware(MiddlewareMixin):
    """Middleware to check if JWT access token is blacklisted."""

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
                outstanding_token = OutstandingToken.objects.get(jti=jti)
                if BlacklistedToken.objects.filter(token=outstanding_token).exists():
                    return JsonResponse(
                        {
                            'detail': 'Token has been revoked. Please login again.',
                            'code': 'token_revoked'
                        },
                        status=401
                    )
            except OutstandingToken.DoesNotExist:
                pass

        except TokenError:
            pass
        except Exception:
            pass

        return None
