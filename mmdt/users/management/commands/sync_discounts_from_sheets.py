from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.google_api_utils import fetch_members_discount_rows
from users.models import DiscountRecord, UserProfile


class Command(BaseCommand):
    help = 'Sync discount data from Google Sheets to UserProfile'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sheet-id',
            type=str,
            help='Google Sheet ID (defaults to settings.GOOGLE_MEMBERS_SPREADSHEET_ID)',
        )
        parser.add_argument(
            '--sheet-name',
            type=str,
            default='',
            help='Worksheet name (defaults to settings.GOOGLE_MEMBERS_WORKSHEET_NAME)',
        )
        parser.add_argument(
            '--email-column',
            type=str,
            default='email',
            help='Column name containing email addresses (default: email)',
        )
        parser.add_argument(
            '--discount-column',
            type=str,
            default='discount',
            help='Column name containing discount values (default: discount)',
        )
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='Skip sending email notifications',
        )

    def handle(self, *args, **options):
        try:
            sheet_id = options.get('sheet_id') or getattr(
                settings, 'GOOGLE_MEMBERS_SPREADSHEET_ID', None
            )
            if not sheet_id:
                self.stdout.write(
                    self.style.ERROR(
                        'Error: Google Sheet ID not provided. Use --sheet-id or set '
                        'GOOGLE_MEMBERS_SPREADSHEET_ID in settings.'
                    )
                )
                return

            sheet_name = options.get('sheet_name') or getattr(
                settings, 'GOOGLE_MEMBERS_WORKSHEET_NAME', 'members'
            )
            email_column = options.get('email_column', 'email').lower()
            discount_column = options.get('discount_column', 'discount').lower()
            send_email = not options.get('no_email')

            self.stdout.write(f'Starting discount sync from Google Sheets: {sheet_id}')
            self.stdout.write(f'Sheet: {sheet_name}, Email Column: {email_column}, Discount Column: {discount_column}')

            # Same OAuth + token files as sync_approvals / sync_expiry_from_sheet
            rows = fetch_members_discount_rows(
                spreadsheet_id=sheet_id,
                worksheet_name=sheet_name,
                email_column=email_column,
                discount_column=discount_column,
            )
            data = [{'email': email, 'discount': discount} for email, discount in rows]

            if not data:
                self.stdout.write(self.style.WARNING('No data found in Google Sheets'))
                return

            # Process and sync data
            results = self._sync_discounts(data, email_column, discount_column)

            # Generate report
            report = self._generate_report(results)
            self.stdout.write(self.style.SUCCESS(report['summary']))

            # Send email notification if enabled
            if send_email:
                self._send_notification_email(report)

        except Exception as e:
            error_msg = f'Error syncing discounts: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            if options.get('no_email') is False:
                self._send_error_notification(str(e))

    def _sync_discounts(self, data, email_column, discount_column):
        """Sync discount data to UserProfile and create DiscountRecord."""
        results = {
            'updated': 0,
            'created': 0,
            'skipped': 0,
            'errors': [],
            'details': []
        }

        today = timezone.now().date()

        for item in data:
            email = item['email']
            new_discount = item['discount']

            try:
                # Find user by email
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    results['errors'].append(f'User with email {email} not found')
                    results['skipped'] += 1
                    continue

                # Get or create UserProfile
                profile, created = UserProfile.objects.get_or_create(user=user)
                old_discount = profile.discount

                # Update discount if changed
                if old_discount != new_discount:
                    profile.discount = new_discount
                    profile.save()

                    # Create DiscountRecord for audit trail
                    DiscountRecord.objects.create(
                        user=user,
                        discount_value=new_discount,
                        effective_from=today,
                        source='excel_sync',
                        notes=f'Synced from Excel. Previous: {old_discount} → New: {new_discount}'
                    )

                    results['updated'] += 1
                    results['details'].append(
                        f'{user.email}: {old_discount} → {new_discount}'
                    )
                else:
                    # No change, count as skipped
                    results['skipped'] += 1

            except Exception as e:
                results['errors'].append(f'Error processing {email}: {str(e)}')

        return results

    def _generate_report(self, results):
        """Generate sync report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        summary = f"""
        ╔════════════════════════════════════════════════╗
        ║     DISCOUNT SYNC REPORT - {timestamp}     ║
        ╚════════════════════════════════════════════════╝

        ✅ Updated: {results['updated']} users
        ⏭️  Skipped: {results['skipped']} users (no change)
        ❌ Errors: {len(results['errors'])} users
        """

        if results['details']:
            summary += "\nDetails:\n"
            for detail in results['details']:
                summary += f"  • {detail}\n"

        if results['errors']:
            summary += "\nErrors:\n"
            for error in results['errors']:
                summary += f"  • {error}\n"

        return {
            'summary': summary,
            'results': results,
            'timestamp': timestamp
        }

    def _send_notification_email(self, report):
        """Send sync completion email to admins."""
        try:
            admin_emails = [email for name, email in settings.ADMINS]

            if not admin_emails:
                return

            results = report['results']
            subject = f"Discount Sync Report - {results['updated']} users updated"

            message = f"""
            Discount sync completed at {report['timestamp']}

            Summary:
            • Updated: {results['updated']} users
            • Skipped: {results['skipped']} users
            • Errors: {len(results['errors'])} users

            Details:
            {chr(10).join(results['details'][:10])}
            {'...' if len(results['details']) > 10 else ''}

            Errors:
            {chr(10).join(results['errors'][:10])}
            {'...' if len(results['errors']) > 10 else ''}

            Check the admin panel for more details.
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=True
            )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Failed to send email: {str(e)}'))

    def _send_error_notification(self, error):
        """Send error notification to admins."""
        try:
            admin_emails = [email for name, email in settings.ADMINS]

            if not admin_emails:
                return

            subject = "❌ Discount Sync Failed"
            message = f"""
            Discount sync encountered an error:

            {error}

            Please check the logs and try again manually.
            Command: python manage.py sync_discounts_from_sheets
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=True
            )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Failed to send error email: {str(e)}'))
