import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.models import User, Student, Grade, Attendance, AttendanceStatus
from app.db.schemas.user import Roles
from app.core.auth import create_access_token

client = TestClient(app)

@pytest.fixture
def test_db(db_session: Session):
    """Create test data"""
    # Create test student
    student_uuid = uuid4()
    student = Student(
        uuid=student_uuid,
        name="Test Student",
        role=Roles.student
    )
    db_session.add(student)
    
    # Create test teacher
    teacher_uuid = uuid4()
    teacher = User(
        uuid=teacher_uuid,
        name="Test Teacher",
        role=Roles.subject_teacher
    )
    db_session.add(teacher)
    
    # Add some grades
    grades = [
        Grade(student_uuid=student_uuid, value=5, subject_uuid=uuid4()),
        Grade(student_uuid=student_uuid, value=4, subject_uuid=uuid4()),
        Grade(student_uuid=student_uuid, value=5, subject_uuid=uuid4())
    ]
    db_session.add_all(grades)
    
    # Add some attendance records
    attendance = [
        Attendance(student_uuid=student_uuid, status=AttendanceStatus.PRESENT),
        Attendance(student_uuid=student_uuid, status=AttendanceStatus.ABSENT),
        Attendance(student_uuid=student_uuid, status=AttendanceStatus.LATE)
    ]
    db_session.add_all(attendance)
    
    db_session.commit()
    return {
        "student_uuid": student_uuid,
        "teacher_uuid": teacher_uuid,
        "db_session": db_session
    }

def test_get_student_statistics_success(test_db):
    """Test successful retrieval of student statistics"""
    # Create access token for teacher
    access_token = create_access_token({"sub": str(test_db["teacher_uuid"])})
    
    response = client.get(
        f"/statistics/student/{test_db['student_uuid']}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check grade distribution
    assert data["grade_distribution"] == {"5": 2, "4": 1}
    
    # Check average grade
    assert data["average_grade"] == 4.67  # (5*2 + 4*1) / 3
    
    # Check attendance stats
    assert data["attendance_stats"] == {
        "present": 1,
        "absent": 1,
        "late": 1
    }
    
    # Check attendance rate
    assert data["attendance_rate"] == 33.3  # 1/3 * 100

def test_get_student_statistics_not_found(test_db):
    """Test getting statistics for non-existent student"""
    access_token = create_access_token({"sub": str(test_db["teacher_uuid"])})
    
    response = client.get(
        f"/statistics/student/{uuid4()}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"

def test_get_student_statistics_unauthorized(test_db):
    """Test getting statistics without authentication"""
    response = client.get(f"/statistics/student/{test_db['student_uuid']}")
    assert response.status_code == 401

def test_get_student_statistics_wrong_student(test_db):
    """Test student trying to access another student's statistics"""
    # Create access token for student
    access_token = create_access_token({"sub": str(test_db["student_uuid"])})
    
    # Try to access another student's statistics
    response = client.get(
        f"/statistics/student/{uuid4()}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 403
    assert response.json()["detail"] == "You can only view your own statistics" 