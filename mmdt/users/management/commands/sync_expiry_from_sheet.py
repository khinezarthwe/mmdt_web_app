"""
Sync DB ``expiry_date`` from the Google Sheet ``members`` tab.

Sheet columns (only ``email`` and ``expired_date`` are read; the rest are ignored)::

    id | full_name | email | cohort_id | first_joined_date |
    latest_renew_date | expired_date | status

Writes to the database only when the sheet's ``expired_date`` (calendar day)
differs from the stored ``SubscriberRequest`` / ``UserProfile`` value.

Schedule daily (example, 06:00 server time)::

   0 6 * * * cd /path/to/mmdt && /path/to/venv/bin/python manage.py sync_expiry_from_sheet

Requires ``GOOGLE_OAUTH_CLIENT_SECRET_*``, ``GOOGLE_TOKEN_FILE``, and a token
that has been authorized once (same as other Sheets automation). For cron,
ensure ``google_token.json`` is present and refreshable on the server.
"""
import logging
from datetime import datetime, time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from blog.google_api_utils import fetch_members_expiry_rows
from blog.models import SubscriberRequest

logger = logging.getLogger(__name__)
User = get_user_model()


def _date_to_expiry_datetime(day):
    dt = datetime.combine(day, time.min)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _expired_date_unchanged(existing, new_dt):
    """True if DB already matches sheet ``expired_date`` (same calendar day)."""
    if existing is None:
        return False
    return timezone.localtime(existing).date() == timezone.localtime(new_dt).date()


class Command(BaseCommand):
    help = (
        "Sync expiry_date from Sheet columns email + expired_date only; "
        "update DB only when expired_date (calendar day) changed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Load the sheet and report changes without writing to the database",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no database writes"))

        try:
            pairs = fetch_members_expiry_rows()
        except Exception as e:
            logger.exception("sync_expiry_from_sheet: failed to load sheet")
            raise CommandError(f"Could not read members sheet: {e}") from e

        updated_sr = 0
        updated_profile = 0
        missing_sr = 0
        missing_user = 0

        for email, expiry_day in pairs:
            expiry_dt = _date_to_expiry_datetime(expiry_day)

            sr = SubscriberRequest.objects.filter(email__iexact=email).first()
            if not sr:
                missing_sr += 1
                logger.info(
                    "sync_expiry_from_sheet: no SubscriberRequest for %s", email
                )
            elif not _expired_date_unchanged(sr.expiry_date, expiry_dt):
                if dry_run:
                    self.stdout.write(
                        f"  would update SubscriberRequest {email} -> {expiry_day}"
                    )
                else:
                    sr.expiry_date = expiry_dt
                    if (
                        sr.expiry_date
                        and timezone.now() < sr.expiry_date
                        and sr.status == "expired"
                    ):
                        sr.status = "approved"
                    sr.save()
                    updated_sr += 1
                    logger.info(
                        "sync_expiry_from_sheet: SubscriberRequest %s expiry -> %s",
                        email,
                        expiry_day,
                    )

            user = User.objects.filter(email__iexact=email).first()
            if not user:
                missing_user += 1
            elif hasattr(user, "profile"):
                profile = user.profile
                if not _expired_date_unchanged(profile.expiry_date, expiry_dt):
                    if dry_run:
                        self.stdout.write(
                            f"  would update UserProfile {email} -> {expiry_day}"
                        )
                    else:
                        profile.expiry_date = expiry_dt
                        profile.save()
                        updated_profile += 1
                        logger.info(
                            "sync_expiry_from_sheet: UserProfile %s expiry -> %s",
                            email,
                            expiry_day,
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Sheet rows (email + expiry): {len(pairs)} | "
                f"SubscriberRequest updated: {updated_sr} | "
                f"UserProfile updated: {updated_profile} | "
                f"rows with no SubscriberRequest: {missing_sr} | "
                f"rows with no User: {missing_user}"
            )
        )
