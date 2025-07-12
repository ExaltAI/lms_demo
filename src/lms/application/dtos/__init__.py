"""Application DTOs."""

from .course_dtos import (
    CreateCourseRequest,
    AddTopicRequest,
    AddAssignmentRequest,
    AddResourceRequest,
    ResourceResponse,
    AssignmentResponse,
    TopicResponse,
    CourseResponse,
    CourseListResponse,
)
from .user_dtos import CreateUserRequest, UserResponse
from .enrollment_dtos import (
    EnrollStudentRequest,
    SubmitAssignmentRequest,
    EvaluateSubmissionRequest,
    SubmissionResponse,
    EnrollmentResponse,
)
from .certificate_dtos import IssueCertificateRequest, CertificateResponse

__all__ = [
    "CreateCourseRequest",
    "AddTopicRequest",
    "AddAssignmentRequest",
    "AddResourceRequest",
    "ResourceResponse",
    "AssignmentResponse",
    "TopicResponse",
    "CourseResponse",
    "CourseListResponse",
    "CreateUserRequest",
    "UserResponse",
    "EnrollStudentRequest",
    "SubmitAssignmentRequest",
    "EvaluateSubmissionRequest",
    "SubmissionResponse",
    "EnrollmentResponse",
    "IssueCertificateRequest",
    "CertificateResponse",
]
