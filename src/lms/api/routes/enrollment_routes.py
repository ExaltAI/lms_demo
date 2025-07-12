"""Enrollment API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from ...application import EnrollmentApplicationService, ApplicationException
from ...application.dtos import (
    EnrollStudentRequest,
    SubmitAssignmentRequest,
    EvaluateSubmissionRequest,
    EnrollmentResponse,
    SubmissionResponse,
)
from ...infrastructure import (
    SQLEnrollmentRepository,
    SQLCourseRepository,
    SQLUserRepository,
)
from ..dependencies import get_db, get_current_user_id

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_in_course(
    request: EnrollStudentRequest,
    student_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Enroll student in a course."""
    enrollment_repo = SQLEnrollmentRepository(db)
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)

    try:
        return service.enroll_student(student_id, request)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my-enrollments", response_model=List[EnrollmentResponse])
def list_my_enrollments(
    student_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """List student's enrollments."""
    enrollment_repo = SQLEnrollmentRepository(db)
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)

    return service.list_student_enrollments(student_id)


@router.get("/course/{course_id}", response_model=List[EnrollmentResponse])
def list_course_enrollments(
    course_id: UUID,
    tutor_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List enrollments for a course (tutor only)."""
    enrollment_repo = SQLEnrollmentRepository(db)
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)

    # TODO: Add authorization check for tutor
    return service.list_course_enrollments(course_id)


@router.get("/{enrollment_id}", response_model=EnrollmentResponse)
def get_enrollment(enrollment_id: UUID, db: Session = Depends(get_db)):
    """Get enrollment details."""
    enrollment_repo = SQLEnrollmentRepository(db)
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)

    try:
        return service.get_enrollment(enrollment_id)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{enrollment_id}/submit", response_model=SubmissionResponse)
def submit_assignment(
    enrollment_id: UUID,
    request: SubmitAssignmentRequest,
    student_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Submit assignment."""
    enrollment_repo = SQLEnrollmentRepository(db)
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)

    try:
        return service.submit_assignment(student_id, enrollment_id, request)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{enrollment_id}/evaluate/{assignment_id}")
def evaluate_submission(
    enrollment_id: UUID,
    assignment_id: UUID,
    request: EvaluateSubmissionRequest,
    tutor_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Evaluate student submission."""
    enrollment_repo = SQLEnrollmentRepository(db)
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)

    try:
        service.evaluate_submission(tutor_id, enrollment_id, assignment_id, request)
        return {"message": "Submission evaluated successfully"}
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
