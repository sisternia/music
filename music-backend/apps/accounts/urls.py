from django.urls import path

from .views import (
    CheckVerifyCodeView,
    ConfirmVerifyCodeView,
    LoginView,
    RegisterView,
    SendVerifyCodeView,
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
]
