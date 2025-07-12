"""Unit tests for CertificateApplicationService."""

import pytest
from datetime import datetime
from uuid import uuid4

from src.lms.application.services import CertificateApplicationService
from src.lms.application.dtos import IssueCertificateRequest, CertificateResponse
from src.lms.application.exceptions import ApplicationException
from src.lms.domain import (
    UserId, Grade, Feedback
)


class TestCertificateApplicationService:
    """Test suite for CertificateApplicationService."""
    
    def test_issue_certificate_success(self, certificate_repo, enrollment_repo, 
                                      course_repo, user_repo, tutor_user, 
                                      student_user, enrollment, published_course):
        """Test successful certificate issuance."""
        # Arrange
        service = CertificateApplicationService(
            certificate_repo, enrollment_repo, course_repo, user_repo
        )
        
        # Complete all assignments
        for topic in published_course.get_topics():
            for assignment in topic.get_assignments():
                # Submit assignment
                enrollment.submit_assignment(
                    assignment_id=assignment.id,
                    content="Completed work"
                )
                
                # Grade it
                submissions = enrollment.get_submissions()
                submission = [s for s in submissions if s.assignment_id == assignment.id][0]
                submission.evaluate(
                    grade=Grade(90),
                    feedback=Feedback("Well done!")
                )
        
        # Mark enrollment as completed
        enrollment.complete()
        enrollment_repo.save(enrollment)
        
        request = IssueCertificateRequest(enrollment_id=enrollment.id)
        
        # Act
        response = service.issue_certificate(tutor_user.id, request)
        
        # Assert
        assert isinstance(response, CertificateResponse)
        assert response.student_id == student_user.id
        assert response.course_id == published_course.id
        assert response.enrollment_id == enrollment.id
        assert response.status == "ISSUED"
        assert response.issue_date is not None
        
        # Verify certificate was saved
        saved_cert = certificate_repo.find_by_id(response.id)
        assert saved_cert is not None
    
    def test_issue_certificate_unauthorized_tutor(self, certificate_repo, enrollment_repo,
                                                 course_repo, user_repo, enrollment):
        """Test non-course tutor cannot issue certificates."""
        # Arrange
        # Create another tutor
        from src.lms.domain import User, EmailAddress, UserRole
        other_tutor = User(
            user_id=UserId(uuid4()),
            email=EmailAddress("other@tutor.com"),
            name="Other Tutor",
            role=UserRole.TUTOR
        )
        user_repo.save(other_tutor)
        
        service = CertificateApplicationService(
            certificate_repo, enrollment_repo, course_repo, user_repo
        )
        request = IssueCertificateRequest(enrollment_id=enrollment.id)
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.issue_certificate(other_tutor.id, request)
        
        assert "not the course tutor" in str(exc_info.value)
    
    def test_issue_certificate_incomplete_enrollment(self, certificate_repo, enrollment_repo,
                                                    course_repo, user_repo, tutor_user,
                                                    enrollment):
        """Test cannot issue certificate for incomplete enrollment."""
        # Arrange
        service = CertificateApplicationService(
            certificate_repo, enrollment_repo, course_repo, user_repo
        )
        request = IssueCertificateRequest(enrollment_id=enrollment.id)
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.issue_certificate(tutor_user.id, request)
        
        assert "not completed" in str(exc_info.value)
    
    def test_issue_certificate_duplicate(self, certificate_repo, enrollment_repo,
                                        course_repo, user_repo, tutor_user,
                                        student_user, enrollment, published_course):
        """Test cannot issue duplicate certificate."""
        # Arrange
        service = CertificateApplicationService(
            certificate_repo, enrollment_repo, course_repo, user_repo
        )
        
        # Complete enrollment
        for topic in published_course.get_topics():
            for assignment in topic.get_assignments():
                enrollment.submit_assignment(
                    assignment_id=assignment.id,
                    content="Completed"
                )
                submission = enrollment.get_submissions()[-1]
                submission.evaluate(Grade(85), Feedback("Good"))
        
        enrollment.complete()
        enrollment_repo.save(enrollment)
        
        request = IssueCertificateRequest(enrollment_id=enrollment.id)
        
        # Issue first certificate
        service.issue_certificate(tutor_user.id, request)
        
        # Act & Assert - Try to issue again
        with pytest.raises(ApplicationException) as exc_info:
            service.issue_certificate(tutor_user.id, request)
        
        assert "already issued" in str(exc_info.value)
    
    def test_issue_certificate_student_cannot_issue(self, certificate_repo, enrollment_repo,
                                                   course_repo, user_repo, student_user,
                                                   enrollment):
        """Test student cannot issue their own certificate."""
        # Arrange
        service = CertificateApplicationService(
            certificate_repo, enrollment_repo, course_repo, user_repo
        )
        request = IssueCertificateRequest(enrollment_id=enrollment.id)
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.issue_certificate(student_user.id, request)
        
        assert "User not found" in str(exc_info.value) or "not a tutor" in str(exc_info.value)
    
    def test_get_certificate_success(self, certificate_repo, enrollment_repo,
                                    course_repo, user_repo, tutor_user,
                                    student_user, enrollment, published_course):
        """Test getting certificate details."""
        # Arrange
        service = CertificateApplicationService(
            certificate_repo, enrollment_repo, course_repo, user_repo
        )
        
        # Complete enrollment and issue certificate
        for topic in published_course.get_topics():
            for assignment in topic.get_assignments():
                enrollment.submit_assignment(assignment.id, "Done")
                submission = enrollment.get_submissions()[-1]
                submission.evaluate(Grade(95), Feedback("Excellent"))
        
        enrollment.complete()
        enrollment_repo.save(enrollment)
        
        cert_response = service.issue_certificate(
            tutor_user.id,
            IssueCertificateRequest(enrollment_id=enrollment.id)
        )
        
        # Act
        response = service.get_certificate(cert_response.id)
        
        # Assert
        assert isinstance(response, CertificateResponse)
        assert response.id == cert_response.id
        assert response.student_id == student_user.id
        assert response.course_id == published_course.id
    
    def test_get_certificate_not_found(self, certificate_repo, enrollment_repo,
                                      course_repo, user_repo):
        """Test getting non-existent certificate."""
        # Arrange
        service = CertificateApplicationService(
            certificate_repo, enrollment_repo, course_repo, user_repo
        )
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.get_certificate(uuid4())
        
        assert "Certificate not found" in str(exc_info.value)
    
    def test_list_student_certificates(self, certificate_repo, enrollment_repo,
                                      course_repo, user_repo, tutor_user,
                                      student_user):
        """Test listing all certificates for a student."""
        # Arrange
        from src.lms.domain import (
            Course, CourseId, CourseTitle, CourseDescription,
            Duration, DateRange, TargetAudience, TopicTitle, TopicDescription,
            AssignmentTitle, AssignmentDescription, Enrollment, Certificate
        )
        
        # Create two courses and complete them
        certificates_issued = []
        
        for i in range(2):
            # Create course
            course = Course(
                course_id=CourseId(uuid4()),
                title=CourseTitle(f"Course {i+1}"),
                description=CourseDescription(f"Description {i+1}"),
                tutor_id=tutor_user.user_id.value,
                duration=Duration(4),
                date_range=DateRange(
                    datetime.now().date(),
                    datetime.now().date()
                ),
                target_audience=TargetAudience("Students")
            )
            
            # Add content
            course.add_topic(
                title=TopicTitle("Topic 1"),
                description=TopicDescription("Topic description")
            )
            topic = course.get_topics()[0]
            course.add_assignment(
                topic_id=topic.id,
                title=AssignmentTitle("Assignment 1"),
                description=AssignmentDescription("Do this"),
                deadline=datetime.now().date()
            )
            
            course.publish()
            course_repo.save(course)
            
            # Create enrollment
            enrollment = Enrollment.create(
                student_id=student_user.user_id,
                course_id=course.course_id
            )
            
            # Complete assignments
            assignment = topic.get_assignments()[0]
            enrollment.submit_assignment(assignment.id, "Completed")
            submission = enrollment.get_submissions()[0]
            submission.evaluate(Grade(90), Feedback("Good"))
            
            enrollment.complete()
            enrollment_repo.save(enrollment)
            
            # Issue certificate
            service = CertificateApplicationService(
                certificate_repo, enrollment_repo, course_repo, user_repo
            )
            cert = service.issue_certificate(
                tutor_user.id,
                IssueCertificateRequest(enrollment_id=enrollment.id)
            )
            certificates_issued.append(cert)
        
        # Act
        certificates = service.list_student_certificates(student_user.id)
        
        # Assert
        assert len(certificates) == 2
        cert_ids = [c.id for c in certificates]
        for issued_cert in certificates_issued:
            assert issued_cert.id in cert_ids
    
    def test_list_student_certificates_empty(self, certificate_repo, enrollment_repo,
                                            course_repo, user_repo, student_user):
        """Test listing certificates for student with none."""
        # Arrange
        service = CertificateApplicationService(
            certificate_repo, enrollment_repo, course_repo, user_repo
        )
        
        # Act
        certificates = service.list_student_certificates(student_user.id)
        
        # Assert
        assert certificates == []
    
    def test_certificate_response_structure(self, certificate_repo, enrollment_repo,
                                           course_repo, user_repo, tutor_user,
                                           student_user, enrollment, published_course):
        """Test CertificateResponse DTO structure."""
        # Arrange
        service = CertificateApplicationService(
            certificate_repo, enrollment_repo, course_repo, user_repo
        )
        
        # Complete enrollment
        for topic in published_course.get_topics():
            for assignment in topic.get_assignments():
                enrollment.submit_assignment(assignment.id, "Done")
                submission = enrollment.get_submissions()[-1]
                submission.evaluate(Grade(88), Feedback("Good work"))
        
        enrollment.complete()
        enrollment_repo.save(enrollment)
        
        # Act
        response = service.issue_certificate(
            tutor_user.id,
            IssueCertificateRequest(enrollment_id=enrollment.id)
        )
        
        # Assert
        assert hasattr(response, 'id')
        assert hasattr(response, 'student_id')
        assert hasattr(response, 'course_id')
        assert hasattr(response, 'enrollment_id')
        assert hasattr(response, 'issue_date')
        assert hasattr(response, 'status')
        
        # Verify types
        assert isinstance(response.id, type(uuid4()))
        assert isinstance(response.student_id, type(uuid4()))
        assert isinstance(response.course_id, type(uuid4()))
        assert isinstance(response.enrollment_id, type(uuid4()))
        assert isinstance(response.issue_date, datetime)
        assert isinstance(response.status, str)
