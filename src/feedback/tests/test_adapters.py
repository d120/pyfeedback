from unittest.mock import MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

# Import your custom adapter
from feedback.auth import FeedbackSocialAccountAdapter


class FeedbackSocialAccountAdapterTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.adapter = FeedbackSocialAccountAdapter()

    def test_pre_social_login_with_existing_user_by_username(self):
        """
        Scenario 1: Unsaved social user matches an existing username in DB.
        Should connect to existing user and elevate permissions.
        """
        # Create an existing non-admin user
        existing_user = User.objects.create_user(
            username="johndoe",
            email="john@example.com",
            is_staff=False,
            is_superuser=False,
        )

        # Mock an unsaved social user with the same username
        unsaved_user = User(username="johndoe", email="john@example.com")
        
        mock_sociallogin = MagicMock()
        mock_sociallogin.user = unsaved_user

        # Run method
        self.adapter.pre_social_login(self.request, mock_sociallogin)

        # Verify sociallogin.connect was called with existing_user
        mock_sociallogin.connect.assert_called_once_with(self.request, existing_user)

        # Verify the existing user was updated to superuser/staff
        existing_user.refresh_from_db()
        self.assertTrue(existing_user.is_staff)
        self.assertTrue(existing_user.is_superuser)

    def test_pre_social_login_with_new_user(self):
        """
        Scenario 2: Unsaved social user does NOT match any username in DB.
        Should save the new user and elevate permissions.
        """
        # Mock an unsaved social user with a brand new username
        unsaved_user = User(username="newuser", email="new@example.com")
        
        mock_sociallogin = MagicMock()
        mock_sociallogin.user = unsaved_user

        # Run method
        self.adapter.pre_social_login(self.request, mock_sociallogin)

        # Verify connect was NOT called
        mock_sociallogin.connect.assert_not_called()

        # Verify user now exists in DB and has superuser/staff permissions
        db_user = User.objects.get(username="newuser")
        self.assertIsNotNone(db_user.id)
        self.assertTrue(db_user.is_staff)
        self.assertTrue(db_user.is_superuser)

    def test_pre_social_login_with_already_saved_user(self):
        """
        Scenario 3: Social user already has an ID (already saved/authenticated).
        Should skip user lookup/creation and elevate permissions.
        """
        # User is already saved in DB
        saved_user = User.objects.create_user(
            username="saveduser",
            is_staff=False,
            is_superuser=False,
        )

        mock_sociallogin = MagicMock()
        mock_sociallogin.user = saved_user

        # Run method
        self.adapter.pre_social_login(self.request, mock_sociallogin)

        # Verify connect was NOT called
        mock_sociallogin.connect.assert_not_called()

        # Verify existing saved user is now superuser/staff
        saved_user.refresh_from_db()
        self.assertTrue(saved_user.is_staff)
        self.assertTrue(saved_user.is_superuser)