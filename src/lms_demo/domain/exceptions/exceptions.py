""" LMS domain specific exceptions."""


class DomainException(Exception):
    """Base domain exception."""
    pass


class CourseNotFoundException(DomainException):
    """Raised when a course is not found."""
    pass


class EnrollmentNotFoundException(DomainException):
    """Raised when enrollment is not found."""
    pass


class UserNotFoundException(DomainException):
    """Raised when a user is not found."""
    pass


class DuplicateEnrollmentException(DomainException):
    """Raised when trying to enroll into a course more than once."""
    pass


class UnauthorizedException(DomainException):
    """Raised when user is not authorized for an action."""
    pass


class InvalidOperationException(DomainException):
    """Raised when an invalid operation is attempted."""
    pass
