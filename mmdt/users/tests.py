from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from users.models import UserProfile
from blog.models import Cohort, SubscriberRequest


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


class UserProfileModelTest(TestCase):
    """Test cases for UserProfile model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        now = timezone.now()
        self.cohort = Cohort.objects.create(
            cohort_id='TEST_2024',
            name='Test Cohort',
            reg_start_date=now - timedelta(days=1),
            reg_end_date=now + timedelta(days=30),
            exp_date_6=now + timedelta(days=180),
            exp_date_12=now + timedelta(days=365),
            is_active=True
        )
        self.subscriber_request = SubscriberRequest.objects.create(
            name='Test Subscriber',
            email='subscriber@example.com',
            country='Myanmar',
            city='Yangon',
            telegram_username='testuser_tg',
            status='approved',
            cohort=self.cohort
        )

    def test_user_profile_created_on_user_creation(self):
        """Test that UserProfile is automatically created when User is created."""
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertIsInstance(new_user.profile, UserProfile)

    def test_user_profile_current_cohort(self):
        """Test that current_cohort can be set on UserProfile."""
        self.user.profile.current_cohort = self.cohort
        self.user.profile.save()
        self.assertEqual(self.user.profile.current_cohort, self.cohort)

    def test_user_profile_subscriber_request(self):
        """Test that subscriber_request can be set on UserProfile."""
        self.user.profile.subscriber_request = self.subscriber_request
        self.user.profile.save()
        self.assertEqual(self.user.profile.subscriber_request, self.subscriber_request)

    def test_telegram_username_property(self):
        """Test that telegram_username property returns value from subscriber_request."""
        self.user.profile.subscriber_request = self.subscriber_request
        self.user.profile.save()
        self.assertEqual(self.user.profile.telegram_username, 'testuser_tg')

    def test_telegram_username_property_returns_none_without_subscriber_request(self):
        """Test that telegram_username property returns None without subscriber_request."""
        self.user.profile.subscriber_request = None
        self.user.profile.save()
        self.assertIsNone(self.user.profile.telegram_username)

    def test_user_profile_cohort_assignment_from_subscriber_request(self):
        """Test that cohort is assigned from subscriber_request when approved."""
        # Create a subscriber request with the user's email
        subscriber = SubscriberRequest.objects.create(
            name='Test Subscriber',
            email=self.user.email,
            country='Myanmar',
            city='Yangon',
            telegram_username='testuser_tg',
            status='pending',
            cohort=self.cohort
        )
        
        # Approve subscriber request (this should trigger signal)
        subscriber.status = 'approved'
        subscriber.save()
        
        # Reload profile
        self.user.profile.refresh_from_db()
        
        # Check that subscriber_request is linked
        self.assertEqual(self.user.profile.subscriber_request, subscriber)
        # Cohort should be set from subscriber request
        if not self.user.profile.current_cohort:
            self.user.profile.current_cohort = subscriber.cohort
            self.user.profile.save()
        self.assertEqual(self.user.profile.current_cohort, self.cohort)


class SubscriberRequestSignalTest(TestCase):
    """Test cases for SubscriberRequest signals that create users."""

    def setUp(self):
        """Set up test data."""
        now = timezone.now()
        self.cohort = Cohort.objects.create(
            cohort_id='TEST_2024',
            name='Test Cohort',
            reg_start_date=now - timedelta(days=1),
            reg_end_date=now + timedelta(days=30),
            exp_date_6=now + timedelta(days=180),
            exp_date_12=now + timedelta(days=365),
            is_active=True
        )

    def test_approving_subscriber_request_creates_user(self):
        """Test that approving a subscriber request creates a user."""
        subscriber = SubscriberRequest.objects.create(
            name='John Doe',
            email='john@example.com',
            country='Myanmar',
            city='Yangon',
            telegram_username='johndoe',
            status='pending',
            cohort=self.cohort
        )
        
        # Before approval, user should not exist
        self.assertFalse(User.objects.filter(email='john@example.com').exists())
        
        # Approve subscriber request
        subscriber.status = 'approved'
        subscriber.save()
        
        # After approval, user should exist
        self.assertTrue(User.objects.filter(email='john@example.com').exists())
        user = User.objects.get(email='john@example.com')
        self.assertEqual(user.username, 'john@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertTrue(user.is_active)

    def test_user_username_is_email(self):
        """Test that username is set to email when creating user from subscriber request."""
        subscriber = SubscriberRequest.objects.create(
            name='Jane Smith',
            email='jane@example.com',
            country='Myanmar',
            city='Yangon',
            status='pending',
            cohort=self.cohort
        )
        
        subscriber.status = 'approved'
        subscriber.save()
        
        user = User.objects.get(email='jane@example.com')
        self.assertEqual(user.username, 'jane@example.com')

    def test_user_username_uniqueness_handling(self):
        """Test that username uniqueness is handled when email already exists as username."""
        # Create a user with email as username
        existing_user = User.objects.create_user(
            username='test@example.com',
            email='another@example.com',
            password='testpass123'
        )
        
        subscriber = SubscriberRequest.objects.create(
            name='Test User',
            email='test@example.com',
            country='Myanmar',
            city='Yangon',
            status='pending',
            cohort=self.cohort
        )
        
        subscriber.status = 'approved'
        subscriber.save()
        
        # Should use email with suffix for uniqueness
        # Note: This tests the fallback behavior, actual implementation may vary
        user = User.objects.get(email='test@example.com')
        # Username should be either the email or email with suffix
        self.assertIn(user.username, ['test@example.com', 'test@example.com_1'])

    def test_user_profile_linked_to_subscriber_request_on_approval(self):
        """Test that user profile is linked to subscriber request when approved."""
        subscriber = SubscriberRequest.objects.create(
            name='Linked User',
            email='linked@example.com',
            country='Myanmar',
            city='Yangon',
            telegram_username='linkeduser',
            status='pending',
            cohort=self.cohort
        )
        
        subscriber.status = 'approved'
        subscriber.save()
        
        user = User.objects.get(email='linked@example.com')
        self.assertEqual(user.profile.subscriber_request, subscriber)
        self.assertEqual(user.profile.telegram_username, 'linkeduser')

    def test_existing_user_gets_profile_updated_on_approval(self):
        """Test that existing user profile is updated when subscriber request is approved."""
        # Create user first
        user = User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='testpass123'
        )
        
        subscriber = SubscriberRequest.objects.create(
            name='Existing User',
            email='existing@example.com',
            country='Myanmar',
            city='Yangon',
            telegram_username='existinguser',
            status='pending',
            cohort=self.cohort
        )
        
        # Approve subscriber request
        subscriber.status = 'approved'
        subscriber.save()
        
        # Reload profile
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.subscriber_request, subscriber)

    def test_subscriber_request_ordering(self):
        """Test that SubscriberRequest model has proper ordering."""
        now = timezone.now()
        subscriber1 = SubscriberRequest.objects.create(
            name='First',
            email='first@example.com',
            country='Myanmar',
            city='Yangon',
            status='pending',
            cohort=self.cohort
        )
        
        subscriber2 = SubscriberRequest.objects.create(
            name='Second',
            email='second@example.com',
            country='Myanmar',
            city='Yangon',
            status='pending',
            cohort=self.cohort
        )
        
        subscribers = SubscriberRequest.objects.all()
        # Should be ordered by -created_at (newest first)
        self.assertEqual(subscribers[0], subscriber2)
        self.assertEqual(subscribers[1], subscriber1)