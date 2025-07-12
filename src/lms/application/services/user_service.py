"""User application service."""

from uuid import UUID, uuid4

from ...domain import User, UserId, EmailAddress, UserRole, UserRepository
from ..dtos import CreateUserRequest, UserResponse
from ..exceptions import ApplicationException


class UserApplicationService:
    """Application service for user operations.

    This service implements the use cases related to user management.
    It follows the Application Service pattern from DDD:

    - Thin orchestration layer (no business logic)
    - Delegates to domain objects for business rules
    - Handles DTO conversion and repository coordination
    - Would handle transactions if we had a Unit of Work pattern
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create_user(self, request: CreateUserRequest) -> UserResponse:
        """Create a new user.

        This method implements the 'Create User' use case:
        1. Validates uniqueness (application-level concern)
        2. Creates domain entity with proper value objects
        3. Persists via repository
        4. Returns DTO response

        Note: In a real system, this would be wrapped in a transaction
        to ensure atomicity of the entire operation.
        """

        existing = self.user_repo.find_by_email(request.email)
        if existing:
            raise ApplicationException("User with this email already exists")

        user = User(
            user_id=UserId(uuid4()),
            email=EmailAddress(request.email),
            name=request.name,
            role=UserRole(request.role),
        )

        self.user_repo.save(user)

        return self._to_response(user)

    def get_user(self, user_id: UUID) -> UserResponse:
        """Get user by ID.

        Simple query use case that:
        1. Retrieves from repository
        2. Handles not-found case
        3. Converts to DTO
        """

        user = self.user_repo.find_by_id(UserId(user_id))

        if not user:
            raise ApplicationException("User not found")

        return self._to_response(user)

    def _to_response(self, user: User) -> UserResponse:
        """Convert user to response DTO.

        This helper method centralizes the domain-to-DTO mapping logic.
        Notice how we:
        - Unwrap value objects (.value) to get primitive types
        - Use the domain entity's ID property (which returns the primitive UUID)

        This mapping could be extracted to a separate mapper class in larger applications.
        """
        return UserResponse(
            id=user.id, email=user.email.value, name=user.name, role=user.role.value
        )
