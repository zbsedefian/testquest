# testquest/routers/teacher.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session
from dependencies import get_current_user
from models import TeacherStudent, User, TestResult, Test
from typing import List


class TestResultOut(BaseModel):
    id: int
    student_id: int
    test_id: int
    score: int
    completed_at: str
    test_name: str

router = APIRouter(prefix="/teacher", tags=["teacher"])

@router.get("/students", response_model=List[User])
def get_assigned_students(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.role == "student":
        raise HTTPException(status_code=403, detail="Not authorized")
    students = session.exec(
        select(User)
        .join(TeacherStudent, TeacherStudent.student_id == User.id)
        .where(TeacherStudent.teacher_id == current_user.id)
    ).all()
    return students

@router.get("/student/{student_id}/results", response_model=List[TestResultOut])
def get_student_results(
        student_id: int,
        current_user=Depends(get_current_user),
        session: Session = Depends(get_session),
):
    # Verify teacher is assigned to student
    assignment = session.exec(
        select(TeacherStudent)
        .where(TeacherStudent.teacher_id == current_user.id)
        .where(TeacherStudent.student_id == student_id)
    ).first()

    if not assignment:
        raise HTTPException(status_code=403, detail="Not authorized to view this student's data")

    results = session.exec(
        select(TestResult, Test.name)
        .join(Test, Test.id == TestResult.test_id)
        .where(TestResult.student_id == student_id)
    ).all()

    # Reshape for frontend
    return [
        {
            "id": r[0].id,
            "student_id": r[0].student_id,
            "test_id": r[0].test_id,
            "score": r[0].score,
            "completed_at": r[0].completed_at,
            "test_name": r[1]
        }
        for r in results
    ]