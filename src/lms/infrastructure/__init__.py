"""Infrastructure layer exports.

The infrastructure layer provides concrete implementations for the persistence
and external service interfaces defined in the domain layer. This layer follows
the Dependency Inversion Principle, implementing the repository interfaces
defined by the domain.

Key components:
- Database: SQLAlchemy-based database connection and session management
- Models: SQLAlchemy ORM models representing database tables
- Repositories: Concrete implementations of domain repository interfaces

The infrastructure layer handles:
- Database connections and transactions
- Object-relational mapping (ORM)
- Converting between domain entities and database models
- Managing database sessions with proper commit/rollback handling

All repository implementations use the Unit of Work pattern through SQLAlchemy
sessions, ensuring transactional consistency across operations.
"""

from .database import Database
from .repositories import (
    SQLUserRepository,
    SQLCourseRepository,
    SQLEnrollmentRepository,
    SQLCertificateRepository,
)

__all__ = [
    "Database",
    "SQLUserRepository",
    "SQLCourseRepository",
    "SQLEnrollmentRepository",
    "SQLCertificateRepository",
]
