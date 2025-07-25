"""Domain services for complex operations."""

from typing import List
from uuid import uuid4

from ..entities import Course, Enrollment, Certificate, Assignment
from ..repositories import (
    CourseRepository,
    UserRepository,
    EnrollmentRepository,
    CertificateRepository,
)
from ..value_objects import (
    CourseId,
    UserId,
    EnrollmentId,
    AssignmentId,
    Grade,
    Feedback,
    CertificateId,
)
from ..exceptions import (
    CourseNotFoundException,
    UserNotFoundException,
    UnauthorizedException,
    InvalidOperationException,
    DuplicateEnrollmentException,
    EnrollmentNotFoundException,
)


class EnrollmentService:
    """Handles enrollment operations."""

    def __init__(
        self,
        enrollment_repo: EnrollmentRepository,
        course_repo: CourseRepository,
        user_repo: UserRepository,
    ):
        self.enrollment_repo = enrollment_repo
        self.course_repo = course_repo
        self.user_repo = user_repo

    def enroll_student(self, student_id: UserId, course_id: CourseId) -> Enrollment:
        """Enroll a student in a course."""

        student = self.user_repo.find_by_id(student_id)
        if not student:
            raise UserNotFoundException(f"Student {student_id} not found")
        if not student.can_enroll_in_course():
            raise UnauthorizedException("User is not a student")

        course = self.course_repo.find_by_id(course_id)
        if not course:
            raise CourseNotFoundException(f"Course {course_id} not found")
        if not course.is_available_for_enrollment():
            raise InvalidOperationException("Course is not available for enrollment")

        existing = self.enrollment_repo.find_by_student_and_course(
            student_id, course_id
        )
        if existing:
            raise DuplicateEnrollmentException("Student already enrolled in course")

        enrollment = Enrollment(
            enrollment_id=EnrollmentId(uuid4()),
            student_id=student_id,
            course_id=course_id,
        )

        self.enrollment_repo.save(enrollment)
        return enrollment


class EvaluationService:
    """Handles assignment evaluation."""

    def __init__(
        self,
        enrollment_repo: EnrollmentRepository,
        course_repo: CourseRepository,
        user_repo: UserRepository,
    ):
        self.enrollment_repo = enrollment_repo
        self.course_repo = course_repo
        self.user_repo = user_repo

    def evaluate_submission(
        self,
        tutor_id: UserId,
        enrollment_id: EnrollmentId,
        assignment_id: AssignmentId,
        grade: Grade,
        feedback: Feedback,
    ) -> None:
        """Evaluate a student's submission."""

        tutor = self.user_repo.find_by_id(tutor_id)
        if not tutor:
            raise UserNotFoundException(f"Tutor {tutor_id} not found")
        if not tutor.can_create_course():
            raise UnauthorizedException("User is not a tutor")

        enrollment = self.enrollment_repo.find_by_id(enrollment_id)
        if not enrollment:
            raise EnrollmentNotFoundException(f"Enrollment {enrollment_id} not found")

        course = self.course_repo.find_by_id(enrollment.course_id)
        if not course:
            raise CourseNotFoundException(f"Course {enrollment.course_id} not found")
        if course.tutor_id != tutor_id:
            raise UnauthorizedException("Only course tutor can evaluate submissions")

        submission = enrollment.get_submission(assignment_id)
        if not submission:
            raise InvalidOperationException("Submission not found")

        submission.evaluate(grade, feedback)
        self.enrollment_repo.save(enrollment)


class CertificateService:
    """Handles certificate issuance."""

    def __init__(
        self,
        certificate_repo: CertificateRepository,
        enrollment_repo: EnrollmentRepository,
        course_repo: CourseRepository,
        user_repo: UserRepository,
    ):
        self.certificate_repo = certificate_repo
        self.enrollment_repo = enrollment_repo
        self.course_repo = course_repo
        self.user_repo = user_repo

    def issue_certificate(
        self, tutor_id: UserId, enrollment_id: EnrollmentId
    ) -> Certificate:
        """Issue a certificate for course completion."""

        tutor = self.user_repo.find_by_id(tutor_id)
        if not tutor:
            raise UserNotFoundException(f"Tutor {tutor_id} not found")
        if not tutor.can_create_course():
            raise UnauthorizedException("User is not a tutor")

        enrollment = self.enrollment_repo.find_by_id(enrollment_id)
        if not enrollment:
            raise EnrollmentNotFoundException(f"Enrollment {enrollment_id} not found")

        course = self.course_repo.find_by_id(enrollment.course_id)
        if not course:
            raise CourseNotFoundException(f"Course {enrollment.course_id} not found")
        if course.tutor_id != tutor_id:
            raise UnauthorizedException("Only course tutor can issue certificates")

        existing = self.certificate_repo.find_by_enrollment(enrollment_id)
        if existing:
            raise InvalidOperationException(
                "Certificate already issued for this enrollment"
            )

        if not self._is_course_completed(course, enrollment):
            raise InvalidOperationException("Course requirements not completed")

        certificate = Certificate(
            certificate_id=CertificateId(uuid4()),
            student_id=enrollment.student_id,
            course_id=enrollment.course_id,
            enrollment_id=enrollment_id,
        )

        enrollment.complete()
        self.enrollment_repo.save(enrollment)
        self.certificate_repo.save(certificate)

        return certificate

    def _is_course_completed(self, course: Course, enrollment: Enrollment) -> bool:
        """Check if all course requirements are met."""

        all_assignments: List[Assignment] = []
        for topic in course.get_topics():
            all_assignments.extend(topic.get_assignments())

        for assignment in all_assignments:
            submission = enrollment.get_submission(assignment.id)
            if not submission or not submission.is_evaluated():
                return False

        return True
