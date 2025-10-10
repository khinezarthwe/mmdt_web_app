from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import UserProfile


class Command(BaseCommand):
    help = 'Check and update expired users based on expiry_date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
        
        now = timezone.now()
        expired_count = 0
        reactivated_count = 0
        
        # Find profiles with expiry_date set
        profiles_with_expiry = UserProfile.objects.filter(expiry_date__isnull=False)
        
        for profile in profiles_with_expiry:
            # Check if user should be expired
            if profile.expiry_date <= now and not profile.expired:
                if not dry_run:
                    profile.expired = True
                    profile.save()  # This will auto-deactivate the user
                expired_count += 1
                self.stdout.write(
                    f'{"Would expire" if dry_run else "Expired"}: {profile.user.username} '
                    f'(expiry_date: {profile.expiry_date})'
                )
            
            # Check if user should be reactivated
            elif profile.expiry_date > now and profile.expired:
                if not dry_run:
                    profile.expired = False
                    profile.save()  # This will auto-activate the user
                reactivated_count += 1
                self.stdout.write(
                    f'{"Would reactivate" if dry_run else "Reactivated"}: {profile.user.username} '
                    f'(expiry_date: {profile.expiry_date})'
                )
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN COMPLETE: Would expire {expired_count} users, '
                    f'would reactivate {reactivated_count} users'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'COMPLETE: Expired {expired_count} users, '
                    f'reactivated {reactivated_count} users'
                )
            )

