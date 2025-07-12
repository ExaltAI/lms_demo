"""Enrollment application service."""

from typing import List
from uuid import UUID

from ...domain import (
    EnrollmentService,
    EvaluationService,
    UserId,
    CourseId,
    EnrollmentId,
    AssignmentId,
    Grade,
    Feedback,
    EnrollmentRepository,
    CourseRepository,
    UserRepository,
    DomainException,
)
from ..dtos import (
    EnrollStudentRequest,
    SubmitAssignmentRequest,
    EvaluateSubmissionRequest,
    EnrollmentResponse,
    SubmissionResponse,
)
from ..exceptions import ApplicationException


class EnrollmentApplicationService:
    """Application service for enrollment operations.

    This service manages the student journey through courses:
    - Enrollment in courses
    - Assignment submission
    - Submission evaluation
    - Progress tracking

    It delegates complex business logic to domain services while
    handling cross-cutting concerns like authorization and error translation.
    """

    def __init__(
        self,
        enrollment_repo: EnrollmentRepository,
        course_repo: CourseRepository,
        user_repo: UserRepository,
    ):
        # Direct repository access for simple queries
        self.enrollment_repo = enrollment_repo

        # Domain services handle complex cross-aggregate operations
        # This keeps the application service thin and focused on orchestration
        self.enrollment_service = EnrollmentService(
            enrollment_repo, course_repo, user_repo
        )
        self.evaluation_service = EvaluationService(
            enrollment_repo, course_repo, user_repo
        )

    def enroll_student(
        self, student_id: UUID, request: EnrollStudentRequest
    ) -> EnrollmentResponse:
        """Enroll student in course.

        This delegates to a domain service because enrollment involves
        multiple aggregates:
        - Verify student exists and has student role
        - Verify course exists and is published
        - Check for duplicate enrollments
        - Create new enrollment aggregate

        The domain service encapsulates these complex rules.
        """
        try:
            # Domain service handles all business rules and cross-aggregate validation
            enrollment = self.enrollment_service.enroll_student(
                student_id=UserId(student_id),  # From auth context
                course_id=CourseId(request.course_id),
            )
            return self._to_response(enrollment)
        except DomainException as e:
            # Translate domain exceptions to application exceptions
            # This provides a consistent error interface for the API layer
            raise ApplicationException(str(e))

    def submit_assignment(
        self, student_id: UUID, enrollment_id: UUID, request: SubmitAssignmentRequest
    ) -> SubmissionResponse:
        """Submit assignment.

        Assignment submission is handled within the enrollment aggregate
        because submissions are part of the enrollment lifecycle.
        This maintains consistency within the aggregate boundary.
        """
        # Load the enrollment aggregate
        enrollment = self.enrollment_repo.find_by_id(EnrollmentId(enrollment_id))
        if not enrollment:
            raise ApplicationException("Enrollment not found")

        # Authorization check: ensure the authenticated student owns this enrollment
        # This prevents students from submitting to other students' enrollments
        if enrollment.student_id != UserId(student_id):
            raise ApplicationException("Not authorized to submit for this enrollment")

        try:
            # Domain method handles business rules:
            # - Assignment must exist in the course
            # - Deadline enforcement
            # - Duplicate submission prevention
            submission = enrollment.submit_assignment(
                assignment_id=AssignmentId(request.assignment_id),
                content=request.content,
            )

            # Save the entire aggregate with the new submission
            self.enrollment_repo.save(enrollment)
            return self._to_submission_response(submission)
        except ValueError as e:
            # Domain raises ValueError for business rule violations
            raise ApplicationException(str(e))

    def evaluate_submission(
        self,
        tutor_id: UUID,
        enrollment_id: UUID,
        assignment_id: UUID,
        request: EvaluateSubmissionRequest,
    ) -> None:
        """Evaluate student submission.

        Evaluation is another cross-aggregate operation delegated to
        a domain service because it needs to:
        - Verify the tutor owns the course
        - Find the submission within the enrollment
        - Apply grading business rules
        - Update submission status

        Note: This returns None because the evaluation is a command,
        not a query. Clients can fetch updated enrollment if needed.
        """
        try:
            # Domain service handles authorization and business rules
            self.evaluation_service.evaluate_submission(
                tutor_id=UserId(tutor_id),  # From auth context
                enrollment_id=EnrollmentId(enrollment_id),
                assignment_id=AssignmentId(assignment_id),
                grade=Grade(request.grade),  # Value object validates grade range
                feedback=Feedback(request.feedback),  # Value object ensures non-empty
            )
        except DomainException as e:
            # Could be authorization error or business rule violation
            raise ApplicationException(str(e))

    def get_enrollment(self, enrollment_id: UUID) -> EnrollmentResponse:
        """Get enrollment details.

        Simple query operation - no authorization needed as enrollments
        are not sensitive (students can see each other's enrollment status).
        In a real system, might filter submission details based on viewer.
        """
        enrollment = self.enrollment_repo.find_by_id(EnrollmentId(enrollment_id))
        if not enrollment:
            raise ApplicationException("Enrollment not found")
        return self._to_response(enrollment)

    def list_student_enrollments(self, student_id: UUID) -> List[EnrollmentResponse]:
        """List student's enrollments.

        Returns all enrollments for a student across all courses.
        Used for student dashboards and progress tracking.
        """
        enrollments = self.enrollment_repo.find_by_student(UserId(student_id))
        return [self._to_response(e) for e in enrollments]

    def list_course_enrollments(self, course_id: UUID) -> List[EnrollmentResponse]:
        """List course enrollments.

        Returns all enrollments for a course. Used by tutors to
        see class roster and track overall progress.

        Note: In production, might need pagination for large courses.
        """
        enrollments = self.enrollment_repo.find_by_course(CourseId(course_id))
        return [self._to_response(e) for e in enrollments]

    def _to_response(self, enrollment) -> EnrollmentResponse:
        """Convert enrollment to response DTO.

        Includes all submissions for progress tracking.
        This denormalization is acceptable for reasonable submission counts.
        """
        return EnrollmentResponse(
            id=enrollment.id,  # Property returns primitive UUID
            student_id=enrollment.student_id,  # Already primitive
            course_id=enrollment.course_id,  # Already primitive
            enrollment_date=enrollment.enrollment_date,
            status=enrollment.status.value,  # Enum to string
            # Include all submissions for complete progress view
            submissions=[
                self._to_submission_response(s) for s in enrollment.get_submissions()
            ],
        )

    def _to_submission_response(self, submission) -> SubmissionResponse:
        """Convert submission to response DTO.

        Handles optional fields gracefully - grade and feedback
        are None until evaluation occurs.
        """
        return SubmissionResponse(
            id=submission.id,
            assignment_id=submission.assignment_id,
            content=submission.content,
            submitted_at=submission.submitted_at,
            status=submission.status.value,
            # Conditional unwrapping of value objects
            # These are None before evaluation, demonstrating the workflow
            grade=submission.grade.value if submission.grade else None,
            feedback=submission.feedback.value if submission.feedback else None,
        )
