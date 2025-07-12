"""User API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from ...application import UserApplicationService, ApplicationException
from ...application.dtos import CreateUserRequest, UserResponse
from ...infrastructure import SQLUserRepository
from ..dependencies import get_db, get_current_user_id

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(request: CreateUserRequest, db: Session = Depends(get_db)):
    """Create a new user."""
    user_repo = SQLUserRepository(db)
    service = UserApplicationService(user_repo)

    try:
        return service.create_user(request)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserResponse)
def get_current_user(
    user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get current user details."""
    user_repo = SQLUserRepository(db)
    service = UserApplicationService(user_repo)

    try:
        return service.get_user(user_id)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Get user by ID."""
    user_repo = SQLUserRepository(db)
    service = UserApplicationService(user_repo)

    try:
        return service.get_user(user_id)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
