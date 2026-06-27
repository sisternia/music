import random
import smtplib
import socket
from contextlib import suppress
from email.utils import parseaddr
from datetime import timedelta

import dns.resolver
from decouple import config
from django.core.mail import send_mail
from django.utils import timezone

from django.conf import settings
from django.contrib.auth.hashers import make_password

from .models import Account
from .models import VerifyAccount


class EmailValidationService:

    SMTP_TIMEOUT = 10
    DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="")

    @staticmethod
    def _is_valid_syntax(email: str) -> bool:

        name, addr = parseaddr(email)
        if addr != email:
            return False

        if "@" not in email:
            return False

        local_part, domain = email.rsplit("@", 1)
        if not local_part or not domain:
            return False

        if local_part.startswith(".") or local_part.endswith("."):
            return False

        if ".." in local_part or ".." in domain:
            return False

        return True

    @staticmethod
    def _get_mx_hosts(domain: str) -> list[str]:

        answers = dns.resolver.resolve(domain, "MX")
        return [
            str(r.exchange).rstrip(".")
            for r in sorted(answers, key=lambda r: r.preference)
        ]

    @staticmethod
    def _smtp_check(email: str, mx_host: str) -> bool:

        try:

            with smtplib.SMTP(
                mx_host,
                25,
                timeout=EmailValidationService.SMTP_TIMEOUT,
            ) as smtp:

                smtp.ehlo_or_helo_if_needed()

                with suppress(smtplib.SMTPException, socket.error):
                    smtp.starttls()
                    smtp.ehlo()

                from_email = (
                    EmailValidationService.DEFAULT_FROM_EMAIL
                    or "no-reply@example.com"
                )

                smtp.mail(from_email)
                code, _ = smtp.rcpt(email)

                return 200 <= code < 300

        except Exception:

            return False

    @staticmethod
    def validate(email: str) -> bool:

        if not EmailValidationService._is_valid_syntax(email):
            return False

        try:

            domain = email.rsplit("@", 1)[1].lower()
            mx_hosts = EmailValidationService._get_mx_hosts(domain)

            if not mx_hosts:
                return False

            for mx_host in mx_hosts[:3]:
                if EmailValidationService._smtp_check(email, mx_host):
                    return True

            return False

        except (
            dns.resolver.NXDOMAIN,
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
        ):

            return False

        except Exception:

            return False


class MailService:

    @staticmethod
    def generate_verify_code():

        return f"{random.randint(0, 999999):06d}"

    @staticmethod
    def send_verify_email(account: Account):

        verify_code = MailService.generate_verify_code()

        verify = (
            VerifyAccount.objects.filter(
                user=account,
            )
            .order_by("-create_time")
            .first()
        )

        if verify:
            VerifyAccount.objects.filter(
                verify_id=verify.verify_id,
            ).update(
                verify_code=verify_code,
                create_time=timezone.now(),
            )
            verify.refresh_from_db()
        else:
            verify = VerifyAccount.objects.create(
                user=account,
                verify_code=verify_code,
            )

        send_mail(
            subject="Music Account Verification",
            message=(
                f"Your verification code is: {verify_code}\n\n"
                "The code consists of 6 digits."
            ),
            from_email=None,
            recipient_list=[
                account.email,
            ],
            fail_silently=False,
        )

        return verify


class VerifyCodeService:

    @staticmethod
    def get_expire_minutes() -> int:

        return getattr(
            settings,
            "VERIFY_CODE_EXPIRE_MINUTES",
            10,
        )

    @staticmethod
    def get_expire_at(verify: VerifyAccount):

        return verify.create_time + timedelta(
            minutes=VerifyCodeService.get_expire_minutes()
        )

    @staticmethod
    def is_expired(verify: VerifyAccount) -> bool:

        return timezone.now() >= VerifyCodeService.get_expire_at(
            verify
        )

    @staticmethod
    def check_code(email: str, verify_code: str):

        try:

            account = Account.objects.get(email=email)
            verify = (
                VerifyAccount.objects.filter(
                    user=account,
                    verify_code=verify_code,
                )
                .order_by("-create_time")
                .first()
            )

            if not verify:
                return {
                    "exists": False,
                    "is_valid": False,
                    "is_expired": False,
                    "message": "Verification code not found.",
                }

            is_expired = VerifyCodeService.is_expired(verify)

            return {
                "exists": True,
                "is_valid": verify.verify_status == VerifyAccount.VerifyStatus.UNVERIFIED
                and not is_expired,
                "is_expired": is_expired,
                "expire_at": VerifyCodeService.get_expire_at(verify),
                "created_at": verify.create_time,
                "verify_status": verify.verify_status,
                "message": (
                    "Verification code is valid."
                    if verify.verify_status == VerifyAccount.VerifyStatus.UNVERIFIED
                    and not is_expired
                    else "Verification code has expired."
                ),
            }

        except Account.DoesNotExist:

            return {
                "exists": False,
                "is_valid": False,
                "is_expired": False,
                "message": "Account not found.",
            }

    @staticmethod
    def confirm_code(email: str, verify_code: str):

        try:

            account = Account.objects.get(email=email)
            verify = (
                VerifyAccount.objects.filter(
                    user=account,
                    verify_code=verify_code,
                )
                .order_by("-create_time")
                .first()
            )

            if not verify:
                return {
                    "exists": False,
                    "confirmed": False,
                    "message": "Verification code not found.",
                }

            if verify.verify_status == VerifyAccount.VerifyStatus.VERIFIED:
                return {
                    "exists": True,
                    "confirmed": True,
                    "is_expired": False,
                    "verify_status": verify.verify_status,
                    "message": "Account already verified.",
                }

            if VerifyCodeService.is_expired(verify):
                return {
                    "exists": True,
                    "confirmed": False,
                    "is_expired": True,
                    "verify_status": verify.verify_status,
                    "message": "Verification code has expired.",
                }

            verify.verify_status = VerifyAccount.VerifyStatus.VERIFIED
            verify.verify_time = timezone.now()
            verify.save(
                update_fields=[
                    "verify_status",
                    "verify_time",
                ]
            )

            return {
                "exists": True,
                "confirmed": True,
                "is_expired": False,
                "verify_status": verify.verify_status,
                "verify_time": verify.verify_time,
                "message": "Account verified successfully.",
            }

        except Account.DoesNotExist:

            return {
                "exists": False,
                "confirmed": False,
                "message": "Account not found.",
            }

    @staticmethod
    def validate_code(email: str, verify_code: str):

        try:

            account = Account.objects.get(email=email)
            verify = (
                VerifyAccount.objects.filter(
                    user=account,
                    verify_code=verify_code,
                )
                .order_by("-create_time")
                .first()
            )

            if not verify:
                return {
                    "exists": False,
                    "is_valid": False,
                    "is_expired": False,
                    "message": "Verification code not found.",
                }

            is_expired = VerifyCodeService.is_expired(verify)
            is_valid = not is_expired

            return {
                "exists": True,
                "is_valid": is_valid,
                "is_expired": is_expired,
                "verify_status": verify.verify_status,
                "created_at": verify.create_time,
                "expire_at": VerifyCodeService.get_expire_at(verify),
                "message": (
                    "Verification code is valid."
                    if is_valid
                    else "Verification code has expired."
                ),
            }

        except Account.DoesNotExist:

            return {
                "exists": False,
                "is_valid": False,
                "is_expired": False,
                "message": "Account not found.",
            }

    @staticmethod
    def reset_password(
        email: str,
        verify_code: str,
        new_password: str,
    ):

        try:

            account = Account.objects.get(email=email)
            verify = (
                VerifyAccount.objects.filter(
                    user=account,
                    verify_code=verify_code,
                )
                .order_by("-create_time")
                .first()
            )

            if not verify:
                return {
                    "exists": False,
                    "reset": False,
                    "message": "Verification code not found.",
                }

            if VerifyCodeService.is_expired(verify):
                return {
                    "exists": True,
                    "reset": False,
                    "is_expired": True,
                    "verify_status": verify.verify_status,
                    "message": "Verification code has expired.",
                }

            account.password = make_password(new_password)
            account.save(update_fields=["password", "update_time"])

            return {
                "exists": True,
                "reset": True,
                "is_expired": False,
                "verify_status": verify.verify_status,
                "user_id": account.user_id,
                "email": account.email,
                "message": "Password reset successfully.",
            }

        except Account.DoesNotExist:

            return {
                "exists": False,
                "reset": False,
                "message": "Account not found.",
            }
