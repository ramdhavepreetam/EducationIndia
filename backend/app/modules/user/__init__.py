# Public interface of the user module.
# Other modules import from here — never from internal files directly.
# ADR-002: "modules communicate only through their public service interfaces"

from app.modules.user.service import UserService, user_service

__all__ = [
    "UserService",
    "user_service",
]
