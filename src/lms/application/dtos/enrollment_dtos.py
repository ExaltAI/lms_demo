"""Enrollment-related DTOs.

This module handles the student journey through courses: enrollment,
assignment submission, and evaluation. The DTOs are designed to:

1. Minimize Required Fields: Only essential data is required in requests
2. Progressive Disclosure: Optional fields appear as the workflow progresses
3. Clear Status Tracking: Both enrollments and submissions have status fields
4. Audit Trail: Timestamps capture when actions occurred
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class EnrollStudentRequest(BaseModel):
    """Request to enroll student in course.

    Minimal DTO - only requires course ID. The student ID comes from
    the authenticated user context (not passed in request body for security).
    This prevents students from enrolling other users.
    """

    course_id: UUID


class SubmitAssignmentRequest(BaseModel):
    """Request to submit assignment.

    Students submit text content for assignments. In a real system,
    this might support file uploads, rich text, or other content types.
    """

    assignment_id: UUID
    content: str = Field(..., min_length=1)


class EvaluateSubmissionRequest(BaseModel):
    """Request to evaluate submission.

    Tutors evaluate student submissions with grades and feedback.
    This DTO enforces grading standards and meaningful feedback.
    """

    grade: int = Field(..., ge=0, le=100)
    feedback: str = Field(..., min_length=1)


class SubmissionResponse(BaseModel):
    """Submission response.

    Represents a student's assignment submission with its evaluation status.
    Uses Optional fields for data that appears later in the workflow.
    """

    id: UUID
    assignment_id: UUID
    content: str
    submitted_at: datetime
    status: str
    grade: Optional[int] = None
    feedback: Optional[str] = None


class EnrollmentResponse(BaseModel):
    """Enrollment response.

    Complete enrollment information including all submissions.
    This denormalized view helps students track their progress
    without multiple API calls.
    """

    id: UUID
    student_id: UUID
    course_id: UUID
    enrollment_date: datetime
    status: str
    submissions: List[SubmissionResponse]
