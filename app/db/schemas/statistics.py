from typing import List, Dict, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class UserStatistics(BaseModel):
    user_uuid: UUID
    user_name: str
    average_grade: float
    attendance_rate: float
    subject_performance: Dict[str, float]
    risk_factors: List[str]
    recommendations: List[str]


class ClassStatistics(BaseModel):
    class_uuid: UUID
    class_name: str
    total_students: int
    average_grade: float
    attendance_rate: float
    subject_performance: Dict[str, float]
    at_risk_students: List[UserStatistics]
    top_performers: List[UserStatistics]
    recommendations: List[str]


class SchoolStatistics(BaseModel):
    school_uuid: UUID
    school_name: str
    total_classes: int
    total_students: int
    average_grade: float
    attendance_rate: float
    subject_performance: Dict[str, float]
    at_risk_classes: List[ClassStatistics]
    top_performing_classes: List[ClassStatistics]
    recommendations: List[str]

    class Config:
        from_attributes = True
