from django.urls import path

from .views import (
    LoginView,
    RegisterView,
    SendVerifyCodeView,
)

urlpatterns = [
    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),

    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),

    path(
        "send-verify-code/",
        SendVerifyCodeView.as_view(),
        name="send_verify_code",
    ),
]