"""Certificate repository implementation.

This module provides the SQLAlchemy-based implementation of the CertificateRepository
interface. It handles all database operations related to course completion certificates.

Certificates are issued to students upon successful completion of a course and serve
as formal recognition of their achievement. Each certificate is unique to a specific
enrollment and can be revoked if necessary.
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from ...domain import (
    Certificate,
    CertificateId,
    UserId,
    CourseId,
    EnrollmentId,
)
from ..database import CertificateModel


class SQLCertificateRepository:
    """SQL implementation of CertificateRepository.

    This class provides concrete implementations for certificate-related database
    operations using SQLAlchemy. It handles the conversion between domain entities
    and database models for course completion certificates.

    The repository ensures that certificates maintain their relationship with
    students, courses, and enrollments, providing a complete audit trail.

    Attributes:
        session: SQLAlchemy database session for executing queries
    """

    def __init__(self, session: Session):
        """Initialize the repository with a database session.

        Args:
            session: SQLAlchemy session for database operations.
                Should typically be obtained from Database.get_session()
        """
        # Dependency injection pattern - session is injected from outside
        # This makes the repository testable with mock sessions
        self.session = session

    def save(self, certificate: Certificate) -> None:
        """Save or update a certificate.

        This method performs an "upsert" operation for certificates. If the
        certificate doesn't exist, it creates a new record. If it exists,
        only the status can be updated (to support revocation).

        Args:
            certificate: Certificate domain entity to persist

        Note:
            - Certificate details (student, course, enrollment, issue date) are
              immutable once created
            - Only the status field can be updated (e.g., from ISSUED to REVOKED)
            - The actual database commit is handled by the session context manager
        """
        # First, check if this certificate already exists
        model = (
            self.session.query(CertificateModel).filter_by(id=certificate.id).first()
        )

        if not model:
            model = CertificateModel(
                id=certificate.id,
                student_id=certificate.student_id,
                course_id=certificate.course_id,
                enrollment_id=certificate.enrollment_id,
                issue_date=certificate.issue_date,
                status=certificate.status,  # Enum stored directly
            )
            self.session.add(model)
        else:
            model.status = certificate.status

    def find_by_id(self, certificate_id: UUID) -> Optional[Certificate]:
        """Find a certificate by its unique identifier.

        Args:
            certificate_id: The unique identifier (UUID) of the certificate

        Returns:
            Certificate domain entity if found, None otherwise
        """

        model = (
            self.session.query(CertificateModel).filter_by(id=certificate_id).first()
        )

        if not model:
            return None

        return self._to_entity(model)

    def find_by_student(self, student_id: UserId) -> List[Certificate]:
        """Find all certificates earned by a specific student.

        This method retrieves all certificates issued to a student across
        all courses they have completed.

        Args:
            student_id: The unique identifier of the student

        Returns:
            List of Certificate domain entities for the student.
            Empty list if the student has no certificates.

        Note:
            Returns certificates in all statuses (issued and revoked)
        """

        models = (
            self.session.query(CertificateModel).filter_by(student_id=student_id).all()
        )

        return [self._to_entity(m) for m in models]

    def find_by_enrollment(self, enrollment_id: EnrollmentId) -> Optional[Certificate]:
        """Find a certificate by its associated enrollment.

        Since each enrollment can have at most one certificate, this method
        returns a single certificate or None. This is useful for checking
        if a student has already received a certificate for a specific
        course enrollment.

        Args:
            enrollment_id: The unique identifier of the enrollment

        Returns:
            Certificate domain entity if one exists for the enrollment,
            None otherwise
        """

        model = (
            self.session.query(CertificateModel)
            .filter_by(enrollment_id=enrollment_id)
            .first()
        )

        if not model:
            return None

        return self._to_entity(model)

    def _to_entity(self, model: CertificateModel) -> Certificate:
        """Convert a database model to a domain entity.

        This method transforms the SQLAlchemy model to a domain entity,
        ensuring proper initialization of all value objects.

        Args:
            model: CertificateModel instance from the database

        Returns:
            Certificate domain entity with properly initialized value objects

        Note:
            - Certificate status is set after construction
            - All certificate fields are immutable except status
        """

        certificate = Certificate(
            certificate_id=CertificateId(model.id),
            student_id=UserId(model.student_id),
            course_id=CourseId(model.course_id),
            enrollment_id=EnrollmentId(model.enrollment_id),
            # issue_date=model.issue_date,
        )
        certificate.status = model.status

        return certificate
