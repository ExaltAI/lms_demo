"""Domain exceptions."""

from .exceptions import (
    DomainException,
    CourseNotFoundException,
    EnrollmentNotFoundException,
    UserNotFoundException,
    DuplicateEnrollmentException,
    UnauthorizedException,
    InvalidOperationException,
)

__all__ = [
    "DomainException",
    "CourseNotFoundException",
    "EnrollmentNotFoundException",
    "UserNotFoundException",
    "DuplicateEnrollmentException",
    "UnauthorizedException",
    "InvalidOperationException",
]
