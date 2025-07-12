"""SQLAlchemy models for the LMS application.

This module defines all database models and enums used in the LMS application.
It includes models for users, courses, topics, assignments, resources, enrollments,
submissions, and certificates. The models use SQLAlchemy ORM for database mapping
and include proper relationships between entities.

The module also provides custom types like GUID for UUID handling in SQLite and
enums for various status fields.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR
import uuid


from ...domain.value_objects import (
    UserRole,
    CourseStatus,
    EnrollmentStatus,
    SubmissionStatus,
    CertificateStatus,
)


Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type for UUID storage.

    This custom type provides consistent UUID handling across different database
    backends. It stores UUIDs as CHAR(36) strings in databases that don't have
    native UUID support (like SQLite), while maintaining the UUID type in Python.

    The type automatically converts between Python UUID objects and their string
    representations for database storage.

    Attributes:
        impl: The underlying SQL type (CHAR(36))
        cache_ok: Set to True for SQLAlchemy query caching
    """

    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert UUID to string for database storage.

        Args:
            value: The UUID value to be stored (can be UUID object or string)
            dialect: The SQL dialect being used (required by SQLAlchemy interface
                but not used in this implementation as UUID-to-string conversion
                is database-agnostic)

        Returns:
            str: String representation of the UUID, or None if value is None
        """
        # When we're saving to the database, we need to convert Python UUID objects to strings
        # because SQLite doesn't have a native UUID type (unlike PostgreSQL)
        if value is not None:
            if isinstance(value, uuid.UUID):
                return str(value)
        return value

    def process_result_value(self, value, dialect):
        """Convert string from database to UUID object.

        Args:
            value: The string value from the database
            dialect: The SQL dialect being used (required by SQLAlchemy interface
                but not used in this implementation as string-to-UUID conversion
                is database-agnostic)

        Returns:
            uuid.UUID: UUID object, or None if value is None

        Raises:
            ValueError: If the value is not a valid UUID string
        """
        # When we're reading from the database, we convert strings back to UUID objects
        # This way, our Python code always works with proper UUID objects, not strings
        if value is not None:
            return uuid.UUID(value)
        return value


# Note: Enums are imported from the domain layer to maintain consistency
# and avoid duplication. This follows the DRY principle and ensures that
# the domain model drives the infrastructure implementation.


# Models
class UserModel(Base):
    """User database model.

    Represents users in the LMS system, including both students and tutors.
    Each user has a unique email address and is assigned a specific role.

    Attributes:
        id: Unique identifier (UUID)
        email: User's email address (unique)
        name: User's full name
        role: User's role (student or tutor)
        created_at: Timestamp of user creation

    Relationships:
        courses: Courses created by the user (for tutors)
        enrollments: Course enrollments (for students)
        certificates: Certificates earned (for students)
    """

    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    courses = relationship("CourseModel", back_populates="tutor")
    enrollments = relationship("EnrollmentModel", back_populates="student")
    certificates = relationship("CertificateModel", back_populates="student")


class CourseModel(Base):
    """Course database model.

    Represents a course in the LMS system. Courses are created by tutors and
    can contain multiple topics, assignments, and resources. Students can
    enroll in published courses.

    Attributes:
        id: Unique identifier (UUID)
        title: Course title
        description: Detailed course description
        tutor_id: ID of the tutor who created the course
        duration_weeks: Course duration in weeks
        start_date: Course start date
        end_date: Course end date
        target_audience: Target audience for the course
        status: Course status (draft/published/archived)
        created_at: Timestamp of course creation
        updated_at: Timestamp of last update

    Relationships:
        tutor: The tutor who created the course
        topics: Topics/modules in the course
        enrollments: Student enrollments
        certificates: Certificates issued for this course
    """

    __tablename__ = "courses"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)

    description = Column(Text, nullable=False)
    tutor_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    target_audience = Column(Text, nullable=False)
    status = Column(SQLEnum(CourseStatus), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    tutor = relationship("UserModel", back_populates="courses")
    topics = relationship(
        "TopicModel", back_populates="course", cascade="all, delete-orphan"
    )
    enrollments = relationship("EnrollmentModel", back_populates="course")
    certificates = relationship("CertificateModel", back_populates="course")


class TopicModel(Base):
    """Topic database model.

    Represents a topic or module within a course. Topics are ordered units
    of learning that contain assignments and resources.

    Attributes:
        id: Unique identifier (UUID)
        course_id: ID of the parent course
        title: Topic title
        description: Topic description
        order: Display order within the course

    Relationships:
        course: The parent course
        assignments: Assignments in this topic
        resources: Learning resources for this topic
    """

    __tablename__ = "topics"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    course_id = Column(GUID, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    order = Column(Integer, nullable=False)

    # Relationships
    course = relationship("CourseModel", back_populates="topics")
    assignments = relationship(
        "AssignmentModel", back_populates="topic", cascade="all, delete-orphan"
    )
    resources = relationship(
        "ResourceModel", back_populates="topic", cascade="all, delete-orphan"
    )


class AssignmentModel(Base):
    """Assignment database model.

    Represents an assignment or task within a course topic that students
    must complete. Assignments have deadlines and can be submitted by
    enrolled students.

    Attributes:
        id: Unique identifier (UUID)
        topic_id: ID of the parent topic
        title: Assignment title
        description: Detailed assignment instructions
        deadline: Submission deadline

    Relationships:
        topic: The parent topic
        submissions: Student submissions for this assignment
    """

    __tablename__ = "assignments"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    # Assignment must belong to a topic - this enforces our hierarchical structure
    # of Course -> Topic -> Assignment
    topic_id = Column(GUID, ForeignKey("topics.id"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    deadline = Column(DateTime, nullable=False)

    # Relationships
    topic = relationship("TopicModel", back_populates="assignments")
    submissions = relationship("SubmissionModel", back_populates="assignment")


class ResourceModel(Base):
    """Resource database model.

    Represents a learning resource (e.g., reading material, video, external link)
    associated with a course topic.

    Attributes:
        id: Unique identifier (UUID)
        topic_id: ID of the parent topic
        title: Resource title
        url: Resource URL or location

    Relationships:
        topic: The parent topic
    """

    __tablename__ = "resources"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    topic_id = Column(GUID, ForeignKey("topics.id"), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)

    # Relationships
    topic = relationship("TopicModel", back_populates="resources")


class EnrollmentModel(Base):
    """Enrollment database model.

    Represents a student's enrollment in a course. Tracks the enrollment
    status and links to all submissions and certificates for the enrollment.

    Attributes:
        id: Unique identifier (UUID)
        student_id: ID of the enrolled student
        course_id: ID of the course
        enrollment_date: Date of enrollment
        status: Current enrollment status (active/completed/withdrawn)

    Relationships:
        student: The enrolled student
        course: The course enrolled in
        submissions: Assignment submissions for this enrollment
        certificate: Completion certificate (if earned)
    """

    __tablename__ = "enrollments"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    student_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    course_id = Column(GUID, ForeignKey("courses.id"), nullable=False)
    enrollment_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(SQLEnum(EnrollmentStatus), nullable=False)

    # Relationships
    student = relationship("UserModel", back_populates="enrollments")
    course = relationship("CourseModel", back_populates="enrollments")
    submissions = relationship(
        "SubmissionModel", back_populates="enrollment", cascade="all, delete-orphan"
    )
    certificate = relationship(
        "CertificateModel", back_populates="enrollment", uselist=False
    )


class SubmissionModel(Base):
    """Submission database model.

    Represents a student's submission for an assignment. Includes the submitted
    content, evaluation status, grade, and feedback from the tutor.

    Attributes:
        id: Unique identifier (UUID)
        enrollment_id: ID of the student's enrollment
        assignment_id: ID of the assignment
        content: Submitted content/answer
        submitted_at: Submission timestamp
        status: Evaluation status (pending/evaluated)
        grade: Numeric grade (0-100, nullable)
        feedback: Tutor's feedback (nullable)

    Relationships:
        enrollment: The student's enrollment
        assignment: The assignment being submitted
    """

    __tablename__ = "submissions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(GUID, ForeignKey("enrollments.id"), nullable=False)
    assignment_id = Column(GUID, ForeignKey("assignments.id"), nullable=False)
    content = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(SQLEnum(SubmissionStatus), nullable=False)
    grade = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)

    # Relationships
    enrollment = relationship("EnrollmentModel", back_populates="submissions")
    assignment = relationship("AssignmentModel", back_populates="submissions")


class CertificateModel(Base):
    """Certificate database model.

    Represents a course completion certificate issued to a student upon
    successful completion of a course. Each certificate is unique to a
    specific enrollment.

    Attributes:
        id: Unique identifier (UUID)
        student_id: ID of the student who earned the certificate
        course_id: ID of the completed course
        enrollment_id: ID of the specific enrollment (unique)
        issue_date: Date the certificate was issued
        status: Certificate status (issued/revoked)

    Relationships:
        student: The student who earned the certificate
        course: The completed course
        enrollment: The specific enrollment that led to the certificate
    """

    __tablename__ = "certificates"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    student_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    course_id = Column(GUID, ForeignKey("courses.id"), nullable=False)
    enrollment_id = Column(
        GUID, ForeignKey("enrollments.id"), unique=True, nullable=False
    )
    issue_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(SQLEnum(CertificateStatus), nullable=False)

    # Relationships
    student = relationship("UserModel", back_populates="certificates")
    course = relationship("CourseModel", back_populates="certificates")
    enrollment = relationship("EnrollmentModel", back_populates="certificate")
