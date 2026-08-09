from io import StringIO
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone

from feedback.models import EmailChange


class CleanupEmailChangeReqCommandTests(TestCase):

    def setUp(self):
        """Set up test instances for different statuses and dates."""
        now = timezone.now()

        # 1. EXPIRED: > 7 days old -> SHOULD BE DELETED
        self.expired_old = EmailChange.objects.create(
            status=EmailChange.Status.EXPIRED,
            dynamic_expiry_time=now - timedelta(days=8),
        )

        # 2. EXPIRED: < 7 days old -> SHOULD NOT BE DELETED
        self.expired_recent = EmailChange.objects.create(
            status=EmailChange.Status.EXPIRED,
            dynamic_expiry_time=now - timedelta(days=5),
        )

        # 3. MAGIC_LINK_SENT: > 30 days old -> SHOULD BE DELETED
        self.link_sent_old = EmailChange.objects.create(
            status=EmailChange.Status.MAGIC_LINK_SENT,
            dynamic_expiry_time=now - timedelta(days=31),
        )

        # 4. OTP_SENT: > 30 days old -> SHOULD BE DELETED
        self.otp_sent_old = EmailChange.objects.create(
            status=EmailChange.Status.OTP_SENT,
            dynamic_expiry_time=now - timedelta(days=32),
        )

        # 5. MAGIC_LINK_SENT: < 30 days old -> SHOULD NOT BE DELETED
        self.link_sent_recent = EmailChange.objects.create(
            status=EmailChange.Status.MAGIC_LINK_SENT,
            dynamic_expiry_time=now - timedelta(days=15),
        )

    @patch("feedback.management.commands.cleanup_email_change_req.logger")
    def test_command_deletes_eligible_records(self, mock_logger):
        """Test deleting eligible records (hits if branch: deleted_count > 0)."""
        out = StringIO()

        # Execute management command
        call_command("cleanup_email_change_req", stdout=out)

        output = out.getvalue()

        # Verify stdout output & logger call
        self.assertIn("Cleanup successful: Deleted 3 EmailChange records.", output)
        mock_logger.info.assert_called_once_with(
            "Cleanup successful: Deleted 3 EmailChange records."
        )

        # Verify correct records were deleted from DB
        remaining_ids = set(EmailChange.objects.values_list("id", flat=True))
        self.assertEqual(remaining_ids, {self.expired_recent.id, self.link_sent_recent.id})

    @patch("feedback.management.commands.cleanup_email_change_req.logger")
    def test_command_when_no_records_eligible(self, mock_logger):
        """Test behavior when no records match (hits else branch: deleted_count == 0)."""
        # Clear out all objects first
        EmailChange.objects.all().delete()

        out = StringIO()
        call_command("cleanup_email_change_req", stdout=out)

        output = out.getvalue()

        # Verify stdout output & logger call for 0 records branch
        self.assertIn("Cleanup run: No records were eligible for deletion.", output)
        mock_logger.info.assert_called_once_with(
            "Cleanup run: No records were eligible for deletion."
        )