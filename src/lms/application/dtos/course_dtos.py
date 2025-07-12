"""Course-related DTOs.

This module contains all DTOs related to course management. The design follows
these principles:

1. Separation of Concerns: Request DTOs validate input, Response DTOs shape output
2. Nested Structure: Response DTOs can be composed to represent complex aggregates
3. Validation at the Edge: All validation happens at the API boundary via Pydantic
4. Performance Optimization: Separate list and detail DTOs to avoid N+1 queries
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, validator
from uuid import UUID


# Request DTOs
class CreateCourseRequest(BaseModel):
    """Request to create a course.

    This DTO enforces business constraints at the API boundary before
    data reaches the domain layer. Validation rules reflect business
    requirements and UX considerations.
    """

    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10)
    duration_weeks: int = Field(..., ge=1, le=52)
    start_date: datetime
    end_date: datetime
    target_audience: str = Field(..., min_length=1)

    @validator("end_date")
    def validate_dates(cls, v, values):
        """Cross-field validation ensures logical date ordering.

        This validator runs after individual field validation, ensuring
        both dates are valid before comparing them. This prevents
        courses with negative duration.
        """
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class AddTopicRequest(BaseModel):
    """Request to add topic to course.

    Topics are the main organizational unit within a course.
    Minimal validation ensures flexibility while maintaining quality.
    """

    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=1)


class AddAssignmentRequest(BaseModel):
    """Request to add assignment to topic.

    Assignments are assessable work items within topics.
    They require deadlines for student planning.
    """

    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=1)
    deadline: datetime


class AddResourceRequest(BaseModel):
    """Request to add learning resource to topic.

    Resources are supplementary materials (videos, articles, etc.)
    URL validation ensures only web resources are added.
    """

    title: str = Field(..., min_length=1)
    url: str = Field(..., pattern=r"^https?://")


# Response DTOs
# These DTOs form a hierarchical structure that mirrors the domain aggregate
# but optimized for API responses (flattened where appropriate)


class ResourceResponse(BaseModel):
    """Learning resource response.

    Minimal DTO for embedded resources within topics.
    Includes only essential fields to reduce payload size.
    """

    id: UUID
    title: str
    url: str


class AssignmentResponse(BaseModel):
    """Assignment response.

    Complete assignment data for display within topics.
    Could be extended with submission status for student views.
    """

    id: UUID
    title: str
    description: str
    deadline: datetime


class TopicResponse(BaseModel):
    """Topic response.

    Topics include their child entities (assignments and resources)
    to provide a complete view without additional API calls.
    This denormalization improves client performance.
    """

    id: UUID
    title: str
    description: str
    order: int
    assignments: List[AssignmentResponse]
    resources: List[ResourceResponse]


class CourseResponse(BaseModel):
    """Course response.

    Complete course representation including all nested entities.
    This DTO is used for detailed course views where all information
    is needed (e.g., course detail page, editing interface).
    """

    id: UUID
    title: str
    description: str
    tutor_id: UUID
    duration_weeks: int
    start_date: datetime
    end_date: datetime
    target_audience: str
    status: str
    topics: List[TopicResponse]


class CourseListResponse(BaseModel):
    """Course list item response.

    Optimized DTO for course listings (search results, browse pages).
    Excludes heavy nested data (topics) to improve performance when
    showing many courses. Client fetches full details when needed.

    This pattern (separate list/detail DTOs) is crucial for scalability.
    """

    id: UUID
    title: str
    description: str
    tutor_id: UUID
    duration_weeks: int
    start_date: datetime
    end_date: datetime
    status: str
