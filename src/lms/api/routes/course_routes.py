"""Course API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from ...application import CourseApplicationService, ApplicationException
from ...application.dtos import (
    CreateCourseRequest,
    AddTopicRequest,
    AddAssignmentRequest,
    AddResourceRequest,
    CourseResponse,
    CourseListResponse,
)
from ...infrastructure import SQLCourseRepository, SQLUserRepository
from ..dependencies import get_db, get_current_user_id

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    request: CreateCourseRequest,
    tutor_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new course."""
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = CourseApplicationService(course_repo, user_repo)

    try:
        return service.create_course(tutor_id, request)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[CourseListResponse])
def list_courses(db: Session = Depends(get_db)):
    """List all published courses."""
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = CourseApplicationService(course_repo, user_repo)

    return service.list_published_courses()


@router.get("/my-courses", response_model=List[CourseResponse])
def list_my_courses(
    tutor_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """List tutor's courses."""
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = CourseApplicationService(course_repo, user_repo)

    return service.list_tutor_courses(tutor_id)


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: UUID, db: Session = Depends(get_db)):
    """Get course details."""
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = CourseApplicationService(course_repo, user_repo)

    try:
        return service.get_course(course_id)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{course_id}/topics", response_model=CourseResponse)
def add_topic(
    course_id: UUID,
    request: AddTopicRequest,
    tutor_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add topic to course."""
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = CourseApplicationService(course_repo, user_repo)

    try:
        return service.add_topic(tutor_id, course_id, request)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{course_id}/topics/{topic_id}/assignments", response_model=CourseResponse
)
def add_assignment(
    course_id: UUID,
    topic_id: UUID,
    request: AddAssignmentRequest,
    tutor_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add assignment to topic."""
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = CourseApplicationService(course_repo, user_repo)

    try:
        return service.add_assignment(tutor_id, course_id, topic_id, request)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{course_id}/topics/{topic_id}/resources", response_model=CourseResponse)
def add_resource(
    course_id: UUID,
    topic_id: UUID,
    request: AddResourceRequest,
    tutor_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add learning resource to topic."""
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = CourseApplicationService(course_repo, user_repo)

    try:
        return service.add_resource(tutor_id, course_id, topic_id, request)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{course_id}/publish", response_model=CourseResponse)
def publish_course(
    course_id: UUID,
    tutor_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Publish a course."""
    course_repo = SQLCourseRepository(db)
    user_repo = SQLUserRepository(db)
    service = CourseApplicationService(course_repo, user_repo)

    try:
        return service.publish_course(tutor_id, course_id)
    except ApplicationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
