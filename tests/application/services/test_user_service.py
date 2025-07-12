"""Unit tests for UserApplicationService."""

import pytest
from uuid import uuid4
from pydantic import ValidationError

from src.lms.application.services import UserApplicationService
from src.lms.application.dtos import CreateUserRequest, UserResponse
from src.lms.application.exceptions import ApplicationException


class TestUserApplicationService:
    """Test suite for UserApplicationService."""
    
    def test_create_user_success(self, user_repo):
        """Test successful user creation."""
        # Arrange
        service = UserApplicationService(user_repo)
        request = CreateUserRequest(
            email="newuser@test.com",
            name="New User",
            role="student"
        )
        
        # Act
        response = service.create_user(request)
        
        # Assert
        assert isinstance(response, UserResponse)
        assert response.email == "newuser@test.com"
        assert response.name == "New User"
        assert response.role == "student"
        assert response.id is not None
        
        # Verify user was saved
        saved_user = user_repo.find_by_email("newuser@test.com")
        assert saved_user is not None
        assert saved_user.name == "New User"
    
    def test_create_user_duplicate_email(self, user_repo, student_user):
        """Test creating user with duplicate email fails."""
        # Arrange
        service = UserApplicationService(user_repo)
        request = CreateUserRequest(
            email=student_user.email.value,  # Use existing email
            name="Another User",
            role="student"
        )
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.create_user(request)
        
        assert "already exists" in str(exc_info.value)
    
    def test_create_user_invalid_email(self, user_repo):
        """Test user creation with invalid email."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CreateUserRequest(
                email="invalid-email",
                name="Test User",
                role="student"
            )
        
        # Verify it's an email validation error
        assert "email" in str(exc_info.value)
    
    def test_create_user_invalid_role(self, user_repo):
        """Test user creation with invalid role."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CreateUserRequest(
                email="user@test.com",
                name="Test User",
                role="INVALID_ROLE"
            )
        
        # Verify it's a role validation error
        assert "role" in str(exc_info.value)
        assert "pattern" in str(exc_info.value)
    
    def test_create_tutor_user(self, user_repo):
        """Test creating a tutor user."""
        # Arrange
        service = UserApplicationService(user_repo)
        request = CreateUserRequest(
            email="tutor@university.com",
            name="Dr. Smith",
            role="tutor"
        )
        
        # Act
        response = service.create_user(request)
        
        # Assert
        assert response.role == "tutor"
        saved_user = user_repo.find_by_email("tutor@university.com")
        assert saved_user.can_create_course() is True
    
    def test_get_user_success(self, user_repo, student_user):
        """Test getting existing user."""
        # Arrange
        service = UserApplicationService(user_repo)
        
        # Act
        response = service.get_user(student_user.id)
        
        # Assert
        assert isinstance(response, UserResponse)
        assert response.id == student_user.id
        assert response.email == student_user.email.value
        assert response.name == student_user.name
        assert response.role == student_user.role.value
    
    def test_get_user_not_found(self, user_repo):
        """Test getting non-existent user."""
        # Arrange
        service = UserApplicationService(user_repo)
        non_existent_id = uuid4()
        
        # Act & Assert
        with pytest.raises(ApplicationException) as exc_info:
            service.get_user(non_existent_id)
        
        assert "User not found" in str(exc_info.value)
    
    def test_user_response_dto_conversion(self, user_repo, tutor_user):
        """Test proper conversion from domain entity to DTO."""
        # Arrange
        service = UserApplicationService(user_repo)
        
        # Act
        response = service.get_user(tutor_user.id)
        
        # Assert
        # Verify all fields are properly converted
        assert response.id == tutor_user.id
        assert response.email == tutor_user.email.value  # Value object unwrapped
        assert response.name == tutor_user.name
        assert response.role == tutor_user.role.value  # Enum converted to string
        
        # Verify response is serializable (no domain objects leaked)
        assert isinstance(response.id, type(uuid4()))
        assert isinstance(response.email, str)
        assert isinstance(response.name, str)
        assert isinstance(response.role, str)
