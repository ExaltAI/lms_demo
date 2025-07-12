"""Certificate-related DTOs.

Certificates represent course completion achievements. The DTOs are
minimal by design because:

1. Certificates are system-generated based on completion rules
2. Most certificate data is derived from enrollments and courses
3. Immutability is important - certificates shouldn't change after issue
4. External verification systems may need simple, stable interfaces
"""

from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class IssueCertificateRequest(BaseModel):
    """Request to issue certificate.

    Extremely minimal request - just the enrollment ID. The system
    determines eligibility based on business rules (all assignments
    completed, passing grades, etc.).

    This design prevents certificate fraud - tutors can't issue
    certificates without meeting completion criteria.
    """

    enrollment_id: UUID


class CertificateResponse(BaseModel):
    """Certificate response.

    Contains all data needed to render or verify a certificate.
    Denormalized to include IDs for easy lookups and verification.

    In production, might include:
    - Verification codes or blockchain hashes
    - Expiration dates for time-limited certifications
    - Grade or achievement level
    - Digital signature data
    """

    id: UUID
    student_id: UUID
    course_id: UUID
    enrollment_id: UUID
    issue_date: datetime
    status: str
