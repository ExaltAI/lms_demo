"""User repository implementation.

This module provides the SQLAlchemy-based implementation of the UserRepository
interface. It handles all database operations related to users, including
creating, updating, and retrieving user records.

The repository uses the Repository pattern to abstract database operations
from the domain layer, ensuring clean separation of concerns.
"""

from typing import Optional
from sqlalchemy.orm import Session


from ...domain import User, UserId, EmailAddress
from ..database import UserModel


class SQLUserRepository:
    """SQL implementation of UserRepository.

    This class provides concrete implementations for user-related database
    operations using SQLAlchemy. It handles the conversion between domain
    entities and database models, ensuring that the domain layer remains
    independent of the persistence mechanism.

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

    def save(self, user: User) -> None:
        """Save or update a user in the database.

        This method performs an "upsert" operation - it creates a new user
        record if the user doesn't exist, or updates the existing record
        if it does. The user is identified by their UUID.

        Args:
            user: User domain entity to persist

        Note:
            The actual database commit is handled by the session context
            manager, not by this method.
        """

        model = self.session.query(UserModel).filter_by(id=user.id).first()

        if not model:
            model = UserModel(
                id=user.id, email=user.email.value, name=user.name, role=user.role
            )

            self.session.add(model)
        else:
            model.email = user.email.value
            model.name = user.name
            model.role = user.role

    def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Find a user by their unique identifier.

        Args:
            user_id: The unique identifier (UUID) of the user to find

        Returns:
            User domain entity if found, None otherwise
        """

        model = self.session.query(UserModel).filter_by(id=user_id).first()

        if not model:
            return None
        return self._to_entity(model)

    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by their email address.

        Email comparison is case-insensitive - the email is converted to
        lowercase before searching.

        Args:
            email: Email address to search for

        Returns:
            User domain entity if found, None otherwise
        """

        model = self.session.query(UserModel).filter_by(email=email.lower()).first()

        if not model:
            return None
        return self._to_entity(model)

    def _to_entity(self, model: UserModel) -> User:
        """Convert a database model to a domain entity.

        This method handles the transformation from the SQLAlchemy model
        (database representation) to the domain entity (business logic
        representation), ensuring proper encapsulation of domain logic.

        Args:
            model: UserModel instance from the database

        Returns:
            User domain entity with properly initialized value objects

        Note:
            This method assumes the model data is valid. Invalid data
            may raise exceptions from the domain value objects.
        """

        return User(
            user_id=UserId(model.id),
            email=EmailAddress(model.email),
            name=model.name,
            role=model.role,
        )
