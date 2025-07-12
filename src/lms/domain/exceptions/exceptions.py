"""Domain exceptions."""


class DomainException(Exception):
    """Base domain exception."""

    pass


class CourseNotFoundException(DomainException):
    """Raised when course is not found."""

    pass


class EnrollmentNotFoundException(DomainException):
    """Raised when enrollment is not found."""

    pass


class UserNotFoundException(DomainException):
    """Raised when user is not found."""

    pass


class DuplicateEnrollmentException(DomainException):
    """Raised when trying to enroll in a course twice."""

    pass


class UnauthorizedException(DomainException):
    """Raised when user is not authorized for an action."""

    pass


class InvalidOperationException(DomainException):
    """Raised when an invalid operation is attempted."""

    pass
