"""Certificate application service."""

from typing import List
from uuid import UUID

from ...domain import (
    CertificateService,
    UserId,
    EnrollmentId,
    CertificateRepository,
    EnrollmentRepository,
    CourseRepository,
    UserRepository,
    DomainException,
)
from ..dtos import IssueCertificateRequest, CertificateResponse
from ..exceptions import ApplicationException


class CertificateApplicationService:
    """Application service for certificate operations."""

    def __init__(
        self,
        certificate_repo: CertificateRepository,
        enrollment_repo: EnrollmentRepository,
        course_repo: CourseRepository,
        user_repo: UserRepository,
    ):
        self.certificate_repo = certificate_repo
        self.certificate_service = CertificateService(
            certificate_repo, enrollment_repo, course_repo, user_repo
        )

    def issue_certificate(
        self, tutor_id: UUID, request: IssueCertificateRequest
    ) -> CertificateResponse:
        """Issue certificate for course completion."""
        try:
            certificate = self.certificate_service.issue_certificate(
                tutor_id=UserId(tutor_id),
                enrollment_id=EnrollmentId(request.enrollment_id),
            )
            return self._to_response(certificate)
        except DomainException as e:
            raise ApplicationException(str(e))

    def get_certificate(self, certificate_id: UUID) -> CertificateResponse:
        """Get certificate details."""
        certificate = self.certificate_repo.find_by_id(certificate_id)
        if not certificate:
            raise ApplicationException("Certificate not found")
        return self._to_response(certificate)

    def list_student_certificates(self, student_id: UUID) -> List[CertificateResponse]:
        """List student's certificates."""
        certificates = self.certificate_repo.find_by_student(UserId(student_id))
        return [self._to_response(c) for c in certificates]

    def _to_response(self, certificate) -> CertificateResponse:
        """Convert certificate to response DTO."""
        return CertificateResponse(
            id=certificate.id,
            student_id=certificate.student_id,
            course_id=certificate.course_id,
            enrollment_id=certificate.enrollment_id,
            issue_date=certificate.issue_date,
            status=certificate.status.value,
        )
