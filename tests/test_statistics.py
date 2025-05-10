import pytest
from datetime import datetime
from app.db.models import User, Student, Grade, Attendance, AttendanceStatus

def test_get_student_statistics_no_data(client, db_session):
    """Test getting statistics for a student with no data"""
    # Create a test user and student
    user = User(chat_id="123", name="Test User", role="student")
    db_session.add(user)
    db_session.commit()
    
    student = Student(name="Test Student", class_id=1)
    db_session.add(student)
    db_session.commit()
    
    # Make request to statistics endpoint
    response = client.get(f"/statistics/student/{student.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["grade_distribution"] == {}
    assert data["average_grade"] is None
    assert data["attendance_stats"] == {"present": 0, "absent": 0, "late": 0}
    assert data["attendance_rate"] is None

def test_get_student_statistics_with_data(client, db_session):
    """Test getting statistics for a student with grades and attendance"""
    # Create a test user and student
    user = User(chat_id="123", name="Test User", role="student")
    db_session.add(user)
    db_session.commit()
    
    student = Student(name="Test Student", class_id=1)
    db_session.add(student)
    db_session.commit()
    
    # Add some grades
    grades = [
        Grade(student_id=student.id, subject_id=1, value=5),
        Grade(student_id=student.id, subject_id=1, value=4),
        Grade(student_id=student.id, subject_id=2, value=5)
    ]
    db_session.add_all(grades)
    
    # Add some attendance records
    attendance = [
        Attendance(
            student_id=student.id,
            date=datetime.utcnow(),
            status=AttendanceStatus.PRESENT.value
        ),
        Attendance(
            student_id=student.id,
            date=datetime.utcnow(),
            status=AttendanceStatus.ABSENT.value
        ),
        Attendance(
            student_id=student.id,
            date=datetime.utcnow(),
            status=AttendanceStatus.PRESENT.value
        )
    ]
    db_session.add_all(attendance)
    db_session.commit()
    
    # Make request to statistics endpoint
    response = client.get(f"/statistics/student/{student.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check grade distribution
    assert data["grade_distribution"] == {"5": 2, "4": 1}
    assert data["average_grade"] == 4.67  # (5*2 + 4*1) / 3
    
    # Check attendance stats
    assert data["attendance_stats"] == {"present": 2, "absent": 1, "late": 0}
    assert data["attendance_rate"] == 66.67  # (2/3) * 100 