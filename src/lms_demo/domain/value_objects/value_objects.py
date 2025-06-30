"""Value objects for the LMS domain."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NewType
import re
from uuid import UUID


# Entity ID Types - Simple type aliases
CourseId = NewType('CourseId', UUID)
TopicId = NewType('TopicId', UUID)
AssignmentId = NewType('AssignmentId', UUID)
ResourceId = NewType('ResourceId', UUID)
UserId = NewType('UserId', UUID)
EnrollmentId = NewType('EnrollmentId', UUID)
SubmissionId = NewType('SubmissionId', UUID)
CertificateId = NewType('CertificateId', UUID)


# Enums
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


# Value Objects
@dataclass(frozen=True)
class EmailAddress:
    email: str

    def __post_init__(self):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                        self.email):
            raise ValueError("Invalid email format")


@dataclass(frozen=True)
class CourseTitle:
    title: str

    def __post_init__(self):
        if not self.title or len(self.title.strip()) < 3:
            raise ValueError("Course title must be at least 3 characters")
        if len(self.title) > 100:
            raise ValueError("Course title must not exceed 100 characters")


@dataclass(frozen=True)
class CourseDescription:
    desc: str

    def __post_init__(self):
        if not self.desc or len(self.desc.strip()) < 10:
            raise ValueError("Course description must be at least 10 characters")


@dataclass(frozen=True)
class TopicTitle:
    title: str

    def __post_init__(self):
        if not self.title or len(self.title.strip()) < 3:
            raise ValueError("Topic title must be at least 3 characters")


@dataclass(frozen=True)
class TopicDescription:
    desc: str

    def __post_init__(self):
        if not self.desc:
            raise ValueError("Topic description cannot be empty")


@dataclass(frozen=True)
class AssignmentTitle:
    title: str

    def __post_init__(self):
        if not self.title or len(self.title.strip()) < 3:
            raise ValueError("Assignment title must be at least 3 characters")


@dataclass(frozen=True)
class AssignmentDescription:
    desc: str

    def __post_init__(self):
        if not self.desc:
            raise ValueError("Assignment description cannot be empty")


@dataclass(frozen=True)
class ResourceTitle:
    title: str

    def __post_init__(self):
        if not self.title:
            raise ValueError("Resource title cannot be empty")


@dataclass(frozen=True)
class ResourceUrl:
    url: str

    def __post_init__(self):
        if not self.url.startswith(('http://', 'https://')):
            raise ValueError("Resource URL must start with http:// or "
                             "https://")


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
    audience: str

    def __post_init__(self):
        if not self.audience:
            raise ValueError("Target audience cannot be empty")


@dataclass(frozen=True)
class Grade:
    grade: int

    def __post_init__(self):
        if self.grade < 0 or self.grade > 100:
            raise ValueError("Grade must be between 0 and 100")


@dataclass(frozen=True)
class Feedback:
    feedback: str

    def __post_init__(self):
        if not self.feedback:
            raise ValueError("Feedback cannot be empty")
