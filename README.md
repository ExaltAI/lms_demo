# LMS - Learning Management System

This repository is for educational purposes only. Commercial use is prohibited.

See [LICENSE](LICENSE) file for details.

---

A Domain-Driven Design (DDD) implementation of a Learning Management System using Python, FastAPI, SQLAlchemy, and Pydantic.

## Architecture Overview

The project follows a clean architecture with clear separation of concerns:

### Layer Structure

```
src/lms/
├── domain/           # Core business logic and rules
│   ├── entities/     # Domain entities (User, Course, Enrollment, etc.)
│   ├── value_objects/# Value objects (IDs, EmailAddress, Grade, etc.)
│   ├── services/     # Domain services (EnrollmentService, etc.)
│   ├── repositories/ # Repository interfaces (protocols)
│   └── exceptions/   # Domain exceptions
├── application/      # Application logic
│   ├── dtos/        # Data Transfer Objects
│   ├── services/    # Application services
│   └── exceptions/  # Application exceptions
├── infrastructure/   # External concerns
│   ├── database/    # SQLAlchemy models and DB config
│   └── repositories/# Repository implementations
└── api/             # Presentation layer
    ├── routes/      # FastAPI route handlers
    └── dependencies/# Dependency injection
```

## Key Design Principles

1. **Domain-Driven Design**: Core business logic is isolated in the domain layer
2. **Aggregate Design**: 
   - Course is an aggregate root containing Topics, Assignments, and Resources
   - Enrollment is an aggregate root containing Submissions
   - Certificate is a standalone aggregate
3. **Clean Architecture**: Dependencies point inward (domain has no external dependencies)
4. **Repository Pattern**: Abstract interfaces in domain, concrete implementations in infrastructure
5. **Value Objects**: Strong typing for domain concepts (EmailAddress, Grade, etc.)

## Installation

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install dependencies:
```bash
uv sync
```

## Running the Application

1. Start the FastAPI server:
```bash
uv run uvicorn src.lms.api.main:app --reload
```

2. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Users
- `POST /api/v1/users` - Create a new user
- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/users/{user_id}` - Get user by ID

### Courses
- `POST /api/v1/courses` - Create a new course (tutor only)
- `GET /api/v1/courses` - List published courses
- `GET /api/v1/courses/my-courses` - List tutor's courses
- `GET /api/v1/courses/{course_id}` - Get course details
- `POST /api/v1/courses/{course_id}/topics` - Add topic
- `POST /api/v1/courses/{course_id}/topics/{topic_id}/assignments` - Add assignment
- `POST /api/v1/courses/{course_id}/topics/{topic_id}/resources` - Add resource
- `POST /api/v1/courses/{course_id}/publish` - Publish course

### Enrollments
- `POST /api/v1/enrollments` - Enroll in course
- `GET /api/v1/enrollments/my-enrollments` - List student's enrollments
- `GET /api/v1/enrollments/course/{course_id}` - List course enrollments
- `GET /api/v1/enrollments/{enrollment_id}` - Get enrollment details
- `POST /api/v1/enrollments/{enrollment_id}/submit` - Submit assignment
- `POST /api/v1/enrollments/{enrollment_id}/evaluate/{assignment_id}` - Evaluate submission

### Certificates
- `POST /api/v1/certificates` - Issue certificate
- `GET /api/v1/certificates/my-certificates` - List student's certificates
- `GET /api/v1/certificates/{certificate_id}` - Get certificate details

## Authentication

The API uses Bearer token authentication. For testing, you can use a UUID as the token:

```bash
curl -H "Authorization: Bearer <user-uuid>" http://localhost:8000/api/v1/users/me
```

## Database

The application uses SQLite by default (lms.db file). The database schema is automatically created on startup.

## Testing the API

A test script is provided to verify all API endpoints:

```bash
uv run python test_api.py
```

This script tests the complete workflow:
1. Creating users (tutor and student)
2. Creating a course with topics, assignments, and resources
3. Publishing the course
4. Student enrollment
5. Assignment submission
6. Tutor evaluation
7. Certificate issuance

## Business Rules

1. **Course Management**:
   - Only tutors can create and manage courses
   - Courses must have at least one topic to be published
   - Each topic must have at least one resource to publish the course
   - Published courses cannot be modified (except adding content)

2. **Enrollment**:
   - Students can only enroll in published courses
   - Cannot enroll in the same course twice
   - Enrollments track submission status

3. **Evaluation**:
   - Only course tutors can evaluate submissions
   - Grades must be between 0-100
   - All assignments must be evaluated for completion

4. **Certificates**:
   - Issued only for completed enrollments
   - All assignments must be evaluated
   - Only course tutors can issue certificates

## Development Guidelines

1. **Adding New Features**:
   - Start with domain entities and value objects
   - Define repository interfaces in domain layer
   - Implement application services for use cases
   - Add infrastructure implementations
   - Create API routes

2. **Testing**:
   - Domain logic should be tested independently
   - Use repository mocks for application service tests
   - Integration tests for API endpoints

3. **Code Quality**:
   - Use type hints throughout
   - Follow PEP 8 style guide
   - Run ruff for linting: `uv run ruff check .`

## Known Issues & Future Improvements

### Current Limitations:
- Authentication uses simple UUID bearer tokens (not secure for production)
- SQLite database (suitable for development only)
- No pagination on list endpoints
- No file upload support for assignments
- No email notifications

### Completed Features:
- Full CRUD operations for users, courses, enrollments, and certificates
- Domain-Driven Design with clean architecture
- Course publication workflow with validation
- Assignment submission and evaluation
- Certificate issuance for completed courses
- API documentation with Swagger UI
- Working test script for end-to-end testing

### Future Work:
- Implement proper JWT authentication with refresh tokens
- Add PostgreSQL support for production
- Add pagination for list endpoints
- Implement course search and filtering
- Add email notifications for enrollments and evaluations
- Support file uploads for assignment submissions
- Add course prerequisites and dependency management
- Implement progress tracking and analytics
- Add unit and integration test suites
- Implement role-based access control (RBAC)
- Add course versioning and archiving
