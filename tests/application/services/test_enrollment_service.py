"""Unit tests for EnrollmentApplicationService."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.lms.application.services import EnrollmentApplicationService
from src.lms.application.dtos import (
    EnrollStudentRequest, SubmitAssignmentRequest,
    EvaluateSubmissionRequest, EnrollmentResponse, SubmissionResponse
)
from src.lms.application.exceptions import ApplicationException
from src.lms.domain import (
    SubmissionStatus, UserId, EnrollmentId, Enrollment
)


class TestEnrollmentApplicationService:
    """Test suite for EnrollmentApplicationService."""
    
    def test_enroll_student_success(self, enrollment_repo, course_repo, user_repo, 
                                   student_user, published_course):
        """Test successful student enrollment."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        request = EnrollStudentRequest(course_id=published_course.id)
        
        # Act
        response = service.enroll_student(student_user.id, request)
        
        # Assert
        assert isinstance(response, EnrollmentResponse)
        assert response.student_id == student_user.id
        assert response.course_id == published_course.id
        assert response.status == "ACTIVE"
        assert response.submissions == []
        assert response.enrollment_date is not None
        
        # Verify enrollment was saved
        saved_enrollment = enrollment_repo.find_by_id(EnrollmentId(response.id))
        assert saved_enrollment is not None
    
    def test_enroll_student_non_existent_course(self, enrollment_repo, course_repo, 
                                               user_repo, student_user):
        """Test enrollment in non-existent course."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        request = EnrollStudentRequest(course_id=uuid4())
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.enroll_student(student_user.id, request)
        
        assert "Course not found" in str(exc_info.value)
    
    def test_enroll_student_draft_course(self, enrollment_repo, course_repo, user_repo,
                                        student_user, sample_course):
        """Test cannot enroll in draft course."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        request = EnrollStudentRequest(course_id=sample_course.id)
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.enroll_student(student_user.id, request)
        
        assert "Course is not published" in str(exc_info.value)
    
    def test_enroll_student_duplicate(self, enrollment_repo, course_repo, user_repo,
                                     student_user, published_course, enrollment):
        """Test cannot enroll in same course twice."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        request = EnrollStudentRequest(course_id=published_course.id)
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.enroll_student(student_user.id, request)
        
        assert "already enrolled" in str(exc_info.value)
    
    def test_enroll_tutor_as_student(self, enrollment_repo, course_repo, user_repo,
                                     tutor_user, published_course):
        """Test tutor cannot enroll as student."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        request = EnrollStudentRequest(course_id=published_course.id)
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.enroll_student(tutor_user.id, request)
        
        assert "Only students can enroll" in str(exc_info.value)
    
    def test_submit_assignment_success(self, enrollment_repo, course_repo, user_repo,
                                      student_user, enrollment, published_course):
        """Test successful assignment submission."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        
        # Get an assignment from the course
        assignment = published_course.get_topics()[0].get_assignments()[0]
        
        request = SubmitAssignmentRequest(
            assignment_id=assignment.id,
            content="def hello_world():\n    print('Hello, World!')"
        )
        
        # Act
        response = service.submit_assignment(
            student_user.id, enrollment.id, request
        )
        
        # Assert
        assert isinstance(response, SubmissionResponse)
        assert response.assignment_id == assignment.id
        assert response.content == "def hello_world():\n    print('Hello, World!')"
        assert response.status == "SUBMITTED"
        assert response.grade is None  # Not graded yet
        assert response.feedback is None
        assert response.submitted_at is not None
        
        # Verify submission was saved
        saved_enrollment = enrollment_repo.find_by_id(enrollment.enrollment_id)
        submissions = saved_enrollment.get_submissions()
        assert len(submissions) == 1
        assert submissions[0].assignment_id == assignment.id
    
    def test_submit_assignment_unauthorized(self, enrollment_repo, course_repo, user_repo,
                                           student_user, enrollment, published_course):
        """Test cannot submit to another student's enrollment."""
        # Arrange
        # Create another student
        from src.lms.domain import User, EmailAddress, UserRole
        other_student = User(
            user_id=UserId(uuid4()),
            email=EmailAddress("other@student.com"),
            name="Other Student",
            role=UserRole.STUDENT
        )
        user_repo.save(other_student)
        
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        assignment = published_course.get_topics()[0].get_assignments()[0]
        request = SubmitAssignmentRequest(
            assignment_id=assignment.id,
            content="Unauthorized submission"
        )
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.submit_assignment(
                other_student.id, enrollment.id, request
            )
        
        assert "Not authorized" in str(exc_info.value)
    
    def test_submit_assignment_not_in_course(self, enrollment_repo, course_repo, user_repo,
                                            student_user, enrollment):
        """Test cannot submit assignment from different course."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        
        # Use a random assignment ID not in the enrolled course
        request = SubmitAssignmentRequest(
            assignment_id=uuid4(),
            content="Assignment from wrong course"
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.submit_assignment(
                student_user.id, enrollment.id, request
            )
        
        assert "Assignment not found in course" in str(exc_info.value)
    
    def test_submit_assignment_duplicate(self, enrollment_repo, course_repo, user_repo,
                                        student_user, enrollment, published_course):
        """Test cannot submit same assignment twice."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        assignment = published_course.get_topics()[0].get_assignments()[0]
        
        # First submission
        request = SubmitAssignmentRequest(
            assignment_id=assignment.id,
            content="First submission"
        )
        service.submit_assignment(student_user.id, enrollment.id, request)
        
        # Second submission attempt
        request2 = SubmitAssignmentRequest(
            assignment_id=assignment.id,
            content="Second submission"
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.submit_assignment(student_user.id, enrollment.id, request2)
        
        assert "already submitted" in str(exc_info.value)
    
    def test_evaluate_submission_success(self, enrollment_repo, course_repo, user_repo,
                                        tutor_user, student_user, enrollment, published_course):
        """Test successful submission evaluation."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        
        # Submit an assignment first
        assignment = published_course.get_topics()[0].get_assignments()[0]
        submit_request = SubmitAssignmentRequest(
            assignment_id=assignment.id,
            content="Student's solution"
        )
        service.submit_assignment(student_user.id, enrollment.id, submit_request)
        
        # Evaluate the submission
        eval_request = EvaluateSubmissionRequest(
            grade=85,
            feedback="Good work! Consider adding more comments."
        )
        
        # Act
        service.evaluate_submission(
            tutor_user.id, enrollment.id, assignment.id, eval_request
        )
        
        # Assert - Get the updated enrollment
        updated_enrollment = enrollment_repo.find_by_id(enrollment.enrollment_id)
        submission = updated_enrollment.get_submissions()[0]
        assert submission.status == SubmissionStatus.GRADED
        assert submission.grade.value == 85
        assert submission.feedback.value == "Good work! Consider adding more comments."
    
    def test_evaluate_submission_unauthorized(self, enrollment_repo, course_repo, user_repo,
                                             student_user, enrollment, published_course):
        """Test non-tutor cannot evaluate submissions."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        
        # Submit an assignment
        assignment = published_course.get_topics()[0].get_assignments()[0]
        submit_request = SubmitAssignmentRequest(
            assignment_id=assignment.id,
            content="Student's solution"
        )
        service.submit_assignment(student_user.id, enrollment.id, submit_request)
        
        # Try to evaluate as another student
        eval_request = EvaluateSubmissionRequest(
            grade=90,
            feedback="Great!"
        )
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.evaluate_submission(
                student_user.id, enrollment.id, assignment.id, eval_request
            )
        
        assert "not the course tutor" in str(exc_info.value)
    
    def test_evaluate_submission_invalid_grade(self, enrollment_repo, course_repo, user_repo,
                                              tutor_user, student_user, enrollment, published_course):
        """Test evaluation with invalid grade."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        
        # Submit an assignment
        assignment = published_course.get_topics()[0].get_assignments()[0]
        submit_request = SubmitAssignmentRequest(
            assignment_id=assignment.id,
            content="Student's solution"
        )
        service.submit_assignment(student_user.id, enrollment.id, submit_request)
        
        # Try to evaluate with invalid grade
        eval_request = EvaluateSubmissionRequest(
            grade=150,  # Over 100
            feedback="Impossible grade"
        )
        
        # Act & Assert
        with pytest.raises(ApplicationException):
            service.evaluate_submission(
                tutor_user.id, enrollment.id, assignment.id, eval_request
            )
    
    def test_evaluate_non_existent_submission(self, enrollment_repo, course_repo, user_repo,
                                             tutor_user, enrollment, published_course):
        """Test evaluation of non-existent submission."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        assignment = published_course.get_topics()[0].get_assignments()[0]
        
        eval_request = EvaluateSubmissionRequest(
            grade=80,
            feedback="Good"
        )
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.evaluate_submission(
                tutor_user.id, enrollment.id, assignment.id, eval_request
            )
        
        assert "Submission not found" in str(exc_info.value)
    
    def test_get_enrollment_success(self, enrollment_repo, course_repo, user_repo, enrollment):
        """Test getting enrollment details."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        
        # Act
        response = service.get_enrollment(enrollment.id)
        
        # Assert
        assert isinstance(response, EnrollmentResponse)
        assert response.id == enrollment.id
        assert response.student_id == enrollment.student_id
        assert response.course_id == enrollment.course_id
        assert response.status == enrollment.status.value
    
    def test_get_enrollment_not_found(self, enrollment_repo, course_repo, user_repo):
        """Test getting non-existent enrollment."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.get_enrollment(uuid4())
        
        assert "Enrollment not found" in str(exc_info.value)
    
    def test_list_student_enrollments(self, enrollment_repo, course_repo, user_repo,
                                     student_user, enrollment):
        """Test listing student's enrollments."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        
        # Create another enrollment for the same student
        from src.lms.domain import Course, CourseId, CourseTitle, CourseDescription, Duration, DateRange, TargetAudience
        another_course = Course(
            course_id=CourseId(uuid4()),
            title=CourseTitle("Another Course"),
            description=CourseDescription("Second course"),
            tutor_id=enrollment.course_id,  # Reuse tutor
            duration=Duration(6),
            date_range=DateRange(
                datetime.now().date(),
                (datetime.now() + timedelta(weeks=6)).date()
            ),
            target_audience=TargetAudience("Students")
        )
        another_course.add_topic(
            title="Topic 1",
            description="First topic"
        )
        another_course.publish()
        course_repo.save(another_course)
        
        # Enroll in second course
        second_enrollment = Enrollment.create(
            student_id=student_user.user_id,
            course_id=another_course.course_id
        )
        enrollment_repo.save(second_enrollment)
        
        # Act
        enrollments = service.list_student_enrollments(student_user.id)
        
        # Assert
        assert len(enrollments) == 2
        enrollment_ids = [e.id for e in enrollments]
        assert enrollment.id in enrollment_ids
        assert second_enrollment.id in enrollment_ids
    
    def test_list_course_enrollments(self, enrollment_repo, course_repo, user_repo,
                                    published_course, enrollment):
        """Test listing course enrollments."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        
        # Create another student and enroll them
        from src.lms.domain import User, EmailAddress, UserRole
        another_student = User(
            user_id=UserId(uuid4()),
            email=EmailAddress("another@student.com"),
            name="Another Student",
            role=UserRole.STUDENT
        )
        user_repo.save(another_student)
        
        another_enrollment = Enrollment.create(
            student_id=another_student.user_id,
            course_id=published_course.course_id
        )
        enrollment_repo.save(another_enrollment)
        
        # Act
        enrollments = service.list_course_enrollments(published_course.id)
        
        # Assert
        assert len(enrollments) == 2
        student_ids = [e.student_id for e in enrollments]
        assert enrollment.student_id in student_ids
        assert another_enrollment.student_id in student_ids
    
    def test_submission_response_structure(self, enrollment_repo, course_repo, user_repo,
                                          student_user, enrollment, published_course):
        """Test SubmissionResponse DTO structure."""
        # Arrange
        service = EnrollmentApplicationService(enrollment_repo, course_repo, user_repo)
        assignment = published_course.get_topics()[0].get_assignments()[0]
        
        # Submit and get response
        request = SubmitAssignmentRequest(
            assignment_id=assignment.id,
            content="Test submission"
        )
        
        # Act
        response = service.submit_assignment(
            student_user.id, enrollment.id, request
        )
        
        # Assert
        assert hasattr(response, 'id')
        assert hasattr(response, 'assignment_id')
        assert hasattr(response, 'content')
        assert hasattr(response, 'submitted_at')
        assert hasattr(response, 'status')
        assert hasattr(response, 'grade')
        assert hasattr(response, 'feedback')
        
        # Verify types
        assert isinstance(response.id, type(uuid4()))
        assert isinstance(response.assignment_id, type(uuid4()))
        assert isinstance(response.content, str)
        assert isinstance(response.submitted_at, datetime)
        assert isinstance(response.status, str)
