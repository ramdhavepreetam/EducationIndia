import os

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


# ── Base ──────────────────────────────────────────────────────────────────────

class ScholarPathException(HTTPException):
    """Base class for all ScholarPath HTTP exceptions."""
    pass


# ── 4xx Client errors ─────────────────────────────────────────────────────────

class BadRequest(ScholarPathException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class Unauthorized(ScholarPathException):
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class Forbidden(ScholarPathException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFound(ScholarPathException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class Conflict(ScholarPathException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnprocessableEntity(ScholarPathException):
    def __init__(self, detail: str = "Unprocessable entity"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


# ── Exception handlers ────────────────────────────────────────────────────────
# Register these with app.add_exception_handler() in main.py

async def scholarpath_exception_handler(
    request: Request, exc: ScholarPathException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


def _cors_headers(request: Request) -> dict:
    """
    Return CORS headers for error responses.

    FastAPI's CORSMiddleware only runs for successful responses in the
    middleware stack — unhandled exceptions bypass it, so error responses
    would lack Access-Control-Allow-Origin, causing browsers to report
    a confusing "Network Error" instead of the real HTTP status.

    We reflect the request Origin only if it matches a known allowed origin
    (same logic as CORSMiddleware), or fall back to the configured FRONTEND_URL.
    """
    origin = request.headers.get("origin", "")

    # Build the allowed-origins list the same way main.py does.
    frontend_url = os.environ.get("FRONTEND_URL", "")
    allowed = {
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        frontend_url,
    }

    allowed_origin = origin if origin in allowed else (frontend_url or "*")

    return {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Credentials": "true",
    }


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    import traceback
    traceback.print_exc()   # logs the real cause to Cloud Run / Render stdout
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "status_code": 500},
        headers=_cors_headers(request),
    )
