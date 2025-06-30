#!/bin/bash

# Create LMS directory structure with __init__.py files

echo "Setting up LMS project structure..."

# Base directory
BASE_DIR="src/lms_demo"

# Create main directories
mkdir -p "$BASE_DIR"

# Create domain layer directories
mkdir -p "$BASE_DIR/domain"
mkdir -p "$BASE_DIR/domain/entities"
mkdir -p "$BASE_DIR/domain/value_objects"
mkdir -p "$BASE_DIR/domain/services"
mkdir -p "$BASE_DIR/domain/repositories"
mkdir -p "$BASE_DIR/domain/exceptions"

# Create application layer directories
mkdir -p "$BASE_DIR/application"
mkdir -p "$BASE_DIR/application/dtos"
mkdir -p "$BASE_DIR/application/services"
mkdir -p "$BASE_DIR/application/exceptions"

# Create infrastructure layer directories
mkdir -p "$BASE_DIR/infrastructure"
mkdir -p "$BASE_DIR/infrastructure/database"
mkdir -p "$BASE_DIR/infrastructure/repositories"

# Create API layer directories
mkdir -p "$BASE_DIR/api"
mkdir -p "$BASE_DIR/api/routes"
mkdir -p "$BASE_DIR/api/dependencies"

# Create __init__.py files
echo "Creating __init__.py files..."

# Root __init__.py
touch "$BASE_DIR/__init__.py"

# Domain layer __init__.py files
touch "$BASE_DIR/domain/__init__.py"
touch "$BASE_DIR/domain/entities/__init__.py"
touch "$BASE_DIR/domain/value_objects/__init__.py"
touch "$BASE_DIR/domain/services/__init__.py"
touch "$BASE_DIR/domain/repositories/__init__.py"
touch "$BASE_DIR/domain/exceptions/__init__.py"

# Application layer __init__.py files
touch "$BASE_DIR/application/__init__.py"
touch "$BASE_DIR/application/dtos/__init__.py"
touch "$BASE_DIR/application/services/__init__.py"
touch "$BASE_DIR/application/exceptions/__init__.py"

# Infrastructure layer __init__.py files
touch "$BASE_DIR/infrastructure/__init__.py"
touch "$BASE_DIR/infrastructure/database/__init__.py"
touch "$BASE_DIR/infrastructure/repositories/__init__.py"

# API layer __init__.py files
touch "$BASE_DIR/api/__init__.py"
touch "$BASE_DIR/api/routes/__init__.py"
touch "$BASE_DIR/api/dependencies/__init__.py"

echo "Project structure created successfully!"

# Display the created structure
echo -e "\nCreated structure:"
tree "$BASE_DIR" -a --charset=ascii 2>/dev/null || find "$BASE_DIR" -type d | sort | sed 's/[^/]*\//|  /g; s/|  \([^|]\)/+--\1/'
