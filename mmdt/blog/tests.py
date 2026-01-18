from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from .models import Post, Comment, SubscriberRequest, Cohort
from .forms import CommentForm, SubscriberRequestForm, FeedbackAnalyzerForm


class PostModelTest(TestCase):
    """Test cases for Post model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            content='This is a test post content.',
            status=1
        )
    
    def test_post_creation(self):
        """Test post creation with required fields."""
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.slug, 'test-post')
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.content, 'This is a test post content.')
        self.assertEqual(self.post.status, 1)
        self.assertFalse(self.post.subscribers_only)
        self.assertEqual(self.post.view_count, 0)
    
    def test_post_str_representation(self):
        """Test string representation of Post."""
        self.assertEqual(str(self.post), 'Test Post')
    
    def test_post_ordering(self):
        """Test that posts are ordered by created_on descending."""
        post2 = Post.objects.create(
            title='Second Post',
            slug='second-post',
            author=self.user,
            content='Second post content.',
            status=1
        )
        posts = Post.objects.all()
        self.assertEqual(posts[0], post2)  # Most recent first
        self.assertEqual(posts[1], self.post)
    
    def test_post_default_values(self):
        """Test default values for Post fields."""
        post = Post.objects.create(
            title='Default Test',
            slug='default-test',
            author=self.user,
            content='Default content.'
        )
        self.assertEqual(post.status, 0)  # Draft
        self.assertFalse(post.subscribers_only)
        self.assertEqual(post.view_count, 0)
        self.assertFalse(post.image)  # ImageField returns False when empty


class CommentModelTest(TestCase):
    """Test cases for Comment model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            content='This is a test post content.',
            status=1
        )
        self.comment = Comment.objects.create(
            post=self.post,
            name='Test Commenter',
            email='commenter@example.com',
            body='This is a test comment.',
            active=True
        )
    
    def test_comment_creation(self):
        """Test comment creation with required fields."""
        self.assertEqual(self.comment.post, self.post)
        self.assertEqual(self.comment.name, 'Test Commenter')
        self.assertEqual(self.comment.email, 'commenter@example.com')
        self.assertEqual(self.comment.body, 'This is a test comment.')
        self.assertTrue(self.comment.active)
    
    def test_comment_str_representation(self):
        """Test string representation of Comment."""
        expected = 'Comment This is a test comment. by Test Commenter'
        self.assertEqual(str(self.comment), expected)
    
    def test_comment_ordering(self):
        """Test that comments are ordered by created_on ascending."""
        comment2 = Comment.objects.create(
            post=self.post,
            name='Second Commenter',
            email='second@example.com',
            body='Second comment.',
            active=True
        )
        comments = Comment.objects.all()
        self.assertEqual(comments[0], self.comment)  # First created
        self.assertEqual(comments[1], comment2)  # Second created
    
    def test_comment_default_active(self):
        """Test default value for active field."""
        comment = Comment.objects.create(
            post=self.post,
            name='Inactive Commenter',
            email='inactive@example.com',
            body='Inactive comment.'
        )
        self.assertFalse(comment.active)  # Default is False


class SubscriberRequestModelTest(TestCase):
    """Test cases for SubscriberRequest model."""

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
        self.subscriber = SubscriberRequest.objects.create(
            name='Test Subscriber',
            email='subscriber@example.com',
            country='Myanmar',
            city='Yangon',
            job_title='Data Scientist',
            telegram_username='testuser',
            plan='6month'
        )
    
    def test_subscriber_request_creation(self):
        """Test subscriber request creation with required fields."""
        self.assertEqual(self.subscriber.name, 'Test Subscriber')
        self.assertEqual(self.subscriber.email, 'subscriber@example.com')
        self.assertEqual(self.subscriber.country, 'Myanmar')
        self.assertEqual(self.subscriber.city, 'Yangon')
        self.assertEqual(self.subscriber.job_title, 'Data Scientist')
        self.assertEqual(self.subscriber.telegram_username, 'testuser')
        self.assertEqual(self.subscriber.plan, '6month')
        self.assertEqual(self.subscriber.status, 'pending')
        self.assertFalse(self.subscriber.free_waiver)
    
    def test_subscriber_request_str_representation(self):
        """Test string representation of SubscriberRequest."""
        expected = 'Test Subscriber - subscriber@example.com'
        self.assertEqual(str(self.subscriber), expected)
    
    def test_calculate_expiry_date_6month(self):
        """Test expiry date calculation for 6-month plan uses cohort date."""
        expiry = self.subscriber.calculate_expiry_date()
        self.assertEqual(expiry, self.cohort.exp_date_6)

    def test_calculate_expiry_date_annual(self):
        """Test expiry date calculation for annual plan uses cohort date."""
        subscriber = SubscriberRequest.objects.create(
            name='Annual Subscriber',
            email='annual@example.com',
            country='Myanmar',
            city='Yangon',
            plan='annual'
        )
        expiry = subscriber.calculate_expiry_date()
        self.assertEqual(expiry, self.cohort.exp_date_12)
    
    def test_automatic_expiry_date_setting(self):
        """Test that expiry date is automatically set on save."""
        subscriber = SubscriberRequest.objects.create(
            name='Auto Expiry',
            email='auto@example.com',
            country='Myanmar',
            city='Yangon',
            plan='6month'
        )
        self.assertIsNotNone(subscriber.expiry_date)
    
    def test_unique_email_constraint(self):
        """Test that emails must be unique across all subscriber requests."""
        with self.assertRaises(Exception):  # IntegrityError
            SubscriberRequest.objects.create(
                name='Duplicate Email',
                email='subscriber@example.com',  # Same email as setUp
                country='Myanmar',
                city='Yangon'
            )

    def test_telegram_username_optional(self):
        """Test that telegram_username is optional."""
        subscriber = SubscriberRequest.objects.create(
            name='No Telegram',
            email='notelegram@example.com',
            country='Myanmar',
            city='Yangon',
            plan='6month'
        )
        self.assertIsNone(subscriber.telegram_username)
    
    def test_telegram_username_saved(self):
        """Test that telegram_username is saved correctly."""
        subscriber = SubscriberRequest.objects.create(
            name='With Telegram',
            email='withtelegram@example.com',
            country='Myanmar',
            city='Yangon',
            telegram_username='myusername',
            plan='6month'
        )
        self.assertEqual(subscriber.telegram_username, 'myusername')
    
    def test_subscriber_request_ordering(self):
        """Test that SubscriberRequest is ordered by created_at descending (newest first)."""
        subscriber2 = SubscriberRequest.objects.create(
            name='Second Subscriber',
            email='second@example.com',
            country='Myanmar',
            city='Yangon',
            plan='6month'
        )
        
        subscribers = SubscriberRequest.objects.all()
        # Should be ordered by -created_at (newest first)
        self.assertEqual(subscribers[0], subscriber2)
        self.assertEqual(subscribers[1], self.subscriber)


class CommentFormTest(TestCase):
    """Test cases for CommentForm."""
    
    def test_comment_form_valid_data(self):
        """Test comment form with valid data."""
        form_data = {
            'name': 'Test Commenter',
            'email': 'commenter@example.com',
            'body': 'This is a test comment.'
        }
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_comment_form_invalid_email(self):
        """Test comment form with invalid email."""
        form_data = {
            'name': 'Test Commenter',
            'email': 'invalid-email',
            'body': 'This is a test comment.'
        }
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_comment_form_missing_required_fields(self):
        """Test comment form with missing required fields."""
        form_data = {
            'name': 'Test Commenter',
            # Missing email and body
        }
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('body', form.errors)


class SubscriberRequestFormTest(TestCase):
    """Test cases for SubscriberRequestForm."""

    def setUp(self):
        """Set up test data."""
        now = timezone.now()
        self.cohort = Cohort.objects.create(
            cohort_id='TEST_FORM',
            name='Test Form Cohort',
            reg_start_date=now - timedelta(days=1),
            reg_end_date=now + timedelta(days=30),
            exp_date_6=now + timedelta(days=180),
            exp_date_12=now + timedelta(days=365),
            is_active=True
        )

    def test_subscriber_request_form_valid_data(self):
        """Test subscriber request form with valid data."""
        form_data = {
            'name': 'Test Subscriber',
            'email': 'subscriber@example.com',
            'country': 'Myanmar',
            'city': 'Yangon',
            'job_title': 'Data Scientist',
            'telegram_username': 'testuser',
            'plan': '6month',
            'free_waiver': False,
            'message': 'Test message'
        }
        form = SubscriberRequestForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_subscriber_request_form_duplicate_email(self):
        """Test subscriber request form with duplicate email."""
        # Create existing subscriber
        SubscriberRequest.objects.create(
            name='Existing Subscriber',
            email='existing@example.com',
            country='Myanmar',
            city='Yangon'
        )
        
        form_data = {
            'name': 'New Subscriber',
            'email': 'existing@example.com',  # Duplicate email
            'country': 'Myanmar',
            'city': 'Yangon',
            'plan': '6month'
        }
        form = SubscriberRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_subscriber_request_form_missing_required_fields(self):
        """Test subscriber request form with missing required fields."""
        form_data = {
            'name': 'Test Subscriber',
            # Missing email, country, city
        }
        form = SubscriberRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('country', form.errors)
        self.assertIn('city', form.errors)


class FeedbackAnalyzerFormTest(TestCase):
    """Test cases for FeedbackAnalyzerForm."""
    
    def test_feedback_analyzer_form_valid_data(self):
        """Test feedback analyzer form with valid data."""
        form_data = {
            'feedback': 'This is a test feedback message.'
        }
        form = FeedbackAnalyzerForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_feedback_analyzer_form_empty_feedback(self):
        """Test feedback analyzer form with empty feedback."""
        form_data = {
            'feedback': ''
        }
        form = FeedbackAnalyzerForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('feedback', form.errors)
    
    def test_feedback_analyzer_form_long_feedback(self):
        """Test feedback analyzer form with feedback exceeding max length."""
        form_data = {
            'feedback': 'x' * 3001  # Exceeds max_length=3000
        }
        form = FeedbackAnalyzerForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('feedback', form.errors)


class PostListViewTest(TestCase):
    """Test cases for PostListView."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create published posts
        self.published_post = Post.objects.create(
            title='Published Post',
            slug='published-post',
            author=self.user,
            content='Published content.',
            status=1,
            subscribers_only=False
        )
        
        # Create draft post
        self.draft_post = Post.objects.create(
            title='Draft Post',
            slug='draft-post',
            author=self.user,
            content='Draft content.',
            status=0,
            subscribers_only=False
        )
        
        # Create subscriber-only post
        self.subscriber_post = Post.objects.create(
            title='Subscriber Post',
            slug='subscriber-post',
            author=self.user,
            content='Subscriber content.',
            status=1,
            subscribers_only=True
        )
    
    def test_post_list_view_returns_published_posts_only(self):
        """Test that PostListView returns only published, non-subscriber posts."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('post_list', response.context)
        
        posts = response.context['post_list']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0], self.published_post)
    
    def test_post_list_view_pagination(self):
        """Test pagination in PostListView."""
        # Create more posts to test pagination
        for i in range(10):
            Post.objects.create(
                title=f'Post {i}',
                slug=f'post-{i}',
                author=self.user,
                content=f'Content {i}.',
                status=1,
                subscribers_only=False
            )
        
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['post_list']), 6)  # paginate_by = 6


class PostDetailViewTest(TestCase):
    """Test cases for PostDetailView."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            content='Test content.',
            status=1,
            subscribers_only=False
        )
        self.subscriber_post = Post.objects.create(
            title='Subscriber Post',
            slug='subscriber-post',
            author=self.user,
            content='Subscriber content.',
            status=1,
            subscribers_only=True
        )
    
    def test_post_detail_view_public_post(self):
        """Test PostDetailView for public posts."""
        response = self.client.get(reverse('post_detail', kwargs={'slug': self.post.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['post'], self.post)
        self.assertIn('comment_form', response.context)
    
    def test_post_detail_view_increments_view_count(self):
        """Test that PostDetailView increments view count."""
        initial_count = self.post.view_count
        self.client.get(reverse('post_detail', kwargs={'slug': self.post.slug}))
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.view_count, initial_count + 1)
    
    def test_post_detail_view_subscriber_only_redirects_anonymous(self):
        """Test that subscriber-only posts redirect anonymous users."""
        response = self.client.get(reverse('post_detail', kwargs={'slug': self.subscriber_post.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions_upgrade.html')
    
    def test_post_detail_view_subscriber_only_allows_authenticated(self):
        """Test that subscriber-only posts allow authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('post_detail', kwargs={'slug': self.subscriber_post.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['post'], self.subscriber_post)


class SubscriberRequestViewTest(TestCase):
    """Test cases for subscriber_request view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        now = timezone.now()
        self.cohort = Cohort.objects.create(
            cohort_id='TEST_VIEW',
            name='Test View Cohort',
            reg_start_date=now - timedelta(days=1),
            reg_end_date=now + timedelta(days=30),
            exp_date_6=now + timedelta(days=180),
            exp_date_12=now + timedelta(days=365),
            is_active=True
        )
    
    def test_subscriber_request_view_get(self):
        """Test GET request to subscriber_request view."""
        response = self.client.get(reverse('subscriber_request'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], SubscriberRequestForm)
    
    def test_subscriber_request_view_redirects_authenticated_user(self):
        """Test that authenticated users are redirected from subscriber_request."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('subscriber_request'))
        self.assertRedirects(response, reverse('home'))
    
    def test_subscriber_request_view_post_valid_data(self):
        """Test POST request with valid data to subscriber_request view."""
        form_data = {
            'name': 'Test Subscriber',
            'email': 'subscriber@example.com',
            'country': 'Myanmar',
            'city': 'Yangon',
            'plan': '6month'
        }
        
        response = self.client.post(reverse('subscriber_request'), data=form_data)
        self.assertRedirects(response, reverse('subscriber_request_success'))
        
        # Check that SubscriberRequest was created
        self.assertTrue(SubscriberRequest.objects.filter(email='subscriber@example.com').exists())
    
    def test_subscriber_request_view_sends_email(self):
        """Test that subscriber_request view sends confirmation email."""
        form_data = {
            'name': 'Test Subscriber',
            'email': 'subscriber@example.com',
            'country': 'Myanmar',
            'city': 'Yangon',
            'plan': '6month'
        }
        
        # Clear mail outbox
        mail.outbox = []
        
        response = self.client.post(reverse('subscriber_request'), data=form_data)
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Thank you for your subscription request')
        self.assertEqual(mail.outbox[0].to, ['subscriber@example.com'])


class PlayGroundViewTest(TestCase):
    """Test cases for PlayGround view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
    
    def test_playground_view_get(self):
        """Test GET request to playground view."""
        response = self.client.get(reverse('our_playground'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], FeedbackAnalyzerForm)
    
    def test_playground_view_post_valid_feedback(self):
        """Test POST request with valid feedback to playground view."""
        form_data = {
            'feedback': 'This is a positive feedback message.'
        }
        
        response = self.client.post(reverse('our_playground'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.context)
        self.assertIn('confidence', response.context)


class URLPatternsTest(TestCase):
    """Test cases for URL patterns."""
    
    def test_home_url(self):
        """Test home URL pattern."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_blog_url(self):
        """Test blog URL pattern."""
        # Blog URL requires authentication, so it redirects to login
        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_about_url(self):
        """Test about URL pattern."""
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)
    
    def test_subscriber_request_url(self):
        """Test subscriber request URL pattern."""
        response = self.client.get('/subscriber-request/')
        self.assertEqual(response.status_code, 200)
    
    def test_playground_url(self):
        """Test playground URL pattern."""
        response = self.client.get('/our_playground/')
        self.assertEqual(response.status_code, 200)


class IntegrationTest(TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Integration Test Post',
            slug='integration-test-post',
            author=self.user,
            content='Integration test content.',
            status=1,
            subscribers_only=False
        )
        now = timezone.now()
        self.cohort = Cohort.objects.create(
            cohort_id='TEST_INTEGRATION',
            name='Test Integration Cohort',
            reg_start_date=now - timedelta(days=1),
            reg_end_date=now + timedelta(days=30),
            exp_date_6=now + timedelta(days=180),
            exp_date_12=now + timedelta(days=365),
            is_active=True
        )
    
    def test_complete_comment_workflow(self):
        """Test complete workflow of viewing post and adding comment."""
        # View post
        response = self.client.get(reverse('post_detail', kwargs={'slug': self.post.slug}))
        self.assertEqual(response.status_code, 200)
        
        # Add comment - PostDetailView doesn't handle POST, so we'll test comment creation directly
        comment_data = {
            'name': 'Integration Tester',
            'email': 'integration@example.com',
            'body': 'This is an integration test comment.'
        }
        
        # Create comment directly since PostDetailView doesn't handle POST
        comment = Comment.objects.create(
            post=self.post,
            name=comment_data['name'],
            email=comment_data['email'],
            body=comment_data['body'],
            active=True
        )
        
        # Check comment was created
        self.assertIsNotNone(comment)
        self.assertEqual(comment.body, 'This is an integration test comment.')
        self.assertEqual(comment.post, self.post)
    
    def test_complete_subscriber_request_workflow(self):
        """Test complete workflow of subscriber request."""
        # Access subscriber request page
        response = self.client.get(reverse('subscriber_request'))
        self.assertEqual(response.status_code, 200)
        
        # Submit subscriber request
        form_data = {
            'name': 'Integration Subscriber',
            'email': 'integration@example.com',
            'country': 'Myanmar',
            'city': 'Yangon',
            'plan': 'annual'
        }
        
        response = self.client.post(reverse('subscriber_request'), data=form_data)
        self.assertRedirects(response, reverse('subscriber_request_success'))
        
        # Check subscriber request was created
        subscriber = SubscriberRequest.objects.filter(email='integration@example.com').first()
        self.assertIsNotNone(subscriber)
        self.assertEqual(subscriber.name, 'Integration Subscriber')
        self.assertEqual(subscriber.plan, 'annual')
        self.assertIsNotNone(subscriber.expiry_date)
