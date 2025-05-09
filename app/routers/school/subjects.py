from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(
    prefix="/subjects",
    tags=["subjects"]
)

@router.get("/")
async def get_subjects():
    """
    Get all subjects
    """
    # TODO: Implement actual subject retrieval logic
    return {"message": "Subjects endpoint"}

@router.get("/{subject_id}")
async def get_subject(subject_id: int):
    """
    Get a specific subject by ID
    """
    # TODO: Implement actual subject retrieval logic
    return {"message": f"Subject {subject_id} details"} 