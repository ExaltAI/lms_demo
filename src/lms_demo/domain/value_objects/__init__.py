"""LMS domain value objects."""

from .value_objects import (
    CourseId, TopicId, AssignmentId, ResourceId, UserId,
    EnrollmentId, SubmissionId, CertificateId,
    CourseTitle, CourseDescription, TopicTitle, TopicDescription,
    AssignmentTitle, AssignmentDescription, ResourceTitle, ResourceUrl,
    Duration, DateRange, TargetAudience, EmailAddress, Grade, Feedback,
    CourseStatus, UserRole, EnrollmentStatus, SubmissionStatus,
    CertificateStatus
)

__all__ = [
    'CourseId', 'TopicId', 'AssignmentId', 'ResourceId', 'UserId',
    'EnrollmentId', 'SubmissionId', 'CertificateId',
    'CourseTitle', 'CourseDescription', 'TopicTitle', 'TopicDescription',
    'AssignmentTitle', 'AssignmentDescription', 'ResourceTitle', 'ResourceUrl',
    'Duration', 'DateRange', 'TargetAudience', 'EmailAddress', 'Grade', 'Feedback',
    'CourseStatus', 'UserRole', 'EnrollmentStatus', 'SubmissionStatus',
    'CertificateStatus'
]
