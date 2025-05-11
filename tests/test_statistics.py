import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

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

@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        name="Test User",
        role=Roles.student,
        chat_id=123456789
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest.fixture
async def test_attendance(db: AsyncSession, test_user: User) -> Attendance:
    """Create a test attendance record"""
    attendance = Attendance(
        user_uuid=test_user.uuid,
        date=datetime.utcnow(),
        status=AttendanceStatus.PRESENT
    )
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    return attendance

@pytest.fixture
async def test_grade(db: AsyncSession, test_user: User) -> Grade:
    """Create a test grade"""
    grade = Grade(
        user_uuid=test_user.uuid,
        subject_uuid="test-subject-uuid",
        value=4.5
    )
    db.add(grade)
    await db.commit()
    await db.refresh(grade)
    return grade

async def test_get_user_attendance(db: AsyncSession, test_user: User, test_attendance: Attendance):
    """Test getting user attendance statistics"""
    from app.routers.statistics import get_user_attendance

    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()

    result = await get_user_attendance(
        user_id=str(test_user.uuid),
        start_date=start_date,
        end_date=end_date,
        db=db
    )

    assert result["total_days"] == 8  # Including both start and end dates
    assert result["present_count"] == 1
    assert result["absent_count"] == 0
    assert result["late_count"] == 0
    assert result["attendance_rate"] == 12.5  # 1/8 * 100

async def test_get_user_grades(db: AsyncSession, test_user: User, test_grade: Grade):
    """Test getting user grade statistics"""
    from app.routers.statistics import get_user_grades

    result = await get_user_grades(
        user_id=str(test_user.uuid),
        db=db
    )

    assert result["total_grades"] == 1
    assert result["average_grade"] == 4.5
    assert result["min_grade"] == 4.5
    assert result["max_grade"] == 4.5
    assert result["grade_distribution"] == {4.5: 1} 