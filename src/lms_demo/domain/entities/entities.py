"""Domain entities for the LMS system."""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from ..value_objects import (
    CourseId, TopicId, AssignmentId, ResourceId, UserId, EnrollmentId,
    SubmissionId, CertificateId, CourseTitle, CourseDescription, TopicTitle,
    TopicDescription, AssignmentTitle, AssignmentDescription, ResourceTitle,
    ResourceUrl, Duration, DateRange, TargetAudience, EmailAddress, Grade,
    Feedback, CourseStatus, UserRole, EnrollmentStatus, SubmissionStatus,
    CertificateStatus
)


# User Aggregate
class User:
    """User aggregate root."""

    def __init__(self, user_id: UserId, email: EmailAddress, name: str, role: UserRole):
        self.id = user_id
        self.email = email
        self.name = name
        self.role = role

    def can_create_course(self) -> bool:
        return self.role == UserRole.TUTOR

    def can_enroll_in_course(self) -> bool:
        return self.role == UserRole.STUDENT


# Course Aggregate - Properly designed without circular references
class LearningResource:
    """Learning resource entity within Topic."""

    def __init__(self, title: ResourceTitle, url: ResourceUrl):
        self.id = ResourceId(uuid4())
        self.title = title
        self.url = url
        # NO topic_id - contained within Topic


class Assignment:
    """Assignment entity within Topic."""

    def __init__(self, title: AssignmentTitle, description: AssignmentDescription,
                 deadline: datetime):
        self.id = AssignmentId(uuid4())
        self.title = title
        self.description = description
        self.deadline = deadline
        # NO topic_id - contained within Topic

    def is_past_deadline(self) -> bool:
        return datetime.now() > self.deadline


class Topic:
    """Topic entity within Course aggregate."""

    def __init__(self, title: TopicTitle, description: TopicDescription, order: int):
        self.id = TopicId(uuid4())
        self.title = title
        self.description = description
        self.order = order
        self._assignments: List[Assignment] = []
        self._resources: List[LearningResource] = []
        # NO course_id - contained within Course

    def add_assignment(self, title: AssignmentTitle, description: AssignmentDescription,
                       deadline: datetime) -> Assignment:
        """Create and add assignment to topic."""
        assignment = Assignment(title, description, deadline)
        self._assignments.append(assignment)
        return assignment

    def add_resource(self, title: ResourceTitle, url: ResourceUrl) -> LearningResource:
        """Create and add resource to topic."""
        resource = LearningResource(title, url)
        self._resources.append(resource)
        return resource

    def get_assignments(self) -> List[Assignment]:
        return list(self._assignments)

    def get_resources(self) -> List[LearningResource]:
        return list(self._resources)


class Course:
    """Course aggregate root."""

    def __init__(self, course_id: CourseId, title: CourseTitle,
                 description: CourseDescription, tutor_id: UserId,
                 duration: Duration, date_range: DateRange,
                 target_audience: TargetAudience):
        self.id = course_id
        self.title = title
        self.description = description
        self.tutor_id = tutor_id
        self.duration = duration
        self.date_range = date_range
        self.target_audience = target_audience
        self.status = CourseStatus.DRAFT
        self._topics: List[Topic] = []

    def add_topic(self, title: TopicTitle, description: TopicDescription) -> Topic:
        """Add topic to course with automatic ordering."""
        if self.status != CourseStatus.DRAFT:
            raise ValueError("Cannot add topics to published or archived courses")

        order = len(self._topics) + 1
        topic = Topic(title, description, order)
        self._topics.append(topic)
        return topic

    def get_topics(self) -> List[Topic]:
        """Get topics in order."""
        return sorted(self._topics, key=lambda t: t.order)

    def publish(self):
        """Publish the course."""
        if self.status != CourseStatus.DRAFT:
            raise ValueError("Only draft courses can be published")
        if not self._topics:
            raise ValueError("Cannot publish course without topics")

        # Ensure all topics have at least one resource
        for topic in self._topics:
            if not topic.get_resources():
                raise ValueError(f"Topic '{topic.title.value}' must have at least one resource")

        self.status = CourseStatus.PUBLISHED

    def archive(self):
        """Archive the course."""
        if self.status != CourseStatus.PUBLISHED:
            raise ValueError("Only published courses can be archived")
        self.status = CourseStatus.ARCHIVED

    def is_available_for_enrollment(self) -> bool:
        """Check if course can be enrolled in."""
        return (self.status == CourseStatus.PUBLISHED and
                datetime.now() < self.date_range.end_date)


# Enrollment Aggregate
class Submission:
    """Submission entity within Enrollment."""

    def __init__(self, assignment_id: AssignmentId, content: str):
        self.id = SubmissionId(uuid4())
        self.assignment_id = assignment_id  # Reference to assignment in Course aggregate
        self.content = content
        self.submitted_at = datetime.now()
        self.status = SubmissionStatus.PENDING
        self.grade: Optional[Grade] = None
        self.feedback: Optional[Feedback] = None

    def evaluate(self, grade: Grade, feedback: Feedback):
        """Evaluate the submission."""
        if self.status == SubmissionStatus.EVALUATED:
            raise ValueError("Submission already evaluated")

        self.grade = grade
        self.feedback = feedback
        self.status = SubmissionStatus.EVALUATED

    def is_evaluated(self) -> bool:
        return self.status == SubmissionStatus.EVALUATED


class Enrollment:
    """Enrollment aggregate root."""

    def __init__(self, enrollment_id: EnrollmentId, student_id: UserId,
                 course_id: CourseId):
        self.id = enrollment_id
        self.student_id = student_id
        self.course_id = course_id
        self.enrollment_date = datetime.now()
        self.status = EnrollmentStatus.ACTIVE
        self._submissions: List[Submission] = []

    def submit_assignment(self, assignment_id: AssignmentId, content: str) -> Submission:
        """Submit an assignment."""
        if self.status != EnrollmentStatus.ACTIVE:
            raise ValueError("Can only submit assignments for active enrollments")

        # Check if already submitted
        existing = [s for s in self._submissions if s.assignment_id == assignment_id]
        if existing:
            raise ValueError("Assignment already submitted")

        submission = Submission(assignment_id, content)
        self._submissions.append(submission)
        return submission

    def get_submission(self, assignment_id: AssignmentId) -> Optional[Submission]:
        """Get submission for specific assignment."""
        for submission in self._submissions:
            if submission.assignment_id == assignment_id:
                return submission
        return None

    def get_submissions(self) -> List[Submission]:
        return list(self._submissions)

    def complete(self):
        """Mark enrollment as completed."""
        if self.status != EnrollmentStatus.ACTIVE:
            raise ValueError("Only active enrollments can be completed")
        self.status = EnrollmentStatus.COMPLETED

    def withdraw(self):
        """Withdraw from course."""
        if self.status != EnrollmentStatus.ACTIVE:
            raise ValueError("Only active enrollments can be withdrawn")
        self.status = EnrollmentStatus.WITHDRAWN


# Certificate Aggregate
class Certificate:
    """Certificate aggregate root."""

    def __init__(self, certificate_id: CertificateId, student_id: UserId,
                 course_id: CourseId, enrollment_id: EnrollmentId):
        self.id = certificate_id
        self.student_id = student_id
        self.course_id = course_id
        self.enrollment_id = enrollment_id
        self.issue_date = datetime.now()
        self.status = CertificateStatus.ISSUED

    def revoke(self):
        """Revoke the certificate."""
        if self.status != CertificateStatus.ISSUED:
            raise ValueError("Can only revoke issued certificates")
        self.status = CertificateStatus.REVOKED

    def is_valid(self) -> bool:
        return self.status == CertificateStatus.ISSUED
