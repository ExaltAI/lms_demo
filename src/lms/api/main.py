"""FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import user_router, course_router, enrollment_router, certificate_router
from .dependencies import set_database
from ..infrastructure import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: Initialize application
    # Initialize database

    database = Database("sqlite:///lms.db")
    set_database(database)

    database.create_tables()

    yield

    # Shutdown: Clean up resources if needed
    # Add any cleanup code here


# Create FastAPI app
app = FastAPI(
    title="LMS API",
    description="Learning Management System API",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user_router, prefix="/api/v1")
app.include_router(course_router, prefix="/api/v1")
app.include_router(enrollment_router, prefix="/api/v1")
app.include_router(certificate_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to the LMS API"}
