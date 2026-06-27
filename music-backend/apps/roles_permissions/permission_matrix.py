"""Central RBAC policy map for auth endpoints."""

from rest_framework.permissions import AllowAny

from .permissions import IsAdminOrUserRole
from .permissions import IsAdminRole
from .permissions import IsUserRole

PERMISSION_ANONYMOUS = "Anonymous"
PERMISSION_USER = "User"
PERMISSION_ADMIN = "Admin"
PERMISSION_ADMIN_OR_USER = "Admin or User"


API_PERMISSION_MATRIX = {
    ("POST", "/api/accounts/auth/register/"): {
        "permission": PERMISSION_ANONYMOUS,
        "permission_classes": [AllowAny],
    },
    ("POST", "/api/accounts/auth/login/"): {
        "permission": PERMISSION_ANONYMOUS,
        "permission_classes": [AllowAny],
    },
    ("POST", "/api/accounts/auth/send-verify-code/"): {
        "permission": PERMISSION_ANONYMOUS,
        "permission_classes": [AllowAny],
    },
    ("POST", "/api/accounts/auth/check-verify-code/"): {
        "permission": PERMISSION_ANONYMOUS,
        "permission_classes": [AllowAny],
    },
    ("POST", "/api/accounts/auth/confirm-verify-code/"): {
        "permission": PERMISSION_ANONYMOUS,
        "permission_classes": [AllowAny],
    },
    ("POST", "/api/accounts/auth/validate-verify-code/"): {
        "permission": PERMISSION_ANONYMOUS,
        "permission_classes": [AllowAny],
    },
    ("POST", "/api/accounts/auth/reset-password/"): {
        "permission": PERMISSION_ANONYMOUS,
        "permission_classes": [AllowAny],
    },
    ("GET", "/api/accounts/auth/me/"): {
        "permission": PERMISSION_ADMIN_OR_USER,
        "permission_classes": [IsAdminOrUserRole],
    },
    ("GET", "/api/accounts/auth/admin-only/"): {
        "permission": PERMISSION_ADMIN,
        "permission_classes": [IsAdminRole],
    },
    ("GET", "/api/accounts/auth/user-only/"): {
        "permission": PERMISSION_USER,
        "permission_classes": [IsUserRole],
    },
}


def get_api_permission(method, path):
    return API_PERMISSION_MATRIX.get((method.upper(), path))


def get_api_permission_classes(method, path):
    policy = get_api_permission(method, path)
    if not policy:
        raise KeyError(f"No API permission policy for {method.upper()} {path}")

    return policy["permission_classes"]
