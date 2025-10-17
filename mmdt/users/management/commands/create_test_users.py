from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Creates test users for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of test users to create (default: 5)',
        )

    def handle(self, *args, **options):
        count = options['count']

        self.stdout.write(self.style.SUCCESS(f'Creating {count} test users...'))

        test_users = []
        for i in range(1, count + 1):
            username = f'testuser{i}'
            email = f'testuser{i}@example.com'
            password = 'testpass123'

            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'User {username} already exists, skipping...'))
                continue

            # Create user (profile will be created automatically via signal)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=f'Test',
                last_name=f'User {i}'
            )

            # Update profile with various expiry states
            profile = user.profile
            if i % 3 == 0:
                # Every 3rd user is expired
                profile.expired = True
                profile.expiry_date = timezone.now() - timedelta(days=10)
                profile.save()
                self.stdout.write(self.style.WARNING(f'  ❌ Created EXPIRED user: {username}'))
            elif i % 2 == 0:
                # Every 2nd user has future expiry
                profile.expired = False
                profile.expiry_date = timezone.now() + timedelta(days=30)
                profile.save()
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created user: {username} (expires in 30 days)'))
            else:
                # Others have no expiry date
                profile.expired = False
                profile.expiry_date = None
                profile.save()
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created user: {username} (no expiry)'))

            test_users.append({
                'username': username,
                'email': email,
                'password': password,
                'id': user.id
            })

        # Print summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Test Users Created Successfully!'))
        self.stdout.write('=' * 50)
        self.stdout.write('\nLogin credentials (all use password: testpass123):')
        for user in test_users:
            self.stdout.write(f"  • ID: {user['id']} | Username: {user['username']} | Email: {user['email']}")

        self.stdout.write('\n' + self.style.SUCCESS('You can now test the API with these users!'))
