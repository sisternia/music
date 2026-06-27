from django.urls import path

from .views import (
    AdminUserListView,
    CheckVerifyCodeView,
    ConfirmVerifyCodeView,
    LoginView,
    RegisterView,
    ResetPasswordView,
    SendVerifyCodeView,
    ValidateVerifyCodeView,
)

urlpatterns = [
    path(
        "auth/register/",
        RegisterView.as_view(),
        name="register",
    ),

    path(
        "auth/login/",
        LoginView.as_view(),
        name="login",
    ),

    path(
        "auth/send-verify-code/",
        SendVerifyCodeView.as_view(),
        name="send_verify_code",
    ),

    path(
        "auth/check-verify-code/",
        CheckVerifyCodeView.as_view(),
        name="check_verify_code",
    ),

    path(
        "auth/confirm-verify-code/",
        ConfirmVerifyCodeView.as_view(),
        name="confirm_verify_code",
    ),

    path(
        "auth/validate-verify-code/",
        ValidateVerifyCodeView.as_view(),
        name="validate_verify_code",
    ),

    path(
        "auth/reset-password/",
        ResetPasswordView.as_view(),
        name="reset_password",
    ),

    path(
        "admin/users/",
        AdminUserListView.as_view(),
        name="admin_users",
    ),
]
