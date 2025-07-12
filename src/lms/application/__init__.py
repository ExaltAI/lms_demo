"""Application layer exports.

The application layer serves as the orchestration layer between the presentation
layer (API/UI) and the domain layer. This follows the Clean Architecture pattern.

Key design decisions:
1. Application Services: These services orchestrate use cases by coordinating
   domain objects and repositories. They handle transaction boundaries,
   validation, and conversion between DTOs and domain entities.

2. DTOs (Data Transfer Objects): Used to decouple the domain model from
   external concerns. This allows the domain to evolve independently of
   API contracts.

3. Application Exceptions: Custom exceptions provide a clear boundary for
   application-level errors, separate from domain and infrastructure errors.
"""

from .services import (
    CourseApplicationService,
    UserApplicationService,
    EnrollmentApplicationService,
    CertificateApplicationService,
)
from .exceptions import ApplicationException

# Export all public application layer components
# This provides a clean API surface for consumers of the application layer
__all__ = [
    "CourseApplicationService",
    "UserApplicationService",
    "EnrollmentApplicationService",
    "CertificateApplicationService",
    "ApplicationException",
]
