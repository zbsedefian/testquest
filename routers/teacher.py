# testquest/routers/teacher.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import TeacherStudent, User, TestResult
from typing import List

router = APIRouter(prefix="/teacher", tags=["teacher"])

@router.get("/students/{teacher_id}", response_model=List[User])
def get_my_students(teacher_id: int, session: Session = Depends(get_session)):
    student_links = session.exec(select(TeacherStudent).where(TeacherStudent.teacher_id == teacher_id)).all()
    student_ids = [s.student_id for s in student_links]
    return session.exec(select(User).where(User.id.in_(student_ids))).all()

@router.get("/results/{student_id}", response_model=List[TestResult])
def get_student_results(student_id: int, session: Session = Depends(get_session)):
    return session.exec(select(TestResult).where(TestResult.student_id == student_id)).all()
