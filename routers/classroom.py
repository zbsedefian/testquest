from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from starlette import status

from dependencies import get_current_user
from models import Classroom, ClassroomStudentLink, User, ClassroomTeacherLink, ClassroomTestAssignment, Test
from database import get_session

router = APIRouter()


class ClassroomCreate(BaseModel):
    classroom_name: str
    teacher_ids: list[int]
    student_ids: list[int]

class StudentAssignment(BaseModel):
    student_ids: list[int]


def teacher_required(user=Depends(get_current_user)):
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teachers or admin only")
    return user


@router.post("/classrooms")
def create_classroom(
    payload: ClassroomCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if user.role not in {"admin", "teacher"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or teachers can create classrooms"
        )

    classroom = Classroom(name=payload.classroom_name)
    session.add(classroom)
    session.commit()
    session.refresh(classroom)

    # Link teachers
    teacher_links = [
        ClassroomTeacherLink(classroom_id=classroom.id, teacher_id=tid)
        for tid in payload.teacher_ids
    ]
    session.add_all(teacher_links)

    # Link students
    student_links = [
        ClassroomStudentLink(classroom_id=classroom.id, student_id=sid)
        for sid in payload.student_ids
    ]
    session.add_all(student_links)

    session.commit()
    return classroom


@router.put("/classrooms/{classroom_id}")
def update_classroom(
    classroom_id: int,
    payload: ClassroomCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if user.role not in {"admin", "teacher"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or teachers can update classrooms"
        )

    classroom = session.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    classroom.name = payload.classroom_name
    session.add(classroom)
    session.query(ClassroomTeacherLink).filter_by(classroom_id=classroom.id).delete()
    session.query(ClassroomStudentLink).filter_by(classroom_id=classroom.id).delete()

    teacher_links = [
        ClassroomTeacherLink(classroom_id=classroom.id, teacher_id=tid)
        for tid in payload.teacher_ids
    ]
    student_links = [
        ClassroomStudentLink(classroom_id=classroom.id, student_id=sid)
        for sid in payload.student_ids
    ]

    session.add_all(teacher_links + student_links)
    session.commit()

    return classroom


@router.delete("/classrooms/{classroom_id}")
def delete_classroom(
    classroom_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if user.role not in {"admin", "teacher"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or teachers can delete classrooms"
        )

    classroom = session.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    # Delete relationships first to maintain referential integrity
    session.query(ClassroomTeacherLink).filter_by(classroom_id=classroom_id).delete()
    session.query(ClassroomStudentLink).filter_by(classroom_id=classroom_id).delete()
    session.query(ClassroomTestAssignment).filter_by(classroom_id=classroom_id).delete()

    # Then delete the classroom itself
    session.delete(classroom)
    session.commit()

    return {"message": "Classroom deleted successfully"}


@router.get("/classrooms")
def get_classrooms(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    # Admin: see all classrooms
    if user.role == "admin":
        classrooms = session.exec(select(Classroom)).all()
    # Teacher: see only assigned classrooms
    elif user.role == "teacher":
        teacher_links = session.exec(
            select(ClassroomTeacherLink).where(ClassroomTeacherLink.teacher_id == user.id)
        ).all()
        classroom_ids = [link.classroom_id for link in teacher_links]
        if not classroom_ids:
            return []
        classrooms = session.exec(
            select(Classroom).where(Classroom.id.in_(classroom_ids))
        ).all()
    else:
        raise HTTPException(status_code=403, detail="Unauthorized")

    result = []
    for cls in classrooms:
        teacher_links = session.exec(
            select(ClassroomTeacherLink).where(ClassroomTeacherLink.classroom_id == cls.id)
        ).all()
        student_links = session.exec(
            select(ClassroomStudentLink).where(ClassroomStudentLink.classroom_id == cls.id)
        ).all()

        teachers = [
            session.exec(select(User).where(User.id == link.teacher_id)).first()
            for link in teacher_links
        ]
        students = [
            session.exec(select(User).where(User.id == link.student_id)).first()
            for link in student_links
        ]

        result.append({
            "classroom": cls,
            "teachers": [{"id": t.id, "username": t.username} for t in teachers if t],
            "students": [{"id": s.id, "username": s.username} for s in students if s]
        })

    return result


@router.get("/classrooms/{classroom_id}/tests", response_model=List[Test])
def get_classroom_tests(
    classroom_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    # Permission check
    if user.role not in ("admin", "teacher"):
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Optional: if teacher, check if they are assigned to this classroom
    if user.role == "teacher":
        assigned = session.exec(
            select(Classroom).where(
                Classroom.id == classroom_id
            )
        ).first()

        if not assigned:
            raise HTTPException(status_code=404, detail="Classroom not found")

        teacher_link = session.exec(
            select(ClassroomTeacherLink).where(
                ClassroomTeacherLink.classroom_id == classroom_id,
                ClassroomTeacherLink.teacher_id == user.id,
            )
        ).first()

        if not teacher_link:
            raise HTTPException(status_code=403, detail="Access denied to this classroom")

    # Fetch all test IDs assigned to this classroom
    test_links = session.exec(
        select(ClassroomTestAssignment.test_id).where(
            ClassroomTestAssignment.classroom_id == classroom_id
        )
    ).all()

    test_ids = [row[0] if isinstance(row, tuple) else row for row in test_links]
    if not test_ids:
        return []

    tests = session.exec(select(Test).where(Test.id.in_(test_ids))).all()
    return tests
