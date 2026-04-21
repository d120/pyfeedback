import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from feedback.models import EmailChange

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Deletes email change requests based on their status. EXPIRED -> 7 days ; MAGIC_LINK_SENT/OTP_SENT -> 30 days'

    def handle(self, *args, **options):
            now = timezone.now()

            # EXPIRED
            limit_7d = now - timedelta(days=7)
            cond_1 = Q(
                status=EmailChange.Status.EXPIRED,
                dynamic_expiry_time__lt=limit_7d
            )

            # LINK SENT or OTP SENT
            limit_30d = now - timedelta(days=30)
            cond_2 = Q(
                status__in=[EmailChange.Status.MAGIC_LINK_SENT, EmailChange.Status.OTP_SENT],
                dynamic_expiry_time__lt=limit_30d
            )

            deleted_count, _ = EmailChange.objects.filter(cond_1 | cond_2).delete()

            if deleted_count > 0:
                msg = f"Cleanup successful: Deleted {deleted_count} EmailChange records."
                self.stdout.write(self.style.SUCCESS(msg))
                logger.info(msg)
            else:
                msg = "Cleanup run: No records were eligible for deletion."
                self.stdout.write(msg)
                logger.info(msg)