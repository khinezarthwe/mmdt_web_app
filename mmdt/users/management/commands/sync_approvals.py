"""
Approve ``SubscriberRequest`` rows that are **pending** and whose email appears on the
members Google Sheet (Email column).

Sheet rows that do not correspond to a pending request are ignored. Pending requests
whose email is **not** on the sheet are left unchanged.

Uses the same spreadsheet / OAuth setup as ``sync_expiry_from_sheet``.

Each ``.save()`` runs separately so ``post_save`` on ``SubscriberRequest`` fires
(user creation / profile sync).
"""
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from blog.google_api_utils import fetch_members_sheet_emails
from blog.models import SubscriberRequest

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = (
        "Approve SubscriberRequest rows that are pending AND listed on the members sheet "
        "(Email column); relies on post_save signals for User/UserProfile."
    )

    def handle(self, *args, **options):
        try:
            sheet_emails = fetch_members_sheet_emails()
        except Exception as e:
            logger.exception("sync_approvals: failed to load Google Sheet")
            raise CommandError(f"Could not read members sheet: {e}") from e

        if not sheet_emails:
            self.stdout.write(self.style.WARNING("No emails found in sheet."))
            return

        sheet_set = {e.strip().lower() for e in sheet_emails if e.strip()}

        pending_qs = SubscriberRequest.objects.filter(status="pending").order_by("pk")
        pending_count = pending_qs.count()

        approved_new_user = 0
        approved_existing_user = 0
        skipped = 0
        matched_pending = 0

        with transaction.atomic():
            for sr in pending_qs.select_for_update():
                if sr.email.strip().lower() not in sheet_set:
                    logger.info(f"still waiting to be approved for {sr.email}")
                    continue

                matched_pending += 1

                if User.objects.filter(username__iexact=sr.email).exclude(
                    email__iexact=sr.email
                ).exists():
                    self.stdout.write(
                        self.style.ERROR(
                            f"Skipped {sr.email} - Username conflict (another account uses "
                            f"this username with a different email)."
                        )
                    )
                    skipped += 1
                    continue

                user_existed = User.objects.filter(email__iexact=sr.email).exists()

                sr.status = "approved"
                sr.save()

                if user_existed:
                    self.stdout.write(
                        f"Approved {sr.email} (user already existed; profile synced via signal)."
                    )
                    approved_existing_user += 1
                else:
                    self.stdout.write(
                        f"Approved {sr.email} and triggered user creation,"
                    )
                    approved_new_user += 1

                logger.info(
                    "sync_approvals: approved email=%s user_existed_before=%s",
                    sr.email,
                    user_existed,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Pending in DB: {pending_count} | "
                f"Pending on sheet (processed): {matched_pending} | "
                f"Approved (new user path): {approved_new_user} | "
                f"Approved (existing user): {approved_existing_user} | "
                f"Skipped (username conflict): {skipped}"
            )
        )
