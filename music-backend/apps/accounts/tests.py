from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Account
from .models import VerifyAccount


class AccountAuthTests(APITestCase):

    def setUp(self):

        self.register_url = "/api/accounts/auth/register/"
        self.login_url = "/api/accounts/auth/login/"
        self.send_verify_url = "/api/accounts/auth/send-verify-code/"
        self.check_verify_url = "/api/accounts/auth/check-verify-code/"
        self.confirm_verify_url = "/api/accounts/auth/confirm-verify-code/"
        self.validate_verify_url = "/api/accounts/auth/validate-verify-code/"
        self.reset_password_url = "/api/accounts/auth/reset-password/"

        self.email = "vu784512000@gmail.com"
        self.password = "OldPass@123"
        self.new_password = "NewPass@123"

        self.account = Account.objects.create(
            email=self.email,
            password="test-password",
        )

    def _create_verify_account(
        self,
        *,
        code="123456",
        minutes_ago=0,
        status_value=VerifyAccount.VerifyStatus.UNVERIFIED,
        verify_time=None,
        lock_time=None,
    ):

        verify = VerifyAccount.objects.create(
            user=self.account,
            verify_code=code,
            verify_status=status_value,
            verify_time=verify_time,
            lock_time=lock_time,
        )

        if minutes_ago:
            VerifyAccount.objects.filter(
                verify_id=verify.verify_id
            ).update(
                create_time=timezone.now() - timedelta(minutes=minutes_ago)
            )
            verify.refresh_from_db()

        return verify

    @patch("apps.accounts.services.EmailValidationService.validate", return_value=True)
    @patch("apps.accounts.services.MailService.send_verify_email")
    def test_register_success(self, mock_send_verify_email, mock_validate):

        mock_verify = VerifyAccount(
            verify_id=1,
            user=self.account,
            verify_code="654321",
            verify_status=VerifyAccount.VerifyStatus.UNVERIFIED,
        )
        mock_send_verify_email.return_value = mock_verify

        response = self.client.post(
            self.register_url,
            {
                "email": "newuser@gmail.com",
                "password": "StrongPass@123",
                "confirm_password": "StrongPass@123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Register Success")
        self.assertTrue(Account.objects.filter(email="newuser@gmail.com").exists())

    @patch("apps.accounts.services.EmailValidationService.validate", return_value=False)
    def test_register_invalid_email(self, mock_validate):

        response = self.client.post(
            self.register_url,
            {
                "email": "fake@gmail.com",
                "password": "StrongPass@123",
                "confirm_password": "StrongPass@123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["errors"]["email"][0],
            "This email address is invalid.",
        )

    def test_login_success(self):

        self.account.password = "pbkdf2_sha256$1000000$test$testhash"
        self.account.save(update_fields=["password"])

        with patch(
            "apps.accounts.views.check_password",
            return_value=True,
        ):
            response = self.client.post(
                self.login_url,
                {
                    "email": self.email,
                    "password": "any-password",
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.email)

    @patch("apps.accounts.services.MailService.send_verify_email")
    def test_send_verify_code_reuses_existing_record(self, mock_send_verify_email):

        verify = self._create_verify_account(code="111111")
        mock_send_verify_email.return_value = verify

        response = self.client.post(
            self.send_verify_url,
            {
                "email": self.email,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Verification code sent successfully.")
        self.assertEqual(
            VerifyAccount.objects.filter(user=self.account).count(),
            1,
        )

    def test_validate_verify_code_success(self):

        verify = self._create_verify_account(code="222222", minutes_ago=1)

        response = self.client.post(
            self.validate_verify_url,
            {
                "email": self.email,
                "verify_code": verify.verify_code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["is_valid"])
        self.assertFalse(response.data["data"]["is_expired"])

    def test_validate_verify_code_expired(self):

        verify = self._create_verify_account(code="333333", minutes_ago=11)

        response = self.client.post(
            self.validate_verify_url,
            {
                "email": self.email,
                "verify_code": verify.verify_code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["data"]["is_valid"])
        self.assertTrue(response.data["data"]["is_expired"])

    def test_confirm_verify_code_success(self):

        verify = self._create_verify_account(code="444444", minutes_ago=1)

        response = self.client.post(
            self.confirm_verify_url,
            {
                "email": self.email,
                "verify_code": verify.verify_code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        verify.refresh_from_db()
        self.assertEqual(
            verify.verify_status,
            VerifyAccount.VerifyStatus.VERIFIED,
        )
        self.assertIsNotNone(verify.verify_time)

    def test_reset_password_success(self):

        verify = self._create_verify_account(code="555555", minutes_ago=1)

        response = self.client.post(
            self.reset_password_url,
            {
                "email": self.email,
                "verify_code": verify.verify_code,
                "new_password": self.new_password,
                "confirm_new_password": self.new_password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.account.refresh_from_db()
        self.assertTrue(
            check_password(self.new_password, self.account.password)
        )

    def test_reset_password_expired_code(self):

        verify = self._create_verify_account(code="666666", minutes_ago=11)

        response = self.client.post(
            self.reset_password_url,
            {
                "email": self.email,
                "verify_code": verify.verify_code,
                "new_password": self.new_password,
                "confirm_new_password": self.new_password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["message"],
            "Verification code has expired.",
        )
