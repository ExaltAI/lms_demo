"""Course repository implementation.

This module provides the SQLAlchemy-based implementation of the CourseRepository
interface. It handles all database operations related to courses, including
their nested entities: topics, assignments, and learning resources.

The repository manages complex object graphs and ensures proper cascading of
operations when saving or updating courses with their related entities.
"""

from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from ...domain import (
    Course,
    Topic,
    Assignment,
    LearningResource,
    CourseId,
    TopicId,
    AssignmentId,
    ResourceId,
    UserId,
    CourseTitle,
    CourseDescription,
    TopicTitle,
    TopicDescription,
    AssignmentTitle,
    AssignmentDescription,
    ResourceTitle,
    ResourceUrl,
    Duration,
    DateRange,
    TargetAudience,
    CourseStatus,
)
from ..database import CourseModel, TopicModel, AssignmentModel, ResourceModel


class SQLCourseRepository:
    """SQL implementation of CourseRepository.

    This class provides concrete implementations for course-related database
    operations using SQLAlchemy. It handles the conversion between domain
    entities and database models for courses and all their nested components
    (topics, assignments, resources).

    The repository uses eager loading strategies to efficiently fetch related
    data and manages the complexity of updating nested collections.

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

    def save(self, course: Course) -> None:
        """Save or update a course and all its nested entities.

        This method performs a deep save operation, handling the course
        and all its topics, assignments, and resources. It properly manages
        additions, updates, and deletions of nested entities.

        The method uses an "upsert" pattern - creating new records or
        updating existing ones based on the entity IDs.

        Args:
            course: Course domain entity to persist, including all nested entities

        Note:
            - Deleted topics, assignments, or resources are automatically removed
            - The actual database commit is handled by the session context manager
        """
        # First, let's check if this course already exists
        model = self.session.query(CourseModel).filter_by(id=course.id).first()

        if not model:
            model = CourseModel(
                id=course.id,
                title=course.title.value,
                description=course.description.value,
                tutor_id=course.tutor_id,
                duration_weeks=course.duration.weeks,
                start_date=course.date_range.start_date,
                end_date=course.date_range.end_date,
                target_audience=course.target_audience.value,
                status=course.status,
            )
            self.session.add(model)
        else:
            model.title = course.title.value
            model.description = course.description.value
            model.duration_weeks = course.duration.weeks
            model.start_date = course.date_range.start_date
            model.end_date = course.date_range.end_date
            model.target_audience = course.target_audience.value
            model.status = course.status

        self._update_topics(model, course)

    def find_by_id(self, course_id: CourseId) -> Optional[Course]:
        """Find a course by its unique identifier.
        This method uses eager loading to fetch the course with all its
        topics, assignments, and resources in a single query, avoiding
        the N+1 query problem.

        Args:
            course_id: The unique identifier of the course to find

        Returns:
            Course domain entity if found (with all nested entities), None otherwise
        """

        model = (
            self.session.query(CourseModel)
            .options(
                joinedload(CourseModel.topics).joinedload(TopicModel.assignments),
                joinedload(CourseModel.topics).joinedload(TopicModel.resources),
            )
            .filter_by(id=course_id)
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)

    def find_published(self) -> List[Course]:
        """Find all courses with published status.
        Note:
            This method loads courses without their nested entities for
            performance. Use find_by_id() if you need full course details.
        """
        # We're filtering by status using the enum directly
        # SQLAlchemy knows how to translate this to the database value
        # This is a simple and efficient way to filter by status
        models = (
            self.session.query(CourseModel)
            .filter_by(status=CourseStatus.PUBLISHED)
            .all()
        )
        return [self._to_entity(model) for model in models]

    def find_by_tutor(self, tutor_id: UserId) -> List[Course]:
        """Find all courses created by a specific tutor.

        Returns courses in all statuses (draft, published, archived).
        """

        models = self.session.query(CourseModel).filter_by(tutor_id=tutor_id).all()
        return [self._to_entity(m) for m in models]

    def _update_topics(self, model: CourseModel, course: Course) -> None:
        """Update course topics and their nested entities.

        This method synchronizes the topics in the database with the topics
        in the domain entity. It handles:
        - Deletion of topics that were removed from the course
        - Creation of new topics that were added to the course
        - Updates to existing topics and their nested entities

        Args:
            model: The CourseModel instance to update
            course: The Course domain entity containing the desired state
        """
        current_topic_ids = {topic.id for topic in course.get_topics()}

        for topic_model in model.topics[:]:
            if topic_model.id not in current_topic_ids:
                self.session.delete(topic_model)

        for topic in course.get_topics():
            topic_model = next((t for t in model.topics if t.id == topic.id), None)

            if not topic_model:
                topic_model = TopicModel(
                    id=topic.id,
                    course_id=model.id,
                    title=topic.title.value,
                    description=topic.description.value,
                    order=topic.order,  # Order is crucial for course flow
                )
                model.topics.append(topic_model)
            else:
                topic_model.title = topic.title.value
                topic_model.description = topic.description.value
                topic_model.order = topic.order

            self._update_assignments(topic_model, topic)
            self._update_resources(topic_model, topic)

    def _update_assignments(self, topic_model: TopicModel, topic: Topic):
        """Update assignments within a topic.
        Synchronizes the assignments in the database with those in the
        domain entity, handling creation, updates, and deletion.

        Args:
            topic_model: The TopicModel instance to update
            topic: The Topic domain entity containing the desired assignments

        Note:
            Assignment deletions cascade to related submissions automatically.
        """
        existing_ids = {a.id for a in topic.get_assignments()}

        for assignment_model in topic_model.assignments[:]:
            if assignment_model.id not in existing_ids:
                self.session.delete(assignment_model)

        for assignment in topic.get_assignments():
            assignment_model = next(
                (a for a in topic_model.assignments if a.id == assignment.id), None
            )
            if not assignment_model:
                assignment_model = AssignmentModel(
                    id=assignment.id,
                    topic_id=topic_model.id,
                    title=assignment.title.value,
                    description=assignment.description.value,
                    deadline=assignment.deadline,
                )
                topic_model.assignments.append(assignment_model)
            else:
                assignment_model.title = assignment.title.value
                assignment_model.description = assignment.description.value
                assignment_model.deadline = assignment.deadline

    def _update_resources(self, topic_model: TopicModel, topic: Topic):
        """Update learning resources within a topic.

        Synchronizes the resources in the database with those in the
        domain entity, handling creation, updates, and deletion.

        Args:
            topic_model: The TopicModel instance to update
            topic: The Topic domain entity containing the desired resources
        """
        existing_ids = {r.id for r in topic.get_resources()}

        for resource_model in topic_model.resources[:]:
            if resource_model.id not in existing_ids:
                self.session.delete(resource_model)

        for resource in topic.get_resources():
            resource_model = next(
                (r for r in topic_model.resources if r.id == resource.id), None
            )

            if not resource_model:
                resource_model = ResourceModel(
                    id=resource.id,
                    topic_id=topic_model.id,
                    title=resource.title.value,
                    url=resource.url.value,
                )
                topic_model.resources.append(resource_model)
            else:
                resource_model.title = resource.title.value
                resource_model.url = resource.url.value

    def _to_entity(self, model: CourseModel) -> Course:
        """Convert a database model to a domain entity.

        This method reconstructs the complete course aggregate from the
        database models, including all topics with their assignments and
        resources. It ensures proper initialization of all value objects
        and maintains the integrity of the domain model.

        Args:
            model: CourseModel instance from the database

        Returns:
            Course domain entity with all nested entities properly initialized

        Note:
            - Topics are sorted by their order field
            - Entity IDs are preserved from the database
            - Direct field access is used for reconstruction to bypass
              domain validation during loading
        """

        course = Course(
            course_id=CourseId(model.id),
            title=CourseTitle(model.title),
            description=CourseDescription(model.description),
            tutor_id=UserId(model.tutor_id),
            duration=Duration(model.duration_weeks),
            date_range=DateRange(model.start_date, model.end_date),
            target_audience=TargetAudience(model.target_audience),
        )

        course.status = model.status

        for topic_model in sorted(model.topics, key=lambda t: t.order):
            topic = Topic(
                title=TopicTitle(topic_model.title),
                description=TopicDescription(topic_model.description),
                order=topic_model.order,
            )
            topic.id = TopicId(topic_model.id)

            for assignment_model in topic_model.assignments:
                assignment = Assignment(
                    title=AssignmentTitle(assignment_model.title),
                    description=AssignmentDescription(assignment_model.description),
                    deadline=assignment_model.deadline,
                )
                assignment.id = AssignmentId(assignment_model.id)
                topic._assignments.append(assignment)

            for resource_model in topic_model.resources:
                resource = LearningResource(
                    title=ResourceTitle(resource_model.title),
                    url=ResourceUrl(resource_model.url),
                )
                resource.id = ResourceId(resource_model.id)
                topic._resources.append(resource)

            course._topics.append(topic)

        return course
