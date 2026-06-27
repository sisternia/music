from rest_framework import serializers

from .models import Account
from .services import EmailValidationService
from .validators import validate_password


class AccountEmailMixin:

    @staticmethod
    def _validate_existing_email(value: str) -> str:

        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already exists."
            )

        if not EmailValidationService.validate(value):
            raise serializers.ValidationError(
                "This email address is invalid."
            )

        return value

    @staticmethod
    def _validate_account_email(value: str):

        try:
            return Account.objects.get(email=value)

        except Account.DoesNotExist:
            raise serializers.ValidationError(
                "Account not found."
            )


class LoginRequestSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RegisterRequestSerializer(AccountEmailMixin, serializers.Serializer):

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    confirm_password = serializers.CharField(write_only=True)

    def validate_email(self, value):

        return self._validate_existing_email(value)

    def validate(self, attrs):

        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {
                    "confirm_password": "Passwords do not match."
                }
            )

        return attrs


class SendVerifyCodeRequestSerializer(AccountEmailMixin, serializers.Serializer):

    email = serializers.EmailField()

    def validate_email(self, value):

        self.account = self._validate_account_email(value)
        return value


class VerifyCodeRequestSerializer(AccountEmailMixin, serializers.Serializer):

    email = serializers.EmailField()

    verify_code = serializers.CharField(
        min_length=6,
        max_length=6,
    )


class ResetPasswordRequestSerializer(AccountEmailMixin, serializers.Serializer):

    email = serializers.EmailField()

    verify_code = serializers.CharField(
        min_length=6,
        max_length=6,
    )

    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):

        if attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError(
                {
                    "confirm_new_password": "Passwords do not match."
                }
            )

        return attrs


class LoginResponseSerializer(serializers.Serializer):

    message = serializers.CharField()
    user_id = serializers.IntegerField()
    email = serializers.EmailField()


class RegisterResponseSerializer(serializers.Serializer):

    message = serializers.CharField()
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    verify_id = serializers.IntegerField()


class ResetPasswordResponseSerializer(serializers.Serializer):

    message = serializers.CharField()
    email = serializers.EmailField()
    user_id = serializers.IntegerField()


class SendVerifyCodeResponseSerializer(serializers.Serializer):

    message = serializers.CharField()
    verify_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    verify_code = serializers.CharField()
    verify_status = serializers.CharField()
    create_time = serializers.DateTimeField()
    verify_time = serializers.DateTimeField(
        allow_null=True,
        required=False,
    )
    lock_time = serializers.DateTimeField(
        allow_null=True,
        required=False,
    )
    expire_at = serializers.DateTimeField()
    expire_minutes = serializers.IntegerField()


class VerifyCodeCheckResponseSerializer(serializers.Serializer):

    message = serializers.CharField()
    verify_status = serializers.CharField()
    is_valid = serializers.BooleanField()
    is_expired = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    expire_at = serializers.DateTimeField()
    expire_minutes = serializers.IntegerField()
    verify_time = serializers.DateTimeField(
        allow_null=True,
        required=False,
    )


class VerifyCodeConfirmResponseSerializer(serializers.Serializer):

    message = serializers.CharField()
    verify_status = serializers.CharField()
    verify_time = serializers.DateTimeField(
        allow_null=True,
        required=False,
    )


# Backward-compatible aliases used by the current views.
class LoginSerializer(LoginRequestSerializer):
    pass


class RegisterSerializer(RegisterRequestSerializer):
    pass


class SendVerifyCodeSerializer(SendVerifyCodeRequestSerializer):
    pass


class VerifyCodeSerializer(VerifyCodeRequestSerializer):
    pass


class ResendVerifyCodeSerializer(SendVerifyCodeRequestSerializer):
    pass
