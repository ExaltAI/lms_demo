"""Certificate API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from ...application import CertificateApplicationService, ApplicationException
from ...application.dtos import IssueCertificateRequest, CertificateResponse
from ...infrastructure import (
    SQLCertificateRepository,
    SQLEnrollmentRepository,
    SQLCourseRepository,
    SQLUserRepository,
)
from ..dependencies import get_db, get_current_user_id

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.post(
    "", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED
)
def issue_certificate(
    request: IssueCertificateRequest,
    tutor_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Issue certificate for course completion."""
    certificate_repo = SQLCertificateRepository(db)
    enrollment_repo = SQLEnrollmentRepository(db)
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = CertificateApplicationService(
        certificate_repo, enrollment_repo, course_repo, user_repo
    )

    try:
        return service.issue_certificate(tutor_id, request)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my-certificates", response_model=List[CertificateResponse])
def list_my_certificates(
    student_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """List student's certificates."""
    certificate_repo = SQLCertificateRepository(db)
    enrollment_repo = SQLEnrollmentRepository(db)
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = CertificateApplicationService(
        certificate_repo, enrollment_repo, course_repo, user_repo
    )

    return service.list_student_certificates(student_id)


@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate(certificate_id: UUID, db: Session = Depends(get_db)):
    """Get certificate details."""
    certificate_repo = SQLCertificateRepository(db)
    enrollment_repo = SQLEnrollmentRepository(db)
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = CertificateApplicationService(
        certificate_repo, enrollment_repo, course_repo, user_repo
    )

    try:
        return service.get_certificate(certificate_id)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
