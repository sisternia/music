from rest_framework import serializers

from apps.roles_permissions.models import RoleAccount

from .models import Account
from .services import EmailValidationService
from .validators import validate_password


class AccountEmailMixin:

    @staticmethod
    def validate_new_email(value: str) -> str:

        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")

        if not EmailValidationService.validate(value):
            raise serializers.ValidationError("This email address is invalid.")

        return value

    @staticmethod
    def get_account_by_email(value: str):

        try:
            return Account.objects.get(email=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account not found.")


class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(AccountEmailMixin, serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return self.validate_new_email(value)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


class SendVerifyCodeSerializer(AccountEmailMixin, serializers.Serializer):

    email = serializers.EmailField()

    def validate_email(self, value):
        self.account = self.get_account_by_email(value)
        return value


class VerifyCodeSerializer(serializers.Serializer):

    email = serializers.EmailField()
    verify_code = serializers.CharField(min_length=6, max_length=6)


class ResetPasswordRequestSerializer(AccountEmailMixin, serializers.Serializer):

    email = serializers.EmailField()
    verify_code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError(
                {"confirm_new_password": "Passwords do not match."}
            )
        return attrs


class AdminUpdateUserRoleSerializer(serializers.Serializer):

    user_id = serializers.IntegerField()
    role_code = serializers.ChoiceField(
        choices=RoleAccount.RoleCode.choices
    )

    def validate_user_id(self, value):

        try:
            self.account = Account.objects.get(user_id=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account not found.")

        return value


# Backward-compatible aliases used by the current views.
LoginRequestSerializer = LoginSerializer
RegisterRequestSerializer = RegisterSerializer
SendVerifyCodeRequestSerializer = SendVerifyCodeSerializer
VerifyCodeRequestSerializer = VerifyCodeSerializer
AdminUpdateUserRoleRequestSerializer = AdminUpdateUserRoleSerializer
