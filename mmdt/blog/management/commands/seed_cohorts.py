from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from blog.models import Cohort


class Command(BaseCommand):
    help = 'Seed cohorts with predefined data from GitHub issue #115'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        cohorts_data = [
            {
                'cohort_id': '2025_01',
                'name': 'March 2025 Cohort',
                'reg_start_date': datetime(2025, 3, 8, 0, 0, 0),
                'reg_end_date': datetime(2025, 5, 16, 23, 59, 59),
                'exp_date_6': datetime(2025, 10, 31, 23, 59, 59),
                'exp_date_12': datetime(2026, 4, 30, 23, 59, 59),
            },
            {
                'cohort_id': '2025_02',
                'name': 'October 2025 Cohort',
                'reg_start_date': datetime(2025, 10, 19, 0, 0, 0),
                'reg_end_date': datetime(2025, 11, 20, 23, 59, 59),
                'exp_date_6': datetime(2026, 4, 30, 23, 59, 59),
                'exp_date_12': datetime(2026, 10, 31, 23, 59, 59),
            },
            {
                'cohort_id': '2026_01',
                'name': 'April 2026 Cohort',
                'reg_start_date': datetime(2026, 4, 1, 0, 0, 0),
                'reg_end_date': datetime(2026, 4, 15, 23, 59, 59),
                'exp_date_6': datetime(2026, 10, 31, 23, 59, 59),
                'exp_date_12': datetime(2027, 4, 30, 23, 59, 59),
            },
            {
                'cohort_id': '2026_02',
                'name': 'October 2026 Cohort',
                'reg_start_date': datetime(2026, 10, 1, 0, 0, 0),
                'reg_end_date': datetime(2026, 10, 15, 23, 59, 59),
                'exp_date_6': datetime(2027, 4, 30, 23, 59, 59),
                'exp_date_12': datetime(2027, 10, 31, 23, 59, 59),
            },
            {
                'cohort_id': '2027_01',
                'name': 'April 2027 Cohort',
                'reg_start_date': datetime(2027, 4, 1, 0, 0, 0),
                'reg_end_date': datetime(2027, 4, 15, 23, 59, 59),
                'exp_date_6': datetime(2027, 10, 31, 23, 59, 59),
                'exp_date_12': datetime(2028, 4, 30, 23, 59, 59),
            },
            {
                'cohort_id': '2027_02',
                'name': 'October 2027 Cohort',
                'reg_start_date': datetime(2027, 10, 1, 0, 0, 0),
                'reg_end_date': datetime(2027, 10, 15, 23, 59, 59),
                'exp_date_6': datetime(2028, 4, 30, 23, 59, 59),
                'exp_date_12': datetime(2028, 10, 31, 23, 59, 59),
            },
            {
                'cohort_id': '2028_01',
                'name': 'April 2028 Cohort',
                'reg_start_date': datetime(2028, 4, 1, 0, 0, 0),
                'reg_end_date': datetime(2028, 4, 15, 23, 59, 59),
                'exp_date_6': datetime(2028, 10, 31, 23, 59, 59),
                'exp_date_12': datetime(2029, 4, 30, 23, 59, 59),
            },
            {
                'cohort_id': '2028_02',
                'name': 'October 2028 Cohort',
                'reg_start_date': datetime(2028, 10, 1, 0, 0, 0),
                'reg_end_date': datetime(2028, 10, 15, 23, 59, 59),
                'exp_date_6': datetime(2029, 4, 30, 23, 59, 59),
                'exp_date_12': datetime(2029, 10, 31, 23, 59, 59),
            },
            {
                'cohort_id': '2029_01',
                'name': 'April 2029 Cohort',
                'reg_start_date': datetime(2029, 4, 1, 0, 0, 0),
                'reg_end_date': datetime(2029, 4, 15, 23, 59, 59),
                'exp_date_6': datetime(2029, 10, 31, 23, 59, 59),
                'exp_date_12': datetime(2030, 4, 30, 23, 59, 59),
            },
            {
                'cohort_id': '2029_02',
                'name': 'October 2029 Cohort',
                'reg_start_date': datetime(2029, 10, 1, 0, 0, 0),
                'reg_end_date': datetime(2029, 10, 15, 23, 59, 59),
                'exp_date_6': datetime(2030, 4, 30, 23, 59, 59),
                'exp_date_12': datetime(2030, 10, 31, 23, 59, 59),
            },
        ]

        for cohort_data in cohorts_data:
            cohort_data['reg_start_date'] = timezone.make_aware(cohort_data['reg_start_date'])
            cohort_data['reg_end_date'] = timezone.make_aware(cohort_data['reg_end_date'])
            cohort_data['exp_date_6'] = timezone.make_aware(cohort_data['exp_date_6'])
            cohort_data['exp_date_12'] = timezone.make_aware(cohort_data['exp_date_12'])

            if not dry_run:
                cohort, created = Cohort.objects.get_or_create(
                    cohort_id=cohort_data['cohort_id'],
                    defaults=cohort_data
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created cohort: {cohort.cohort_id}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Cohort already exists: {cohort.cohort_id}")
                    )
            else:
                self.stdout.write(f"Would create: {cohort_data['cohort_id']}")

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('Cohort seeding complete'))
