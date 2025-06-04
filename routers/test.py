from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete
from sqlmodel import Session, select

from dependencies import get_current_user
from models import Classroom, ClassroomStudentLink, User, StudentTestAssignment, Test, ClassroomTeacherLink, \
    ClassroomTestAssignment
from database import get_session

router = APIRouter()


class TestClassroomAssignmentRequest(BaseModel):
    classroom_id: int
    test_id: int

def admin_required(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user


@router.post("/tests/{test_id}/assign-to-classroom/{classroom_id}")
def assign_test_to_classroom(test_id: int, classroom_id: int, session: Session = Depends(get_session)):
    statement = select(ClassroomStudentLink).where(ClassroomStudentLink.classroom_id == classroom_id)
    links = session.exec(statement).all()
    if not links:
        raise HTTPException(status_code=404, detail="No students in classroom.")
    for link in links:
        assignment = StudentTestAssignment(test_id=test_id, student_id=link.student_id)
        session.add(assignment)
    session.commit()
    return {"message": "Test assigned to all students in classroom."}


@router.get("/tests", response_model=List[Test])
def get_all_tests(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if user.role == "admin":
        return session.exec(select(Test)).all()

    if user.role == "teacher":
        # 1. Get classrooms this teacher is assigned to
        class_links = session.exec(
            select(ClassroomTeacherLink).where(ClassroomTeacherLink.teacher_id == user.id)
        ).all()
        classroom_ids = [link.classroom_id for link in class_links]

        # 2. Get all students in those classrooms
        student_links = session.exec(
            select(ClassroomStudentLink).where(ClassroomStudentLink.classroom_id.in_(classroom_ids))
        ).all()
        student_ids = [link.student_id for link in student_links]

        # 3. Get all tests assigned to those students
        assigned_test_ids = session.exec(
            select(StudentTestAssignment.test_id).where(StudentTestAssignment.student_id.in_(student_ids))
        ).all()
        assigned_test_ids = set(assigned_test_ids)  # <-- FIXED HERE

        # 4. Also include tests created by the teacher
        created_tests = session.exec(
            select(Test).where(Test.created_by == user.id)
        ).all()

        # 5. Combine both sets of test IDs
        if assigned_test_ids:
            assigned_tests = session.exec(
                select(Test).where(Test.id.in_(assigned_test_ids))
            ).all()
        else:
            assigned_tests = []

        all_tests = {t.id: t for t in created_tests + assigned_tests}
        return list(all_tests.values())

    raise HTTPException(status_code=403, detail="Unauthorized role")


@router.post("/assign-test-to-classroom")
def assign_test_to_classroom(data: TestClassroomAssignmentRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    # Prevent duplicates
    exists = session.exec(
        select(ClassroomTestAssignment)
        .where(ClassroomTestAssignment.classroom_id == data.classroom_id)
        .where(ClassroomTestAssignment.test_id == data.test_id)
    ).first()
    if not exists:
        session.add(ClassroomTestAssignment(classroom_id=data.classroom_id, test_id=data.test_id))

    # Then assign to students
    student_links = session.exec(
        select(ClassroomStudentLink).where(ClassroomStudentLink.classroom_id == data.classroom_id)
    ).all()
    for link in student_links:
        already = session.exec(
            select(StudentTestAssignment)
            .where(StudentTestAssignment.student_id == link.student_id)
            .where(StudentTestAssignment.test_id == data.test_id)
        ).first()
        if not already:
            session.add(StudentTestAssignment(
                student_id=link.student_id,
                test_id=data.test_id
            ))
    session.commit()
    return {"message": "Assigned successfully"}

@router.get("/tests/{test_id}/assigned-classrooms")
def get_assigned_classrooms(test_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    links = session.exec(
        select(ClassroomTestAssignment).where(ClassroomTestAssignment.test_id == test_id)
    ).all()
    return {"classroom_ids": [link.classroom_id for link in links]}


@router.post("/unassign-test-from-classroom")
def unassign_test(data: TestClassroomAssignmentRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    session.exec(
        delete(ClassroomTestAssignment)
        .where(ClassroomTestAssignment.test_id == data.test_id)
        .where(ClassroomTestAssignment.classroom_id == data.classroom_id)
    )
    # Remove from student assignments
    student_links = session.exec(
        select(ClassroomStudentLink).where(ClassroomStudentLink.classroom_id == data.classroom_id)
    ).all()
    for link in student_links:
        assignment = session.exec(
            select(StudentTestAssignment)
            .where(StudentTestAssignment.student_id == link.student_id)
            .where(StudentTestAssignment.test_id == data.test_id)
        ).first()
        if assignment:
            session.delete(assignment)
    session.commit()
    return {"message": "Unassigned successfully"}
