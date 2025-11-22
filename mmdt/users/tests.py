from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from users.models import UserProfile


User = get_user_model()


class AuthTokenAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_password = "admin-pass-123"
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password=self.admin_password,
        )

    def test_admin_can_obtain_token(self):
        response = self.client.post(
            "/auth/token",
            {"username": "admin", "password": self.admin_password},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.data)
        self.assertIn("expires_in", response.data)
        self.assertEqual(response.data.get("token_type"), "Bearer")

        # Basic sanity check on expires_in (should be around 15 minutes)
        self.assertGreaterEqual(response.data["expires_in"], 800)
        self.assertLessEqual(response.data["expires_in"], 1000)

    def test_non_admin_cannot_obtain_token(self):
        user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="user-pass-123",
        )
        self.assertFalse(user.is_staff)

        response = self.client.post(
            "/auth/token",
            {"username": "user", "password": "user-pass-123"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)


class UserDetailByEmailAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin-pass-123",
        )

        # Create a regular user with a profile and expiry date
        # Note: UserProfile is automatically created by signal when User is created
        self.user = User.objects.create_user(
            username="testuser",
            email="user@example.com",
            password="user-pass-123",
        )
        expiry_date = timezone.now() + timedelta(days=30)
        # Update the profile that was automatically created by the signal
        self.profile = self.user.profile
        self.profile.expiry_date = expiry_date
        self.profile.save()

        # Authenticate as admin using a JWT access token
        access_token = AccessToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    def test_get_user_by_email_returns_email_and_enddate(self):
        response = self.client.get("/api/users", {"email": "user@example.com"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "user@example.com")
        self.assertIsNotNone(response.data["enddate"])

    def test_missing_email_query_param_returns_400(self):
        response = self.client.get("/api/users")

        self.assertEqual(response.status_code, 400)

    def test_unknown_email_returns_404(self):
        response = self.client.get("/api/users", {"email": "unknown@example.com"})

        self.assertEqual(response.status_code, 404)


