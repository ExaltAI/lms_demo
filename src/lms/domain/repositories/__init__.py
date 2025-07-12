"""Domain repository protocols."""

from .repositories import (
    CourseRepository,
    UserRepository,
    EnrollmentRepository,
    CertificateRepository,
)

__all__ = [
    "CourseRepository",
    "UserRepository",
    "EnrollmentRepository",
    "CertificateRepository",
]
