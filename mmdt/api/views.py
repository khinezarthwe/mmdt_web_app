import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.views.generic import TemplateView
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from users.models import UserProfile
from blog.models import SubscriberRequest
from blog.google_api_utils import get_or_create_renewal_url


logger = logging.getLogger(__name__)

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
            logger.warning("Token request failed: missing username or password")
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)

        if user is None or not user.is_staff:
            logger.warning("Token request failed for username=%s: invalid credentials or not admin", username)
            return Response(
                {"detail": "Invalid credentials or not an admin user."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = AccessToken.for_user(user)

        expires_in = int(
            settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
        )

        logger.info("Token issued for admin user=%s", username)
        return Response(
            {
                "access_token": str(access_token),
                "expires_in": expires_in,
                "token_type": "Bearer",
            }
        )


class UserDetailByEmailView(APIView):
    """
    Get user details by email.

    Retrieve a user's email and subscription expiry date. Looks up the user
    in the User model and returns their profile's expiry_date if available.

    Authentication:
        - Requires a valid JWT access token in the `Authorization: Bearer <token>` header.
        - Only admin users (is_staff=True) are allowed to access this endpoint.

    ---
    security:
      - bearerAuth: []
    parameters:
      - name: email
        in: query
        required: true
        schema:
          type: string
          format: email
        description: The user's email address to look up
        example: user@example.com
    responses:
      200:
        description: User details retrieved successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                  description: User's email address
                  example: user@example.com
                enddate:
                  type: string
                  format: date-time
                  nullable: true
                  description: Subscription expiry date (ISO 8601) or null if no profile
                  example: "2025-12-31T23:59:59Z"
      400:
        description: Bad request - missing email query parameter
        content:
          application/json:
            schema:
              type: object
              properties:
                detail:
                  type: string
                  example: "Query parameter 'email' is required."
      401:
        description: Unauthorized - missing or invalid JWT token
      403:
        description: Forbidden - authenticated user is not an admin
      404:
        description: User not found
        content:
          application/json:
            schema:
              type: object
              properties:
                detail:
                  type: string
                  example: User not found.
      500:
        description: Server error - multiple users found with same email
        content:
          application/json:
            schema:
              type: object
              properties:
                detail:
                  type: string
                  example: Multiple users found with this email address. Please contact support.
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
        except UserProfile.DoesNotExist:
            profile = None

        enddate = profile.expiry_date if profile else None
        telegram_username = profile.telegram_username if profile else None

        logger.info("User detail returned for email=%s, enddate=%s", email, enddate)
        return Response(
            {
                "email": user.email,
                "enddate": enddate,
                "telegram_username": telegram_username,
            }
        )


class UserRenewalRequestView(APIView):
    """
    Request membership renewal.

    Submit a renewal request for an existing active user. Identify the user
    by either `email` or `telegram_name` (at least one is required).
    The user must exist in the User model and have is_active=True.

    Behavior:
        1. Looks up user in the User model (not SubscriberRequest)
        2. Verifies user account is active (is_active=True)
        3. Checks Google Sheet for existing entry by email:
           - If found: returns existing upload URL from the sheet
           - If not found: creates new Google Drive folder and logs to sheet
        4. Marks renewal_requested=True on the linked SubscriberRequest

    Authentication:
        - Requires a valid JWT access token in the `Authorization: Bearer <token>` header.
        - Only admin users (is_staff=True) are allowed to access this endpoint.

    ---
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
                format: email
                description: User's email address (looked up in User model)
                example: user@example.com
              telegram_name:
                type: string
                description: User's Telegram username (looked up via UserProfile)
                example: username123
              plan:
                type: string
                enum: [6month, 12month]
                description: Subscription plan duration for renewal
                example: 6month
            required:
              - plan
    responses:
      200:
        description: Renewal request submitted successfully. Returns upload URL (existing from sheet or newly created).
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                message:
                  type: string
                  example: Renewal request received
                upload_url:
                  type: string
                  format: uri
                  description: Google Drive folder URL for payment proof upload
                  example: https://drive.google.com/drive/folders/...
      400:
        description: Bad request - missing or invalid parameters
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: error
                message:
                  type: string
                  example: Plan is required.
      401:
        description: Unauthorized - missing or invalid JWT token
      403:
        description: Forbidden - authenticated user is not an admin, or target user account is not active
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: error
                message:
                  type: string
                  example: User account is not active.
      404:
        description: User not found or no subscription record linked
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: error
                message:
                  type: string
                  example: User not found.
      409:
        description: Renewal request already pending
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: pending
                message:
                  type: string
                  example: Renewal request already submitted. Please wait for admin approval.
      500:
        description: Server error - failed to generate upload URL
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: error
                message:
                  type: string
                  example: Failed to generate upload URL. Please try again later.
    """

    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        email = request.data.get("email")
        telegram_name = request.data.get("telegram_name")
        plan = request.data.get("plan")

        logger.debug("Renewal request received: email=%s, telegram_name=%s, plan=%s", email, telegram_name, plan)

        if not plan:
            logger.warning("Renewal request failed: missing plan")
            return Response(
                {"status": "error", "message": "Plan is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_plans = dict(SubscriberRequest.PLAN_CHOICES).keys()
        if plan not in valid_plans:
            logger.warning("Renewal request failed: invalid plan=%s", plan)
            return Response(
                {
                    "status": "error",
                    "message": "Invalid plan. Must be one of: {}.".format(", ".join(valid_plans)),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not email and not telegram_name:
            logger.warning("Renewal request failed: missing email and telegram_name")
            return Response(
                {"status": "error", "message": "Either email or telegram_name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if email:
                user = User.objects.get(email=email)
            else:
                name_clean = telegram_name.lstrip('@')
                qs = User.objects.filter(
                    Q(profile__subscriber_request__telegram_username=name_clean) |
                    Q(profile__subscriber_request__telegram_username=f'@{name_clean}')
                )
                if not qs.exists():
                    raise User.DoesNotExist
                if qs.count() > 1:
                    raise User.MultipleObjectsReturned
                user = qs.first()
        except User.DoesNotExist:
            logger.info("Renewal request failed: user not found (email=%s, telegram=%s)", email, telegram_name)
            return Response(
                {"status": "error", "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except User.MultipleObjectsReturned:
            logger.error("Multiple users found for telegram_name=%s", telegram_name)
            return Response(
                {"status": "error", "message": "Multiple users found. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not user.is_active:
            logger.info("Renewal request failed: user is not active (user_id=%s)", user.pk)
            return Response(
                {"status": "error", "message": "User account is not active."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            profile = user.profile
            subscriber = profile.subscriber_request
            if not subscriber:
                raise UserProfile.DoesNotExist
        except (UserProfile.DoesNotExist, AttributeError):
            logger.info("Renewal request failed: no subscriber request linked (user_id=%s)", user.pk)
            return Response(
                {"status": "error", "message": "No subscription record found for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if profile.renewal_requested:
            logger.info("Renewal request already pending for user_id=%s", user.pk)
            existing_url, _ = get_or_create_renewal_url(subscriber, plan)
            return Response(
                {
                    "status": "pending",
                    "message": "Renewal request already submitted. Please wait for admin approval.",
                    "upload_url": existing_url or "",
                },
                status=status.HTTP_409_CONFLICT,
            )

        upload_url, is_existing = get_or_create_renewal_url(subscriber, plan)

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

        # Atomically mark renewal as requested on UserProfile
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


class SwaggerUIView(TemplateView):
    """Render Swagger UI that uses the OpenAPI schema endpoint."""

    template_name = "swagger-ui.html"

