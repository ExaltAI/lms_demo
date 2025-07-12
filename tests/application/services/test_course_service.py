"""Unit tests for CourseApplicationService."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from pydantic import ValidationError

from src.lms.application.services import CourseApplicationService
from src.lms.application.dtos import (
    CreateCourseRequest, AddTopicRequest, AddAssignmentRequest,
    AddResourceRequest, CourseResponse
)
from src.lms.application.exceptions import ApplicationException
from src.lms.domain import CourseStatus, User, UserId, EmailAddress, UserRole


class TestCourseApplicationService:
    """Test suite for CourseApplicationService."""
    
    def test_create_course_success(self, course_repo, user_repo, tutor_user):
        """Test successful course creation by tutor."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        request = CreateCourseRequest(
            title="Advanced Python Programming",
            description="Deep dive into Python's advanced features",
            duration_weeks=10,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(weeks=10)).date(),
            target_audience="Intermediate Python developers"
        )
        
        # Act
        response = service.create_course(tutor_user.id, request)
        
        # Assert
        assert isinstance(response, CourseResponse)
        assert response.title == "Advanced Python Programming"
        assert response.description == "Deep dive into Python's advanced features"
        assert response.tutor_id == tutor_user.id
        assert response.duration_weeks == 10
        assert response.status == "draft"
        assert response.topics == []
        
        # Verify course was saved
        saved_course = course_repo.find_by_id(response.id)
        assert saved_course is not None
    
    def test_create_course_invalid_tutor(self, course_repo, user_repo):
        """Test course creation with non-existent tutor."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        request = CreateCourseRequest(
            title="Test Course",
            description="Test description",
            duration_weeks=8,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(weeks=8)).date(),
            target_audience="Everyone"
        )
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.create_course(uuid4(), request)
        
        assert "Tutor not found" in str(exc_info.value)
    
    def test_create_course_student_unauthorized(self, course_repo, user_repo, student_user):
        """Test student cannot create courses."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        request = CreateCourseRequest(
            title="Unauthorized Course",
            description="Should not be created",
            duration_weeks=4,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(weeks=4)).date(),
            target_audience="Students"
        )
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.create_course(student_user.id, request)
        
        assert "not authorized to create courses" in str(exc_info.value)
    
    def test_create_course_invalid_dates(self, course_repo, user_repo, tutor_user):
        """Test creating course with end date before start date."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CreateCourseRequest(
                title="Invalid Course",
                description="This course has invalid dates",
                duration_weeks=8,
                start_date=datetime.now(),
                end_date=datetime.now() - timedelta(days=1),
                target_audience="Students"
            )
        
        # Verify it's a date validation error
        assert "End date must be after start date" in str(exc_info.value)
    
    def test_add_topic_success(self, course_repo, user_repo, sample_course, tutor_user):
        """Test adding topic to course."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        request = AddTopicRequest(
            title="Advanced Topics",
            description="More complex Python concepts"
        )
        
        # Act
        response = service.add_topic(tutor_user.id, sample_course.id, request)
        
        # Assert
        assert len(response.topics) == 2  # Original topic + new one
        new_topic = response.topics[1]
        assert new_topic.title == "Advanced Topics"
        assert new_topic.description == "More complex Python concepts"
        assert new_topic.order == 2
    
    def test_add_topic_unauthorized(self, course_repo, user_repo, sample_course, student_user):
        """Test non-tutor cannot add topics."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        request = AddTopicRequest(
            title="Unauthorized Topic",
            description="Should not be added"
        )
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.add_topic(student_user.id, sample_course.id, request)
        
        assert "Not authorized to modify this course" in str(exc_info.value)
    
    def test_add_topic_to_published_course(self, course_repo, user_repo, published_course, tutor_user):
        """Test cannot add topic to published course."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        request = AddTopicRequest(
            title="Late Topic",
            description="Cannot add to published course"
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.add_topic(tutor_user.id, published_course.id, request)
        
        assert "Cannot modify published course" in str(exc_info.value)
    
    def test_add_assignment_success(self, course_repo, user_repo, sample_course, tutor_user):
        """Test adding assignment to topic."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        topic_id = sample_course.get_topics()[0].id
        request = AddAssignmentRequest(
            title="Advanced Assignment",
            description="Implement a complex algorithm",
            deadline=(datetime.now() + timedelta(days=14)).date()
        )
        
        # Act
        response = service.add_assignment(
            tutor_user.id, sample_course.id, topic_id, request
        )
        
        # Assert
        topic = response.topics[0]
        assert len(topic.assignments) == 2  # Original + new one
        new_assignment = topic.assignments[1]
        assert new_assignment.title == "Advanced Assignment"
        assert new_assignment.description == "Implement a complex algorithm"
    
    def test_add_assignment_invalid_topic(self, course_repo, user_repo, sample_course, tutor_user):
        """Test adding assignment to non-existent topic."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        request = AddAssignmentRequest(
            title="Lost Assignment",
            description="No topic for this",
            deadline=(datetime.now() + timedelta(days=7)).date()
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.add_assignment(
                tutor_user.id, sample_course.id, uuid4(), request
            )
        
        assert "Topic not found" in str(exc_info.value)
    
    def test_add_resource_success(self, course_repo, user_repo, sample_course, tutor_user):
        """Test adding resource to topic."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        topic_id = sample_course.get_topics()[0].id
        request = AddResourceRequest(
            title="Python Documentation",
            url="https://docs.python.org"
        )
        
        # Act
        response = service.add_resource(
            tutor_user.id, sample_course.id, topic_id, request
        )
        
        # Assert
        topic = response.topics[0]
        assert len(topic.resources) == 1
        resource = topic.resources[0]
        assert resource.title == "Python Documentation"
        assert resource.url == "https://docs.python.org"
    
    def test_add_resource_invalid_url(self, course_repo, user_repo, sample_course, tutor_user):
        """Test adding resource with invalid URL."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        topic_id = sample_course.get_topics()[0].id
        request = AddResourceRequest(
            title="Bad Resource",
            url="not-a-valid-url"
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.add_resource(
                tutor_user.id, sample_course.id, topic_id, request
            )
        
        assert "Invalid URL format" in str(exc_info.value)
    
    def test_publish_course_success(self, course_repo, user_repo, sample_course, tutor_user):
        """Test publishing a course."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        
        # Act
        response = service.publish_course(tutor_user.id, sample_course.id)
        
        # Assert
        assert response.status == "PUBLISHED"
        
        # Verify in repository
        saved_course = course_repo.find_by_id(sample_course.course_id)
        assert saved_course.status == CourseStatus.PUBLISHED
    
    def test_publish_course_without_topics(self, course_repo, user_repo, tutor_user):
        """Test cannot publish course without topics."""
        # Arrange
        from src.lms.domain import Course, CourseId, CourseTitle, CourseDescription, Duration, DateRange, TargetAudience
        
        empty_course = Course(
            course_id=CourseId(uuid4()),
            title=CourseTitle("Empty Course"),
            description=CourseDescription("No content"),
            tutor_id=tutor_user.id,
            duration=Duration(4),
            date_range=DateRange(
                datetime.now().date(),
                (datetime.now() + timedelta(weeks=4)).date()
            ),
            target_audience=TargetAudience("Nobody")
        )
        course_repo.save(empty_course)
        
        service = CourseApplicationService(course_repo, user_repo)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.publish_course(tutor_user.id, empty_course.id)
        
        assert "Cannot publish course without topics" in str(exc_info.value)
    
    def test_get_course_success(self, course_repo, user_repo, sample_course):
        """Test getting course details."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        
        # Act
        response = service.get_course(sample_course.id)
        
        # Assert
        assert isinstance(response, CourseResponse)
        assert response.id == sample_course.id
        assert response.title == sample_course.title.value
        assert len(response.topics) == 1
        assert len(response.topics[0].assignments) == 1
    
    def test_get_course_not_found(self, course_repo, user_repo):
        """Test getting non-existent course."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.get_course(uuid4())
        
        assert "Course not found" in str(exc_info.value)
    
    def test_list_published_courses(self, course_repo, user_repo, sample_course, published_course):
        """Test listing only published courses."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        
        # Act
        courses = service.list_published_courses()
        
        # Assert
        assert len(courses) == 1
        assert courses[0].id == published_course.id
        assert courses[0].status == "PUBLISHED"
        
        # Verify draft course not included
        course_ids = [c.id for c in courses]
        assert sample_course.id not in course_ids
    
    def test_list_tutor_courses(self, course_repo, user_repo, tutor_user, sample_course, published_course):
        """Test listing all courses for a tutor."""
        # Arrange
        # Create another tutor with their own course
        other_tutor = User(
            user_id=UserId(uuid4()),
            email=EmailAddress("other@tutor.com"),
            name="Other Tutor",
            role=UserRole.TUTOR
        )
        user_repo.save(other_tutor)
        
        from src.lms.domain import Course, CourseId, CourseTitle, CourseDescription, Duration, DateRange, TargetAudience
        other_course = Course(
            course_id=CourseId(uuid4()),
            title=CourseTitle("Other Course"),
            description=CourseDescription("Not our tutor's course"),
            tutor_id=other_tutor.user_id.value,
            duration=Duration(6),
            date_range=DateRange(
                datetime.now().date(),
                (datetime.now() + timedelta(weeks=6)).date()
            ),
            target_audience=TargetAudience("Others")
        )
        course_repo.save(other_course)
        
        service = CourseApplicationService(course_repo, user_repo)
        
        # Act
        courses = service.list_tutor_courses(tutor_user.id)
        
        # Assert
        assert len(courses) == 2  # Both draft and published
        course_ids = [c.id for c in courses]
        assert sample_course.id in course_ids
        assert published_course.id in course_ids
        assert other_course.id not in course_ids
    
    def test_course_response_dto_structure(self, course_repo, user_repo, sample_course):
        """Test CourseResponse DTO has correct structure."""
        # Arrange
        service = CourseApplicationService(course_repo, user_repo)
        
        # Act
        response = service.get_course(sample_course.id)
        
        # Assert
        # Verify top-level fields
        assert hasattr(response, 'id')
        assert hasattr(response, 'title')
        assert hasattr(response, 'description')
        assert hasattr(response, 'tutor_id')
        assert hasattr(response, 'duration_weeks')
        assert hasattr(response, 'start_date')
        assert hasattr(response, 'end_date')
        assert hasattr(response, 'target_audience')
        assert hasattr(response, 'status')
        assert hasattr(response, 'topics')
        
        # Verify nested structure
        topic = response.topics[0]
        assert hasattr(topic, 'id')
        assert hasattr(topic, 'title')
        assert hasattr(topic, 'description')
        assert hasattr(topic, 'order')
        assert hasattr(topic, 'assignments')
        assert hasattr(topic, 'resources')
        
        assignment = topic.assignments[0]
        assert hasattr(assignment, 'id')
        assert hasattr(assignment, 'title')
        assert hasattr(assignment, 'description')
        assert hasattr(assignment, 'deadline')
