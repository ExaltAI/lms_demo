"""Simple test script to verify API functionality."""

import requests
from datetime import datetime, timedelta
import time

BASE_URL = "http://localhost:8000/api/v1"

def create_user(email, name, role):
    """Create a user."""
    response = requests.post(
        f"{BASE_URL}/users",
        json={"email": email, "name": name, "role": role}
    )
    return response.json()

def create_course(course_data, tutor_id):
    """Create a course."""
    response = requests.post(
        f"{BASE_URL}/courses",
        json=course_data,
        headers={"Authorization": f"Bearer {tutor_id}"}
    )

    if response.status_code != 200:
        print(f"Error creating course: {response.text}")
        response.raise_for_status()

    return response.json()

def add_topic(course_id, topic_data, tutor_id):
    """Add a topic to a course."""
    response = requests.post(
        f"{BASE_URL}/courses/{course_id}/topics",
        json=topic_data,
        headers={"Authorization": f"Bearer {tutor_id}"}
    )

    if response.status_code != 200:
        print(f"Error adding topic: {response.text}")
        response.raise_for_status()

    return response.json()

def add_assignment(course_id, topic_id, assignment_data, tutor_id):
    """Add an assignment to a topic."""
    response = requests.post(
        f"{BASE_URL}/courses/{course_id}/topics/{topic_id}/assignments",
        json=assignment_data,
        headers={"Authorization": f"Bearer {tutor_id}"}
    )
    return response.json()

def add_resource(course_id, topic_id, resource_data, tutor_id):
    """Add a resource to a topic."""
    response = requests.post(
        f"{BASE_URL}/courses/{course_id}/topics/{topic_id}/resources",
        json=resource_data,
        headers={"Authorization": f"Bearer {tutor_id}"}
    )
    return response.json()

def publish_course(course_id, tutor_id):
    """Publish a course."""
    response = requests.post(
        f"{BASE_URL}/courses/{course_id}/publish",
        headers={"Authorization": f"Bearer {tutor_id}"}
    )
    return response.json()

def enroll_student(course_id, student_id):
    """Enroll a student in a course."""
    response = requests.post(
        f"{BASE_URL}/enrollments",
        json={"course_id": course_id},
        headers={"Authorization": f"Bearer {student_id}"}
    )
    return response.json()

def submit_assignment(enrollment_id, assignment_id, content, student_id):
    """Submit an assignment."""
    response = requests.post(
        f"{BASE_URL}/enrollments/{enrollment_id}/submit",
        json={
            "assignment_id": assignment_id,
            "content": content
        },
        headers={"Authorization": f"Bearer {student_id}"}
    )
    return response.json()

def evaluate_submission(enrollment_id, assignment_id, grade, feedback, tutor_id):
    """Evaluate a student's submission."""
    response = requests.post(
        f"{BASE_URL}/enrollments/{enrollment_id}/evaluate/{assignment_id}",
        json={
            "grade": grade,
            "feedback": feedback
        },
        headers={"Authorization": f"Bearer {tutor_id}"}
    )
    return response.json()

def issue_certificate(enrollment_id, tutor_id):
    """Issue a certificate for a completed course."""
    response = requests.post(
        f"{BASE_URL}/certificates",
        json={"enrollment_id": enrollment_id},
        headers={"Authorization": f"Bearer {tutor_id}"}
    )
    return response.json()

def test_api():
    """Test basic API functionality."""
    print("Testing LMS API...")

    # Use timestamp to make emails unique
    timestamp = int(time.time())

    # Create a tutor
    print("\n1. Creating tutor...")
    tutor = create_user(f"tutor{timestamp}@example.com", "John Tutor", "tutor")
    print(f"Tutor created: {tutor}")
    tutor_id = tutor["id"]

    # Create a student
    print("\n2. Creating student...")
    student = create_user(f"student{timestamp}@example.com", "Jane Student", "student")
    print(f"Student created: {student}")
    student_id = student["id"]

    # Create a course
    print("\n3. Creating course...")
    course_data = {
        "title": "Python Programming",
        "description": "Learn Python from scratch",
        "duration_weeks": 8,
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(weeks=8)).isoformat(),
        "target_audience": "Beginners with no programming experience"
    }

    course = create_course(course_data, tutor_id)
    print(f"Course created: {course['title']} (ID: {course['id']})")
    course_id = course["id"]

    # Add a topic
    print("\n4. Adding topic to course...")
    topic_data = {
        "title": "Introduction to Python",
        "description": "Basic concepts and syntax",
        "order": 1
    }

    course = add_topic(course_id, topic_data, tutor_id)
    topic_id = course["topics"][0]["id"]
    print(f"Topic added: {course['topics'][0]['title']}")

    # Add an assignment
    print("\n5. Adding assignment to topic...")
    assignment_data = {
        "title": "Hello World Program",
        "description": "Write your first Python program",
        "deadline": (datetime.now() + timedelta(days=7)).isoformat()
    }

    course = add_assignment(course_id, topic_id, assignment_data, tutor_id)
    assignment_id = course["topics"][0]["assignments"][0]["id"]
    print(f"Assignment added: {course['topics'][0]['assignments'][0]['title']}")

    # Add a resource to the topic
    print("\n6. Adding resource to topic...")
    resource_data = {
        "title": "Python Documentation",
        "url": "https://docs.python.org/3/"
    }

    course = add_resource(course_id, topic_id, resource_data, tutor_id)
    print(f"Resource added: {course['topics'][0]['resources'][0]['title']}")

    # Publish the course
    print("\n7. Publishing course...")
    course = publish_course(course_id, tutor_id)
    print(f"Course published! Status: {course['status']}")

    # Student enrolls in course
    print("\n8. Student enrolling in course...")
    enrollment = enroll_student(course_id, student_id)
    enrollment_id = enrollment["id"]
    print(f"Enrollment successful! ID: {enrollment_id}")

    # Student submits assignment
    print("\n9. Student submitting assignment...")
    submission = submit_assignment(
        enrollment_id,
        assignment_id,
        "print('Hello, World!')",
        student_id
    )
    print(f"Assignment submitted! Status: {submission['status']}")

    # Tutor evaluates submission
    print("\n10. Tutor evaluating submission...")
    result = evaluate_submission(
        enrollment_id,
        assignment_id,
        95,
        "Excellent work! Your first Python program is excellent.",
        tutor_id
    )
    print("Submission evaluated!")

    # Issue certificate
    print("\n11. Issuing certificate...")
    certificate = issue_certificate(enrollment_id, tutor_id)
    print(f"Certificate issued! ID: {certificate['id']}")

    print("\n All tests passed! The LMS API is working correctly.")

if __name__ == "__main__":
    test_api()
