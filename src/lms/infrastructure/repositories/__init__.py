"""Repository implementations.

This module contains SQLAlchemy-based implementations of the repository
interfaces defined in the domain layer. These repositories provide the
concrete data persistence mechanisms for the LMS application.

Repository Implementations:
- SQLUserRepository: Manages user persistence and retrieval
- SQLCourseRepository: Handles course data with nested entities (topics, assignments, resources)
- SQLEnrollmentRepository: Manages student enrollments and submissions
- SQLCertificateRepository: Handles course completion certificates

All repositories follow consistent patterns:
1. Accept a SQLAlchemy session in the constructor
2. Implement save() methods that perform "upsert" operations
3. Provide various find methods for querying
4. Handle conversion between domain entities and database models
5. Manage nested entity relationships where applicable

The repositories ensure data integrity and handle transaction boundaries
through the SQLAlchemy session, which should be managed using the
Database.get_session() context manager.
"""

from .user_repository import SQLUserRepository
from .course_repository import SQLCourseRepository
from .enrollment_repository import SQLEnrollmentRepository
from .certificate_repository import SQLCertificateRepository

__all__ = [
    "SQLUserRepository",
    "SQLCourseRepository",
    "SQLEnrollmentRepository",
    "SQLCertificateRepository",
]
