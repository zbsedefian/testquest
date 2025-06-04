from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from dependencies import get_current_user
from models import Classroom, User, ClassroomTeacherLink, ClassroomStudentLink

router = APIRouter()


@router.get("/classrooms-with-users")
def get_classrooms_with_users(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    if user.role != "admin":
        return []

    classrooms = session.exec(select(Classroom)).all()
    classroom_data = []

    for cls in classrooms:
        # Get assigned teachers
        teacher_links = session.exec(
            select(ClassroomTeacherLink).where(ClassroomTeacherLink.classroom_id == cls.id)
        ).all()
        teacher_ids = [link.teacher_id for link in teacher_links]
        teachers = session.exec(select(User).where(User.id.in_(teacher_ids))).all()

        # Get first 5 students and count
        student_links = session.exec(
            select(ClassroomStudentLink).where(ClassroomStudentLink.classroom_id == cls.id)
        ).all()
        student_ids = [link.student_id for link in student_links]
        students = session.exec(select(User).where(User.id.in_(student_ids))).all()
        preview_students = students[:5]

        classroom_data.append({
            "id": cls.id,
            "name": cls.name,
            "teachers": [{"id": t.id, "username": t.username} for t in teachers],
            "students": [{"id": s.id, "username": s.username} for s in preview_students],
            "total_students": len(students)
        })

    return classroom_data


@router.get("/classrooms/{classroom_id}/students")
def get_students_for_classroom(
    classroom_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    links = session.exec(
        select(ClassroomStudentLink).where(ClassroomStudentLink.classroom_id == classroom_id)
    ).all()
    student_ids = [link.student_id for link in links]

    students = session.exec(
        select(User).where(User.id.in_(student_ids))
    ).all()

    return [{"id": s.id, "username": s.username} for s in students]
