from rest_framework import permissions

from .models import RoleAccount


ROLE_CODE_CACHE_ATTR = "_role_code_cache"


def get_user_role_code(user):

    if not user or not user.is_authenticated:
        return None

    if hasattr(user, ROLE_CODE_CACHE_ATTR):
        return getattr(user, ROLE_CODE_CACHE_ATTR)

    role = getattr(user, "role", None)
    role_code = getattr(role, "role_code", None)
    setattr(user, ROLE_CODE_CACHE_ATTR, role_code)
    return role_code


def has_role(user, role_codes):

    if getattr(user, "is_superuser", False) and RoleAccount.RoleCode.ADMIN in role_codes:
        return True

    return get_user_role_code(user) in role_codes


class HasRole(permissions.BasePermission):

    role_codes = ()
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and has_role(
                request.user,
                set(self.role_codes),
            )
        )


class IsAdminRole(HasRole):
    role_codes = (RoleAccount.RoleCode.ADMIN,)


class IsUserRole(HasRole):
    role_codes = (RoleAccount.RoleCode.USER,)


class IsAdminOrUserRole(HasRole):
    role_codes = (RoleAccount.RoleCode.ADMIN, RoleAccount.RoleCode.USER)
