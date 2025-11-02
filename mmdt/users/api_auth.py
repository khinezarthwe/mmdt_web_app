"""
JWT Authentication views with session tracking support.

Supports authentication via username or email and tracks sessions
for multi-device support.
"""
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, inline_serializer
from drf_spectacular.types import OpenApiTypes

from .models import UserSession
from .serializers import UserDetailSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that supports email or username login
    and tracks device sessions.
    """

    @classmethod
    def get_token(cls, user):
        """Add custom claims to token."""
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token

    def validate(self, attrs):
        """Validate and authenticate user with username or email."""
        # Get username (which can be either username or email)
        login = attrs.get('username')
        password = attrs.get('password')

        # Try to authenticate with username first
        user = authenticate(username=login, password=password)

        # If authentication failed and login looks like email, try email
        if not user and '@' in login:
            try:
                user_obj = User.objects.get(email=login)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if not user:
            raise InvalidToken('Invalid username/email or password')

        # Check if user is active
        if not user.is_active:
            raise InvalidToken('User account is disabled')

        # Generate tokens
        refresh = self.get_token(user)
        access = refresh.access_token

        # Extract device/client info from request
        request = self.context.get('request')
        client_type = request.data.get('client_type', 'unknown')
        device_name = request.data.get('device_name', None)
        telegram_user_id = request.data.get('telegram_user_id', None)
        telegram_username = request.data.get('telegram_username', None)

        # Store session in database
        session = UserSession.objects.create(
            user=user,
            refresh_token_jti=str(refresh['jti']),
            access_token_jti=str(access['jti']),
            client_type=client_type,
            device_name=device_name,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Return tokens and user info
        return {
            'refresh': str(refresh),
            'access': str(access),
            'user': UserDetailSerializer(user).data,
            'session_id': session.id,
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    JWT token obtain view with session tracking.

    Accepts username or email for login and tracks device sessions.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Obtain JWT token pair",
        description="Login with username or email to obtain access and refresh tokens. "
                    "Optionally provide client information for session tracking.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'username': {
                        'type': 'string',
                        'description': 'Username or email address'
                    },
                    'password': {
                        'type': 'string',
                        'description': 'User password'
                    },
                    'client_type': {
                        'type': 'string',
                        'description': 'Client type (telegram_bot, website, mobile)',
                        'default': 'unknown'
                    },
                    'device_name': {
                        'type': 'string',
                        'description': 'Human-readable device name',
                        'nullable': True
                    },
                    'telegram_user_id': {
                        'type': 'integer',
                        'description': 'Telegram user ID (for bot authentication)',
                        'nullable': True
                    },
                    'telegram_username': {
                        'type': 'string',
                        'description': 'Telegram username',
                        'nullable': True
                    }
                },
                'required': ['username', 'password']
            }
        },
        responses={
            200: {
                'description': 'Login successful',
                'content': {
                    'application/json': {
                        'example': {
                            'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                            'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                            'user': {
                                'id': 1,
                                'username': 'john_doe',
                                'email': 'john@example.com',
                                'first_name': 'John',
                                'last_name': 'Doe'
                            },
                            'session_id': 123
                        }
                    }
                }
            },
            401: {'description': 'Invalid credentials'}
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    """JWT token refresh view."""

    @extend_schema(
        summary="Refresh access token",
        description="Use refresh token to obtain a new access token. "
                    "If token rotation is enabled, a new refresh token will also be provided.",
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    """
    Logout view that revokes the current session.
    """

    @extend_schema(
        summary="Logout and revoke session",
        description="Revokes the current refresh token and marks the session as inactive. "
                    "Note: The access token will remain valid until it expires (1 hour). "
                    "For immediate revocation, use logout/all/ or implement token blacklist checking.",
        request=inline_serializer(
            name='LogoutRequest',
            fields={
                'refresh': serializers.CharField(help_text='Refresh token to revoke'),
            }
        ),
        responses={
            200: inline_serializer(
                name='LogoutResponse',
                fields={
                    'message': serializers.CharField(),
                    'detail': serializers.CharField(),
                }
            ),
            400: {'description': 'Invalid token'}
        },
        tags=['Authentication']
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Decode refresh token to get JTI
            token = RefreshToken(refresh_token)
            refresh_jti = str(token['jti'])

            # Get the access token JTI from the refresh token payload
            access_jti = str(token.access_token['jti'])

            # Find and revoke session
            try:
                session = UserSession.objects.get(refresh_token_jti=refresh_jti)
                session.revoke()

                # Try to blacklist both tokens
                # Blacklist refresh token
                token.blacklist()

                # Blacklist access token if it exists in OutstandingToken
                try:
                    access_token_record = OutstandingToken.objects.filter(jti=access_jti).first()
                    if access_token_record:
                        BlacklistedToken.objects.get_or_create(token=access_token_record)
                except Exception:
                    pass  # Access token might not be in OutstandingToken table

            except UserSession.DoesNotExist:
                # Still try to blacklist the token even if session not found
                token.blacklist()

            return Response({
                'message': 'Logout successful',
                'detail': 'Session revoked and tokens blacklisted. Note: Access token remains valid until expiry.'
            }, status=status.HTTP_200_OK)

        except TokenError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'An error occurred during logout'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutAllView(APIView):
    """
    Logout from all devices by revoking all user sessions.
    """

    @extend_schema(
        summary="Logout from all devices",
        description="Revokes all active sessions for the current user and blacklists all refresh tokens. "
                    "Note: Existing access tokens will remain valid until they expire.",
        responses={
            200: inline_serializer(
                name='LogoutAllResponse',
                fields={
                    'message': serializers.CharField(),
                    'revoked_sessions': serializers.IntegerField(),
                }
            ),
            401: {'description': 'Authentication required'}
        },
        tags=['Authentication']
    )
    def post(self, request):
        user = request.user

        # Get all active sessions
        sessions = UserSession.objects.filter(user=user, is_active=True)
        count = sessions.count()

        # Revoke all sessions and blacklist tokens
        for session in sessions:
            session.revoke()

            # Try to blacklist the refresh token
            try:
                token_record = OutstandingToken.objects.filter(jti=session.refresh_token_jti).first()
                if token_record:
                    BlacklistedToken.objects.get_or_create(token=token_record)
            except Exception:
                pass

            # Try to blacklist the access token
            try:
                if session.access_token_jti:
                    access_token_record = OutstandingToken.objects.filter(jti=session.access_token_jti).first()
                    if access_token_record:
                        BlacklistedToken.objects.get_or_create(token=access_token_record)
            except Exception:
                pass

        return Response({
            'message': f'Logged out from {count} device(s)',
            'revoked_sessions': count
        }, status=status.HTTP_200_OK)
