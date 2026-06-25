import random
import smtplib
import socket
from contextlib import suppress
from email.utils import parseaddr

import dns.resolver
from decouple import config
from django.core.mail import send_mail

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
