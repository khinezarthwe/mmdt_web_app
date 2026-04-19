"""
API views for authentication and user management.
"""
import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.views.generic import TemplateView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from blog.models import Cohort, SubscriberRequest
from blog.google_api_utils import get_or_create_renewal_url
from users.models import UserProfile

from .serializers import (
    RenewalRequestSerializer,
    TokenRequestSerializer,
)


logger = logging.getLogger(__name__)
User = get_user_model()


class AdminTokenView(APIView):
    """
    Issue short-lived access tokens for admin users only.

    POST /api/auth/token
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = TokenRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("Token request failed: %s", serializer.errors)
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)

        if user is None or not user.is_staff:
            logger.warning(
                "Token request failed for username=%s: invalid credentials or not admin",
                username
            )
            return Response(
                {"detail": "Invalid credentials or not an admin user."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = AccessToken.for_user(user)
        expires_in = int(
            settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
        )

        logger.info("Token issued for admin user=%s", username)
        return Response({
            "access_token": str(access_token),
            "expires_in": expires_in,
            "token_type": "Bearer",
        })


class UserDetailByEmailView(APIView):
    """
    Get user details by email.

    GET /api/users?email=user@example.com

    Requires JWT authentication with admin privileges.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            logger.warning("User detail request failed: missing email parameter")
            return Response(
                {"detail": "Query parameter 'email' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.debug("User detail lookup for email=%s", email)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.info("User detail lookup failed: user not found for email=%s", email)
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except User.MultipleObjectsReturned:
            logger.error("Multiple users found for email=%s", email)
            return Response(
                {"detail": "Multiple users found with this email address. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            profile = user.profile
            enddate = profile.expiry_date
        except UserProfile.DoesNotExist:
            enddate = None

        logger.info("User detail returned for email=%s, enddate=%s", email, enddate)
        return Response({
            "email": user.email,
            "enddate": enddate,
        })


class UserDetailByTelegramView(APIView):
    """
    Get user details by telegram username.

    GET /api/users/telegram?telegram_name=username

    Requires JWT authentication with admin privileges.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        telegram_name = request.query_params.get("telegram_name")
        if not telegram_name:
            logger.warning("User detail request failed: missing telegram_name parameter")
            return Response(
                {"detail": "Query parameter 'telegram_name' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Clean telegram name (remove @ prefix if present)
        name_clean = telegram_name.lstrip('@')
        logger.debug("User detail lookup for telegram_name=%s", name_clean)

        try:
            subscriber = SubscriberRequest.objects.filter(
                telegram_username__iexact=name_clean
            ).first() or SubscriberRequest.objects.filter(
                telegram_username__iexact=f'@{name_clean}'
            ).first()

            if not subscriber:
                logger.info("User detail lookup failed: subscriber not found for telegram=%s", telegram_name)
                return Response(
                    {"detail": "User not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Find the user associated with this subscriber
            user = User.objects.filter(email=subscriber.email).first()
            if not user:
                logger.info("User detail lookup failed: user not found for telegram=%s", telegram_name)
                return Response(
                    {"detail": "User not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        except Exception as e:
            logger.error("Error looking up user by telegram: %s", e)
            return Response(
                {"detail": "An error occurred while looking up the user."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            profile = user.profile
            enddate = profile.expiry_date
        except UserProfile.DoesNotExist:
            enddate = None

        registration_open = Cohort.get_active_cohort() is not None

        logger.info("User detail returned for telegram=%s, email=%s, enddate=%s", telegram_name, user.email, enddate)
        return Response({
            "email": user.email,
            "enddate": enddate,
            "registration_open": registration_open,
        })


class UserRenewalRequestView(APIView):
    """
    Request membership renewal.

    POST /api/user/request_renew

    Submit a renewal request for an existing active user.
    Requires JWT authentication with admin privileges.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = RenewalRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("Renewal request validation failed: %s", serializer.errors)
            first_error = next(iter(serializer.errors.values()))[0]
            return Response(
                {"status": "error", "message": str(first_error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # active_cohort = Cohort.get_active_cohort()
        # if not active_cohort:
        #     logger.info("Renewal request rejected: no active cohort registration window is open")
        #     return Response(
        #         {"status": "error", "message": "Registration is currently closed. No active cohort registration window is open."},
        #         status=status.HTTP_403_FORBIDDEN,
        #     )

        email = serializer.validated_data.get("email")
        telegram_name = serializer.validated_data.get("telegram_name")
        plan = serializer.validated_data["plan"]

        logger.debug(
            "Renewal request received: email=%s, telegram_name=%s, plan=%s",
            email, telegram_name, plan
        )

        user = self._get_user(email, telegram_name)
        if isinstance(user, Response):
            return user

        if not user.is_active:
            logger.info("Renewal request failed: user is not active (user_id=%s)", user.pk)
            return Response(
                {"status": "error", "message": "User account is not active."},
                status=status.HTTP_403_FORBIDDEN,
            )

        profile, subscriber = self._get_profile_and_subscriber(user)
        if isinstance(profile, Response):
            return profile

        if profile.renewal_requested:
            logger.info("Renewal request already pending for user_id=%s", user.pk)
            return Response(
                {
                    "status": "pending",
                    "message": "Renewal request already submitted. Please wait for admin approval.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        upload_url, is_existing = get_or_create_renewal_url(
            subscriber, plan, user_profile=profile
        )

        if not upload_url:
            logger.error("Failed to generate upload URL for user_id=%s", user.pk)
            return Response(
                {"status": "error", "message": "Failed to generate upload URL. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if is_existing:
            logger.info("Found existing URL in spreadsheet for user_id=%s", user.pk)
        else:
            logger.info("Created new folder and logged to spreadsheet for user_id=%s", user.pk)

        updated = UserProfile.objects.filter(
            pk=profile.pk,
            renewal_requested=False,
        ).update(
            renewal_requested=True,
            renewal_plan=plan,
        )

        if updated == 0:
            logger.info("Concurrent renewal request detected for user_id=%s", user.pk)
            return Response(
                {
                    "status": "pending",
                    "message": "Renewal request already submitted. Please wait for admin approval.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        logger.info("Renewal request submitted: user_id=%s, plan=%s", user.pk, plan)
        return Response(
            {
                "status": "success",
                "message": "Renewal request received",
                "upload_url": upload_url,
            },
            status=status.HTTP_200_OK,
        )

    def _get_user(self, email, telegram_name):
        """Look up user by email and verify telegram_name matches."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.info(
                "Renewal request failed: user not found (email=%s, telegram=%s)",
                email, telegram_name
            )
            return Response(
                {"status": "error", "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except User.MultipleObjectsReturned:
            logger.error("Multiple users found for email=%s", email)
            return Response(
                {"status": "error", "message": "Multiple users found. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Verify telegram_name matches for consistency
        try:
            profile = user.profile
            subscriber = profile.subscriber_request
            if subscriber:
                stored_telegram = subscriber.telegram_username or ''
                provided_telegram = telegram_name.lstrip('@')
                stored_telegram_clean = stored_telegram.lstrip('@')

                if stored_telegram_clean.lower() != provided_telegram.lower():
                    logger.warning(
                        "Telegram name mismatch: stored=%s, provided=%s (email=%s)",
                        stored_telegram, telegram_name, email
                    )
                    return Response(
                        {"status": "error", "message": "Email and telegram_name do not match."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        except (AttributeError, Exception) as e:
            logger.debug("Could not verify telegram_name: %s", e)

        return user

    def _get_profile_and_subscriber(self, user):
        """Get user profile and linked subscriber request."""
        try:
            profile = UserProfile.objects.select_related(
                'current_cohort',
                'subscriber_request',
                'subscriber_request__cohort',
            ).get(user_id=user.pk)
            subscriber = profile.subscriber_request
            if not subscriber:
                raise UserProfile.DoesNotExist
            return profile, subscriber
        except (UserProfile.DoesNotExist, AttributeError):
            logger.info(
                "Renewal request failed: no subscriber request linked (user_id=%s)",
                user.pk
            )
            return Response(
                {"status": "error", "message": "No subscription record found for this user."},
                status=status.HTTP_404_NOT_FOUND,
            ), None


class SwaggerUIView(TemplateView):
    """Render Swagger UI that uses the OpenAPI schema endpoint."""
    template_name = "swagger-ui.html"
