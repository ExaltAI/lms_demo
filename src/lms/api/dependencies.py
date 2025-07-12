"""API dependencies."""

from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

from ..infrastructure import Database

# Security scheme
security = HTTPBearer()

# Global database instance
_database: Database = None


def set_database(database: Database) -> None:
    """Set the global database instance."""
    global _database
    _database = database


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    if not _database:
        raise RuntimeError("Database not initialized")

    with _database.get_session() as session:
        yield session


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """Get current user ID from token."""
    # In a real application, this would decode and validate the JWT token
    # For now, we'll use a simple UUID from the token
    try:
        user_id = UUID(credentials.credentials)
        return user_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
