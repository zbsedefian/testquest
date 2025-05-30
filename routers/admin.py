# testquest/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import User, TeacherStudent
from typing import List
from dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/teachers", response_model=List[User])
def list_teachers(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden")
    return session.exec(select(User).where(User.role == "teacher")).all()

@router.get("/students/{teacher_id}", response_model=List[User])
def get_teacher_students(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden")
    links = session.exec(select(TeacherStudent).where(TeacherStudent.teacher_id == teacher_id)).all()
    student_ids = [l.student_id for l in links]
    return session.exec(select(User).where(User.id.in_(student_ids))).all()
