"""Repository protocols for the domain layer."""

from typing import Protocol, Optional, List

from ..entities import Course, User, Enrollment, Certificate
from ..value_objects import CourseId, UserId, EnrollmentId, CertificateId


class CourseRepository(Protocol):
    """Protocol for course repository."""

    def save(self, course: Course) -> None:
        """Save a course."""
        ...

    def find_by_id(self, course_id: CourseId) -> Optional[Course]:
        """Find course by ID."""
        ...

    def find_published(self) -> List[Course]:
        """Find all published courses."""
        ...

    def find_by_tutor(self, tutor_id: UserId) -> List[Course]:
        """Find courses by tutor."""
        ...


class UserRepository(Protocol):
    """Protocol for user repository."""

    def save(self, user: User) -> None:
        """Save a user."""
        ...

    def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Find user by ID."""
        ...

    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        ...


class EnrollmentRepository(Protocol):
    """Protocol for enrollment repository."""

    def save(self, enrollment: Enrollment) -> None:
        """Save an enrollment."""
        ...

    def find_by_id(self, enrollment_id: EnrollmentId) -> Optional[Enrollment]:
        """Find enrollment by ID."""
        ...

    def find_by_student_and_course(
        self, student_id: UserId, course_id: CourseId
    ) -> Optional[Enrollment]:
        """Find enrollment by student and course."""
        ...

    def find_by_student(self, student_id: UserId) -> List[Enrollment]:
        """Find enrollments by student."""
        ...

    def find_by_course(self, course_id: CourseId) -> List[Enrollment]:
        """Find enrollments by course."""
        ...


class CertificateRepository(Protocol):
    """Protocol for certificate repository."""

    def save(self, certificate: Certificate) -> None:
        """Save a certificate."""
        ...

    def find_by_id(self, certificate_id: CertificateId) -> Optional[Certificate]:
        """Find certificate by ID."""
        ...

    def find_by_enrollment(self, enrollment_id: EnrollmentId) -> Optional[Certificate]:
        """Find certificate by enrollment."""
        ...

    def find_by_student(self, student_id: UserId) -> List[Certificate]:
        """Find certificates by student."""
        ...
