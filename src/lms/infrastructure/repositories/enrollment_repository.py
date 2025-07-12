"""Enrollment repository implementation.

This module provides the SQLAlchemy-based implementation of the EnrollmentRepository
interface. It handles all database operations related to student enrollments in courses,
including their assignment submissions.

The repository manages the relationship between students and courses, tracking enrollment
status and all submission records associated with each enrollment.
"""

from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from ...domain import (
    Enrollment,
    Submission,
    EnrollmentId,
    SubmissionId,
    UserId,
    CourseId,
    AssignmentId,
    Grade,
    Feedback,
)
from ..database import EnrollmentModel, SubmissionModel


class SQLEnrollmentRepository:
    """SQL implementation of EnrollmentRepository.

    This class provides concrete implementations for enrollment-related database
    operations using SQLAlchemy. It handles the conversion between domain entities
    and database models for enrollments and their associated submissions.

    The repository ensures data consistency between enrollments and submissions,
    managing the lifecycle of student participation in courses.

    Attributes:
        session: SQLAlchemy database session for executing queries
    """

    def __init__(self, session: Session):
        """Initialize the repository with a database session.

        Args:
            session: SQLAlchemy session for database operations.
                Should typically be obtained from Database.get_session()
        """
        self.session = session

    def save(self, enrollment: Enrollment) -> None:
        """Save or update an enrollment and its submissions.

        This method performs an "upsert" operation for enrollments and manages
        all associated submissions. It only updates the enrollment status if the
        enrollment already exists (enrollment date and IDs are immutable).

        Args:
            enrollment: Enrollment domain entity to persist, including all submissions

        Note:
            - New submissions are added, existing submissions are updated
            - Submission deletion is not handled by this method
            - The actual database commit is handled by the session context manager
        """
        model = self.session.query(EnrollmentModel).filter_by(id=enrollment.id).first()

        if not model:
            model = EnrollmentModel(
                id=enrollment.id,
                student_id=enrollment.student_id,
                course_id=enrollment.course_id,
                enrollment_date=enrollment.enrollment_date,
                status=enrollment.status,  # Enum is stored directly
            )
            self.session.add(model)
        else:
            model.status = enrollment.status

        self._update_submissions(model, enrollment)

    def find_by_id(self, enrollment_id: EnrollmentId) -> Optional[Enrollment]:
        """Find an enrollment by its unique identifier.

        This method uses eager loading to fetch the enrollment with all its
        submissions in a single query, avoiding the N+1 query problem.

        Args:
            enrollment_id: The unique identifier (UUID) of the enrollment

        Returns:
            Enrollment domain entity with all submissions if found, None otherwise
        """

        model = (
            self.session.query(EnrollmentModel)
            .options(joinedload(EnrollmentModel.submissions))
            .filter_by(id=enrollment_id)
            .first()
        )

        if not model:
            return None
        return self._to_entity(model)

    def find_by_student(self, student_id: UserId) -> List[Enrollment]:
        """Find all enrollments for a specific student.

        Args:
            student_id: The unique identifier of the student

        Returns:
            List of Enrollment domain entities for the student.
            Empty list if the student has no enrollments.

        Note:
            This method loads enrollments without their submissions for
            performance. Use find_by_id() if you need submission details.
        """
        models = (
            self.session.query(EnrollmentModel).filter_by(student_id=student_id).all()
        )
        return [self._to_entity(m) for m in models]

    def find_by_course(self, course_id: CourseId) -> List[Enrollment]:
        """Find all enrollments for a specific course.

        Args:
            course_id: The unique identifier of the course

        Returns:
            List of Enrollment domain entities for the course.
            Empty list if the course has no enrollments.

        Note:
            Useful for generating class rosters or analyzing course participation.
        """
        models = (
            self.session.query(EnrollmentModel).filter_by(course_id=course_id).all()
        )
        return [self._to_entity(m) for m in models]

    def find_by_student_and_course(
        self, student_id: UserId, course_id: CourseId
    ) -> Optional[Enrollment]:
        """Find a specific enrollment by student and course combination.

        This method is useful for checking if a student is enrolled in a
        specific course and retrieving their enrollment details.
        """

        model = (
            self.session.query(EnrollmentModel)
            .options(joinedload(EnrollmentModel.submissions))
            .filter_by(student_id=student_id, course_id=course_id)
            .first()
        )

        if not model:
            return None

        return self._to_entity(model)

    def _update_submissions(
        self, model: EnrollmentModel, enrollment: Enrollment
    ) -> None:
        """Update submissions associated with an enrollment.

        This method synchronizes the submissions in the database with those in
        the domain entity. It creates new submissions and updates existing ones.
        Note that submission deletion is not implemented as submissions should
        be preserved for academic records.

        We're intentionally not deleting submissions here
        Because academic records should be preserved, even if a student "deletes" their work
        """
        # Update or create submissions
        # We're iterating over the submissions in the domain entity
        # And updating or creating the corresponding submissions in the database
        for submission in enrollment.get_submissions():
            submission_model = next(
                (s for s in model.submissions if s.id == submission.id), None
            )

            if not submission_model:
                submission_model = SubmissionModel(
                    id=submission.id,
                    enrollment_id=model.id,
                    assignment_id=submission.assignment_id,
                    content=submission.content,
                    submitted_at=submission.submitted_at,
                    status=submission.status,
                    grade=submission.grade.value if submission.grade else None,
                    feedback=submission.feedback.value if submission.feedback else None,
                )
                model.submissions.append(submission_model)
            else:
                submission_model.status = submission.status
                submission_model.grade = (
                    submission.grade.value if submission.grade else None
                )
                submission_model.feedback = (
                    submission.feedback.value if submission.feedback else None
                )

    def _to_entity(self, model: EnrollmentModel) -> Enrollment:
        """Convert a database model to a domain entity.

        This method reconstructs the enrollment aggregate from the database
        models, including all submissions. It ensures proper initialization
        of all value objects and maintains the integrity of the domain model.

        Args:
            model: EnrollmentModel instance from the database

        Returns:
            Enrollment domain entity with all submissions properly initialized

        Note:
            - Direct field access is used for reconstruction to bypass
              domain validation during loading
            - Handles optional fields (grade, feedback) gracefully
        """

        enrollment = Enrollment(
            enrollment_id=EnrollmentId(model.id),
            student_id=UserId(model.student_id),
            course_id=CourseId(model.course_id),
        )

        enrollment.enrollment_date = model.enrollment_date
        enrollment.status = model.status

        for submission_model in model.submissions:
            submission = Submission(
                assignment_id=AssignmentId(submission_model.assignment_id),
                content=submission_model.content,
            )
            submission.id = SubmissionId(submission_model.id)
            submission.submitted_at = submission_model.submitted_at
            submission.status = submission_model.status

            if submission_model.grade is not None:
                submission.grade = Grade(submission_model.grade)

            if submission_model.feedback:
                submission.feedback = Feedback(submission_model.feedback)

            enrollment._submissions.append(submission)

        return enrollment
