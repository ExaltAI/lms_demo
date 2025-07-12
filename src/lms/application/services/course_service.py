"""Course application service."""

from typing import List
from uuid import UUID, uuid4

from ...domain import (
    Course,
    CourseId,
    UserId,
    CourseTitle,
    CourseDescription,
    Duration,
    DateRange,
    TargetAudience,
    TopicTitle,
    TopicDescription,
    AssignmentTitle,
    AssignmentDescription,
    ResourceTitle,
    ResourceUrl,
    CourseRepository,
    UserRepository,
)
from ..dtos import (
    CreateCourseRequest,
    AddTopicRequest,
    AddAssignmentRequest,
    AddResourceRequest,
    CourseResponse,
    CourseListResponse,
    TopicResponse,
    AssignmentResponse,
    ResourceResponse,
)
from ..exceptions import ApplicationException


class CourseApplicationService:
    """Application service for course operations.

    This service orchestrates course-related use cases while respecting
    domain boundaries. It handles:

    - Course lifecycle (creation, modification, publishing)
    - Content management (topics, assignments, resources)
    - Authorization (tutor-only operations)
    - Query operations (listings, details)
    """

    def __init__(self, course_repo: CourseRepository, user_repo: UserRepository):
        self.course_repo = course_repo
        self.user_repo = user_repo

    def create_course(
        self, tutor_id: UUID, request: CreateCourseRequest
    ) -> CourseResponse:
        """Create a new course.

        This use case demonstrates cross-aggregate validation:
        1. Validate the tutor exists and has the right role
        2. Create the course aggregate with all invariants enforced
        3. Persist and return the result
        """

        tutor = self.user_repo.find_by_id(UserId(tutor_id))
        if not tutor:
            raise ApplicationException("Tutor not found")

        if not tutor.can_create_course():
            raise ApplicationException("User is not authorized to create courses")

        course = Course(
            course_id=CourseId(uuid4()),
            title=CourseTitle(request.title),
            description=CourseDescription(request.description),
            tutor_id=UserId(tutor_id),
            duration=Duration(request.duration_weeks),
            date_range=DateRange(request.start_date, request.end_date),
            target_audience=TargetAudience(request.target_audience),
        )

        # Persist through repository - implementation details hidden
        self.course_repo.save(course)

        # Convert to DTO for API response
        return self._to_course_response(course)

    def add_topic(
        self, tutor_id: UUID, course_id: UUID, request: AddTopicRequest
    ) -> CourseResponse:
        """Add topic to course.

        Topics are part of the Course aggregate. This method:
        1. Loads the aggregate root (Course)
        2. Delegates to domain method to maintain invariants
        3. Persists the entire aggregate
        """
        # Authorization and loading happen together
        course = self._get_course_for_tutor(CourseId(course_id), UserId(tutor_id))

        # Domain method handles topic creation and ordering
        # The course aggregate maintains the invariant that topics are ordered
        course.add_topic(
            title=TopicTitle(request.title),
            description=TopicDescription(request.description),
        )

        # Save entire aggregate - repository handles nested entities
        self.course_repo.save(course)

        # Return full course to show updated state
        return self._to_course_response(course)

    def add_assignment(
        self,
        tutor_id: UUID,
        course_id: UUID,
        topic_id: UUID,
        request: AddAssignmentRequest,
    ) -> CourseResponse:
        """Add assignment to topic.

        Assignments are nested within topics within courses.
        This shows navigation through the aggregate to maintain consistency.
        """
        # Load and authorize in one step
        course = self._get_course_for_tutor(CourseId(course_id), UserId(tutor_id))

        # Navigate the aggregate to find the topic
        # In a larger system, might add a method like course.find_topic(topic_id)
        topic = None
        for t in course.get_topics():
            if t.id == topic_id:
                topic = t
                break

        if not topic:
            # Application exception because this is a client error (wrong ID)
            raise ApplicationException("Topic not found")

        # Add assignment through the topic (part of course aggregate)
        # The topic handles assignment ID generation and maintains its collection
        topic.add_assignment(
            title=AssignmentTitle(request.title),
            description=AssignmentDescription(request.description),
            deadline=request.deadline,
        )

        # Save the aggregate root - changes to nested entities are persisted
        self.course_repo.save(course)
        return self._to_course_response(course)

    def add_resource(
        self,
        tutor_id: UUID,
        course_id: UUID,
        topic_id: UUID,
        request: AddResourceRequest,
    ) -> CourseResponse:
        """Add learning resource to topic."""
        course = self._get_course_for_tutor(CourseId(course_id), UserId(tutor_id))

        # Find topic
        topic = None
        for t in course.get_topics():
            if t.id == topic_id:
                topic = t
                break

        if not topic:
            raise ApplicationException("Topic not found")

        topic.add_resource(
            title=ResourceTitle(request.title), url=ResourceUrl(request.url)
        )

        self.course_repo.save(course)
        return self._to_course_response(course)

    def publish_course(self, tutor_id: UUID, course_id: UUID) -> CourseResponse:
        """Publish a course.

        Publishing is a domain operation with business rules.
        The domain method ensures the course is ready for publication.
        """
        course = self._get_course_for_tutor(CourseId(course_id), UserId(tutor_id))

        # Domain method enforces publishing rules:
        # - Course must have topics
        # - Dates must be valid
        # - Status transitions must be valid
        course.publish()

        self.course_repo.save(course)
        return self._to_course_response(course)

    def get_course(self, course_id: UUID) -> CourseResponse:
        """Get course details.

        Public query method - no authorization needed.
        Returns full course details including all nested entities.
        """
        course = self.course_repo.find_by_id(CourseId(course_id))
        if not course:
            raise ApplicationException("Course not found")
        return self._to_course_response(course)

    def list_published_courses(self) -> List[CourseListResponse]:
        """List all published courses.

        Returns lightweight DTOs for performance.
        Only published courses are shown to students.
        """
        courses = self.course_repo.find_published()

        # Use list response DTO to avoid loading all topics/assignments
        return [self._to_course_list_response(c) for c in courses]

    def list_tutor_courses(self, tutor_id: UUID) -> List[CourseListResponse]:
        """List courses by tutor.

        Returns all courses for a tutor (published and draft).
        Used in tutor's dashboard.
        """
        courses = self.course_repo.find_by_tutor(UserId(tutor_id))
        return [self._to_course_list_response(c) for c in courses]

    def _get_course_for_tutor(self, course_id: CourseId, tutor_id: UserId) -> Course:
        """Get course and verify tutor ownership.

        This helper method centralizes the authorization logic for
        tutor-only operations. It ensures:
        1. The course exists
        2. The requesting user is the course tutor

        This pattern prevents unauthorized modifications while keeping
        the authorization logic in the application layer (not domain).
        """
        course = self.course_repo.find_by_id(course_id)
        if not course:
            raise ApplicationException("Course not found")

        # Authorization is an application concern, not a domain invariant
        # The domain doesn't know about the current user context
        if course.tutor_id != tutor_id:
            raise ApplicationException("Not authorized to modify this course")

        return course

    def _to_course_response(self, course: Course) -> CourseResponse:
        """Convert course to response DTO.

        Full conversion including all nested entities.
        Note how we unwrap value objects to primitive types
        for the API response.
        """
        return CourseResponse(
            id=course.id,  # Property returns primitive UUID
            title=course.title.value,  # Unwrap value object
            description=course.description.value,
            tutor_id=course.tutor_id,  # Already primitive from property
            duration_weeks=course.duration.weeks,  # Access value object field
            start_date=course.date_range.start_date,  # Value object field
            end_date=course.date_range.end_date,
            target_audience=course.target_audience.value,
            status=course.status.value,  # Enum to string
            # Recursive conversion of nested entities
            topics=[self._to_topic_response(t) for t in course.get_topics()],
        )

    def _to_course_list_response(self, course: Course) -> CourseListResponse:
        """Convert course to list response DTO.

        Lightweight DTO without nested entities.
        This optimization prevents N+1 queries and reduces payload size
        for list views where full details aren't needed.
        """
        return CourseListResponse(
            id=course.id,
            title=course.title.value,
            description=course.description.value,
            tutor_id=course.tutor_id,
            duration_weeks=course.duration.weeks,
            start_date=course.date_range.start_date,
            end_date=course.date_range.end_date,
            status=course.status.value,
            # Note: No topics included - key optimization
        )

    def _to_topic_response(self, topic) -> TopicResponse:
        """Convert topic to response DTO."""
        return TopicResponse(
            id=topic.id,
            title=topic.title.value,
            description=topic.description.value,
            order=topic.order,
            assignments=[
                self._to_assignment_response(a) for a in topic.get_assignments()
            ],
            resources=[self._to_resource_response(r) for r in topic.get_resources()],
        )

    def _to_assignment_response(self, assignment) -> AssignmentResponse:
        """Convert assignment to response DTO."""
        return AssignmentResponse(
            id=assignment.id,
            title=assignment.title.value,
            description=assignment.description.value,
            deadline=assignment.deadline,
        )

    def _to_resource_response(self, resource) -> ResourceResponse:
        """Convert resource to response DTO."""
        return ResourceResponse(
            id=resource.id, title=resource.title.value, url=resource.url.value
        )
