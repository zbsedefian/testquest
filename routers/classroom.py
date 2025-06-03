from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from dependencies import get_current_user
from models import Classroom, ClassroomStudentLink, User, StudentTestAssignment
from database import get_session

router = APIRouter()


class ClassroomCreate(BaseModel):
    name: str

class StudentAssignment(BaseModel):
    student_ids: list[int]


def teacher_required(user=Depends(get_current_user)):
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teachers or admin only")
    return user


@router.post("/classrooms/")
def create_classroom(
    payload: ClassroomCreate,
    user=Depends(teacher_required),
    session: Session = Depends(get_session)
):
    classroom = Classroom(name=payload.name, teacher_id=user.id)
    session.add(classroom)
    session.commit()
    session.refresh(classroom)
    return classroom


@router.get("/classrooms")
def get_classrooms_by_teacher(user=Depends(teacher_required), session: Session = Depends(get_session)):
    statement = select(Classroom).where(Classroom.teacher_id == user.id)
    results = session.exec(statement).all()
    return results


@router.post("/classrooms/{classroom_id}/students")
def assign_students_to_classroom(
    classroom_id: int,
    payload: StudentAssignment,
    session: Session = Depends(get_session),
    user=Depends(teacher_required)
):
    for student_id in payload.student_ids:
        link = ClassroomStudentLink(classroom_id=classroom_id, student_id=student_id)
        session.add(link)
    session.commit()
    return {"message": "Students assigned to classroom."}

