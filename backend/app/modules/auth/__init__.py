# Public interface of the auth module.
# Other modules import from here — never from internal files directly.
# ADR-002: "modules communicate only through their public service interfaces"

from app.modules.auth.dependencies import (
    UserIdentity,
    require_admin,
    require_parent,
    require_role,
    require_student,
    require_super_admin,
    require_teacher,
    verify_token,
)

__all__ = [
    "UserIdentity",
    "verify_token",
    "require_role",
    "require_student",
    "require_parent",
    "require_teacher",
    "require_admin",
    "require_super_admin",
]
