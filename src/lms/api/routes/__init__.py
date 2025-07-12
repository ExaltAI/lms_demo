"""API routes."""

from .user_routes import router as user_router
from .course_routes import router as course_router
from .enrollment_routes import router as enrollment_router
from .certificate_routes import router as certificate_router

__all__ = ["user_router", "course_router", "enrollment_router", "certificate_router"]
