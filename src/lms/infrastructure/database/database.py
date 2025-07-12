"""Database configuration and session management.

This module provides the core database functionality for the LMS application,
including connection management, session handling, and table operations.
It uses SQLAlchemy as the ORM and provides a context manager for safe
database session handling.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from .models import Base


class Database:
    """Database connection and session management.

    This class handles the database connection, session creation, and table management
    for the LMS application. It provides a context manager for database sessions that
    automatically handles commits, rollbacks, and session cleanup.

    Attributes:
        engine: SQLAlchemy engine instance for database connections
        SessionLocal: Session factory for creating database sessions
    """

    def __init__(self, database_url: str):
        """Initialize database connection.

        Args:
            database_url: Database connection URL in SQLAlchemy format.
                Examples:
                    - sqlite:///lms.db
                    - postgresql://user:password@localhost/lms
                    - mysql+pymysql://user:password@localhost/lms

        Raises:
            sqlalchemy.exc.ArgumentError: If the database URL is invalid
        """

        self.engine = create_engine(database_url)

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_tables(self):
        """Create all database tables.

        Creates all tables defined in the models module if they don't already exist.
        This method is idempotent - it's safe to call multiple times as it will
        only create tables that don't exist.

        Note:
            This method should be called during application initialization
            or database setup.
        """

        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all database tables.

        Drops all tables defined in the models module. This is a destructive
        operation that will delete all data.

        Warning:
            This method will permanently delete all data in the database.
            Use with extreme caution, typically only in testing or development.
        """

        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic transaction management.

        Provides a context manager that yields a database session. The session
        will automatically commit on successful completion or rollback on exception.
        The session is always closed when the context exits.

        Yields:
            Session: SQLAlchemy session for database operations

        Raises:
            Exception: Any exception raised within the context will cause a rollback
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
