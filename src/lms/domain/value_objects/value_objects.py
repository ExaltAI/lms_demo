"""Value objects for the LMS domain."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NewType
import re
from uuid import UUID


CourseId = NewType("CourseId", UUID)
TopicId = NewType("TopicId", UUID)
AssignmentId = NewType("AssignmentId", UUID)
ResourceId = NewType("ResourceId", UUID)
UserId = NewType("UserId", UUID)
EnrollmentId = NewType("EnrollmentId", UUID)
SubmissionId = NewType("SubmissionId", UUID)
CertificateId = NewType("CertificateId", UUID)


class UserRole(Enum):
    STUDENT = "student"
    TUTOR = "tutor"


class CourseStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class EnrollmentStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"


class SubmissionStatus(Enum):
    PENDING = "pending"
    EVALUATED = "evaluated"


class CertificateStatus(Enum):
    ISSUED = "issued"
    REVOKED = "revoked"


@dataclass(frozen=True)
class EmailAddress:
    value: str

    def __post_init__(self):
        if not re.match(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", self.value
        ):
            raise ValueError("Invalid email format")


@dataclass(frozen=True)
class CourseTitle:
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) < 3:
            raise ValueError("Course title must be at least 3 characters")
        if len(self.value) > 100:
            raise ValueError("Course title must not exceed 100 characters")


@dataclass(frozen=True)
class CourseDescription:
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) < 10:
            raise ValueError("Course description must be at least 10 characters")


@dataclass(frozen=True)
class TopicTitle:
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) < 3:
            raise ValueError("Topic title must be at least 3 characters")


@dataclass(frozen=True)
class TopicDescription:
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Topic description cannot be empty")


@dataclass(frozen=True)
class AssignmentTitle:
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) < 3:
            raise ValueError("Assignment title must be at least 3 characters")


@dataclass(frozen=True)
class AssignmentDescription:
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Assignment description cannot be empty")


@dataclass(frozen=True)
class ResourceTitle:
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Resource title cannot be empty")


@dataclass(frozen=True)
class ResourceUrl:
    value: str

    def __post_init__(self):
        if not self.value.startswith(("http://", "https://")):
            raise ValueError("Resource URL must start with http:// or https://")


@dataclass(frozen=True)
class Duration:
    weeks: int

    def __post_init__(self):
        if self.weeks < 1:
            raise ValueError("Duration must be at least 1 week")
        if self.weeks > 52:
            raise ValueError("Duration cannot exceed 52 weeks")


@dataclass(frozen=True)
class DateRange:
    start_date: datetime
    end_date: datetime

    def __post_init__(self):
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")


@dataclass(frozen=True)
class TargetAudience:
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Target audience cannot be empty")


@dataclass(frozen=True)
class Grade:
    value: int

    def __post_init__(self):
        if self.value < 0 or self.value > 100:
            raise ValueError("Grade must be between 0 and 100")


@dataclass(frozen=True)
class Feedback:
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Feedback cannot be empty")
