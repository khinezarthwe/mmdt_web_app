from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.views.generic import TemplateView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from users.models import UserProfile
from blog.models import SubscriberRequest
from blog.google_api_utils import get_folder_upload_url


User = get_user_model()


class AdminTokenView(APIView):
    """
    Issue short-lived access tokens for admin users only.

    POST /auth/token
    Request body:
        {
            "username": "<admin username>",
            "password": "<admin password>"
        }
    Response:
        {
            "access_token": "<jwt>",
            "expires_in": 900,
            "token_type": "Bearer"
        }
    """

    # Login endpoint – we validate credentials manually.
    authentication_classes: list = []
    permission_classes: list = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)

        if user is None or not user.is_staff:
            return Response(
                {"detail": "Invalid credentials or not an admin user."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = AccessToken.for_user(user)

        expires_in = int(
            settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
        )

        return Response(
            {
                "access_token": str(access_token),
                "expires_in": expires_in,
                "token_type": "Bearer",
            }
        )


class UserDetailByEmailView(APIView):
    """
    Retrieve a user's email and subscription end date (expiry_date) by email.

    Authentication:
        - Requires a valid JWT access token in the `Authorization: Bearer <token>` header.
        - Only admin users (is_staff=True) are allowed to access this endpoint.

    GET /api/users

    Query parameters:
        - email (string, required): The user's email address to look up.

    Successful response (200):
        {
            "email": "mmdt@example.com",
            "enddate": "2025-12-31T23:59:59Z"  # ISO 8601 datetime or null
        }

    Error responses:
        - 400: Missing `email` query parameter.
        - 401: Missing or invalid JWT access token.
        - 403: Authenticated user is not an admin.
        - 404: No user found with the given email.
    """

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            return Response(
                {"detail": "Query parameter 'email' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except User.MultipleObjectsReturned:
            return Response(
                {"detail": "Multiple users found with this email address. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = None

        enddate = profile.expiry_date if profile else None

        return Response(
            {
                "email": user.email,
                "enddate": enddate,
            }
        )


class UserRenewalRequestView(APIView):
    """
    Request membership renewal for an existing subscriber.

    POST /api/user/request_renew

    Request body (one of):
        {
            "email": "user@example.com",
            "plan": "6month"
        }
        OR
        {
            "telegram_name": "username123",
            "plan": "6month"
        }

    Response (success):
        {
            "status": "success",
            "message": "Renewal request received",
            "upload_url": "https://drive.google.com/..."
        }

    Response (error):
        {
            "status": "error",
            "message": "User not found"
        }
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        telegram_name = request.data.get("telegram_name")
        plan = request.data.get("plan")

        if not plan:
            return Response(
                {"status": "error", "message": "Plan is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if plan not in ['6month', 'annual']:
            return Response(
                {"status": "error", "message": "Invalid plan. Must be '6month' or 'annual'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not email and not telegram_name:
            return Response(
                {"status": "error", "message": "Either email or telegram_name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if email:
                subscriber = SubscriberRequest.objects.get(email=email)
            else:
                subscriber = SubscriberRequest.objects.get(telegram_username=telegram_name)
        except SubscriberRequest.DoesNotExist:
            return Response(
                {"status": "error", "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except SubscriberRequest.MultipleObjectsReturned:
            return Response(
                {"status": "error", "message": "Multiple users found. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        upload_url = get_folder_upload_url(subscriber)

        if not upload_url:
            return Response(
                {"status": "error", "message": "Failed to generate upload URL. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "status": "success",
                "message": "Renewal request received",
                "upload_url": upload_url,
            },
            status=status.HTTP_200_OK,
        )


class SwaggerUIView(TemplateView):
    """Render Swagger UI that uses the OpenAPI schema endpoint."""

    template_name = "swagger-ui.html"

