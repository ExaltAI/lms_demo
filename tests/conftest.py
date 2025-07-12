"""Test configuration and fixtures for application layer tests."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from typing import Optional, List

from src.lms.domain import (
    Course, User, Enrollment, Certificate,
    CourseId, UserId, EnrollmentId, CertificateId,
    EmailAddress, UserRole,
    CourseTitle, CourseDescription, Duration, DateRange, TargetAudience,
    TopicTitle, TopicDescription,
    AssignmentTitle, AssignmentDescription,
    ResourceTitle, ResourceUrl,CourseStatus,
    # Repositories
    UserRepository, CourseRepository, EnrollmentRepository, CertificateRepository
)


class MockUserRepository(UserRepository):
    """Mock implementation of UserRepository for testing."""
    
    def __init__(self):
        self.users = {}
        self.email_index = {}
    
    def save(self, user: User) -> None:
        self.users[user.id] = user
        self.email_index[user.email.value] = user
    
    def find_by_id(self, user_id: UserId) -> Optional[User]:
        # Handle both UserId and UUID types for backward compatibility
        if hasattr(user_id, 'value'):
            return self.users.get(user_id.value)
        return self.users.get(user_id)
    
    def find_by_email(self, email: str) -> Optional[User]:
        return self.email_index.get(email)


class MockCourseRepository(CourseRepository):
    """Mock implementation of CourseRepository for testing."""
    
    def __init__(self):
        self.courses = {}
    
    def save(self, course: Course) -> None:
        self.courses[course.id] = course
    
    def find_by_id(self, course_id: CourseId) -> Optional[Course]:
        # Handle both CourseId and UUID types
        if hasattr(course_id, 'value'):
            return self.courses.get(course_id.value)
        return self.courses.get(course_id)
    
    def find_published(self) -> List[Course]:
        return [c for c in self.courses.values() if c.status == CourseStatus.PUBLISHED]
    
    def find_by_tutor(self, tutor_id: UserId) -> List[Course]:
        return [c for c in self.courses.values() if c.tutor_id == tutor_id.value]


class MockEnrollmentRepository(EnrollmentRepository):
    """Mock implementation of EnrollmentRepository for testing."""
    
    def __init__(self):
        self.enrollments = {}
        self.student_index = {}
        self.course_index = {}
    
    def save(self, enrollment: Enrollment) -> None:
        self.enrollments[enrollment.id] = enrollment
        
        # Update indices
        student_id = enrollment.student_id
        if student_id not in self.student_index:
            self.student_index[student_id] = []
        if enrollment.id not in self.student_index[student_id]:
            self.student_index[student_id].append(enrollment.id)
        
        course_id = enrollment.course_id
        if course_id not in self.course_index:
            self.course_index[course_id] = []
        if enrollment.id not in self.course_index[course_id]:
            self.course_index[course_id].append(enrollment.id)
    
    def find_by_id(self, enrollment_id: EnrollmentId) -> Optional[Enrollment]:
        # Handle both EnrollmentId and UUID types
        if hasattr(enrollment_id, 'value'):
            return self.enrollments.get(enrollment_id.value)
        return self.enrollments.get(enrollment_id)
    
    def find_by_student(self, student_id: UserId) -> List[Enrollment]:
        enrollment_ids = self.student_index.get(student_id.value, [])
        return [self.enrollments[eid] for eid in enrollment_ids]
    
    def find_by_course(self, course_id: CourseId) -> List[Enrollment]:
        enrollment_ids = self.course_index.get(course_id.value, [])
        return [self.enrollments[eid] for eid in enrollment_ids]
    
    def find_by_student_and_course(self, student_id: UserId, course_id: CourseId) -> Optional[Enrollment]:
        student_enrollments = self.find_by_student(student_id)
        for enrollment in student_enrollments:
            if enrollment.course_id == course_id.value:
                return enrollment
        return None


class MockCertificateRepository(CertificateRepository):
    """Mock implementation of CertificateRepository for testing."""
    
    def __init__(self):
        self.certificates = {}
        self.student_index = {}
    
    def save(self, certificate: Certificate) -> None:
        self.certificates[certificate.id] = certificate
        
        # Update student index
        student_id = certificate.student_id
        if student_id not in self.student_index:
            self.student_index[student_id] = []
        if certificate.id not in self.student_index[student_id]:
            self.student_index[student_id].append(certificate.id)
    
    def find_by_id(self, certificate_id: UUID) -> Optional[Certificate]:
        return self.certificates.get(certificate_id)
    
    def find_by_student(self, student_id: UserId) -> List[Certificate]:
        certificate_ids = self.student_index.get(student_id.value, [])
        return [self.certificates[cid] for cid in certificate_ids]
    
    def find_by_enrollment(self, enrollment_id: EnrollmentId) -> Optional[Certificate]:
        for cert in self.certificates.values():
            if cert.enrollment_id == enrollment_id.value:
                return cert
        return None


@pytest.fixture
def user_repo():
    """Provides a mock user repository."""
    return MockUserRepository()


@pytest.fixture
def course_repo():
    """Provides a mock course repository."""
    return MockCourseRepository()


@pytest.fixture
def enrollment_repo():
    """Provides a mock enrollment repository."""
    return MockEnrollmentRepository()


@pytest.fixture
def certificate_repo():
    """Provides a mock certificate repository."""
    return MockCertificateRepository()


@pytest.fixture
def tutor_user(user_repo):
    """Creates and saves a tutor user."""
    user = User(
        user_id=UserId(uuid4()),
        email=EmailAddress("tutor@test.com"),
        name="Test Tutor",
        role=UserRole.TUTOR
    )
    user_repo.save(user)
    return user


@pytest.fixture
def student_user(user_repo):
    """Creates and saves a student user."""
    user = User(
        user_id=UserId(uuid4()),
        email=EmailAddress("student@test.com"),
        name="Test Student",
        role=UserRole.STUDENT
    )
    user_repo.save(user)
    return user


@pytest.fixture
def sample_course(course_repo, tutor_user):
    """Creates and saves a sample course."""
    course = Course(
        course_id=CourseId(uuid4()),
        title=CourseTitle("Introduction to Python"),
        description=CourseDescription("Learn Python programming from scratch"),
        tutor_id=tutor_user.id,
        duration=Duration(8),
        date_range=DateRange(
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(weeks=8)).date()
        ),
        target_audience=TargetAudience("Beginners with no programming experience")
    )
    
    # Add a topic with assignment
    course.add_topic(
        title=TopicTitle("Python Basics"),
        description=TopicDescription("Variables, data types, and basic operations")
    )
    
    topic = course.get_topics()[0]
    # Add assignment to the topic, not the course
    topic.add_assignment(
        title=AssignmentTitle("Assignment 1"),
        description=AssignmentDescription("Do this"),
        deadline=datetime.now() + timedelta(days=7)
    )
    
    # Add a resource to the topic
    topic.add_resource(
        title=ResourceTitle("Lecture Notes"),
        url=ResourceUrl("https://example.com/lecture1.pdf")
    )
    
    course_repo.save(course)
    return course


@pytest.fixture
def published_course(sample_course, course_repo):
    """Creates a published course."""
    sample_course.publish()
    course_repo.save(sample_course)
    return sample_course


@pytest.fixture
def enrollment(enrollment_repo, student_user, published_course):
    """Creates and saves an enrollment."""
    enrollment = Enrollment.create(
        student_id=student_user.user_id,
        course_id=published_course.course_id
    )
    enrollment_repo.save(enrollment)
    return enrollment
